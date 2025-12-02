"""Market integration service.

This module provides a bridge between the backend, market data services, and the trading engine.
It ensures proper data flow between components and standardizes the interfaces.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from functools import lru_cache
import json
import time

from sqlalchemy.orm import Session

# Import backend services and models
from app.models.trade import Trade, TradeStatus, OrderType, OrderSide
from app.models.portfolio import Portfolio, Position
from app.models.user import User
from app.services.market_data import MarketDataService
from app.services.broker.factory import get_resilient_broker
from app.services.order_reconciliation import OrderReconciliationService
from app.core.metrics import metrics
from app.core.config import settings

# Import trading engine components
from trading_engine.strategies.combined_strategy import CombinedStrategy
from trading_engine.strategies.moving_average import MovingAverageStrategy
from trading_engine.data_engine.data_sources import (
    MarketDataSource as TradeEngineDataSource,
    DataSourceConfig
)
from trading_engine.engine.trade_executor import TradeExecutor
from trading_engine.ai_model_engine.market_prediction import MarketPredictionModel
from trading_engine.timeframe_engine.timeframe_converter import TimeframeConverter

logger = logging.getLogger(__name__)


class MarketIntegrationService:
    """
    Integration service that connects the backend, market data services, and trading engine.
    
    This service provides:
    1. Standardized data flow between backend and trading engine
    2. Proper initialization and configuration of trading engine components
    3. Conversion between backend models and trading engine models
    4. Coordinated execution of trading strategies
    5. Market data bridging between systems
    """
    
    def __init__(
        self,
        db: Session,
        market_data_service: Optional[MarketDataService] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the market integration service.
        
        Args:
            db: Database session
            market_data_service: Market data service instance
            config: Configuration parameters
        """
        self.db = db
        self.config = config or {}
        
        # Initialize services
        self.market_data = market_data_service or MarketDataService()
        self.broker = get_resilient_broker(db=db)
        self.order_reconciliation = OrderReconciliationService(db=db)
        
        # Initialize trading engine components
        self.strategies = {}
        self.trade_executor = TradeExecutor(
            broker=self.broker,
            market_data=self._get_trading_engine_data_source(),
            max_slippage_percent=self.config.get("max_slippage_percent", 0.05),
            max_retry_attempts=self.config.get("max_retry_attempts", 3),
            default_order_type=self.config.get("default_order_type", "market")
        )
        
        # Initialize AI prediction models
        self.prediction_models = {}
        self._initialize_prediction_models()
        
        # Initialize timeframe converter
        self.timeframe_converter = TimeframeConverter()
        
        # Metrics and monitoring
        self.last_strategy_run = {}
        self.strategy_performance = {}
        self.integration_errors = 0
        
        logger.info("Market integration service initialized")
        metrics.increment("market_integration.initialized")
    
    def _initialize_prediction_models(self) -> None:
        """Initialize AI prediction models for market forecasting."""
        try:
            # Initialize default prediction model
            self.prediction_models["default"] = MarketPredictionModel(
                model_path=self.config.get("default_model_path"),
                features=self.config.get("default_model_features", ["price", "volume", "rsi", "macd"])
            )
            
            # Initialize specialized models if configured
            if self.config.get("specialized_models"):
                for name, config in self.config["specialized_models"].items():
                    self.prediction_models[name] = MarketPredictionModel(
                        model_path=config.get("model_path"),
                        features=config.get("features", ["price", "volume", "rsi", "macd"])
                    )
            
            logger.info(f"Initialized {len(self.prediction_models)} prediction models")
        except Exception as e:
            logger.error(f"Error initializing prediction models: {str(e)}", exc_info=True)
            # Fallback to basic model
            self.prediction_models["default"] = MarketPredictionModel()
    
    def _get_trading_engine_data_source(self) -> TradeEngineDataSource:
        """Create and configure a trading engine data source.
        
        This bridges the backend market data service with the trading engine.
        """
        # Create a wrapper function that calls our backend market data service
        async def get_market_data(
            symbol: str,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            interval: str = "1d"
        ) -> Dict[str, Any]:
            """Bridge function to get market data from backend service."""
            try:
                if start_date and end_date:
                    # Get historical data
                    data = await self.market_data.get_historical_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval
                    )
                    return data
                else:
                    # Get latest quote
                    data = await self.market_data.get_quote(symbol)
                    return data
            except Exception as e:
                logger.error(f"Error in market data bridge: {str(e)}")
                raise e
        
        # Create data source configuration
        config = DataSourceConfig(
            api_key=settings.ALPHA_VANTAGE_API_KEY,
            cache_dir=self.config.get("cache_dir", "/tmp/market_data_cache"),
            use_cache=self.config.get("use_cache", True),
            max_retries=self.config.get("max_retries", 3),
            timeout=self.config.get("timeout", 30)
        )
        
        # Create and return the trading engine data source
        return TradeEngineDataSource(
            config=config,
            get_data_func=get_market_data
        )
    
    def get_strategy(self, strategy_name: str, risk_level: str = "medium") -> Any:
        """Get a trading strategy instance by name and risk level.
        
        Args:
            strategy_name: Name of the strategy to get
            risk_level: Risk level to configure the strategy with
            
        Returns:
            A strategy instance
        """
        # Create cache key
        cache_key = f"{strategy_name}:{risk_level}"
        
        # Return from cache if exists
        if cache_key in self.strategies:
            return self.strategies[cache_key]
        
        # Create new strategy instance
        if strategy_name == "combined":
            strategy = CombinedStrategy(risk_level=risk_level)
        elif strategy_name == "moving_average":
            strategy = MovingAverageStrategy(risk_level=risk_level)
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        # Cache the strategy
        self.strategies[cache_key] = strategy
        
        return strategy
    
    async def get_market_data_for_symbols(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """Get market data for multiple symbols.
        
        Args:
            symbols: List of symbol tickers
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval (1d, 1h, etc.)
            
        Returns:
            Dictionary with market data for each symbol
        """
        start_time = time.time()
        
        try:
            if start_date and end_date:
                # Get historical data
                tasks = []
                for symbol in symbols:
                    tasks.append(self.market_data.get_historical_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval
                    ))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                data = {}
                for symbol, result in zip(symbols, results):
                    if isinstance(result, Exception):
                        logger.error(f"Error getting historical data for {symbol}: {str(result)}")
                        data[symbol] = {"error": str(result)}
                    else:
                        data[symbol] = result
                
                # Record metrics
                duration = time.time() - start_time
                metrics.timing("market_integration.historical_data", duration * 1000)
                metrics.gauge("market_integration.symbols_count", len(symbols))
                
                return data
            else:
                # Get latest quotes
                data = await self.market_data.get_batch_quotes(symbols)
                
                # Record metrics
                duration = time.time() - start_time
                metrics.timing("market_integration.quotes", duration * 1000)
                metrics.gauge("market_integration.symbols_count", len(symbols))
                
                return data
                
        except Exception as e:
            self.integration_errors += 1
            logger.error(f"Error getting market data: {str(e)}", exc_info=True)
            metrics.increment("market_integration.error")
            raise e
    
    def _convert_portfolio_to_engine_format(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Convert database portfolio model to trading engine format.
        
        Args:
            portfolio: Database portfolio object
            
        Returns:
            Dictionary in trading engine format
        """
        # Get positions for this portfolio
        positions = self.db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        
        # Format for trading engine
        return {
            "portfolio_id": portfolio.id,
            "user_id": portfolio.user_id,
            "cash": float(portfolio.cash_balance),
            "total_value": float(portfolio.total_value),
            "positions": {
                p.symbol: {
                    "quantity": float(p.quantity),
                    "cost_basis": float(p.cost_basis) if p.cost_basis else None,
                    "current_price": float(p.current_price) if p.current_price else None,
                    "last_updated": p.last_updated.isoformat() if p.last_updated else None
                } for p in positions
            }
        }
    
    def _convert_recommendations_to_trades(
        self,
        recommendations: List[Dict[str, Any]],
        user_id: int,
        portfolio_id: int
    ) -> List[Trade]:
        """Convert strategy recommendations to trade objects.
        
        Args:
            recommendations: List of recommendation dictionaries from strategy
            user_id: User ID for the trades
            portfolio_id: Portfolio ID for the trades
            
        Returns:
            List of Trade objects
        """
        trades = []
        
        for rec in recommendations:
            # Create trade object
            trade = Trade(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=rec["symbol"],
                quantity=rec["quantity"],
                price=rec["price"],
                trade_type=rec["action"],
                order_type=OrderType.MARKET,  # Default to market orders
                status=TradeStatus.PENDING,
                requested_by_user_id=None,  # System-generated
                total_amount=rec["quantity"] * rec["price"],
                metadata={
                    "strategy": rec["strategy_name"],
                    "confidence": rec["confidence"],
                    "reason": rec["reason"]
                }
            )
            
            trades.append(trade)
        
        return trades
    
    async def generate_recommendations(
        self,
        user_id: int,
        strategy_name: str = "combined",
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate trade recommendations using trading engine strategies.
        
        Args:
            user_id: User ID to generate recommendations for
            strategy_name: Name of the strategy to use
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        start_time = time.time()
        
        try:
            # Get user and portfolio
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return []
                
            portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
            if not portfolio:
                logger.error(f"Portfolio not found for user: {user_id}")
                return []
            
            # Get strategy instance
            strategy = self.get_strategy(strategy_name, portfolio.risk_profile)
            
            # Get symbols to analyze
            positions = self.db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
            position_symbols = [p.symbol for p in positions]
            
            # Add some common market symbols and potential recommendation candidates
            symbols_to_analyze = list(set(position_symbols + ["SPY", "QQQ", "VTI", "AAPL", "MSFT", "GOOGL", "AMZN"]))
            
            # Get market data in batch
            market_data = await self.get_market_data_for_symbols(symbols_to_analyze)
            
            # Convert portfolio to engine format
            portfolio_data = self._convert_portfolio_to_engine_format(portfolio)
            
            # Generate recommendations from strategy
            recommendations = strategy.get_recommendations(
                portfolio=portfolio_data,
                market_data=market_data
            )
            
            # Log and record metrics
            duration = time.time() - start_time
            rec_count = len(recommendations)
            logger.info(f"Generated {rec_count} recommendations for user {user_id} in {duration:.2f}s")
            
            metrics.timing("market_integration.recommendation_generation", duration * 1000)
            metrics.gauge("market_integration.recommendation_count", rec_count)
            
            # Track strategy run time and performance
            self.last_strategy_run[strategy_name] = datetime.now()
            
            # Limit number of recommendations
            return recommendations[:max_recommendations]
            
        except Exception as e:
            self.integration_errors += 1
            logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
            metrics.increment("market_integration.recommendation_error")
            raise e
    
    async def execute_trades_from_recommendations(
        self,
        user_id: int,
        recommendations: List[Dict[str, Any]]
    ) -> List[Trade]:
        """Execute trades based on recommendations.
        
        Args:
            user_id: User ID to execute trades for
            recommendations: List of recommendation dictionaries
            
        Returns:
            List of created and executed Trade objects
        """
        start_time = time.time()
        
        try:
            # Get user and portfolio
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found: {user_id}")
                return []
                
            portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
            if not portfolio:
                logger.error(f"Portfolio not found for user: {user_id}")
                return []
            
            # Convert recommendations to trades
            trades = self._convert_recommendations_to_trades(
                recommendations=recommendations,
                user_id=user_id,
                portfolio_id=portfolio.id
            )
            
            # Save trades to database
            for trade in trades:
                self.db.add(trade)
            self.db.commit()
            
            # Refresh trades to get IDs
            for trade in trades:
                self.db.refresh(trade)
            
            # Execute trades with trade executor
            executed_trades = []
            for trade in trades:
                try:
                    # Execute the trade
                    result = await self.trade_executor.execute_trade(
                        symbol=trade.symbol,
                        quantity=float(trade.quantity),
                        price=float(trade.price),
                        side=trade.trade_type,
                        order_type=trade.order_type.value,
                        user_id=trade.user_id,
                        portfolio_id=trade.portfolio_id
                    )
                    
                    # Update trade with execution details
                    trade.broker_order_id = result.get("broker_order_id")
                    trade.status = result.get("status")
                    trade.executed_at = datetime.now()
                    
                    # Add to executed trades list
                    executed_trades.append(trade)
                    
                except Exception as e:
                    logger.error(f"Error executing trade {trade.id}: {str(e)}")
                    trade.status = TradeStatus.ERROR
                    trade.rejection_reason = str(e)
            
            # Commit updates
            self.db.commit()
            
            # Log and record metrics
            duration = time.time() - start_time
            logger.info(f"Executed {len(executed_trades)} trades for user {user_id} in {duration:.2f}s")
            
            metrics.timing("market_integration.trade_execution", duration * 1000)
            metrics.gauge("market_integration.executed_trades", len(executed_trades))
            
            return executed_trades
            
        except Exception as e:
            self.integration_errors += 1
            logger.error(f"Error executing trades: {str(e)}", exc_info=True)
            metrics.increment("market_integration.execution_error")
            raise e
    
    async def reconcile_orders(self, max_age_days: int = 30) -> Tuple[int, int]:
        """Reconcile pending orders with broker system.
        
        Args:
            max_age_days: Maximum age of orders to reconcile
            
        Returns:
            Tuple of (updated_count, total_count)
        """
        start_time = time.time()
        
        try:
            # Use order reconciliation service
            updated_count, total_count = self.order_reconciliation.reconcile_pending_trades(max_age_days)
            
            # Log and record metrics
            duration = time.time() - start_time
            logger.info(f"Reconciled {updated_count}/{total_count} trades in {duration:.2f}s")
            
            metrics.timing("market_integration.order_reconciliation", duration * 1000)
            metrics.gauge("market_integration.reconciled_orders", updated_count)
            
            return updated_count, total_count
            
        except Exception as e:
            self.integration_errors += 1
            logger.error(f"Error reconciling orders: {str(e)}", exc_info=True)
            metrics.increment("market_integration.reconciliation_error")
            raise e
    
    async def update_market_prices(self, portfolio_id: int) -> int:
        """Update current market prices for all positions in a portfolio.
        
        Args:
            portfolio_id: Portfolio ID to update
            
        Returns:
            Number of positions updated
        """
        start_time = time.time()
        
        try:
            # Get portfolio positions
            positions = self.db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
            if not positions:
                logger.info(f"No positions found for portfolio {portfolio_id}")
                return 0
            
            # Get symbols
            symbols = [p.symbol for p in positions]
            
            # Get current quotes
            quotes = await self.market_data.get_batch_quotes(symbols)
            
            # Update positions
            updated_count = 0
            for position in positions:
                quote_data = quotes.get(position.symbol)
                if quote_data and "price" in quote_data and quote_data["price"] is not None:
                    # Update position price
                    position.current_price = quote_data["price"]
                    position.last_updated = datetime.now()
                    updated_count += 1
            
            # Update portfolio total value
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if portfolio:
                # Calculate total value of positions
                position_value = sum(p.quantity * p.current_price for p in positions if p.current_price is not None)
                # Add cash balance
                portfolio.total_value = portfolio.cash_balance + position_value
                portfolio.last_updated = datetime.now()
            
            # Commit changes
            self.db.commit()
            
            # Log and record metrics
            duration = time.time() - start_time
            logger.info(f"Updated {updated_count}/{len(positions)} position prices for portfolio {portfolio_id} in {duration:.2f}s")
            
            metrics.timing("market_integration.price_update", duration * 1000)
            metrics.gauge("market_integration.updated_positions", updated_count)
            
            return updated_count
            
        except Exception as e:
            self.integration_errors += 1
            logger.error(f"Error updating market prices: {str(e)}", exc_info=True)
            metrics.increment("market_integration.price_update_error")
            raise e
    
    async def get_prediction(
        self,
        symbol: str,
        prediction_type: str = "price",
        days_ahead: int = 5,
        model_name: str = "default"
    ) -> Dict[str, Any]:
        """Get AI-powered market prediction for a symbol.
        
        Args:
            symbol: Symbol to predict
            prediction_type: Type of prediction (price, trend, volatility)
            days_ahead: Number of days ahead to predict
            model_name: Name of model to use
            
        Returns:
            Dictionary with prediction results
        """
        start_time = time.time()
        
        try:
            # Get model
            model = self.prediction_models.get(model_name)
            if not model:
                logger.error(f"Prediction model not found: {model_name}")
                return {"error": f"Model not found: {model_name}"}
            
            # Get historical data for training/prediction
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Use 90 days of data
            
            historical_data = await self.market_data.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1d"
            )
            
            # Ensure we have data
            if not historical_data or not historical_data.get("data"):
                logger.error(f"No historical data found for {symbol}")
                return {"error": f"No historical data for {symbol}"}
            
            # Generate prediction
            prediction = model.predict(
                data=historical_data["data"],
                symbol=symbol,
                prediction_type=prediction_type,
                days_ahead=days_ahead
            )
            
            # Add metadata
            prediction["generated_at"] = datetime.now().isoformat()
            prediction["model_name"] = model_name
            prediction["symbol"] = symbol
            
            # Log and record metrics
            duration = time.time() - start_time
            logger.info(f"Generated {prediction_type} prediction for {symbol} in {duration:.2f}s")
            
            metrics.timing("market_integration.prediction", duration * 1000)
            metrics.increment("market_integration.prediction_count")
            
            return prediction
            
        except Exception as e:
            self.integration_errors += 1
            logger.error(f"Error generating prediction: {str(e)}", exc_info=True)
            metrics.increment("market_integration.prediction_error")
            return {"error": str(e)}
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of market integration service.
        
        Returns:
            Dictionary with status information
        """
        return {
            "initialized_strategies": list(self.strategies.keys()),
            "initialized_models": list(self.prediction_models.keys()),
            "last_strategy_run": {k: v.isoformat() for k, v in self.last_strategy_run.items()},
            "integration_errors": self.integration_errors,
            "market_data_quality": await self.market_data.get_data_quality_metrics(),
            "timeframes_supported": self.timeframe_converter.get_supported_timeframes(),
        }
    
    async def close(self) -> None:
        """Close all connections and resources."""
        # Close market data service
        if hasattr(self.market_data, "close"):
            await self.market_data.close()
        
        # Close any other resources
        logger.info("Market integration service closed")


def get_market_integration_service(
    db: Session,
    market_data_service: Optional[MarketDataService] = None,
    config: Optional[Dict[str, Any]] = None
) -> MarketIntegrationService:
    """Factory function to get a market integration service instance.
    
    Args:
        db: Database session
        market_data_service: Market data service instance
        config: Configuration parameters
        
    Returns:
        MarketIntegrationService instance
    """
    return MarketIntegrationService(
        db=db,
        market_data_service=market_data_service,
        config=config
    )
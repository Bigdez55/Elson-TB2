"""
Advanced Trading Service

This service integrates the sophisticated trading engine components
including AI/ML models, risk management, and quantum-inspired algorithms.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.ml_models.quantum_models.quantum_classifier import QuantumInspiredClassifier
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.services.market_data import MarketDataService
from trading_engine.engine.circuit_breaker import get_circuit_breaker
from trading_engine.engine.risk_config import RiskProfile, get_risk_config
from trading_engine.engine.trade_executor import TradeExecutor
from trading_engine.strategies.moving_average import MovingAverageStrategy

logger = logging.getLogger(__name__)


class AdvancedTradingService:
    """
    Advanced trading service that combines multiple strategies,
    AI/ML models, and sophisticated risk management.
    """

    def __init__(
        self,
        db: Session,
        market_data_service: MarketDataService,
        risk_profile: RiskProfile = RiskProfile.MODERATE,
    ):
        """
        Initialize the advanced trading service

        Args:
            db: Database session
            market_data_service: Market data service
            risk_profile: Risk profile to use
        """
        self.db = db
        self.market_data_service = market_data_service
        self.risk_profile = risk_profile

        # Initialize risk management
        self.risk_config = get_risk_config(risk_profile)
        self.circuit_breaker = get_circuit_breaker()

        # Initialize strategies
        self.strategies = {}
        self.ai_models = {}

        # Performance tracking
        self.performance_metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "total_return": 0.0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
        }

        logger.info(
            f"Initialized AdvancedTradingService with risk profile: {risk_profile.value}"
        )

    async def initialize_strategies(self, symbols: List[str]) -> None:
        """
        Initialize trading strategies for given symbols

        Args:
            symbols: List of symbols to create strategies for
        """
        try:
            for symbol in symbols:
                # Create moving average strategy
                ma_strategy = MovingAverageStrategy(
                    symbol=symbol,
                    market_data_service=self.market_data_service,
                    short_window=20,
                    long_window=50,
                )

                # Create trade executor for this strategy
                trade_executor = TradeExecutor(
                    market_data_service=self.market_data_service, strategy=ma_strategy
                )

                self.strategies[symbol] = {
                    "strategy": ma_strategy,
                    "executor": trade_executor,
                }

                logger.info(f"Initialized strategy for {symbol}")

            logger.info(f"Initialized strategies for {len(symbols)} symbols")

        except Exception as e:
            logger.error(f"Error initializing strategies: {str(e)}")
            raise

    async def initialize_ai_models(self, symbols: List[str]) -> None:
        """
        Initialize AI/ML models for prediction

        Args:
            symbols: List of symbols to create models for
        """
        try:
            for symbol in symbols:
                # Create quantum-inspired classifier
                quantum_model = QuantumInspiredClassifier(
                    n_features=10, n_qubits=4, learning_rate=0.01, max_iterations=100
                )

                self.ai_models[symbol] = {
                    "quantum_classifier": quantum_model,
                    "is_trained": False,
                    "last_prediction": None,
                    "prediction_confidence": 0.0,
                }

                logger.info(f"Initialized AI models for {symbol}")

            # Train models if we have historical data
            await self._train_ai_models()

        except Exception as e:
            logger.error(f"Error initializing AI models: {str(e)}")
            raise

    async def _train_ai_models(self) -> None:
        """Train AI models using historical data"""
        try:
            for symbol, models in self.ai_models.items():
                logger.info(f"Training AI models for {symbol}...")

                # Get historical data for training
                historical_data = await self._get_training_data(symbol)

                if historical_data is not None and len(historical_data) > 50:
                    # Prepare features and labels
                    X, y = self._prepare_training_data(historical_data)

                    if len(X) > 20:  # Minimum data requirement
                        # Train quantum classifier
                        quantum_model = models["quantum_classifier"]
                        quantum_model.fit(X, y)
                        models["is_trained"] = True

                        training_summary = quantum_model.get_training_summary()
                        logger.info(
                            f"Trained quantum model for {symbol}: {training_summary}"
                        )
                    else:
                        logger.warning(f"Insufficient data for training {symbol} model")
                else:
                    logger.warning(
                        f"No historical data available for training {symbol}"
                    )

        except Exception as e:
            logger.error(f"Error training AI models: {str(e)}")

    async def _get_training_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get historical data for model training"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)  # 1 year of data

            data = await self.market_data_service.get_historical_data(
                symbol, start_date.isoformat(), end_date.isoformat()
            )

            if data:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = data

                # Ensure we have required columns
                if "close" in df.columns and "volume" in df.columns:
                    return df

            return None

        except Exception as e:
            logger.error(f"Error getting training data for {symbol}: {str(e)}")
            return None

    def _prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """Prepare features and labels for ML training"""
        try:
            # Calculate technical indicators as features
            df["price_change"] = df["close"].pct_change()
            df["volume_change"] = df["volume"].pct_change()
            df["sma_5"] = df["close"].rolling(window=5).mean()
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["rsi"] = self._calculate_rsi(df["close"], window=14)
            df["bb_upper"], df["bb_lower"] = self._calculate_bollinger_bands(
                df["close"]
            )
            df["macd"] = self._calculate_macd(df["close"])

            # Create features
            feature_columns = [
                "price_change",
                "volume_change",
                "sma_5",
                "sma_20",
                "rsi",
                "bb_upper",
                "bb_lower",
                "macd",
            ]

            # Add relative position features
            df["price_vs_sma5"] = df["close"] / df["sma_5"] - 1
            df["price_vs_sma20"] = df["close"] / df["sma_20"] - 1
            feature_columns.extend(["price_vs_sma5", "price_vs_sma20"])

            # Create labels (1 if price goes up next day, 0 otherwise)
            df["future_return"] = df["close"].shift(-1) / df["close"] - 1
            df["label"] = (df["future_return"] > 0).astype(int)

            # Remove rows with NaN values
            df = df.dropna()

            if len(df) == 0:
                return np.array([]), np.array([])

            X = df[feature_columns].values
            y = df["label"].values

            return X, y

        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            return np.array([]), np.array([])

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_bollinger_bands(
        self, prices: pd.Series, window: int = 20, num_std: float = 2
    ):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, lower_band

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26
    ) -> pd.Series:
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        return exp1 - exp2

    async def generate_trading_signals(
        self, portfolio: Portfolio
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals for all active strategies

        Args:
            portfolio: Portfolio to trade

        Returns:
            List of trading signals
        """
        signals = []

        try:
            # Check circuit breakers first
            trading_allowed, breaker_status = self.circuit_breaker.check()
            if not trading_allowed:
                logger.warning(
                    f"Trading halted due to circuit breaker: {breaker_status}"
                )
                return signals

            for symbol, strategy_data in self.strategies.items():
                try:
                    # Get current market data
                    market_data = await self.market_data_service.get_quote(symbol)

                    if not market_data:
                        logger.warning(f"No market data available for {symbol}")
                        continue

                    # Generate signal from strategy
                    strategy = strategy_data["strategy"]
                    signal = await strategy.generate_signal(market_data)

                    if signal and signal["action"] != "hold":
                        # Enhance signal with AI prediction if available
                        ai_prediction = await self._get_ai_prediction(
                            symbol, market_data
                        )
                        if ai_prediction:
                            signal["ai_confidence"] = ai_prediction["confidence"]
                            signal["ai_prediction"] = ai_prediction["prediction"]

                            # Combine strategy and AI confidence
                            combined_confidence = (
                                signal["confidence"] + ai_prediction["confidence"]
                            ) / 2
                            signal["combined_confidence"] = combined_confidence

                        # Validate signal
                        if await strategy.validate_signal(signal, market_data):
                            signals.append(
                                {
                                    "symbol": symbol,
                                    "signal": signal,
                                    "strategy_name": strategy.name,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )

                except Exception as e:
                    logger.error(f"Error generating signal for {symbol}: {str(e)}")
                    continue

            logger.info(f"Generated {len(signals)} trading signals")
            return signals

        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            return signals

    async def _get_ai_prediction(
        self, symbol: str, market_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get AI model prediction for a symbol"""
        try:
            if symbol not in self.ai_models:
                return None

            model_data = self.ai_models[symbol]
            if not model_data["is_trained"]:
                return None

            # Prepare current features
            current_features = await self._prepare_current_features(symbol, market_data)
            if current_features is None:
                return None

            # Make prediction
            quantum_model = model_data["quantum_classifier"]
            prediction_proba = quantum_model.predict_proba(
                current_features.reshape(1, -1)
            )

            prediction = prediction_proba[0][1]  # Probability of positive movement
            confidence = max(prediction, 1 - prediction)  # Distance from 0.5

            model_data["last_prediction"] = prediction
            model_data["prediction_confidence"] = confidence

            return {
                "prediction": prediction,
                "confidence": confidence,
                "model_type": "quantum_classifier",
            }

        except Exception as e:
            logger.error(f"Error getting AI prediction for {symbol}: {str(e)}")
            return None

    async def _prepare_current_features(
        self, symbol: str, market_data: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """Prepare current market features for AI prediction"""
        try:
            # Get recent historical data for feature calculation
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            historical_data = await self.market_data_service.get_historical_data(
                symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not historical_data:
                return None

            if isinstance(historical_data, list):
                df = pd.DataFrame(historical_data)
            else:
                df = historical_data

            # Add current data point
            current_row = {
                "close": market_data["price"],
                "volume": market_data.get("volume", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }

            df = pd.concat([df, pd.DataFrame([current_row])], ignore_index=True)

            # Calculate features (same as training)
            X, _ = self._prepare_training_data(df)

            if len(X) > 0:
                return X[-1]  # Return the last (current) feature vector

            return None

        except Exception as e:
            logger.error(f"Error preparing current features for {symbol}: {str(e)}")
            return None

    async def execute_trades(
        self, signals: List[Dict[str, Any]], portfolio: Portfolio
    ) -> List[Trade]:
        """
        Execute trades based on signals

        Args:
            signals: List of trading signals
            portfolio: Portfolio to execute trades for

        Returns:
            List of executed trades
        """
        executed_trades = []

        try:
            for signal_data in signals:
                try:
                    symbol = signal_data["symbol"]
                    signal = signal_data["signal"]

                    if symbol not in self.strategies:
                        logger.warning(f"No strategy found for {symbol}")
                        continue

                    # Get trade executor
                    executor = self.strategies[symbol]["executor"]

                    # Execute the trade
                    trade = await executor.execute_strategy_signal(signal, portfolio)

                    if trade:
                        executed_trades.append(trade)
                        logger.info(
                            f"Executed trade for {symbol}: {trade.side.value} {trade.quantity} shares"
                        )

                        # Update performance metrics
                        self.performance_metrics["total_trades"] += 1

                except Exception as e:
                    logger.error(f"Error executing trade for signal: {str(e)}")
                    continue

            logger.info(f"Executed {len(executed_trades)} trades")
            return executed_trades

        except Exception as e:
            logger.error(f"Error executing trades: {str(e)}")
            return executed_trades

    async def monitor_positions(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Monitor existing positions and risk metrics

        Args:
            portfolio: Portfolio to monitor

        Returns:
            Position monitoring summary
        """
        try:
            monitoring_summary = {
                "total_positions": 0,
                "total_value": 0.0,
                "unrealized_pnl": 0.0,
                "risk_metrics": {},
                "alerts": [],
            }

            # Check portfolio risk limits
            daily_drawdown = portfolio.get_daily_drawdown()
            if daily_drawdown:
                max_daily_drawdown = self.risk_config.get_param(
                    "drawdown_limits.max_daily_drawdown"
                )
                if daily_drawdown > max_daily_drawdown:
                    monitoring_summary["alerts"].append(
                        {
                            "type": "risk_limit_breach",
                            "message": f"Daily drawdown {daily_drawdown:.2%} exceeds limit {max_daily_drawdown:.2%}",
                            "severity": "high",
                        }
                    )

            # Check trade frequency
            daily_trades = portfolio.get_daily_trade_count()
            max_daily_trades = self.risk_config.get_param(
                "trade_limitations.max_trades_per_day"
            )
            if daily_trades >= max_daily_trades:
                monitoring_summary["alerts"].append(
                    {
                        "type": "trade_frequency_limit",
                        "message": f"Daily trade count {daily_trades} at limit {max_daily_trades}",
                        "severity": "medium",
                    }
                )

            monitoring_summary["risk_metrics"] = {
                "daily_drawdown": daily_drawdown,
                "daily_trades": daily_trades,
                "portfolio_value": float(portfolio.total_value),
                "risk_profile": self.risk_profile.value,
            }

            return monitoring_summary

        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")
            return {"error": str(e)}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get trading performance summary"""
        return {
            "performance_metrics": self.performance_metrics,
            "active_strategies": len(self.strategies),
            "trained_ai_models": sum(
                1 for models in self.ai_models.values() if models["is_trained"]
            ),
            "risk_profile": self.risk_profile.value,
            "circuit_breaker_status": self.circuit_breaker.get_status(),
        }

    async def update_risk_profile(self, new_profile: RiskProfile) -> bool:
        """
        Update the risk profile

        Args:
            new_profile: New risk profile to use

        Returns:
            True if successful
        """
        try:
            self.risk_profile = new_profile
            self.risk_config.update_profile(new_profile)

            logger.info(f"Updated risk profile to {new_profile.value}")
            return True

        except Exception as e:
            logger.error(f"Error updating risk profile: {str(e)}")
            return False

"""
Auto Trading Service - Continuously executes trading strategies

This service runs enabled strategies in the background, generating signals
and executing trades automatically based on user-configured parameters.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.services.market_data import MarketDataService
from app.trading_engine.strategies.registry import StrategyRegistry
from app.trading_engine.strategies.base import TradingStrategy
from app.trading_engine.engine.trade_executor import TradeExecutor
from app.trading_engine.engine.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)


class AutoTradingService:
    """
    Manages automated trading by continuously running enabled strategies
    and executing trades based on generated signals.
    """

    _instance = None
    _running_tasks: Dict[int, asyncio.Task] = {}  # user_id -> task
    _active_strategies: Dict[int, Dict[str, TradingStrategy]] = {}  # user_id -> {strategy_name: strategy}
    _market_data_service: Optional[MarketDataService] = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, market_data_service: MarketDataService):
        """Initialize the service with required dependencies"""
        cls._market_data_service = market_data_service
        logger.info("AutoTradingService initialized")

    @classmethod
    async def start_auto_trading(
        cls,
        user_id: int,
        portfolio_id: int,
        strategy_names: List[str],
        symbols: List[str],
        db: Session,
    ) -> bool:
        """
        Start automated trading for a user with specified strategies.

        Args:
            user_id: User ID
            portfolio_id: Portfolio to trade
            strategy_names: List of strategy names to enable
            symbols: List of symbols to trade
            db: Database session

        Returns:
            True if started successfully
        """
        try:
            # Check if already running
            if user_id in cls._running_tasks:
                logger.warning(f"Auto-trading already running for user {user_id}")
                return False

            # Get user and portfolio
            user = db.query(User).filter(User.id == user_id).first()
            portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

            if not user or not portfolio:
                logger.error(f"User {user_id} or portfolio {portfolio_id} not found")
                return False

            # Mark portfolio as having auto-trading enabled
            portfolio.auto_rebalance = True
            db.commit()

            # Create strategy instances
            strategies = {}
            for strategy_name in strategy_names:
                for symbol in symbols:
                    strategy = StrategyRegistry.create(
                        name=strategy_name,
                        symbol=symbol,
                        market_data_service=cls._market_data_service,
                        min_confidence=0.6,  # Configurable
                    )
                    if strategy:
                        key = f"{strategy_name}_{symbol}"
                        strategies[key] = strategy
                        logger.info(f"Created strategy: {key} for user {user_id}")

            if not strategies:
                logger.error(f"No strategies created for user {user_id}")
                return False

            cls._active_strategies[user_id] = strategies

            # Start background task
            task = asyncio.create_task(
                cls._auto_trading_loop(user_id, portfolio_id, db)
            )
            cls._running_tasks[user_id] = task

            logger.info(
                f"Started auto-trading for user {user_id} with {len(strategies)} strategies"
            )
            return True

        except Exception as e:
            logger.error(f"Error starting auto-trading for user {user_id}: {str(e)}")
            return False

    @classmethod
    async def stop_auto_trading(cls, user_id: int, db: Session) -> bool:
        """
        Stop automated trading for a user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            True if stopped successfully
        """
        try:
            # Cancel background task
            if user_id in cls._running_tasks:
                task = cls._running_tasks[user_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del cls._running_tasks[user_id]

            # Clean up strategies
            if user_id in cls._active_strategies:
                strategies = cls._active_strategies[user_id]
                for strategy in strategies.values():
                    strategy.deactivate()
                del cls._active_strategies[user_id]

            # Update portfolio
            portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            for portfolio in portfolios:
                portfolio.auto_rebalance = False
            db.commit()

            logger.info(f"Stopped auto-trading for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping auto-trading for user {user_id}: {str(e)}")
            return False

    @classmethod
    async def _auto_trading_loop(
        cls, user_id: int, portfolio_id: int, db: Session
    ):
        """
        Main loop that continuously generates signals and executes trades.

        Args:
            user_id: User ID
            portfolio_id: Portfolio to trade
            db: Database session
        """
        logger.info(f"Starting auto-trading loop for user {user_id}")

        try:
            while True:
                # Check if market is open
                if not cls._is_market_open():
                    logger.debug(f"Market closed, waiting... (user {user_id})")
                    await asyncio.sleep(60)  # Check every minute
                    continue

                # Get active strategies for this user
                strategies = cls._active_strategies.get(user_id, {})
                if not strategies:
                    logger.warning(f"No active strategies for user {user_id}")
                    break

                # Get portfolio
                portfolio = (
                    db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
                )
                if not portfolio:
                    logger.error(f"Portfolio {portfolio_id} not found")
                    break

                # Check circuit breakers
                circuit_breaker = get_circuit_breaker()
                if not circuit_breaker.check():
                    logger.warning(
                        f"Circuit breaker active, pausing auto-trading for user {user_id}"
                    )
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue

                # Process each strategy
                for strategy_key, strategy in strategies.items():
                    try:
                        await cls._process_strategy(
                            strategy, portfolio, db, user_id
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing strategy {strategy_key}: {str(e)}"
                        )
                        continue

                # Wait before next iteration (configurable - default 30 seconds)
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info(f"Auto-trading loop cancelled for user {user_id}")
            raise
        except Exception as e:
            logger.error(f"Error in auto-trading loop for user {user_id}: {str(e)}")
        finally:
            logger.info(f"Auto-trading loop ended for user {user_id}")

    @classmethod
    async def _process_strategy(
        cls,
        strategy: TradingStrategy,
        portfolio: Portfolio,
        db: Session,
        user_id: int,
    ):
        """
        Process a single strategy: generate signal and execute if valid.

        Args:
            strategy: Trading strategy instance
            portfolio: Portfolio to trade
            db: Database session
            user_id: User ID
        """
        try:
            # Get current market data
            symbol = strategy.symbol
            market_data = await cls._market_data_service.get_quote(symbol)

            if not market_data:
                logger.warning(f"No market data for {symbol}")
                return

            # Generate signal
            signal = await strategy.generate_signal(market_data)

            if not signal or signal.get("action") == "hold":
                logger.debug(f"Strategy {strategy.name} for {symbol}: HOLD")
                return

            # Validate signal
            is_valid = await strategy.validate_signal(signal, market_data)
            if not is_valid:
                logger.debug(
                    f"Signal from {strategy.name} for {symbol} failed validation"
                )
                return

            logger.info(
                f"Valid signal from {strategy.name} for {symbol}: "
                f"{signal['action']} (confidence: {signal['confidence']:.2f})"
            )

            # Create trade executor
            executor = TradeExecutor(
                market_data_service=cls._market_data_service,
                strategy=strategy,
            )

            # Execute the trade
            trade = await executor.execute_strategy_signal(signal, portfolio)

            if trade:
                # Save trade to database
                db.add(trade)
                db.commit()

                logger.info(
                    f"Trade executed: {trade.side.value} {trade.quantity} "
                    f"{trade.symbol} @ ${trade.price}"
                )

                # Update strategy performance
                strategy.last_signal_time = datetime.utcnow()

        except Exception as e:
            logger.error(
                f"Error processing strategy {strategy.name} for {strategy.symbol}: {str(e)}"
            )

    @classmethod
    def _is_market_open(cls) -> bool:
        """Check if the market is currently open"""
        now = datetime.utcnow()

        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        # Check market hours (9:30 AM - 4:00 PM ET)
        # Simplified - would use proper timezone handling in production
        et_hour = (now.hour - 4) % 24

        if et_hour < 9 or et_hour >= 16:
            return False

        if et_hour == 9 and now.minute < 30:
            return False

        return True

    @classmethod
    def get_active_strategies(cls, user_id: int) -> Dict[str, Dict]:
        """
        Get information about active strategies for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary of strategy info
        """
        strategies = cls._active_strategies.get(user_id, {})

        return {
            strategy_key: {
                "name": strategy.name,
                "symbol": strategy.symbol,
                "is_active": strategy.is_active,
                "last_signal_time": strategy.last_signal_time,
                "performance": strategy.get_performance_summary(),
            }
            for strategy_key, strategy in strategies.items()
        }

    @classmethod
    def is_auto_trading_active(cls, user_id: int) -> bool:
        """Check if auto-trading is active for a user"""
        return user_id in cls._running_tasks

    @classmethod
    async def add_strategy(
        cls,
        user_id: int,
        strategy_name: str,
        symbol: str,
        parameters: Optional[Dict] = None,
    ) -> bool:
        """
        Add a new strategy to an active auto-trading session.

        Args:
            user_id: User ID
            strategy_name: Name of strategy to add
            symbol: Trading symbol
            parameters: Optional strategy parameters

        Returns:
            True if added successfully
        """
        try:
            if user_id not in cls._active_strategies:
                logger.error(f"Auto-trading not active for user {user_id}")
                return False

            strategy = StrategyRegistry.create(
                name=strategy_name,
                symbol=symbol,
                market_data_service=cls._market_data_service,
                **(parameters or {}),
            )

            if not strategy:
                logger.error(f"Failed to create strategy: {strategy_name}")
                return False

            key = f"{strategy_name}_{symbol}"
            cls._active_strategies[user_id][key] = strategy

            logger.info(f"Added strategy {key} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding strategy: {str(e)}")
            return False

    @classmethod
    async def remove_strategy(
        cls, user_id: int, strategy_name: str, symbol: str
    ) -> bool:
        """
        Remove a strategy from an active auto-trading session.

        Args:
            user_id: User ID
            strategy_name: Name of strategy to remove
            symbol: Trading symbol

        Returns:
            True if removed successfully
        """
        try:
            if user_id not in cls._active_strategies:
                return False

            key = f"{strategy_name}_{symbol}"
            strategies = cls._active_strategies[user_id]

            if key in strategies:
                strategy = strategies[key]
                strategy.deactivate()
                del strategies[key]

                logger.info(f"Removed strategy {key} for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error removing strategy: {str(e)}")
            return False


# Initialize on module load
def initialize_auto_trading_service(market_data_service: MarketDataService):
    """Initialize the auto trading service"""
    AutoTradingService.initialize(market_data_service)
    return AutoTradingService()

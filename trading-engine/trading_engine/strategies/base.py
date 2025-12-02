import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TradingStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    This class defines the interface that all trading strategies must implement
    to work with the trading engine. It provides common functionality for
    position sizing, risk management, and performance tracking.
    """

    def __init__(
        self,
        symbol: str,
        name: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the trading strategy

        Args:
            symbol: Primary symbol this strategy trades
            name: Human-readable name for the strategy
            description: Description of the strategy
            parameters: Strategy-specific parameters
        """
        self.symbol = symbol
        self.name = name
        self.description = description
        self.parameters = parameters or {}

        # Performance tracking
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
        }

        # Strategy state
        self.is_active = True
        self.last_signal_time = None
        self.current_position = 0.0

        logger.info(f"Initialized strategy: {self.name} for symbol: {self.symbol}")

    @abstractmethod
    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a trading signal based on market data

        Args:
            market_data: Dictionary containing current market data

        Returns:
            Dictionary with signal information:
            {
                'action': 'buy' | 'sell' | 'hold',
                'confidence': float (0-1),
                'price': float,
                'stop_loss': float (optional),
                'take_profit': float (optional),
                'reason': str (optional explanation)
            }
        """
        pass

    @abstractmethod
    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """
        Update strategy parameters

        Args:
            new_parameters: Dictionary of new parameter values

        Returns:
            True if update successful, False otherwise
        """
        pass

    async def calculate_position_size(
        self,
        portfolio_value: float,
        current_price: float,
        confidence: float,
        volatility: Optional[float] = None,
    ) -> float:
        """
        Calculate the position size for a trade based on risk management rules

        Args:
            portfolio_value: Total portfolio value
            current_price: Current price of the asset
            confidence: Signal confidence (0-1)
            volatility: Current volatility measure (optional)

        Returns:
            Position size in number of shares/units
        """
        try:
            # Get risk parameters from strategy config
            max_position_pct = self.parameters.get(
                "max_position_pct", 0.05
            )  # 5% default
            base_position_pct = self.parameters.get(
                "base_position_pct", 0.02
            )  # 2% default
            confidence_multiplier = self.parameters.get("confidence_multiplier", 1.5)

            # Calculate base position size
            position_pct = base_position_pct * confidence * confidence_multiplier

            # Apply volatility adjustment if available
            if volatility is not None:
                if volatility > 0.3:  # High volatility
                    position_pct *= 0.5
                elif volatility > 0.2:  # Medium volatility
                    position_pct *= 0.75
                # Low volatility - no adjustment

            # Cap at maximum position size
            position_pct = min(position_pct, max_position_pct)

            # Convert to position value and then to shares
            position_value = portfolio_value * position_pct
            position_size = position_value / current_price

            logger.debug(
                f"Calculated position size: {position_size:.4f} shares "
                f"(${position_value:.2f}, {position_pct:.2%} of portfolio)"
            )

            return position_size
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    async def validate_signal(
        self, signal: Dict[str, Any], market_data: Dict[str, Any]
    ) -> bool:
        """
        Validate a trading signal before execution

        Args:
            signal: Trading signal to validate
            market_data: Current market data

        Returns:
            True if signal is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ["action", "confidence", "price"]
            for field in required_fields:
                if field not in signal:
                    logger.warning(f"Signal missing required field: {field}")
                    return False

            # Validate action
            valid_actions = ["buy", "sell", "hold"]
            if signal["action"] not in valid_actions:
                logger.warning(f"Invalid action: {signal['action']}")
                return False

            # Validate confidence
            if not 0 <= signal["confidence"] <= 1:
                logger.warning(f"Invalid confidence: {signal['confidence']}")
                return False

            # Validate price
            if signal["price"] <= 0:
                logger.warning(f"Invalid price: {signal['price']}")
                return False

            # Check minimum confidence threshold
            min_confidence = self.parameters.get("min_confidence", 0.3)
            if signal["confidence"] < min_confidence:
                logger.debug(
                    f"Signal confidence {signal['confidence']:.2f} below threshold {min_confidence:.2f}"
                )
                return False

            # Strategy-specific validation
            return await self._custom_validation(signal, market_data)
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False

    async def _custom_validation(
        self, signal: Dict[str, Any], market_data: Dict[str, Any]
    ) -> bool:
        """
        Custom validation logic for specific strategies
        Override in subclasses for strategy-specific validation
        """
        return True

    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """
        Update strategy performance metrics

        Args:
            trade_result: Dictionary containing trade outcome information
        """
        try:
            self.performance_metrics["total_trades"] += 1

            pnl = trade_result.get("pnl", 0.0)
            self.performance_metrics["total_return"] += pnl

            if pnl > 0:
                self.performance_metrics["winning_trades"] += 1
            elif pnl < 0:
                self.performance_metrics["losing_trades"] += 1

            # Update win rate
            total_trades = self.performance_metrics["total_trades"]
            if total_trades > 0:
                self.performance_metrics["win_rate"] = (
                    self.performance_metrics["winning_trades"] / total_trades
                )

            # Update max drawdown if necessary
            current_drawdown = trade_result.get("drawdown", 0.0)
            if current_drawdown > self.performance_metrics["max_drawdown"]:
                self.performance_metrics["max_drawdown"] = current_drawdown

            logger.debug(
                f"Updated performance for {self.name}: Win rate: {self.performance_metrics['win_rate']:.2%}"
            )
        except Exception as e:
            logger.error(f"Error updating performance: {str(e)}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of strategy performance

        Returns:
            Dictionary with performance metrics
        """
        return {
            "strategy_name": self.name,
            "symbol": self.symbol,
            "total_trades": self.performance_metrics["total_trades"],
            "win_rate": self.performance_metrics["win_rate"],
            "total_return": self.performance_metrics["total_return"],
            "max_drawdown": self.performance_metrics["max_drawdown"],
            "sharpe_ratio": self.performance_metrics["sharpe_ratio"],
            "is_active": self.is_active,
            "last_signal_time": self.last_signal_time,
        }

    def activate(self) -> None:
        """Activate the strategy"""
        self.is_active = True
        logger.info(f"Activated strategy: {self.name}")

    def deactivate(self) -> None:
        """Deactivate the strategy"""
        self.is_active = False
        logger.info(f"Deactivated strategy: {self.name}")

    def reset_performance(self) -> None:
        """Reset all performance metrics"""
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
        }
        logger.info(f"Reset performance metrics for strategy: {self.name}")

    async def on_market_open(self) -> None:
        """
        Called when the market opens
        Override in subclasses for market open logic
        """
        pass

    async def on_market_close(self) -> None:
        """
        Called when the market closes
        Override in subclasses for market close logic
        """
        pass

    async def on_position_update(self, new_position: float) -> None:
        """
        Called when position is updated

        Args:
            new_position: New position size
        """
        self.current_position = new_position
        logger.debug(f"Position updated for {self.name}: {new_position}")

    def __str__(self) -> str:
        return f"TradingStrategy(name={self.name}, symbol={self.symbol}, active={self.is_active})"

    def __repr__(self) -> str:
        return self.__str__()

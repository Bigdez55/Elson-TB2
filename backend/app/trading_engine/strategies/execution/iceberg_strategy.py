"""
Iceberg Order Execution Strategy

Breaks large orders into smaller visible portions to minimize market impact
while maintaining a consistent presence in the order book.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..base import TradingStrategy
from ..registry import StrategyCategory, StrategyRegistry

logger = logging.getLogger(__name__)


@StrategyRegistry.register(
    name="iceberg_execution",
    category=StrategyCategory.EXECUTION,
    description="Iceberg order execution for large positions",
    default_parameters={
        "total_quantity": 10000,
        "display_quantity": 100,  # Visible portion
        "randomize_display": True,
        "display_variance": 0.3,  # +/- 30% variation
        "refresh_delay_seconds": 1,  # Delay between refreshes
        "price_limit": None,
        "use_limit_orders": True,
        "limit_offset_pct": 0.001,  # 0.1% from mid
        "adaptive_sizing": True,
    },
    required_data=["close", "bid", "ask"],
    timeframes=["1m"],
    risk_level="low",
)
class IcebergExecutionStrategy(TradingStrategy):
    """
    Iceberg Order Execution Strategy

    Hides the true size of a large order by showing only a small
    portion at a time, refreshing as each slice is filled.

    Features:
    - Configurable display size
    - Randomized display quantity
    - Adaptive sizing based on market
    - Price limit support
    - Limit order placement
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: Any = None,
        total_quantity: float = 10000,
        display_quantity: float = 100,
        randomize_display: bool = True,
        display_variance: float = 0.3,
        refresh_delay_seconds: float = 1,
        price_limit: Optional[float] = None,
        use_limit_orders: bool = True,
        limit_offset_pct: float = 0.001,
        adaptive_sizing: bool = True,
        side: str = "buy",
        **kwargs,
    ):
        super().__init__(
            symbol=symbol,
            name="Iceberg Execution",
            description="Hidden large order execution",
            parameters={
                "total_quantity": total_quantity,
                "display_quantity": display_quantity,
                "randomize_display": randomize_display,
                "display_variance": display_variance,
                "refresh_delay_seconds": refresh_delay_seconds,
                "price_limit": price_limit,
                "use_limit_orders": use_limit_orders,
                "limit_offset_pct": limit_offset_pct,
                "adaptive_sizing": adaptive_sizing,
                "side": side,
            },
        )
        self.market_data_service = market_data_service
        self.total_quantity = total_quantity
        self.display_quantity = display_quantity
        self.randomize_display = randomize_display
        self.display_variance = display_variance
        self.refresh_delay_seconds = refresh_delay_seconds
        self.price_limit = price_limit
        self.use_limit_orders = use_limit_orders
        self.limit_offset_pct = limit_offset_pct
        self.adaptive_sizing = adaptive_sizing
        self.side = side

        # Execution state
        self.executed_quantity: float = 0.0
        self.executed_value: float = 0.0
        self.current_display_quantity: float = 0.0
        self.last_refresh_time: Optional[datetime] = None
        self.current_order_id: Optional[str] = None
        self.execution_complete: bool = False
        self.slice_count: int = 0
        self.start_time: Optional[datetime] = None

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate iceberg execution signal"""
        try:
            current_price = market_data.get("price", 0.0)
            bid = market_data.get("bid", current_price * 0.999)
            ask = market_data.get("ask", current_price * 1.001)
            current_time = datetime.utcnow()

            if current_price <= 0:
                return self._create_hold_signal(0.0, "Invalid price")

            # Initialize if needed
            if self.start_time is None:
                self.start_time = current_time

            # Check if execution is complete
            if self.execution_complete:
                return self._create_completion_signal(current_price)

            remaining = self.total_quantity - self.executed_quantity
            if remaining <= 0:
                self.execution_complete = True
                return self._create_completion_signal(current_price)

            # Check price limit
            if not self._check_price_limit(current_price):
                return self._create_hold_signal(
                    current_price, f"Price {current_price:.2f} beyond limit"
                )

            # Check if we need to refresh the display order
            should_refresh = self._should_refresh_order(current_time)

            if not should_refresh:
                return self._create_hold_signal(
                    current_price, "Order active, waiting for fill"
                )

            # Calculate display quantity for this slice
            display_qty = self._calculate_display_quantity(market_data, remaining)

            # Calculate limit price if using limit orders
            if self.use_limit_orders:
                if self.side == "buy":
                    # Place bid slightly below ask
                    limit_price = ask * (1 - self.limit_offset_pct)
                else:
                    # Place ask slightly above bid
                    limit_price = bid * (1 + self.limit_offset_pct)
            else:
                limit_price = None

            # Apply price limit
            if self.price_limit:
                if self.side == "buy" and limit_price:
                    limit_price = min(limit_price, self.price_limit)
                elif self.side == "sell" and limit_price:
                    limit_price = max(limit_price, self.price_limit)

            self.current_display_quantity = display_qty
            self.last_refresh_time = current_time
            self.slice_count += 1

            # Calculate metrics
            avg_price = (
                self.executed_value / self.executed_quantity
                if self.executed_quantity > 0
                else current_price
            )
            progress = self.executed_quantity / self.total_quantity

            reasons = [
                f"Iceberg slice {self.slice_count}",
                f"Display: {display_qty:.0f} of {remaining:.0f} remaining",
                f"Progress: {progress:.1%}",
            ]

            signal = {
                "action": self.side,
                "confidence": 0.85,
                "price": limit_price or current_price,
                "timestamp": current_time.isoformat(),
                "reason": "; ".join(reasons),
                "order_quantity": display_qty,
                "order_type": "limit" if self.use_limit_orders else "market",
                "indicators": {
                    "display_quantity": display_qty,
                    "hidden_quantity": remaining - display_qty,
                    "total_quantity": self.total_quantity,
                    "executed_quantity": self.executed_quantity,
                    "remaining_quantity": remaining,
                    "average_price": avg_price,
                    "limit_price": limit_price,
                    "slice_count": self.slice_count,
                    "execution_progress": progress,
                    "bid": bid,
                    "ask": ask,
                    "spread": ask - bid,
                },
            }

            self.last_signal_time = current_time
            return signal

        except Exception as e:
            logger.error(f"Error in iceberg execution: {str(e)}")
            return self._create_hold_signal(
                market_data.get("price", 0.0), f"Error: {str(e)}"
            )

    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """Update strategy parameters"""
        try:
            for key, value in new_parameters.items():
                if key in self.parameters:
                    self.parameters[key] = value
                    if hasattr(self, key):
                        setattr(self, key, value)
            return True
        except Exception:
            return False

    def _should_refresh_order(self, current_time: datetime) -> bool:
        """Check if we need to place a new display order"""
        # First order
        if self.last_refresh_time is None:
            return True

        # Check refresh delay
        time_since_refresh = (current_time - self.last_refresh_time).total_seconds()
        return time_since_refresh >= self.refresh_delay_seconds

    def _calculate_display_quantity(
        self, market_data: Dict[str, Any], remaining: float
    ) -> float:
        """Calculate the display quantity for next slice"""
        base_qty = self.display_quantity

        # Adaptive sizing based on market conditions
        if self.adaptive_sizing:
            volume = market_data.get("volume", 0)
            if volume > 0:
                # Scale display size with volume
                volume_factor = min(2.0, max(0.5, volume / 10000))
                base_qty *= volume_factor

            # Reduce size if spread is wide
            bid = market_data.get("bid", 0)
            ask = market_data.get("ask", 0)
            if bid > 0 and ask > 0:
                spread_pct = (ask - bid) / bid
                if spread_pct > 0.002:  # > 0.2% spread
                    base_qty *= 0.7

        # Apply randomization
        if self.randomize_display:
            variance = random.uniform(-self.display_variance, self.display_variance)
            base_qty *= 1 + variance

        # Cap at remaining
        display_qty = min(base_qty, remaining)

        # Ensure minimum size (at least 1 share)
        display_qty = max(1, round(display_qty))

        return display_qty

    def _check_price_limit(self, current_price: float) -> bool:
        """Check if current price is within limit"""
        if self.price_limit is None:
            return True

        if self.side == "buy":
            return current_price <= self.price_limit
        else:
            return current_price >= self.price_limit

    def record_fill(self, quantity: float, price: float) -> None:
        """Record a partial or complete fill"""
        self.executed_quantity += quantity
        self.executed_value += quantity * price

        logger.debug(
            f"Iceberg fill: {quantity} @ {price:.2f}, "
            f"Total: {self.executed_quantity}/{self.total_quantity}"
        )

        if self.executed_quantity >= self.total_quantity:
            self.execution_complete = True
            logger.info(f"Iceberg execution complete: {self.slice_count} slices")

    def record_order_placed(self, order_id: str) -> None:
        """Record that a new display order was placed"""
        self.current_order_id = order_id

    def cancel_current_order(self) -> Optional[str]:
        """Get current order ID for cancellation"""
        return self.current_order_id

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution performance summary"""
        avg_price = (
            self.executed_value / self.executed_quantity
            if self.executed_quantity > 0
            else 0
        )

        execution_time = None
        if self.start_time and self.execution_complete:
            execution_time = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "symbol": self.symbol,
            "side": self.side,
            "total_quantity": self.total_quantity,
            "executed_quantity": self.executed_quantity,
            "remaining_quantity": self.total_quantity - self.executed_quantity,
            "executed_value": self.executed_value,
            "average_price": avg_price,
            "slice_count": self.slice_count,
            "average_slice_size": (
                self.executed_quantity / self.slice_count if self.slice_count > 0 else 0
            ),
            "execution_complete": self.execution_complete,
            "execution_time_seconds": execution_time,
        }

    def _create_completion_signal(self, price: float) -> Dict[str, Any]:
        """Create signal for completed execution"""
        summary = self.get_execution_summary()

        return {
            "action": "hold",
            "confidence": 1.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": f"Iceberg complete: {summary['slice_count']} slices",
            "indicators": {
                "execution_complete": True,
                "executed_quantity": summary["executed_quantity"],
                "average_price": summary["average_price"],
                "slice_count": summary["slice_count"],
            },
        }

    def _create_hold_signal(self, price: float, reason: str) -> Dict[str, Any]:
        """Create hold signal"""
        return {
            "action": "hold",
            "confidence": 0.0,
            "price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "indicators": {
                "executed_quantity": self.executed_quantity,
                "remaining_quantity": self.total_quantity - self.executed_quantity,
                "current_display": self.current_display_quantity,
                "slice_count": self.slice_count,
            },
        }

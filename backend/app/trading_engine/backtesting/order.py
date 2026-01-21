"""
Order Management for Backtesting

Defines order types, statuses, and order execution logic.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderType(Enum):
    """Order types"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order side"""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order statuses"""

    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """
    Represents a trading order in the backtest.
    """

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    trailing_pct: Optional[float] = None

    # Auto-generated fields
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: OrderStatus = OrderStatus.PENDING

    # Execution fields
    filled_quantity: float = 0.0
    average_fill_price: float = 0.0
    filled_at: Optional[datetime] = None
    commission: float = 0.0
    slippage: float = 0.0

    # Stop management
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None

    # Strategy reference
    strategy_name: Optional[str] = None
    signal_id: Optional[str] = None

    @property
    def remaining_quantity(self) -> float:
        """Get unfilled quantity"""
        return self.quantity - self.filled_quantity

    @property
    def is_complete(self) -> bool:
        """Check if order is complete (filled or terminal state)"""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        ]

    @property
    def fill_value(self) -> float:
        """Total value of filled portion"""
        return self.filled_quantity * self.average_fill_price

    def fill(
        self,
        quantity: float,
        price: float,
        timestamp: datetime,
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        """
        Fill the order (partially or fully).

        Args:
            quantity: Quantity to fill
            price: Fill price
            timestamp: Fill timestamp
            commission: Commission for this fill
            slippage: Slippage amount
        """
        fill_quantity = min(quantity, self.remaining_quantity)

        if fill_quantity <= 0:
            return

        # Update average fill price
        total_value = (self.filled_quantity * self.average_fill_price) + (
            fill_quantity * price
        )
        self.filled_quantity += fill_quantity
        self.average_fill_price = total_value / self.filled_quantity

        self.commission += commission
        self.slippage += slippage
        self.filled_at = timestamp

        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self) -> None:
        """Cancel the order"""
        if not self.is_complete:
            self.status = OrderStatus.CANCELLED

    def reject(self, reason: str = "") -> None:
        """Reject the order"""
        self.status = OrderStatus.REJECTED

    def can_fill_at_price(self, current_price: float, high: float, low: float) -> bool:
        """
        Check if order can be filled at given price bar.

        Args:
            current_price: Current/close price
            high: High price of bar
            low: Low price of bar

        Returns:
            True if order can be filled
        """
        if self.order_type == OrderType.MARKET:
            return True

        elif self.order_type == OrderType.LIMIT:
            if self.side == OrderSide.BUY:
                return low <= self.limit_price
            else:
                return high >= self.limit_price

        elif self.order_type == OrderType.STOP:
            if self.side == OrderSide.BUY:
                return high >= self.stop_price
            else:
                return low <= self.stop_price

        elif self.order_type == OrderType.STOP_LIMIT:
            # Stop must be triggered first, then limit checked
            if self.side == OrderSide.BUY:
                stop_triggered = high >= self.stop_price
                limit_ok = low <= self.limit_price
            else:
                stop_triggered = low <= self.stop_price
                limit_ok = high >= self.limit_price
            return stop_triggered and limit_ok

        return False

    def get_fill_price(self, current_price: float, slippage_pct: float = 0.0) -> float:
        """
        Calculate fill price with slippage.

        Args:
            current_price: Current market price
            slippage_pct: Slippage percentage

        Returns:
            Fill price after slippage
        """
        if self.order_type == OrderType.LIMIT:
            # Limit orders fill at limit or better
            if self.side == OrderSide.BUY:
                return min(current_price, self.limit_price)
            else:
                return max(current_price, self.limit_price)

        elif self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            # Stop orders may have slippage from stop price
            base_price = self.stop_price
        else:
            base_price = current_price

        # Apply slippage
        if self.side == OrderSide.BUY:
            return base_price * (1 + slippage_pct)
        else:
            return base_price * (1 - slippage_pct)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "order_type": self.order_type.value,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "average_fill_price": self.average_fill_price,
            "commission": self.commission,
            "slippage": self.slippage,
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "strategy_name": self.strategy_name,
        }

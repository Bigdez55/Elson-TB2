"""
Portfolio Management for Backtesting

Tracks positions, cash, and portfolio value throughout the backtest.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .order import Order, OrderSide, OrderStatus

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a position in a single security"""
    symbol: str
    quantity: float = 0.0
    average_cost: float = 0.0
    current_price: float = 0.0
    realized_pnl: float = 0.0

    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss"""
        return (self.current_price - self.average_cost) * self.quantity

    @property
    def total_pnl(self) -> float:
        """Total profit/loss (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def cost_basis(self) -> float:
        """Total cost basis"""
        return self.quantity * self.average_cost

    @property
    def return_pct(self) -> float:
        """Return percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def update_price(self, price: float) -> None:
        """Update current price"""
        self.current_price = price

    def add(self, quantity: float, price: float) -> None:
        """Add to position (buy)"""
        if quantity <= 0:
            return

        total_cost = (self.quantity * self.average_cost) + (quantity * price)
        self.quantity += quantity
        self.average_cost = total_cost / self.quantity if self.quantity > 0 else 0
        self.current_price = price

    def reduce(self, quantity: float, price: float) -> float:
        """
        Reduce position (sell).

        Returns:
            Realized P&L from this sale
        """
        if quantity <= 0 or self.quantity <= 0:
            return 0.0

        sell_quantity = min(quantity, self.quantity)
        realized = (price - self.average_cost) * sell_quantity

        self.quantity -= sell_quantity
        self.realized_pnl += realized
        self.current_price = price

        return realized

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "return_pct": self.return_pct,
        }


@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time"""
    timestamp: datetime
    cash: float
    positions_value: float
    total_value: float
    realized_pnl: float
    unrealized_pnl: float
    positions: Dict[str, dict] = field(default_factory=dict)


class Portfolio:
    """
    Portfolio manager for backtesting.

    Tracks cash, positions, and provides portfolio analytics.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,  # 0.1%
        slippage_rate: float = 0.0005,  # 0.05%
        margin_requirement: float = 1.0,  # 1.0 = no margin
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.margin_requirement = margin_requirement

        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.filled_orders: List[Order] = []
        self.trades: List[Dict[str, Any]] = []
        self.snapshots: List[PortfolioSnapshot] = []

        self._current_timestamp: Optional[datetime] = None

    @property
    def positions_value(self) -> float:
        """Total value of all positions"""
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)"""
        return self.cash + self.positions_value

    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L"""
        return sum(p.unrealized_pnl for p in self.positions.values())

    @property
    def realized_pnl(self) -> float:
        """Total realized P&L"""
        return sum(p.realized_pnl for p in self.positions.values())

    @property
    def total_return(self) -> float:
        """Total return percentage"""
        return ((self.total_value - self.initial_capital) / self.initial_capital) * 100

    @property
    def buying_power(self) -> float:
        """Available buying power"""
        return self.cash / self.margin_requirement

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if we have a position in symbol"""
        pos = self.positions.get(symbol)
        return pos is not None and pos.quantity > 0

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices for all positions"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)

    def submit_order(self, order: Order) -> bool:
        """
        Submit an order to the portfolio.

        Args:
            order: Order to submit

        Returns:
            True if order was accepted
        """
        # Validate order
        if order.quantity <= 0:
            order.reject("Invalid quantity")
            return False

        # Check buying power for buys
        if order.side == OrderSide.BUY:
            estimated_cost = order.quantity * (order.limit_price or order.stop_price or 0)
            if estimated_cost > self.buying_power:
                order.reject("Insufficient buying power")
                return False

        # Check position for sells
        if order.side == OrderSide.SELL:
            position = self.get_position(order.symbol)
            if not position or position.quantity < order.quantity:
                order.reject("Insufficient position")
                return False

        order.status = OrderStatus.OPEN
        self.orders.append(order)
        return True

    def execute_order(
        self,
        order: Order,
        fill_price: float,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Execute a filled order.

        Args:
            order: Order to execute
            fill_price: Execution price
            timestamp: Execution timestamp

        Returns:
            Trade details
        """
        # Calculate costs
        trade_value = order.quantity * fill_price
        commission = trade_value * self.commission_rate
        slippage = trade_value * self.slippage_rate

        if order.side == OrderSide.BUY:
            total_cost = trade_value + commission + slippage

            if total_cost > self.cash:
                order.reject("Insufficient cash")
                return {}

            # Update cash
            self.cash -= total_cost

            # Update or create position
            if order.symbol not in self.positions:
                self.positions[order.symbol] = Position(symbol=order.symbol)

            self.positions[order.symbol].add(order.quantity, fill_price)
            realized_pnl = 0.0

        else:  # SELL
            position = self.positions.get(order.symbol)
            if not position or position.quantity < order.quantity:
                order.reject("Insufficient position")
                return {}

            # Update position
            realized_pnl = position.reduce(order.quantity, fill_price)

            # Update cash (minus costs)
            net_proceeds = trade_value - commission - slippage
            self.cash += net_proceeds

            # Remove empty positions
            if position.quantity <= 0:
                del self.positions[order.symbol]

        # Update order
        order.fill(order.quantity, fill_price, timestamp, commission, slippage)
        self.filled_orders.append(order)

        # Record trade
        trade = {
            "timestamp": timestamp,
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": fill_price,
            "value": trade_value,
            "commission": commission,
            "slippage": slippage,
            "realized_pnl": realized_pnl,
            "strategy": order.strategy_name,
        }
        self.trades.append(trade)

        logger.debug(
            f"Trade executed: {order.side.value} {order.quantity} {order.symbol} "
            f"@ {fill_price:.2f}, PnL: {realized_pnl:.2f}"
        )

        return trade

    def take_snapshot(self, timestamp: datetime) -> PortfolioSnapshot:
        """Take a snapshot of current portfolio state"""
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            cash=self.cash,
            positions_value=self.positions_value,
            total_value=self.total_value,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            positions={s: p.to_dict() for s, p in self.positions.items()},
        )
        self.snapshots.append(snapshot)
        self._current_timestamp = timestamp
        return snapshot

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get pending/open orders"""
        pending = [o for o in self.orders if o.status in [OrderStatus.PENDING, OrderStatus.OPEN]]
        if symbol:
            pending = [o for o in pending if o.symbol == symbol]
        return pending

    def cancel_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel pending orders"""
        count = 0
        for order in self.get_pending_orders(symbol):
            order.cancel()
            count += 1
        return count

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """Get equity curve from snapshots"""
        return [
            {
                "timestamp": s.timestamp,
                "total_value": s.total_value,
                "cash": s.cash,
                "positions_value": s.positions_value,
                "unrealized_pnl": s.unrealized_pnl,
                "realized_pnl": s.realized_pnl,
            }
            for s in self.snapshots
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        return {
            "initial_capital": self.initial_capital,
            "current_value": self.total_value,
            "cash": self.cash,
            "positions_value": self.positions_value,
            "total_return_pct": self.total_return,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_trades": len(self.trades),
            "open_positions": len([p for p in self.positions.values() if p.quantity > 0]),
            "positions": {s: p.to_dict() for s, p in self.positions.items()},
        }

    def reset(self) -> None:
        """Reset portfolio to initial state"""
        self.cash = self.initial_capital
        self.positions.clear()
        self.orders.clear()
        self.filled_orders.clear()
        self.trades.clear()
        self.snapshots.clear()
        self._current_timestamp = None

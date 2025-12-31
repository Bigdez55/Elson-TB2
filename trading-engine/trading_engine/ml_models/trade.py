import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class OrderType(enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(enum.Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(enum.Enum):
    PENDING_APPROVAL = "pending_approval"  # For minors, waiting for guardian approval
    PENDING = "pending"  # Order placed, waiting for execution
    FILLED = "filled"  # Successfully executed
    PARTIALLY_FILLED = "partially_filled"  # Partially executed
    CANCELLED = "cancelled"  # Cancelled by user or system
    REJECTED = "rejected"  # Rejected by guardian or system
    EXPIRED = "expired"  # Order expired


class InvestmentType(enum.Enum):
    QUANTITY_BASED = "quantity_based"  # Traditional share-based orders
    DOLLAR_BASED = "dollar_based"  # Dollar-based investments (for fractional shares)


class TradeSource(enum.Enum):
    USER_INITIATED = "user_initiated"  # Normal user-initiated trade
    RECURRING = "recurring"  # Recurring investment
    REBALANCING = "rebalancing"  # Portfolio rebalancing
    DIVIDEND_REINVESTMENT = "dividend_reinvestment"  # DRIP
    AGGREGATED = "aggregated"  # Part of an aggregated order


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(10), nullable=False)

    # Using Numeric for precise decimal handling for financial calculations
    quantity = Column(
        Numeric(16, 8), nullable=True
    )  # Nullable for dollar-based investments
    price = Column(Numeric(16, 8), nullable=True)  # Execution or limit price

    # For dollar-based investments
    investment_amount = Column(
        Numeric(16, 2), nullable=True
    )  # Dollar amount for investment
    investment_type = Column(
        Enum(InvestmentType), default=InvestmentType.QUANTITY_BASED, nullable=False
    )

    # Order details
    trade_type = Column(String(10), nullable=False)  # "buy" or "sell"
    order_type = Column(Enum(OrderType), default=OrderType.MARKET, nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING, nullable=False)

    # Financial details
    total_amount = Column(
        Numeric(16, 2), nullable=True
    )  # Total transaction amount including commission
    commission = Column(Numeric(10, 2), default=Decimal("0.00"))  # Trade commission
    fees = Column(Numeric(10, 2), default=Decimal("0.00"))  # Additional fees
    filled_quantity = Column(
        Numeric(16, 8), nullable=True
    )  # Actual filled quantity (for partial fills)
    average_price = Column(Numeric(16, 8), nullable=True)  # Average fill price
    realized_pnl = Column(
        Numeric(16, 2), nullable=True
    )  # Realized profit/loss for sells

    # Fractional shares specific
    is_fractional = Column(
        Boolean, default=False, nullable=False
    )  # Whether this is a fractional trade
    parent_order_id = Column(
        Integer, ForeignKey("trades.id"), nullable=True
    )  # For aggregated orders
    minimum_quantity = Column(
        Numeric(16, 8), nullable=True
    )  # Minimum execution quantity
    recurring_investment_id = Column(
        Integer, ForeignKey("recurring_investments.id"), nullable=True
    )  # Link to recurring investment

    # Trade source
    trade_source = Column(
        Enum(TradeSource), default=TradeSource.USER_INITIATED, nullable=False
    )

    # Broker integration
    broker_order_id = Column(
        String(50), nullable=True
    )  # Order ID assigned by the broker
    broker_account_id = Column(String(50), nullable=True)  # Broker account ID
    broker_status = Column(String(50), nullable=True)  # Status reported by broker
    executed_by = Column(
        String(20), nullable=True
    )  # Which broker executed this trade (schwab, alpaca, paper)

    # Approval flow fields
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    settlement_date = Column(DateTime, nullable=True)  # Trade settlement date

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="trades")
    portfolio = relationship("Portfolio", back_populates="trades")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    child_orders = relationship(
        "Trade",
        foreign_keys=[parent_order_id],
        backref="parent_trade",
        remote_side=[id],
    )
    recurring_investment = relationship(
        "RecurringInvestment", foreign_keys=[recurring_investment_id], backref="trades"
    )

    def __repr__(self):
        return f"<Trade {self.trade_type} {self.quantity} {self.symbol} @ {self.price} ({self.status.value})>"

    def calculate_total_cost(self) -> Decimal:
        """Calculate total cost including fees and commissions"""
        if not self.total_amount:
            return Decimal("0")

        return (
            self.total_amount
            + (self.commission or Decimal("0"))
            + (self.fees or Decimal("0"))
        )

    def is_executable(self) -> bool:
        """Check if trade can be executed based on current status"""
        return self.status in [TradeStatus.PENDING, TradeStatus.PENDING_APPROVAL]

    def requires_approval(self) -> bool:
        """Check if trade requires guardian approval (for minor accounts)"""
        return self.status == TradeStatus.PENDING_APPROVAL

    def mark_filled(
        self,
        filled_quantity: Decimal,
        average_price: Decimal,
        realized_pnl: Decimal = None,
    ) -> None:
        """Mark trade as filled with execution details"""
        self.status = TradeStatus.FILLED
        self.filled_quantity = filled_quantity
        self.average_price = average_price
        self.executed_at = datetime.utcnow()

        if realized_pnl is not None:
            self.realized_pnl = realized_pnl

        # Calculate total amount if not set
        if not self.total_amount:
            self.total_amount = filled_quantity * average_price

    def validate_trade_limits(self, user, portfolio) -> tuple[bool, str]:
        """Validate trade against user and portfolio limits"""
        # Check if user can trade
        can_trade, reason = user.can_place_trade(
            self.investment_amount or (self.quantity * self.price)
        )
        if not can_trade:
            return False, reason

        # Check portfolio concentration limits
        if portfolio and self.trade_type.lower() == "buy":
            trade_value = self.investment_amount or (
                self.quantity * self.price
                if self.quantity and self.price
                else Decimal("0")
            )
            if not portfolio.validate_position_concentration(self.symbol, trade_value):
                return False, "Trade would exceed position concentration limits"

        return True, "Trade validation passed"

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


# Alias for compatibility with TradeExecutor
OrderSide = TradeType


class TradeStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    CANCELED = "canceled"  # Added for compatibility
    PENDING_CANCEL = "pending_cancel"  # Added for live trading
    REJECTED = "rejected"
    EXPIRED = "expired"
    ERROR = "error"
    UNKNOWN = "unknown"


# Alias for compatibility with TradeExecutor
OrderStatus = TradeStatus


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class InvestmentType(str, enum.Enum):
    STANDARD = "standard"
    MICRO = "micro"
    ROUNDUP = "roundup"
    RECURRING = "recurring"
    DOLLAR_COST_AVERAGE = "dca"


class TradeSource(str, enum.Enum):
    MANUAL = "manual"
    MICRO_DEPOSIT = "micro_deposit"
    ROUNDUP = "roundup"
    RECURRING = "recurring"
    AI_RECOMMENDATION = "ai_recommendation"
    REBALANCING = "rebalancing"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )

    # Basic trade information
    symbol = Column(String(20), nullable=False, index=True)
    trade_type: Column[TradeType] = Column(Enum(TradeType), nullable=False)  # For backward compatibility
    side: Column[TradeType] = Column(Enum(TradeType), nullable=False)  # TradeExecutor expects 'side'
    order_type: Column[OrderType] = Column(Enum(OrderType), nullable=False)

    # Quantities and prices
    quantity = Column(Float, nullable=True)  # Can be None for dollar-based orders
    price = Column(Float, nullable=True)  # None for market orders
    filled_quantity = Column(Float, default=0.0)
    filled_price = Column(Float, nullable=True)

    # Investment amount for fractional shares
    investment_amount = Column(Float, nullable=True)  # For dollar-based investing

    # Order details
    stop_price = Column(Float, nullable=True)  # For stop orders
    limit_price = Column(Float, nullable=True)  # For limit orders

    # Status and tracking
    status: Column[TradeStatus] = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    broker_order_id = Column(String(255), nullable=True, index=True)
    external_order_id = Column(
        String(255), nullable=True, index=True
    )  # TradeExecutor expects this

    # Financial calculations
    total_cost = Column(Float, nullable=True)  # Total cost including fees
    commission = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)

    # Strategy and reasoning
    strategy = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Risk management
    is_paper_trade = Column(Boolean, default=True)
    parent_order_id = Column(
        String(36), nullable=True
    )  # For stop loss/take profit orders

    # Additional fields for Schwab broker integration
    account_id = Column(String(255), nullable=True)  # Broker account ID
    is_fractional = Column(
        Boolean, default=False
    )  # Whether this is a fractional share order
    extended_hours = Column(
        Boolean, default=False
    )  # Whether to trade in extended hours

    # Micro-investing fields
    investment_type: Column[InvestmentType] = Column(Enum(InvestmentType), default=InvestmentType.STANDARD)
    trade_source: Column[TradeSource] = Column(Enum(TradeSource), default=TradeSource.MANUAL)
    trade_metadata = Column(Text, nullable=True)  # JSON metadata for additional info
    total_amount = Column(Float, nullable=True)  # Total amount for fractional shares
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    user = relationship("User")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    filled_at = Column(
        DateTime(timezone=True), nullable=True
    )  # TradeExecutor expects this

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")

    def __init__(self, **kwargs):
        """Initialize Trade with proper defaults for TradeExecutor compatibility"""
        # Set side from trade_type if provided but side is not
        if 'trade_type' in kwargs and 'side' not in kwargs:
            kwargs['side'] = kwargs['trade_type']
        elif 'side' in kwargs and 'trade_type' not in kwargs:
            kwargs['trade_type'] = kwargs['side']
            
        super().__init__(**kwargs)
        
        # Ensure both fields are set after initialization
        if hasattr(self, "trade_type") and not hasattr(self, "side"):
            self.side = self.trade_type
        elif hasattr(self, "side") and not hasattr(self, "trade_type"):
            self.trade_type = self.side


class RoundupTransaction(Base):
    __tablename__ = "roundup_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Transaction details
    transaction_amount = Column(Float, nullable=False)
    roundup_amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(255), nullable=True)
    source = Column(String(100), nullable=True)

    # Investment tracking
    status = Column(String(50), default="pending")  # pending, invested
    invested_at = Column(DateTime(timezone=True), nullable=True)
    trade_id = Column(String(36), ForeignKey("trades.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    trade = relationship("Trade")


class TradeExecution(Base):
    __tablename__ = "trade_executions"

    id = Column(Integer, primary_key=True, index=True)

    # Trade reference
    trade_id = Column(String(36), ForeignKey("trades.id"), nullable=False)

    # Execution details
    executed_quantity = Column(Float, nullable=False)
    executed_price = Column(Float, nullable=False)
    execution_time = Column(DateTime(timezone=True), nullable=False)

    # Broker information
    execution_id = Column(String(255), nullable=True)
    broker_commission = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trade = relationship("Trade")

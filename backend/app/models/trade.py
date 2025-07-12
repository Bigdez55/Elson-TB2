import enum

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    # Basic trade information
    symbol = Column(String(20), nullable=False, index=True)
    trade_type = Column(Enum(TradeType), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)

    # Quantities and prices
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # None for market orders
    filled_quantity = Column(Float, default=0.0)
    filled_price = Column(Float, nullable=True)

    # Order details
    stop_price = Column(Float, nullable=True)  # For stop orders
    limit_price = Column(Float, nullable=True)  # For limit orders

    # Status and tracking
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    broker_order_id = Column(String(255), nullable=True, index=True)

    # Financial calculations
    total_cost = Column(Float, nullable=True)  # Total cost including fees
    commission = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)

    # Strategy and reasoning
    strategy = Column(
        String(100), nullable=True
    )  # AI recommendation, manual, etc.
    notes = Column(Text, nullable=True)

    # Risk management
    is_paper_trade = Column(Boolean, default=True)  # Safety first

    # Relationships
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")


class TradeExecution(Base):
    __tablename__ = "trade_executions"

    id = Column(Integer, primary_key=True, index=True)

    # Trade reference
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)

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

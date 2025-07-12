from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Portfolio financials
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    invested_amount = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    total_return_percentage = Column(Float, default=0.0)

    # Portfolio settings
    auto_rebalance = Column(Boolean, default=False)
    rebalance_threshold = Column(Float, default=0.05)  # 5% deviation threshold

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)

    # Asset information
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)  # stock, crypto, bond, etf

    # Holding details
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)

    # Performance
    unrealized_gain_loss = Column(Float, default=0.0)
    unrealized_gain_loss_percentage = Column(Float, default=0.0)

    # Target allocation
    target_allocation_percentage = Column(Float, nullable=True)
    current_allocation_percentage = Column(Float, nullable=True)

    # Portfolio relationship
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")

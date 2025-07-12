from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
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

    def get_daily_drawdown(self) -> Optional[Decimal]:
        """
        Calculate daily portfolio drawdown

        Returns:
            Daily drawdown as a decimal (e.g., 0.02 for 2%) or None if not available
        """
        try:
            # In production, this would calculate actual drawdown from daily high
            # using historical portfolio values

            # This is a simplified implementation
            # In production, you would track portfolio values throughout the day
            # and calculate actual drawdown from the daily high

            # For now, just return None to indicate no significant drawdown
            # In a real implementation, this would query historical portfolio values
            return None
        except Exception:
            return None

    def get_daily_trade_count(self) -> int:
        """
        Get the number of trades executed today

        Returns:
            Number of trades executed today
        """
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())

            # Count trades created today
            # Note: This is a simplified version - in production you'd use session.query
            daily_trades = [trade for trade in self.trades if trade.created_at and trade.created_at >= start_of_day]
            return len(daily_trades)
        except Exception:
            return 0


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


class Position:
    """
    Lightweight position tracking class for the trading engine

    This is a separate class from Holding to provide a simple interface
    for the TradeExecutor to track positions during trading.
    """

    def __init__(self, symbol: str, quantity: float, cost_basis: float):
        """
        Initialize a position

        Args:
            symbol: Asset symbol
            quantity: Number of shares/units
            cost_basis: Average cost basis per share
        """
        self.symbol = symbol
        self.quantity = quantity
        self.cost_basis = cost_basis
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_position(self, new_quantity: float, new_cost_basis: float) -> None:
        """
        Update position with new quantity and cost basis

        Args:
            new_quantity: New quantity
            new_cost_basis: New cost basis
        """
        self.quantity = new_quantity
        self.cost_basis = new_cost_basis
        self.updated_at = datetime.utcnow()

    def get_market_value(self, current_price: float) -> float:
        """
        Calculate current market value of the position

        Args:
            current_price: Current market price

        Returns:
            Market value of the position
        """
        return self.quantity * current_price

    def get_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized profit/loss

        Args:
            current_price: Current market price

        Returns:
            Unrealized P&L
        """
        return (current_price - self.cost_basis) * self.quantity

    def __str__(self) -> str:
        return f"Position(symbol={self.symbol}, quantity={self.quantity}, cost_basis={self.cost_basis:.2f})"

    def __repr__(self) -> str:
        return self.__str__()

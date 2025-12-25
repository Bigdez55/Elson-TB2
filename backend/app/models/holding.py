from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


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

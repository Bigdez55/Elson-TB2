import enum
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Session, relationship

from .base import Base
from .trade import Trade, TradeStatus


class RiskProfile(enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PortfolioType(enum.Enum):
    STANDARD = "standard"
    CUSTODIAL = "custodial"
    RETIREMENT = "retirement"
    PAPER = "paper"


logger = logging.getLogger(__name__)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )  # Link to specific account

    # Financial fields using Numeric for precision
    total_value = Column(Numeric(16, 2), default=Decimal("0.00"))
    cash_balance = Column(Numeric(16, 2), default=Decimal("0.00"))
    invested_amount = Column(Numeric(16, 2), default=Decimal("0.00"))
    available_buying_power = Column(Numeric(16, 2), default=Decimal("0.00"))

    # Portfolio configuration
    portfolio_type = Column(
        Enum(PortfolioType), default=PortfolioType.STANDARD, nullable=False
    )
    risk_profile = Column(
        Enum(RiskProfile), default=RiskProfile.MODERATE, nullable=False
    )

    # Performance tracking
    daily_return = Column(Numeric(10, 4), default=Decimal("0.0000"))
    total_return = Column(Numeric(10, 4), default=Decimal("0.0000"))
    total_return_percent = Column(Numeric(10, 4), default=Decimal("0.0000"))

    # Risk management
    max_position_concentration = Column(
        Numeric(5, 2), default=Decimal("20.00")
    )  # Max % of portfolio in single position
    rebalancing_threshold = Column(
        Numeric(5, 2), default=Decimal("5.00")
    )  # Threshold for automatic rebalancing

    # Metadata
    positions = Column(
        JSON, default=dict
    )  # Stores current positions as JSON for quick access
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_rebalanced_at = Column(DateTime, nullable=True)
    last_valued_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="portfolio")
    account = relationship("Account", back_populates="portfolio")
    positions_detail = relationship("Position", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")

    def __repr__(self):
        return f"<Portfolio user_id={self.user_id} value=${self.total_value:,.2f}>"

    def validate_position_concentration(self, symbol: str, amount: Decimal) -> bool:
        """Check if adding this position would exceed concentration limits"""
        # Calculate new position value
        new_position_value = amount

        # Get current position value for this symbol
        current_position_value = Decimal("0")
        for position in self.positions_detail:
            if position.symbol == symbol:
                current_position_value = position.market_value or Decimal("0")
                break

        # Calculate total position value after trade
        total_position_value = current_position_value + new_position_value

        # Check against concentration limit
        if self.total_value > 0:
            concentration_percent = (total_position_value / self.total_value) * 100
            return concentration_percent <= self.max_position_concentration

        return True

    def check_rebalancing_needed(self) -> bool:
        """Check if portfolio needs rebalancing based on drift from target allocation"""
        # Simple implementation - check if any position exceeds threshold
        if self.total_value <= 0:
            return False

        for position in self.positions_detail:
            if position.market_value:
                position_percent = (position.market_value / self.total_value) * 100
                # If any position has drifted more than threshold, rebalancing needed
                if (
                    abs(position_percent - (100 / len(self.positions_detail)))
                    > self.rebalancing_threshold
                ):
                    return True

        return False

    def update_performance_metrics(self) -> None:
        """Update portfolio performance metrics"""
        # This would typically fetch current market prices and calculate returns
        # For now, we'll update the last_valued_at timestamp
        self.last_valued_at = datetime.utcnow()

        # Calculate total portfolio value from positions
        total_value = self.cash_balance
        for position in self.positions_detail:
            if position.market_value:
                total_value += position.market_value

        self.total_value = total_value

    def get_daily_drawdown(self) -> Optional[Decimal]:
        """
        Calculate the daily drawdown as a percentage of portfolio value
        """
        try:
            # This is a simplified calculation for demonstration purposes
            # In a real implementation, you would:
            # 1. Compare the current portfolio value to the previous day's closing value
            # 2. Use time-weighted returns for accurate measurement
            # 3. Account for deposits and withdrawals

            # For now, we'll estimate based on recent trades
            if not hasattr(self, "_session"):
                return None

            # Find the previous day's value (this is an estimate)
            yesterday = datetime.utcnow() - timedelta(days=1)
            day_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

            # Get all trades for this portfolio today
            today_trades = (
                self._session.query(Trade)
                .filter(
                    Trade.portfolio_id == self.id,
                    Trade.status == TradeStatus.FILLED,
                    Trade.created_at >= day_start,
                )
                .all()
            )

            # Calculate P&L for today
            daily_pnl = 0
            for trade in today_trades:
                if hasattr(trade, "realized_pnl") and trade.realized_pnl:
                    daily_pnl += trade.realized_pnl

            # Calculate unrealized P&L
            for position in self.positions_detail:
                if hasattr(position, "unrealized_pl") and position.unrealized_pl:
                    daily_pnl += position.unrealized_pl

            # If there's any loss, calculate as percentage of portfolio
            if daily_pnl < 0:
                return Decimal(str(abs(daily_pnl))) / Decimal(str(self.total_value))

            return Decimal("0")

        except Exception as e:
            logger.error(f"Error calculating daily drawdown: {str(e)}")
            return None

    def daily_loss_limit_reached(self) -> bool:
        """
        Check if the daily loss limit has been reached
        Default limit is 2% of portfolio value
        """
        drawdown = self.get_daily_drawdown()
        if drawdown is None:
            return False

        # Default limit is 2%
        limit = Decimal("0.02")
        return drawdown > limit

    def get_daily_trade_count(self) -> int:
        """
        Get the number of trades executed today
        """
        try:
            if not hasattr(self, "_session"):
                return 0

            # Define today
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # Count trades from today
            trade_count = (
                self._session.query(Trade)
                .filter(Trade.portfolio_id == self.id, Trade.created_at >= today)
                .count()
            )

            return trade_count

        except Exception as e:
            logger.error(f"Error counting daily trades: {str(e)}")
            return 0

    def get_sector_exposure(self) -> Dict[str, Decimal]:
        """
        Calculate sector exposure percentages
        This is a simplified implementation - in reality you would use
        sector classification data from a market data provider
        """
        # Map of symbols to sectors (simplified example)
        sector_map = {
            # Technology
            "AAPL": "Technology",
            "MSFT": "Technology",
            "GOOGL": "Technology",
            # Financial
            "JPM": "Financial",
            "BAC": "Financial",
            "WFC": "Financial",
            # Energy
            "XOM": "Energy",
            "CVX": "Energy",
            "COP": "Energy",
            # Healthcare
            "JNJ": "Healthcare",
            "PFE": "Healthcare",
            "MRK": "Healthcare",
        }

        # Group positions by sector
        sectors = {}
        for position in self.positions_detail:
            symbol = position.symbol
            sector = sector_map.get(symbol, "Other")

            position_value = Decimal(str(position.quantity)) * Decimal(
                str(position.current_price)
            )

            if sector not in sectors:
                sectors[sector] = position_value
            else:
                sectors[sector] += position_value

        # Calculate percentages
        total_value = Decimal(str(self.total_value))
        if total_value == 0:
            return {}

        sector_percentages = {}
        for sector, value in sectors.items():
            sector_percentages[sector] = value / total_value

        return sector_percentages


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(
        Integer, ForeignKey("portfolios.id"), nullable=False, index=True
    )
    symbol = Column(String(10), nullable=False, index=True)
    quantity = Column(Numeric(16, 8), nullable=False)
    average_price = Column(Numeric(16, 8), nullable=False)
    current_price = Column(Numeric(16, 8))

    # Added stored values for faster calculations
    cost_basis = Column(Numeric(16, 2), nullable=True)
    market_value = Column(Numeric(16, 2), nullable=True)
    unrealized_pl = Column(Numeric(16, 2), default=0.0)

    # Fractional specific fields
    is_fractional = Column(Boolean, default=False, nullable=False)
    minimum_investment = Column(Numeric(10, 2), nullable=True)

    # Metadata
    sector = Column(String(30), nullable=True)
    asset_class = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_trade_date = Column(DateTime, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions_detail")

    __table_args__ = (
        # Ensure unique symbol per portfolio
        sa.UniqueConstraint(
            "portfolio_id", "symbol", name="uix_position_portfolio_symbol"
        ),
    )

    def __repr__(self):
        return f"<Position {self.symbol} qty={self.quantity} is_fractional={self.is_fractional}>"

    def update_market_value(self) -> Decimal:
        """Update the stored market value based on current price"""
        if self.quantity and self.current_price:
            self.market_value = self.quantity * self.current_price
        else:
            self.market_value = Decimal("0")
        return self.market_value

    def update_cost_basis(self) -> Decimal:
        """Update the stored cost basis"""
        if self.quantity and self.average_price:
            self.cost_basis = self.quantity * self.average_price
        else:
            self.cost_basis = Decimal("0")
        return self.cost_basis

    def update_unrealized_pl(self) -> Decimal:
        """Calculate and update unrealized P&L"""
        # Ensure market_value and cost_basis are up to date
        self.update_market_value()
        self.update_cost_basis()

        if self.market_value > 0 and self.cost_basis > 0:
            self.unrealized_pl = self.market_value - self.cost_basis
        else:
            self.unrealized_pl = Decimal("0")
        return self.unrealized_pl

    def update_all_calculations(self) -> None:
        """Update all calculated fields"""
        self.update_cost_basis()
        self.update_market_value()
        self.update_unrealized_pl()

    def get_holding_period(self) -> timedelta:
        """Get the holding period for this position"""
        return datetime.utcnow() - self.created_at

    @property
    def unrealized_pl_percent(self) -> Decimal:
        """Calculate unrealized P&L as a percentage of cost basis"""
        if self.cost_basis and self.cost_basis > 0:
            return (self.unrealized_pl / self.cost_basis) * 100
        return Decimal("0")

    def add_quantity(self, quantity: Decimal, price: Decimal) -> None:
        """Add to position using dollar cost averaging"""
        if quantity <= 0:
            return

        # Dollar cost average the position
        new_total_quantity = self.quantity + quantity
        new_total_cost = (self.quantity * self.average_price) + (quantity * price)

        # Update the position
        self.average_price = (
            new_total_cost / new_total_quantity
            if new_total_quantity > 0
            else Decimal("0")
        )
        self.quantity = new_total_quantity
        self.last_trade_date = datetime.utcnow()

        # Mark as fractional if either current position or new quantity is fractional
        if quantity != int(quantity) or self.quantity != int(self.quantity):
            self.is_fractional = True

        # Update calculated fields
        self.update_all_calculations()

    def remove_quantity(self, quantity: Decimal, price: Decimal) -> Decimal:
        """Remove from position and return the realized P&L"""
        if quantity <= 0 or quantity > self.quantity:
            return Decimal("0")

        # Calculate realized P&L for the sold portion
        realized_pl = (price - self.average_price) * quantity

        # Update the position
        self.quantity -= quantity
        self.last_trade_date = datetime.utcnow()

        # Position could be closed out
        if self.quantity <= 0:
            self.quantity = Decimal("0")

        # Update calculated fields
        self.update_all_calculations()

        return realized_pl

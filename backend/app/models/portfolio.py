from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict
import enum
import logging

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from app.db.base import Base

logger = logging.getLogger(__name__)


class RiskProfile(str, enum.Enum):
    """Portfolio risk profile levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PortfolioType(str, enum.Enum):
    """Portfolio type classifications"""
    STANDARD = "standard"
    CUSTODIAL = "custodial"
    RETIREMENT = "retirement"
    PAPER = "paper"


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

    # Portfolio type and risk configuration
    portfolio_type = Column(Enum(PortfolioType), default=PortfolioType.STANDARD, nullable=False)
    risk_profile = Column(Enum(RiskProfile), default=RiskProfile.MODERATE, nullable=False)
    max_position_concentration = Column(Float, default=20.0)  # Max % of portfolio in single position

    # Performance tracking
    daily_return = Column(Float, default=0.0)
    total_return_percent = Column(Float, default=0.0)
    available_buying_power = Column(Float, default=0.0)

    # Rebalancing
    last_rebalanced_at = Column(DateTime(timezone=True), nullable=True)
    last_valued_at = Column(DateTime(timezone=True), nullable=True)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Alias for owner_id compatibility

    # Account relationship for family accounts (temporarily commented out)
    # account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="portfolios", foreign_keys=[owner_id])
    # account = relationship("Account", back_populates="portfolio")  # Commented out until account_id FK is added
    holdings = relationship("Holding", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")

    def get_daily_drawdown(self, session: Optional[Session] = None) -> Decimal:
        """
        Calculate the daily drawdown as a percentage of portfolio value.

        Args:
            session: Optional SQLAlchemy session for database queries

        Returns:
            Daily drawdown as a decimal (e.g., 0.02 for 2%), defaults to 0.0
        """
        try:
            if not session:
                # If no session provided, return 0 (no drawdown can be calculated)
                return Decimal("0")

            # Import here to avoid circular dependency
            from app.models.trade import Trade, TradeStatus

            # Find the previous day's value (this is an estimate)
            yesterday = datetime.utcnow() - timedelta(days=1)
            day_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

            # Get all trades for this portfolio today
            today_trades = session.query(Trade).filter(
                Trade.portfolio_id == self.id,
                Trade.status == TradeStatus.FILLED,
                Trade.created_at >= day_start
            ).all()

            # Calculate P&L for today
            daily_pnl = 0
            for trade in today_trades:
                if hasattr(trade, "realized_pnl") and trade.realized_pnl:
                    daily_pnl += float(trade.realized_pnl)

            # Calculate unrealized P&L from holdings
            for holding in self.holdings:
                if hasattr(holding, "unrealized_pl") and holding.unrealized_pl:
                    daily_pnl += float(holding.unrealized_pl)

            # If there's any loss, calculate as percentage of portfolio
            if daily_pnl < 0 and self.total_value > 0:
                return Decimal(str(abs(daily_pnl))) / Decimal(str(self.total_value))

            return Decimal("0")

        except Exception as e:
            logger.error(f"Error calculating daily drawdown: {str(e)}")
            return Decimal("0")

    def daily_loss_limit_reached(self, session: Optional[Session] = None, limit: Optional[Decimal] = None) -> bool:
        """
        Check if the daily loss limit has been reached.

        Args:
            session: Optional SQLAlchemy session for database queries
            limit: Optional custom limit (default: 2% of portfolio value)

        Returns:
            True if daily loss limit exceeded, False otherwise
        """
        try:
            drawdown = self.get_daily_drawdown(session)

            # Default limit is 2%
            if limit is None:
                limit = Decimal("0.02")

            return drawdown > limit

        except Exception as e:
            logger.error(f"Error checking daily loss limit: {str(e)}")
            return False

    def get_daily_trade_count(self, session: Optional[Session] = None) -> int:
        """
        Get the number of trades executed today.

        Args:
            session: Optional SQLAlchemy session for database queries

        Returns:
            Number of trades executed today
        """
        try:
            if session:
                # Import here to avoid circular dependency
                from app.models.trade import Trade

                # Define today
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

                # Count trades from today
                trade_count = session.query(Trade).filter(
                    Trade.portfolio_id == self.id,
                    Trade.created_at >= today
                ).count()

                return trade_count
            else:
                # Fallback to in-memory count
                today = datetime.now().date()
                start_of_day = datetime.combine(today, datetime.min.time())
                daily_trades = [
                    trade
                    for trade in self.trades
                    if trade.created_at and trade.created_at >= start_of_day
                ]
                return len(daily_trades)

        except Exception as e:
            logger.error(f"Error counting daily trades: {str(e)}")
            return 0

    def get_sector_exposure(self) -> Dict[str, Decimal]:
        """
        Calculate sector exposure percentages.

        Note: This is a simplified implementation. In production, you would use
        sector classification data from a market data provider.

        Returns:
            Dictionary mapping sector names to exposure percentages
        """
        try:
            # Map of symbols to sectors (simplified example)
            sector_map = {
                # Technology
                "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
                "GOOG": "Technology", "NVDA": "Technology", "META": "Technology",
                # Financial
                "JPM": "Financial", "BAC": "Financial", "WFC": "Financial",
                "GS": "Financial", "MS": "Financial", "C": "Financial",
                # Energy
                "XOM": "Energy", "CVX": "Energy", "COP": "Energy",
                # Healthcare
                "JNJ": "Healthcare", "PFE": "Healthcare", "MRK": "Healthcare",
                "UNH": "Healthcare", "ABBV": "Healthcare",
                # Consumer
                "AMZN": "Consumer", "TSLA": "Consumer", "WMT": "Consumer",
            }

            # Group holdings by sector
            sectors = {}
            for holding in self.holdings:
                symbol = holding.symbol
                sector = sector_map.get(symbol, "Other")

                # Calculate position value
                position_value = Decimal(str(holding.quantity)) * Decimal(str(holding.current_price or 0))

                if sector not in sectors:
                    sectors[sector] = position_value
                else:
                    sectors[sector] += position_value

            # Calculate percentages
            total_value = Decimal(str(self.total_value)) if self.total_value else Decimal("0")
            if total_value == 0:
                return {}

            sector_percentages = {}
            for sector, value in sectors.items():
                sector_percentages[sector] = (value / total_value) * Decimal("100")

            return sector_percentages

        except Exception as e:
            logger.error(f"Error calculating sector exposure: {str(e)}")
            return {}

    def validate_position_concentration(self, symbol: str, amount: Decimal) -> bool:
        """Check if adding this position would exceed concentration limits"""
        # Calculate new position value
        new_position_value = amount

        # Get current position value for this symbol
        current_position_value = Decimal("0")
        for holding in self.holdings:
            if holding.symbol == symbol:
                current_position_value = Decimal(str(holding.market_value or 0))
                break

        # Calculate total position value after trade
        total_position_value = current_position_value + new_position_value

        # Check against concentration limit
        if self.total_value and self.total_value > 0:
            concentration_percent = (total_position_value / Decimal(str(self.total_value))) * 100
            return concentration_percent <= Decimal(str(self.max_position_concentration))

        return True

    def update_performance_metrics(self) -> None:
        """Update portfolio performance metrics"""
        self.last_valued_at = datetime.utcnow()

        # Calculate total portfolio value from holdings
        total_value = Decimal(str(self.cash_balance)) if self.cash_balance else Decimal("0")
        for holding in self.holdings:
            if holding.market_value:
                total_value += Decimal(str(holding.market_value))

        self.total_value = float(total_value)

    def check_rebalancing_needed(self) -> bool:
        """Check if portfolio needs rebalancing based on drift from target allocation"""
        if not self.total_value or self.total_value <= 0:
            return False

        for holding in self.holdings:
            if holding.market_value:
                position_percent = (Decimal(str(holding.market_value)) / Decimal(str(self.total_value))) * 100
                # If any position has drifted more than threshold, rebalancing needed
                holding_count = len(self.holdings) if self.holdings else 1
                target_percent = Decimal("100") / Decimal(str(holding_count))
                if abs(position_percent - target_percent) > Decimal(str(self.rebalance_threshold * 100)):
                    return True

        return False

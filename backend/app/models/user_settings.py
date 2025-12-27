import enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RoundupFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    THRESHOLD = "threshold"


class MicroInvestTarget(str, enum.Enum):
    DEFAULT_PORTFOLIO = "default_portfolio"
    SPECIFIC_PORTFOLIO = "specific_portfolio"
    SPECIFIC_SYMBOL = "specific_symbol"
    RECOMMENDED_ETF = "recommended_etf"


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Micro-investing settings
    micro_investing_enabled = Column(Boolean, default=False)
    roundup_enabled = Column(Boolean, default=False)
    roundup_multiplier = Column(Float, default=1.0)
    roundup_frequency = Column(Enum(RoundupFrequency), default=RoundupFrequency.WEEKLY)
    roundup_threshold = Column(Float, default=5.0)  # Minimum amount to invest roundups

    # Investment target settings
    micro_invest_target_type = Column(
        Enum(MicroInvestTarget), default=MicroInvestTarget.DEFAULT_PORTFOLIO
    )
    micro_invest_portfolio_id = Column(
        Integer, ForeignKey("portfolios.id"), nullable=True
    )
    micro_invest_symbol = Column(String(20), nullable=True)

    # Notification settings
    notify_on_roundup = Column(Boolean, default=True)
    notify_on_investment = Column(Boolean, default=True)

    # Limits
    max_weekly_roundup = Column(Float, default=50.0)
    max_monthly_micro_invest = Column(Float, default=200.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    micro_invest_portfolio = relationship(
        "Portfolio", foreign_keys=[micro_invest_portfolio_id]
    )

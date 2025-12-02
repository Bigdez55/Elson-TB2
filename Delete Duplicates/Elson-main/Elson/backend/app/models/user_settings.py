from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.init_db import Base

class RoundupFrequency(enum.Enum):
    """How often to invest collected roundups"""
    DAILY = "daily"
    WEEKLY = "weekly"
    WHEN_THRESHOLD_REACHED = "threshold"

class MicroInvestTarget(enum.Enum):
    """Investment targets for micro-investing"""
    DEFAULT_PORTFOLIO = "default_portfolio"  # User's default portfolio
    SPECIFIC_PORTFOLIO = "specific_portfolio"  # A specific portfolio
    SPECIFIC_SYMBOL = "specific_symbol"  # A specific stock/ETF
    RECOMMENDED_ETF = "recommended_etf"  # System-recommended ETF based on risk profile

class UserSettings(Base):
    """User settings and preferences model"""
    
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Micro-investing settings
    micro_investing_enabled = Column(Boolean, default=False)
    roundup_enabled = Column(Boolean, default=False)
    roundup_multiplier = Column(Float, default=1.0)  # 1x, 2x, 3x roundups
    roundup_frequency = Column(Enum(RoundupFrequency), default=RoundupFrequency.WEEKLY)
    roundup_threshold = Column(Float, default=5.0)  # Minimum amount to trigger investment
    
    # Investment target for micro-investing
    micro_invest_target_type = Column(Enum(MicroInvestTarget), default=MicroInvestTarget.DEFAULT_PORTFOLIO)
    micro_invest_portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)
    micro_invest_symbol = Column(String(10), nullable=True)
    
    # Linked accounts for roundups
    bank_account_linked = Column(Boolean, default=False)
    card_accounts_linked = Column(Boolean, default=False)
    linked_accounts_data = Column(JSON, nullable=True)  # Store linked account info
    
    # Notification preferences
    notify_on_roundup = Column(Boolean, default=True)
    notify_on_investment = Column(Boolean, default=True)
    
    # Auto-investment caps
    max_weekly_roundup = Column(Float, default=100.0)  # Maximum weekly roundup amount
    max_monthly_micro_invest = Column(Float, default=500.0)  # Maximum monthly micro-invest
    
    # Educational integration
    completed_micro_invest_education = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="settings")
    target_portfolio = relationship("Portfolio", foreign_keys=[micro_invest_portfolio_id])
import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
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

from app.db.base import Base


class AccountType(enum.Enum):
    PERSONAL = "personal"
    CUSTODIAL = "custodial"


class AccountStatus(str, enum.Enum):
    """Account status options."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CLOSED = "closed"


class RecurringFrequency(str, enum.Enum):
    """Frequency options for recurring investments."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    guardian_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    account_type: Column[AccountType] = Column(
        Enum(AccountType), nullable=False, default=AccountType.PERSONAL
    )

    # Account identification
    account_number = Column(String, unique=True, index=True, nullable=False)
    institution = Column(String, nullable=False)

    # Account status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("User", foreign_keys=[user_id], back_populates="accounts")
    # guardian = relationship(
    #     "User", foreign_keys=[guardian_id], back_populates="guardian_accounts"
    # )
    # portfolio = relationship("Portfolio", back_populates="account", uselist=False)  # Commented out until FK is added

    def __repr__(self):
        return f"<Account {self.account_number} ({self.account_type.value})>"


class RecurringInvestment(Base):
    """Model for recurring investment plans."""

    __tablename__ = "recurring_investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)

    # Investment details
    symbol = Column(String(20), nullable=False)
    investment_amount = Column(Numeric(precision=16, scale=2), nullable=False)

    # Schedule
    frequency: Column[RecurringFrequency] = Column(
        Enum(RecurringFrequency), nullable=False
    )
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    next_investment_date = Column(DateTime, nullable=False)
    last_execution_date = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)

    # Description/notes
    description = Column(Text, nullable=True)

    # Additional configuration (specific days, custom settings, etc.)
    investment_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="recurring_investments")
    portfolio = relationship("Portfolio", backref="recurring_investments")

    def __repr__(self):
        return f"<RecurringInvestment {self.symbol} - ${self.investment_amount} {self.frequency.value}>"

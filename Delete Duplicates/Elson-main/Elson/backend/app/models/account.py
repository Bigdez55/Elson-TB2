from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base
from app.core.field_encryption import EncryptedField, EncryptedString

class AccountType(enum.Enum):
    PERSONAL = "personal"
    CUSTODIAL = "custodial"

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
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.PERSONAL)
    
    # We need to keep a plain account number for indexing but also have an encrypted version
    account_number = Column(String, unique=True, index=True, nullable=False)
    _encrypted_account_number = Column(EncryptedString, nullable=True)
    encrypted_account_number = EncryptedField("_encrypted_account_number")
    
    institution = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="accounts")
    guardian = relationship("User", foreign_keys=[guardian_id], back_populates="guardian_accounts")
    portfolio = relationship("Portfolio", back_populates="account", uselist=False)

    def __repr__(self):
        return f"<Account {self.account_number} ({self.account_type.value})>"
        
    def sync_encrypted_account_number(self):
        """
        Synchronize the encrypted account number with the plain account number.
        
        This should be called whenever the account number is changed.
        """
        self.encrypted_account_number = self.account_number

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
    frequency = Column(Enum(RecurringFrequency), nullable=False)
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
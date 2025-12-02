from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from datetime import datetime
import json
import enum
import os

from .base import Base
from app.core.field_encryption import EncryptedField, EncryptedString

class UserRole(enum.Enum):
    ADULT = "adult"
    MINOR = "minor"
    ADMIN = "admin"
    
class SubscriptionPlan(enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    FAMILY = "family"

class BillingCycle(enum.Enum):
    MONTHLY = "monthly"
    ANNUALLY = "annually"

# Check if we're using SQLite (for tests) or PostgreSQL
is_sqlite = 'sqlite' in os.environ.get('DATABASE_URL', '').lower()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Encrypted PII fields
    # We store the plain email for lookups/login but keep an encrypted version for data protection
    email = Column(String, unique=True, index=True, nullable=False)
    _encrypted_email = Column(EncryptedString, nullable=True)
    
    hashed_password = Column(String, nullable=False)
    
    # Store encrypted versions of PII
    _first_name = Column(EncryptedString, nullable=True)
    first_name = EncryptedField("_first_name")
    
    _last_name = Column(EncryptedString, nullable=True)
    last_name = EncryptedField("_last_name")
    
    # Standard non-PII fields
    role = Column(Enum(UserRole), default=UserRole.ADULT, nullable=False)
    
    # Encrypted birthdate
    _birthdate = Column(EncryptedString, nullable=True)
    birthdate = EncryptedField("_birthdate")
    
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Two-factor authentication fields
    two_factor_enabled = Column(Boolean, default=False)
    
    # Encrypted 2FA secret
    _two_factor_secret = Column(EncryptedString, nullable=True)
    two_factor_secret = EncryptedField("_two_factor_secret")
    
    # Use JSON string for SQLite and ARRAY for PostgreSQL
    if is_sqlite:
        # Store as JSON string in SQLite
        two_factor_backup_codes = Column(String, nullable=True)
    else:
        # Use native ARRAY type in PostgreSQL
        two_factor_backup_codes = Column(ARRAY(String), nullable=True)
    
    # Account security fields
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    password_last_changed = Column(DateTime, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    trades = relationship("Trade", foreign_keys="Trade.user_id", back_populates="user")
    accounts = relationship("Account", foreign_keys="Account.user_id", back_populates="user")
    guardian_accounts = relationship("Account", foreign_keys="Account.guardian_id", back_populates="guardian")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    # Educational progress tracking
    educational_progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    trading_permissions = relationship("UserPermission", foreign_keys="UserPermission.user_id", 
                                       back_populates="user", cascade="all, delete-orphan")
    permissions_granted = relationship("UserPermission", foreign_keys="UserPermission.granted_by_user_id")

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
        
    def sync_encrypted_email(self):
        """
        Synchronize the encrypted email with the plain email.
        
        This should be called whenever the email is changed.
        """
        # Using our field encryption system
        encrypted_value = EncryptedField("_encrypted_email")._get_encrypted_value(self.email)
        self._encrypted_email = encrypted_value
    
    @property
    def is_adult(self):
        return self.role == UserRole.ADULT
    
    @property
    def is_minor(self):
        return self.role == UserRole.MINOR
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
        
    def get_active_subscription(self):
        """Get the user's active subscription if any"""
        if not hasattr(self, 'subscriptions') or not self.subscriptions:
            return None
            
        for subscription in self.subscriptions:
            if subscription.is_active and (not subscription.end_date or subscription.end_date > datetime.utcnow()):
                return subscription
                
        return None
        
    def is_subscribed(self):
        """Check if user has an active paid subscription"""
        subscription = self.get_active_subscription()
        if subscription and subscription.plan in (SubscriptionPlan.PREMIUM, SubscriptionPlan.FAMILY):
            return True
        return False
        
    def has_family_plan(self):
        """Check if user has an active family plan subscription"""
        subscription = self.get_active_subscription()
        if subscription and subscription.plan == SubscriptionPlan.FAMILY:
            return True
        return False
        
    def get_subscription_tier(self):
        """Get the user's subscription tier"""
        subscription = self.get_active_subscription()
        if not subscription:
            return SubscriptionPlan.FREE
        return subscription.plan
    
    def can_access_feature(self, feature: str) -> bool:
        """Check if user can access a specific feature based on subscription plan"""
        # Admin can access everything
        if self.role == UserRole.ADMIN:
            return True
            
        # Free plan features
        free_features = {
            "basic_trading", "paper_trading", "basic_education", 
            "market_data_basic", "portfolio_tracking"
        }
        
        # Premium plan features
        premium_features = {
            *free_features,
            "advanced_trading", "fractional_shares", "ai_recommendations",
            "unlimited_recurring_investments", "tax_loss_harvesting",
            "advanced_education", "market_data_advanced", "high_yield_savings",
            "retirement_accounts", "api_access"
        }
        
        # Family plan features
        family_features = {
            *premium_features,
            "custodial_accounts", "guardian_approval", "family_challenges",
            "educational_games", "multiple_retirement_accounts"
        }
        
        # Return based on subscription plan
        if feature in free_features:
            return True
        
        tier = self.get_subscription_tier()
        
        if tier == SubscriptionPlan.PREMIUM and feature in premium_features:
            return True
        
        if tier == SubscriptionPlan.FAMILY and feature in family_features:
            return True
        
        return False
    
    def get_custodial_account_limit(self) -> int:
        """Get the maximum number of custodial accounts allowed"""
        if self.has_family_plan():
            return 5
        return 0
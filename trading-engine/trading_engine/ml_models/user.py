import enum
import json
import os
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import (
    UUID,
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
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.field_encryption import EncryptedField, EncryptedString

from .base import Base


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


class RiskLevel(enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


# Check if we're using SQLite (for tests) or PostgreSQL
is_sqlite = "sqlite" in os.environ.get("DATABASE_URL", "").lower()


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

    # Trading-specific risk management fields
    risk_tolerance = Column(Enum(RiskLevel), default=RiskLevel.MODERATE, nullable=False)
    max_position_size = Column(
        Numeric(10, 2), nullable=True
    )  # Maximum position size as percentage of portfolio
    max_daily_loss = Column(Numeric(10, 2), nullable=True)  # Maximum daily loss limit
    max_monthly_loss = Column(
        Numeric(10, 2), nullable=True
    )  # Maximum monthly loss limit
    trading_enabled = Column(Boolean, default=True, nullable=False)
    paper_trading_only = Column(Boolean, default=False, nullable=False)

    # Two-factor authentication fields
    two_factor_enabled = Column(Boolean, default=False)

    # Encrypted 2FA secret
    _two_factor_secret = Column(EncryptedString, nullable=True)
    two_factor_secret = EncryptedField("_two_factor_secret")

    # Use JSON for both SQLite and PostgreSQL for consistency
    two_factor_backup_codes = Column(String, nullable=True)

    # Account security fields
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    password_last_changed = Column(DateTime, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    trades = relationship("Trade", foreign_keys="Trade.user_id", back_populates="user")
    accounts = relationship(
        "Account", foreign_keys="Account.user_id", back_populates="user"
    )
    guardian_accounts = relationship(
        "Account", foreign_keys="Account.guardian_id", back_populates="guardian"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    # Educational progress tracking
    educational_progress = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )
    trading_permissions = relationship(
        "UserPermission",
        foreign_keys="UserPermission.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    permissions_granted = relationship(
        "UserPermission", foreign_keys="UserPermission.granted_by_user_id"
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

    def sync_encrypted_email(self):
        """
        Synchronize the encrypted email with the plain email.

        This should be called whenever the email is changed.
        """
        # Using our field encryption system
        encrypted_value = EncryptedField("_encrypted_email")._get_encrypted_value(
            self.email
        )
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
        if not hasattr(self, "subscriptions") or not self.subscriptions:
            return None

        for subscription in self.subscriptions:
            if subscription.is_active and (
                not subscription.end_date or subscription.end_date > datetime.utcnow()
            ):
                return subscription

        return None

    def is_subscribed(self):
        """Check if user has an active paid subscription"""
        subscription = self.get_active_subscription()
        if subscription and subscription.plan in (
            SubscriptionPlan.PREMIUM,
            SubscriptionPlan.FAMILY,
        ):
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
            "basic_trading",
            "paper_trading",
            "basic_education",
            "market_data_basic",
            "portfolio_tracking",
        }

        # Premium plan features
        premium_features = {
            *free_features,
            "advanced_trading",
            "fractional_shares",
            "ai_recommendations",
            "unlimited_recurring_investments",
            "tax_loss_harvesting",
            "advanced_education",
            "market_data_advanced",
            "high_yield_savings",
            "retirement_accounts",
            "api_access",
        }

        # Family plan features
        family_features = {
            *premium_features,
            "custodial_accounts",
            "guardian_approval",
            "family_challenges",
            "educational_games",
            "multiple_retirement_accounts",
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

    def validate_risk_limits(self, amount: Decimal) -> bool:
        """Validate if an investment amount is within user's risk limits"""
        if not self.trading_enabled:
            return False

        # Check position size limit (percentage of portfolio)
        if self.max_position_size and hasattr(self, "portfolio") and self.portfolio:
            if self.portfolio.total_value > 0:
                position_percentage = (amount / self.portfolio.total_value) * 100
                if position_percentage > self.max_position_size:
                    return False

        return True

    def can_place_trade(self, trade_amount: Decimal = None) -> tuple[bool, str]:
        """Check if user can place a trade with optional amount validation"""
        if not self.is_active:
            return False, "Account is not active"

        if not self.trading_enabled:
            return False, "Trading is disabled for this account"

        if self.role == UserRole.MINOR and not hasattr(self, "_guardian_approved"):
            return False, "Minor accounts require guardian approval"

        if trade_amount and not self.validate_risk_limits(trade_amount):
            return False, "Trade amount exceeds risk limits"

        return True, "Trade allowed"

    def get_custodial_account_limit(self) -> int:
        """Get the maximum number of custodial accounts allowed"""
        if self.has_family_plan():
            return 5
        return 0

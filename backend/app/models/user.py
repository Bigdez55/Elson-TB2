import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Import canonical SubscriptionPlan from subscription models
from app.models.subscription import SubscriptionPlan


class UserRole(enum.Enum):
    ADULT = "adult"
    MINOR = "minor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # User role for family accounts
    role: Column[UserRole] = Column(
        Enum(UserRole), default=UserRole.ADULT, nullable=False
    )

    # Birthdate for age verification (stored as string for now)
    birthdate = Column(String(255), nullable=True)

    # Trading preferences
    risk_tolerance = Column(
        String(50), default="moderate"
    )  # conservative, moderate, aggressive
    trading_style = Column(
        String(50), default="long_term"
    )  # day_trading, swing, long_term

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # Two-factor authentication
    two_factor_enabled = Column(Boolean, default=False)

    # Account security
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    password_last_changed = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    portfolios = relationship(
        "Portfolio", back_populates="owner", foreign_keys="[Portfolio.owner_id]"
    )
    # accounts = relationship(
    #     "Account", foreign_keys="Account.user_id", back_populates="user"
    # )
    # guardian_accounts = relationship(
    #     "Account", foreign_keys="Account.guardian_id", back_populates="guardian"
    # )
    notifications = relationship("Notification", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")

    # Security relationships
    devices = relationship(
        "Device", back_populates="user", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    two_factor_config = relationship(
        "TwoFactorConfig",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    security_settings = relationship(
        "SecuritySettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    security_alerts = relationship(
        "SecurityAlert", back_populates="user", cascade="all, delete-orphan"
    )
    login_history = relationship(
        "LoginHistory", back_populates="user", cascade="all, delete-orphan"
    )
    security_audit_logs = relationship(
        "SecurityAuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    webauthn_credentials = relationship(
        "WebAuthnCredential", back_populates="user", cascade="all, delete-orphan"
    )

    # Educational and permissions relationships
    educational_progress = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )
    trading_permissions = relationship(
        "UserPermission",
        foreign_keys="UserPermission.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

    @property
    def is_adult(self):
        return self.role == UserRole.ADULT

    @property
    def is_minor(self):
        return self.role == UserRole.MINOR

    def get_subscription_tier(self):
        """Get the user's subscription tier - placeholder for future subscription implementation"""
        # TODO: Implement subscription checking when subscription model is added
        return SubscriptionPlan.FREE

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

    def get_custodial_account_limit(self) -> int:
        """Get the maximum number of custodial accounts allowed"""
        tier = self.get_subscription_tier()
        if tier == SubscriptionPlan.FAMILY:
            return 5
        return 0

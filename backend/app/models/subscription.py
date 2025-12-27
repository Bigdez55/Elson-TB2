from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Float,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.db.base import Base


class SubscriptionPlan(enum.Enum):
    """Subscription plan types"""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"


class BillingCycle(enum.Enum):
    """Billing cycle options"""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class PaymentMethod(enum.Enum):
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan: Column[SubscriptionPlan] = Column(Enum(SubscriptionPlan), nullable=False)
    billing_cycle: Column[BillingCycle] = Column(Enum(BillingCycle), nullable=False)
    price = Column(Float, nullable=False)  # Price per cycle

    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)  # Null means auto-renew
    auto_renew = Column(Boolean, default=True)
    trial_end_date = Column(DateTime, nullable=True)

    # Payment tracking
    payment_method_id = Column(String, nullable=True)
    payment_method_type: Column[PaymentMethod] = Column(Enum(PaymentMethod), nullable=True)
    encrypted_payment_details = Column(Text, nullable=True)  # AES-256 encrypted

    # PayPal specific fields (added in migration 20250401_add_paypal_support)
    paypal_agreement_id = Column(
        String, nullable=True
    )  # Billing agreement ID for recurring payments
    paypal_payer_id = Column(String, nullable=True)  # PayPal payer ID for the customer

    # Status tracking
    is_active = Column(Boolean, default=True)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription")
    history = relationship("SubscriptionHistory", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription {self.id}: {self.plan.value} for user {self.user_id}>"

    @property
    def is_in_trial(self):
        """Check if subscription is in trial period"""
        if self.trial_end_date and self.trial_end_date > datetime.utcnow():
            return True
        return False

    @property
    def days_until_renewal(self):
        """Get days until renewal or expiration"""
        if not self.end_date:
            return None

        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)

    @property
    def status(self):
        """Get human-readable subscription status"""
        if not self.is_active:
            return "Canceled"

        if self.is_in_trial:
            return "Trial"

        if self.end_date and self.end_date < datetime.utcnow():
            return "Expired"

        return "Active"

    @property
    def is_paypal(self):
        """Check if this is a PayPal subscription"""
        return self.payment_method_type == PaymentMethod.PAYPAL or (
            self.paypal_agreement_id is not None and self.paypal_payer_id is not None
        )


class SubscriptionPayment(Base):
    __tablename__ = "subscription_payments"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status: Column[PaymentStatus] = Column(Enum(PaymentStatus), nullable=False)

    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    provider_payment_id = Column(String, nullable=True)  # ID from payment processor
    provider_payment_data = Column(
        JSON, nullable=True
    )  # Additional data from payment processor

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.id}: {self.amount} for subscription {self.subscription_id}>"


class SubscriptionHistory(Base):
    """Tracks history of changes to subscriptions for auditing and analytics"""

    __tablename__ = "subscription_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(
        Integer, ForeignKey("subscriptions.id"), nullable=False, index=True
    )
    change_type = Column(String, nullable=False)  # created, updated, cancelled, etc.
    change_data = Column(JSON, nullable=True)  # Contains details of what changed
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", back_populates="history")

    def __repr__(self):
        return f"<SubscriptionHistory {self.id}: {self.change_type} for subscription {self.subscription_id}>"

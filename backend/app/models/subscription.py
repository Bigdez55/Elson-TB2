import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Subscription(Base):
    """Subscription model for premium features"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Stripe identifiers
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Subscription details
    plan_name = Column(String(100), nullable=False)  # e.g., "Basic", "Premium", "Pro"
    status = Column(String(50), nullable=False, default="active")  # active, cancelled, past_due, etc.
    amount = Column(Float, nullable=False)  # Monthly/yearly amount
    currency = Column(String(3), default="usd")
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly

    # Subscription period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Flags
    cancel_at_period_end = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Metadata
    metadata = Column(Text, nullable=True)  # JSON string for additional data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription")


class SubscriptionPayment(Base):
    """Payment records for subscriptions"""
    __tablename__ = "subscription_payments"

    id = Column(Integer, primary_key=True, index=True)

    # Subscription reference
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    # Payment identifiers
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_invoice_id = Column(String(255), nullable=True, index=True)

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    # Payment method
    payment_method_type = Column(String(50), nullable=True)  # card, bank_account
    last_four = Column(String(4), nullable=True)  # Last 4 digits of card/account

    # Error handling
    failure_message = Column(Text, nullable=True)
    failure_code = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

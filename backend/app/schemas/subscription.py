from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr, Field, validator

# Import canonical SubscriptionPlan from models
from app.models.subscription import SubscriptionPlan


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class ChangeType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    CANCELLED = "cancelled"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PLAN_CHANGED = "plan_changed"
    REACTIVATED = "reactivated"


# Base models
class SubscriptionBase(BaseModel):
    plan: SubscriptionPlan
    billing_cycle: BillingCycle
    price: float
    auto_renew: bool = True


class SubscriptionPaymentBase(BaseModel):
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    provider_payment_id: Optional[str] = None


class SubscriptionHistoryBase(BaseModel):
    change_type: ChangeType
    change_data: Optional[Dict[str, Any]] = None


# Create models
class SubscriptionCreate(SubscriptionBase):
    user_id: int
    payment_method_id: Optional[str] = None
    payment_method_type: Optional[PaymentMethod] = None
    trial_days: Optional[int] = None  # Days for trial period
    # PayPal specific fields
    paypal_agreement_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None


class SubscriptionPaymentCreate(SubscriptionPaymentBase):
    subscription_id: int
    provider_payment_data: Optional[Dict[str, Any]] = None


class SubscriptionHistoryCreate(SubscriptionHistoryBase):
    subscription_id: int


# Update models
class SubscriptionUpdate(BaseModel):
    plan: Optional[SubscriptionPlan] = None
    billing_cycle: Optional[BillingCycle] = None
    price: Optional[float] = None
    auto_renew: Optional[bool] = None
    payment_method_id: Optional[str] = None
    payment_method_type: Optional[PaymentMethod] = None
    is_active: Optional[bool] = None
    # PayPal specific fields
    paypal_agreement_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None


class SubscriptionPaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    provider_payment_id: Optional[str] = None
    provider_payment_data: Optional[Dict[str, Any]] = None


# Response models
class SubscriptionHistoryResponse(SubscriptionHistoryBase):
    id: int
    subscription_id: int
    changed_at: datetime

    class Config:
        orm_mode = True


class SubscriptionPaymentResponse(SubscriptionPaymentBase):
    id: int
    subscription_id: int
    payment_date: datetime
    provider_payment_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    payment_method_id: Optional[str] = None
    payment_method_type: Optional[PaymentMethod] = None
    paypal_agreement_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None
    is_active: bool
    canceled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    payments: List[SubscriptionPaymentResponse] = []
    history: List[SubscriptionHistoryResponse] = []
    status: str  # Computed field from model property
    is_paypal: bool  # Computed field from model property

    class Config:
        orm_mode = True


# Payment processing
class CreditCardInfo(BaseModel):
    card_number: str
    expiry_month: int
    expiry_year: int
    cvc: str
    cardholder_name: str
    billing_address: Optional[Dict[str, str]] = None


class BankAccountInfo(BaseModel):
    account_number: str
    routing_number: str
    account_type: str
    account_holder_name: str


class PaymentMethodCreate(BaseModel):
    type: PaymentMethod
    credit_card: Optional[CreditCardInfo] = None
    bank_account: Optional[BankAccountInfo] = None
    save_for_future: bool = True


class SubscriptionWithPaymentCreate(SubscriptionCreate):
    payment_method: PaymentMethodCreate


# Subscription management
class CancelSubscription(BaseModel):
    reason: Optional[str] = None
    immediate: bool = (
        False  # If true, cancel immediately, otherwise at end of billing period
    )


class ChangeSubscriptionPlan(BaseModel):
    new_plan: SubscriptionPlan
    new_billing_cycle: Optional[BillingCycle] = None
    prorate: bool = True


# Feature access
class FeatureAccessCheck(BaseModel):
    feature: str


class FeatureAccessResponse(BaseModel):
    feature: str
    has_access: bool
    required_plan: Optional[SubscriptionPlan] = None

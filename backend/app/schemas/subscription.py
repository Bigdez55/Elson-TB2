from typing import Optional
from pydantic import BaseModel, Field, validator


class CreditCardInfo(BaseModel):
    """Schema for credit card information"""
    card_number: str = Field(..., description="Credit card number")
    expiry_month: int = Field(..., ge=1, le=12, description="Expiration month (1-12)")
    expiry_year: int = Field(..., description="Expiration year (4 digits)")
    cvc: str = Field(..., min_length=3, max_length=4, description="Card security code")
    cardholder_name: str = Field(..., description="Name on the card")
    billing_zip: Optional[str] = Field(None, description="Billing ZIP code")

    @validator('card_number')
    def validate_card_number(cls, v):
        """Validate card number format"""
        # Remove spaces and hyphens
        card_number = v.replace(' ', '').replace('-', '')

        # Check if it's all digits
        if not card_number.isdigit():
            raise ValueError('Card number must contain only digits')

        # Check length (typically 13-19 digits)
        if len(card_number) < 13 or len(card_number) > 19:
            raise ValueError('Card number must be between 13 and 19 digits')

        return card_number

    @validator('cvc')
    def validate_cvc(cls, v):
        """Validate CVC format"""
        if not v.isdigit():
            raise ValueError('CVC must contain only digits')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "card_number": "4242424242424242",
                "expiry_month": 12,
                "expiry_year": 2025,
                "cvc": "123",
                "cardholder_name": "John Doe",
                "billing_zip": "12345"
            }
        }


class BankAccountInfo(BaseModel):
    """Schema for bank account information"""
    account_number: str = Field(..., description="Bank account number")
    routing_number: str = Field(..., description="Bank routing number (9 digits for US)")
    account_type: str = Field(..., description="Account type: checking or savings")
    account_holder_name: str = Field(..., description="Name on the bank account")

    @validator('routing_number')
    def validate_routing_number(cls, v):
        """Validate routing number format (US banks)"""
        # Remove spaces and hyphens
        routing = v.replace(' ', '').replace('-', '')

        # Check if it's all digits
        if not routing.isdigit():
            raise ValueError('Routing number must contain only digits')

        # US routing numbers are 9 digits
        if len(routing) != 9:
            raise ValueError('US routing number must be exactly 9 digits')

        return routing

    @validator('account_type')
    def validate_account_type(cls, v):
        """Validate account type"""
        valid_types = ['checking', 'savings']
        if v.lower() not in valid_types:
            raise ValueError(f'Account type must be one of: {", ".join(valid_types)}')
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "account_number": "000123456789",
                "routing_number": "110000000",
                "account_type": "checking",
                "account_holder_name": "John Doe"
            }
        }


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription"""
    plan_name: str = Field(..., description="Subscription plan name")
    price_id: str = Field(..., description="Stripe price ID")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    billing_cycle: str = Field("monthly", description="Billing cycle: monthly or yearly")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_name": "Premium",
                "price_id": "price_1234567890",
                "payment_method_id": "pm_1234567890",
                "billing_cycle": "monthly"
            }
        }


class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: int
    user_id: int
    plan_name: str
    status: str
    amount: float
    currency: str
    billing_cycle: str
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool
    is_active: bool

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "plan_name": "Premium",
                "status": "active",
                "amount": 29.99,
                "currency": "usd",
                "billing_cycle": "monthly",
                "current_period_end": "2024-12-31T23:59:59Z",
                "cancel_at_period_end": False,
                "is_active": True
            }
        }


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    subscription_id: int
    amount: float
    currency: str
    status: str
    payment_method_type: Optional[str] = None
    last_four: Optional[str] = None
    paid_at: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "subscription_id": 1,
                "amount": 29.99,
                "currency": "usd",
                "status": "completed",
                "payment_method_type": "card",
                "last_four": "4242",
                "paid_at": "2024-01-15T12:00:00Z"
            }
        }

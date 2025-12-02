from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime, date
from uuid import UUID
from enum import Enum

class MinorCreate(BaseModel):
    """Schema for creating a new minor account"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    birthdate: date
    
    @validator('birthdate')
    def validate_birthdate(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age >= 18:
            raise ValueError('Minor must be under 18 years old')
        return v

class MinorResponse(BaseModel):
    """Schema for minor account information"""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    birthdate: date
    guardian_id: int
    guardian_name: str
    account_id: Optional[int] = None
    
    class Config:
        orm_mode = True

class GuardianMinorRelationship(BaseModel):
    """Schema for guardian-minor relationship"""
    guardian_id: int
    minor_id: int
    relationship_type: str = "custodial"  # Could be other types in the future
    
    class Config:
        orm_mode = True

class ApproveTradeRequest(BaseModel):
    """Schema for approving/rejecting a minor's trade"""
    approved: bool
    rejection_reason: Optional[str] = None
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v, values):
        # If trade is rejected, reason is required
        if not values.get('approved') and (v is None or v.strip() == ''):
            raise ValueError('Rejection reason is required when rejecting a trade')
        return v

class MinorTradeResponse(BaseModel):
    """Schema for displaying a minor's trade with additional info"""
    trade_id: int
    minor_id: int
    minor_name: str
    symbol: str
    quantity: float
    price: float
    trade_type: str
    created_at: datetime
    status: str
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class GuardianStatusResponse(BaseModel):
    """Schema for guardian status and statistics."""
    is_guardian: bool
    minor_count: int
    total_trades: int
    pending_approvals: int
    two_factor_enabled: bool
    requires_2fa_setup: bool
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "is_guardian": True,
                "minor_count": 2,
                "total_trades": 15,
                "pending_approvals": 3,
                "two_factor_enabled": True,
                "requires_2fa_setup": False
            }
        }

class NotificationType(str, Enum):
    """Types of notifications for guardians."""
    TRADE_REQUEST = "trade_request"
    TRADE_EXECUTED = "trade_executed"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    LOGIN = "login"
    SETTINGS_CHANGE = "settings_change"
    REQUEST = "request"

class GuardianNotificationResponse(BaseModel):
    """Schema for guardian notifications."""
    id: str
    minor_account_id: int
    minor_name: str
    type: NotificationType
    message: str
    requires_action: bool
    timestamp: datetime
    is_read: bool
    trade_id: Optional[int] = None
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    trade_type: Optional[str] = None
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "1",
                "minor_account_id": 123,
                "minor_name": "Alex Smith",
                "type": "trade_request",
                "message": "Requested permission to trade AAPL",
                "requires_action": True,
                "timestamp": "2025-03-21T12:34:56",
                "is_read": False,
                "trade_id": 456,
                "symbol": "AAPL",
                "quantity": 1.0,
                "price": 150.0,
                "trade_type": "buy"
            }
        }
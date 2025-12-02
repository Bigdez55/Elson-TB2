from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

from .base import TimestampedSchema

class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)
    
    @validator("password")
    def password_complexity(cls, v):
        """Validate password complexity"""
        from ..core.auth import validate_password_complexity
        
        if not validate_password_complexity(v):
            raise ValueError(
                "Password must be at least 8 characters long and contain at least "
                "one uppercase letter, one lowercase letter, one digit, and one special character"
            )
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(UserBase, TimestampedSchema):
    """Schema for user response data"""
    id: int
    is_active: bool
    
    class Config:
        orm_mode = True

class TokenData(BaseModel):
    """Schema for JWT token data"""
    email: Optional[str] = None
    user_id: Optional[int] = None
    token_id: Optional[str] = None
    is_refresh: Optional[bool] = False
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int


class UserTwoFactorCreate(BaseModel):
    """Schema for enabling 2FA"""
    secret: str
    code: str


class UserTwoFactorVerify(BaseModel):
    """Schema for verifying 2FA"""
    code: str


class UserTwoFactorResponse(BaseModel):
    """Schema for 2FA response data"""
    secret: str
    qr_uri: str
    backup_codes: List[str]


class UserTwoFactorStatus(BaseModel):
    """Schema for 2FA status"""
    enabled: bool
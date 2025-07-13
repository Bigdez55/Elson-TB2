from typing import Optional

from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    risk_tolerance: str = "moderate"
    trading_style: str = "long_term"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    risk_tolerance: str
    trading_style: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse

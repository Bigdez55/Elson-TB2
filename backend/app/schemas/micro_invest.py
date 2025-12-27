from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class RoundupTransactionCreate(BaseModel):
    user_id: int
    transaction_amount: float = Field(
        ..., gt=0, description="Original transaction amount"
    )
    roundup_amount: float = Field(..., gt=0, description="Amount to round up")
    description: Optional[str] = None
    source: Optional[str] = None

    @validator("roundup_amount")
    def validate_roundup_amount(cls, v, values):
        if "transaction_amount" in values and v > values["transaction_amount"]:
            raise ValueError("Roundup amount cannot exceed transaction amount")
        return v


class RoundupTransactionUpdate(BaseModel):
    status: Optional[str] = None
    invested_at: Optional[datetime] = None
    trade_id: Optional[str] = None


class UserSettingsCreate(BaseModel):
    user_id: int
    micro_investing_enabled: bool = False
    roundup_enabled: bool = False
    roundup_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)
    roundup_frequency: str = "weekly"
    roundup_threshold: float = Field(default=5.0, ge=1.0, le=100.0)
    micro_invest_target_type: str = "default_portfolio"
    micro_invest_portfolio_id: Optional[int] = None
    micro_invest_symbol: Optional[str] = None
    notify_on_roundup: bool = True
    notify_on_investment: bool = True
    max_weekly_roundup: float = Field(default=50.0, ge=1.0, le=1000.0)
    max_monthly_micro_invest: float = Field(default=200.0, ge=1.0, le=5000.0)


class UserSettingsUpdate(BaseModel):
    micro_investing_enabled: Optional[bool] = None
    roundup_enabled: Optional[bool] = None
    roundup_multiplier: Optional[float] = Field(None, ge=0.1, le=5.0)
    roundup_frequency: Optional[str] = None
    roundup_threshold: Optional[float] = Field(None, ge=1.0, le=100.0)
    micro_invest_target_type: Optional[str] = None
    micro_invest_portfolio_id: Optional[int] = None
    micro_invest_symbol: Optional[str] = None
    notify_on_roundup: Optional[bool] = None
    notify_on_investment: Optional[bool] = None
    max_weekly_roundup: Optional[float] = Field(None, ge=1.0, le=1000.0)
    max_monthly_micro_invest: Optional[float] = Field(None, ge=1.0, le=5000.0)


class MicroInvestmentCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    investment_amount: float = Field(..., gt=0, le=10000)
    portfolio_id: int


class RoundupSummary(BaseModel):
    total_roundups: int
    total_amount: float
    pending_amount: float
    invested_amount: float
    total_investments: int
    last_investment_date: Optional[datetime]


class MicroInvestStats(BaseModel):
    total_micro_invested: float
    total_transactions: int
    average_transaction: float
    total_roundups: int
    total_roundup_amount: float
    this_month: Dict[str, Any]
    last_month: Dict[str, Any]


class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    micro_investing_enabled: bool
    roundup_enabled: bool
    roundup_multiplier: float
    roundup_frequency: str
    roundup_threshold: float
    micro_invest_target_type: str
    micro_invest_portfolio_id: Optional[int]
    micro_invest_symbol: Optional[str]
    notify_on_roundup: bool
    notify_on_investment: bool
    max_weekly_roundup: float
    max_monthly_micro_invest: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoundupTransactionResponse(BaseModel):
    id: int
    user_id: int
    transaction_amount: float
    roundup_amount: float
    transaction_date: datetime
    description: Optional[str]
    source: Optional[str]
    status: str
    invested_at: Optional[datetime]
    trade_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

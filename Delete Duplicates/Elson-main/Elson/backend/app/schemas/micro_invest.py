from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, conint, confloat, validator
from datetime import datetime
from enum import Enum

# Enum definitions for the schemas
class RoundupFrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    THRESHOLD = "threshold"

class MicroInvestTargetEnum(str, Enum):
    DEFAULT_PORTFOLIO = "default_portfolio"
    SPECIFIC_PORTFOLIO = "specific_portfolio"
    SPECIFIC_SYMBOL = "specific_symbol"
    RECOMMENDED_ETF = "recommended_etf"

# Base schemas
class RoundupTransactionBase(BaseModel):
    transaction_amount: float = Field(..., description="Original transaction amount")
    roundup_amount: float = Field(..., description="Amount rounded up (difference)")
    description: Optional[str] = Field(None, description="Description of the transaction")
    source: Optional[str] = Field(None, description="Source of transaction (e.g., 'card', 'bank')")

class UserSettingsBase(BaseModel):
    micro_investing_enabled: bool = Field(False, description="Whether micro-investing is enabled")
    roundup_enabled: bool = Field(False, description="Whether roundups are enabled")
    roundup_multiplier: float = Field(1.0, description="Multiplier for roundups (1x, 2x, 3x)")
    roundup_frequency: RoundupFrequencyEnum = Field(RoundupFrequencyEnum.WEEKLY, description="How often to invest collected roundups")
    roundup_threshold: float = Field(5.0, description="Minimum amount to trigger investment")
    micro_invest_target_type: MicroInvestTargetEnum = Field(MicroInvestTargetEnum.DEFAULT_PORTFOLIO, description="Where to invest micro-investments")
    micro_invest_portfolio_id: Optional[int] = Field(None, description="Target portfolio ID for micro-investments")
    micro_invest_symbol: Optional[str] = Field(None, description="Target symbol for micro-investments")
    notify_on_roundup: bool = Field(True, description="Whether to notify on roundup collection")
    notify_on_investment: bool = Field(True, description="Whether to notify on investment")
    max_weekly_roundup: float = Field(100.0, description="Maximum weekly roundup amount")
    max_monthly_micro_invest: float = Field(500.0, description="Maximum monthly micro-investment amount")

class MicroInvestmentBase(BaseModel):
    portfolio_id: int = Field(..., description="Portfolio ID for the investment")
    symbol: str = Field(..., description="Symbol to invest in")
    investment_amount: float = Field(..., gt=0, description="Amount to invest in dollars")
    description: Optional[str] = Field(None, description="Optional description for the investment")
    
    @validator('investment_amount')
    def validate_investment_amount(cls, v):
        if v < 0.01:
            raise ValueError('Investment amount must be at least $0.01')
        return v

# Create schemas
class RoundupTransactionCreate(RoundupTransactionBase):
    user_id: int

class UserSettingsCreate(UserSettingsBase):
    user_id: int

class MicroInvestmentCreate(MicroInvestmentBase):
    pass

# Update schemas
class UserSettingsUpdate(BaseModel):
    micro_investing_enabled: Optional[bool] = None
    roundup_enabled: Optional[bool] = None
    roundup_multiplier: Optional[float] = None
    roundup_frequency: Optional[RoundupFrequencyEnum] = None
    roundup_threshold: Optional[float] = None
    micro_invest_target_type: Optional[MicroInvestTargetEnum] = None
    micro_invest_portfolio_id: Optional[int] = None
    micro_invest_symbol: Optional[str] = None
    notify_on_roundup: Optional[bool] = None
    notify_on_investment: Optional[bool] = None
    max_weekly_roundup: Optional[float] = None
    max_monthly_micro_invest: Optional[float] = None

class RoundupTransactionUpdate(BaseModel):
    status: Optional[str] = None
    trade_id: Optional[int] = None
    invested_at: Optional[datetime] = None

# Response schemas
class RoundupTransactionResponse(RoundupTransactionBase):
    id: int
    user_id: int
    transaction_date: datetime
    status: str
    invested_at: Optional[datetime] = None
    trade_id: Optional[int] = None
    
    class Config:
        orm_mode = True

class UserSettingsResponse(UserSettingsBase):
    id: int
    user_id: int
    bank_account_linked: bool
    card_accounts_linked: bool
    completed_micro_invest_education: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class MicroInvestmentResponse(MicroInvestmentBase):
    id: int
    user_id: int
    created_at: datetime
    status: str
    trade_id: Optional[int] = None
    
    class Config:
        orm_mode = True

# Summary schemas
class RoundupSummary(BaseModel):
    total_roundups: int
    total_amount: float
    pending_amount: float
    invested_amount: float
    total_investments: int
    last_investment_date: Optional[datetime] = None

class MicroInvestStats(BaseModel):
    total_micro_invested: float
    total_transactions: int
    average_transaction: float
    total_roundups: int
    total_roundup_amount: float
    this_month: Dict[str, float]
    last_month: Dict[str, float]
    
# Linked account schemas
class LinkedAccountBase(BaseModel):
    account_type: str
    account_name: str
    account_mask: str
    institution_name: str

class LinkedAccountCreate(LinkedAccountBase):
    access_token: str
    account_id: str
    
class LinkedAccountResponse(LinkedAccountBase):
    id: str
    created_at: datetime
    last_transaction_sync: Optional[datetime] = None
    
    class Config:
        orm_mode = True
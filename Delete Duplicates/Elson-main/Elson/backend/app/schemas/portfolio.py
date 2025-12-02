from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

from .base import TimestampedSchema

class PositionBase(BaseModel):
    """Base schema for position data."""
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: Decimal = Field(..., gt=0)
    average_price: Decimal = Field(..., gt=0)
    
    # Fractional share support
    is_fractional: bool = Field(False, description="Whether this is a fractional position")

class PositionCreate(PositionBase):
    """Schema for creating a new position."""
    portfolio_id: int
    
    # Optional fields for position creation
    current_price: Optional[Decimal] = Field(None, gt=0)
    asset_class: Optional[str] = None
    sector: Optional[str] = None

class PositionResponse(PositionBase, TimestampedSchema):
    """Schema for position response with calculated values."""
    id: int
    current_price: Optional[Decimal] = None
    
    # Stored calculated values
    market_value: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    unrealized_pl: Optional[Decimal] = None
    unrealized_pl_percent: Optional[Decimal] = None
    
    # Additional metadata
    sector: Optional[str] = None
    asset_class: Optional[str] = None
    last_trade_date: Optional[datetime] = None
    
    # Fractional share support
    minimum_investment: Optional[Decimal] = None
    
    class Config:
        orm_mode = True
        
    # Fallback calculators if stored values aren't available
    
    @property
    def calculated_market_value(self) -> Decimal:
        """Calculate market value if not provided."""
        if self.market_value is not None:
            return self.market_value
            
        if self.current_price:
            return self.quantity * self.current_price
        return Decimal('0')

    @property
    def calculated_cost_basis(self) -> Decimal:
        """Calculate cost basis if not provided."""
        if self.cost_basis is not None:
            return self.cost_basis
            
        return self.quantity * self.average_price

    @property
    def calculated_unrealized_pl(self) -> Decimal:
        """Calculate unrealized P&L if not provided."""
        if self.unrealized_pl is not None:
            return self.unrealized_pl
        
        return self.calculated_market_value - self.calculated_cost_basis

    @property
    def calculated_unrealized_pl_percent(self) -> Decimal:
        """Calculate unrealized P&L percent if not provided."""
        if self.unrealized_pl_percent is not None:
            return self.unrealized_pl_percent
            
        cost_basis = self.calculated_cost_basis
        if cost_basis > 0:
            return (self.calculated_unrealized_pl / cost_basis) * 100
        return Decimal('0')

class PortfolioBase(BaseModel):
    """Base schema for portfolio data"""
    cash_balance: Decimal = Field(..., ge=0)

class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio"""
    user_id: int

class PortfolioResponse(PortfolioBase, TimestampedSchema):
    """Schema for portfolio response"""
    id: int
    total_value: Decimal
    invested_amount: Decimal
    positions: List[PositionResponse]
    total_pl: Optional[Decimal]
    total_pl_percent: Optional[Decimal]
    daily_pl: Optional[Decimal]
    daily_pl_percent: Optional[Decimal]

class PortfolioStats(BaseModel):
    """Schema for portfolio performance statistics"""
    start_date: datetime
    end_date: datetime
    starting_value: Decimal
    ending_value: Decimal
    total_return: Decimal
    total_return_percent: Decimal
    annualized_return: Decimal
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[Decimal]
    best_day: Optional[Dict[str, Decimal]]
    worst_day: Optional[Dict[str, Decimal]]
    volatility: Optional[float]

class PortfolioHistory(BaseModel):
    """Schema for portfolio value history"""
    date: datetime
    total_value: Decimal
    cash_balance: Decimal
    invested_amount: Decimal
    daily_pl: Optional[Decimal]
    daily_pl_percent: Optional[Decimal]
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

from .base import TimestampedSchema
from ..models.trade import OrderType, OrderSide, TradeStatus, InvestmentType, TradeSource

class TradeBase(BaseModel):
    """Base schema for trade data"""
    symbol: str = Field(..., min_length=1, max_length=10)
    order_type: OrderType
    side: OrderSide
    quantity: Decimal = Field(..., gt=0)
    limit_price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)

    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()

class TradeCreate(BaseModel):
    """Schema for creating a new trade"""
    portfolio_id: int
    symbol: str
    quantity: float = Field(..., gt=0)
    trade_type: str = Field(..., description="Type of trade (buy or sell)")

class DollarBasedInvestmentBase(BaseModel):
    """Base schema for dollar-based investments."""
    symbol: str = Field(..., description="Symbol of the asset to trade", min_length=1, max_length=10)
    investment_amount: Decimal = Field(..., description="Dollar amount to invest", ge=1.0)
    portfolio_id: int = Field(..., description="Portfolio ID")
    trade_type: str = Field(..., description="Trade type (buy or sell)")
    note: Optional[str] = Field(None, description="Optional note for the investment")
    
    @validator('investment_amount')
    def validate_investment_amount(cls, v):
        """Validate investment amount is reasonable."""
        min_amount = Decimal('1.00')
        max_amount = Decimal('1000000.00')
        
        if v < min_amount:
            raise ValueError(f"Investment amount must be at least ${min_amount}")
        
        if v > max_amount:
            raise ValueError(f"Investment amount cannot exceed ${max_amount}")
            
        return v
    
    @validator('trade_type')
    def validate_trade_type(cls, v):
        """Validate trade type."""
        if v.lower() not in ['buy', 'sell']:
            raise ValueError("Trade type must be 'buy' or 'sell'")
        return v.lower()
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()


class DollarBasedInvestmentCreate(DollarBasedInvestmentBase):
    """Schema for creating a new dollar-based investment."""
    pass


class RecurringInvestmentBase(DollarBasedInvestmentBase):
    """Base schema for recurring investments."""
    frequency: str = Field(..., description="Frequency of recurring investment (daily, weekly, monthly, quarterly)")
    start_date: datetime = Field(..., description="Date to start the recurring investment")
    end_date: Optional[datetime] = Field(None, description="Date to end the recurring investment (optional)")
    description: Optional[str] = Field(None, description="Description or purpose of the recurring investment")
    
    @validator('frequency')
    def validate_frequency(cls, v):
        """Validate frequency."""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
        if v.lower() not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {', '.join(valid_frequencies)}")
        return v.lower()
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date is after start date."""
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v


class RecurringInvestmentCreate(RecurringInvestmentBase):
    """Schema for creating a new recurring investment."""
    pass


class RecurringInvestmentUpdate(BaseModel):
    """Schema for updating an existing recurring investment."""
    investment_amount: Optional[Decimal] = Field(None, description="Dollar amount to invest", ge=1.0)
    frequency: Optional[str] = Field(None, description="Frequency of recurring investment (daily, weekly, monthly, quarterly)")
    end_date: Optional[datetime] = Field(None, description="Date to end the recurring investment")
    is_active: Optional[bool] = Field(None, description="Whether the recurring investment is active")
    description: Optional[str] = Field(None, description="Description or purpose of the recurring investment")
    
    @validator('frequency')
    def validate_frequency(cls, v):
        """Validate frequency."""
        if v is None:
            return v
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
        if v.lower() not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {', '.join(valid_frequencies)}")
        return v.lower()

    @validator('investment_amount')
    def validate_investment_amount(cls, v):
        """Validate investment amount is reasonable."""
        if v is None:
            return v
        
        min_amount = Decimal('1.00')
        max_amount = Decimal('1000000.00')
        
        if v < min_amount:
            raise ValueError(f"Investment amount must be at least ${min_amount}")
        
        if v > max_amount:
            raise ValueError(f"Investment amount cannot exceed ${max_amount}")
            
        return v


class RecurringInvestmentResponse(TimestampedSchema):
    """Schema for recurring investment response."""
    id: int
    user_id: int
    portfolio_id: int
    symbol: str
    investment_amount: float
    frequency: str
    start_date: datetime
    end_date: Optional[datetime] = None
    next_investment_date: datetime
    last_execution_date: Optional[datetime] = None
    is_active: bool
    execution_count: int
    description: Optional[str] = None
    
    class Config:
        orm_mode = True


class QuantityBasedTradeCreate(TradeCreate):
    """Schema for creating a new quantity-based trade."""
    quantity: Decimal = Field(..., description="Quantity to trade")
    price: Optional[Decimal] = Field(None, description="Limit price (for limit orders)")

class TradeUpdate(BaseModel):
    """Schema for updating a trade"""
    status: Optional[TradeStatus]
    filled_quantity: Optional[Decimal] = Field(None, ge=0)
    filled_price: Optional[Decimal] = Field(None, gt=0)
    broker_order_id: Optional[str] = None
    broker_status: Optional[str] = None
    average_price: Optional[Decimal] = Field(None, gt=0)
    commission: Optional[Decimal] = Field(None, ge=0)

class TradeResponse(TimestampedSchema):
    """Schema for trade response"""
    id: int
    portfolio_id: int
    symbol: str
    quantity: Optional[float]
    price: Optional[float]
    trade_type: str
    status: str
    total_amount: Optional[float]
    
    # Fractional share details
    is_fractional: Optional[bool] = False
    investment_amount: Optional[float] = None
    investment_type: Optional[str] = None
    filled_quantity: Optional[float] = None
    average_price: Optional[float] = None
    parent_order_id: Optional[int] = None
    trade_source: Optional[str] = None
    
    # Recurring investment details
    recurring_investment_id: Optional[int] = None
    
    # Broker details
    broker_order_id: Optional[str] = None
    broker_status: Optional[str] = None
    commission: Optional[float] = None
    executed_at: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class OrderBook(BaseModel):
    """Schema for order book data"""
    symbol: str
    buy_orders: List[TradeResponse]
    sell_orders: List[TradeResponse]
    timestamp: datetime

class MarketDataResponse(BaseModel):
    """Schema for market data"""
    symbol: str
    price: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    timestamp: datetime
    source: str

    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()

class WSMarketData(BaseModel):
    """Schema for WebSocket market data updates"""
    type: str = "market_data"
    data: dict
    timestamp: datetime


class TradeStatusUpdate(BaseModel):
    """Schema for updating trade status."""
    status: str = Field(..., description="New status for the trade")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status."""
        try:
            TradeStatus(v)
            return v
        except ValueError:
            valid_statuses = [s.value for s in TradeStatus]
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")


class TradeBatch(BaseModel):
    """Schema for batch trading."""
    trades: List[Union[QuantityBasedTradeCreate, DollarBasedInvestmentCreate]]
    batch_note: Optional[str] = Field(None, description="Note for the batch")


class TradeAggregationResponse(BaseModel):
    """Schema for trade aggregation statistics."""
    orders_aggregated: int
    parent_orders_created: int
    symbols_processed: int
    errors: int
    
    
class TradingConfig(BaseModel):
    """Schema for trading configuration."""
    minInvestmentAmount: float = Field(..., description="Minimum investment amount in dollars")
    maxInvestmentAmount: float = Field(..., description="Maximum investment amount in dollars")
    fractionalSharesEnabled: bool = Field(..., description="Whether fractional shares are enabled")
    dollarBasedTradingEnabled: bool = Field(..., description="Whether dollar-based trading is enabled")
    supportedOrderTypes: List[str] = Field(..., description="List of supported order types")
    availableTradingHours: Dict[str, str] = Field(..., description="Available trading hours")
    minFractionalQuantity: float = Field(..., description="Minimum fractional quantity allowed")
    investmentTiers: List[Dict[str, Any]] = Field(..., description="Investment tiers configuration")
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator

from app.models.trade import OrderType, TradeStatus, TradeType


class TradeOrderRequest(BaseModel):
    symbol: str
    trade_type: TradeType
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    strategy: Optional[str] = "manual"
    notes: Optional[str] = None

    @validator("symbol")
    def symbol_must_be_uppercase(cls, v):
        return v.upper()

    @validator("quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

    @validator("limit_price")
    def validate_limit_price(cls, v, values):
        if values.get("order_type") == OrderType.LIMIT and v is None:
            raise ValueError("Limit price required for limit orders")
        if v is not None and v <= 0:
            raise ValueError("Limit price must be positive")
        return v


class TradeResponse(BaseModel):
    id: int
    symbol: str
    trade_type: TradeType
    order_type: OrderType
    quantity: float
    price: Optional[float]
    filled_quantity: float
    filled_price: Optional[float]
    status: TradeStatus
    total_cost: Optional[float]
    commission: float
    fees: float
    strategy: Optional[str]
    notes: Optional[str]
    is_paper_trade: bool
    created_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TradeExecutionResponse(BaseModel):
    id: int
    trade_id: int
    executed_quantity: float
    executed_price: float
    execution_time: datetime
    execution_id: Optional[str]
    broker_commission: float

    class Config:
        from_attributes = True


class OrderCancelRequest(BaseModel):
    trade_id: int


class TradingStatsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_loss: float
    average_profit_loss: float
    largest_win: float
    largest_loss: float
    total_commission: float


class PositionResponse(BaseModel):
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_percentage: float
    asset_type: str

    class Config:
        from_attributes = True

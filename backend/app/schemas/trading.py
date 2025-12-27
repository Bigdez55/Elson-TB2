"""
Trading Schemas

Pydantic models for trading-related API requests and responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OrderSideEnum(str, Enum):
    """Order side enumeration"""

    BUY = "buy"
    SELL = "sell"


class OrderStatusEnum(str, Enum):
    """Order status enumeration"""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class RiskProfileEnum(str, Enum):
    """Risk profile enumeration"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class TradingSignalResponse(BaseModel):
    """Trading signal response model"""

    symbol: str
    action: str = Field(..., description="Trading action: buy, sell, or hold")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    price: float = Field(..., gt=0, description="Current price")
    timestamp: str = Field(..., description="Signal generation timestamp")
    indicators: Dict[str, float] = Field(
        default_factory=dict, description="Technical indicators"
    )
    reason: str = Field(..., description="Reason for the signal")
    stop_loss: Optional[float] = Field(None, description="Stop loss level")
    take_profit: Optional[float] = Field(None, description="Take profit level")
    ai_confidence: Optional[float] = Field(None, description="AI model confidence")
    ai_prediction: Optional[float] = Field(None, description="AI model prediction")
    combined_confidence: Optional[float] = Field(
        None, description="Combined strategy and AI confidence"
    )


class AdvancedTradingRequest(BaseModel):
    """Advanced trading request model"""

    portfolio_id: int = Field(..., description="Portfolio ID to trade")
    symbols: Optional[List[str]] = Field(
        None, description="Symbols to trade (optional)"
    )
    risk_profile: RiskProfileEnum = Field(
        RiskProfileEnum.MODERATE, description="Risk profile to use"
    )
    enable_ai: bool = Field(True, description="Enable AI model predictions")
    auto_execute: bool = Field(False, description="Automatically execute trades")


class RiskProfileUpdate(BaseModel):
    """Risk profile update model"""

    risk_profile: RiskProfileEnum = Field(..., description="New risk profile")


class PerformanceMetrics(BaseModel):
    """Performance metrics model"""

    total_trades: int = Field(..., description="Total number of trades")
    successful_trades: int = Field(..., description="Number of successful trades")
    total_return: float = Field(..., description="Total return")
    win_rate: float = Field(..., description="Win rate percentage")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status model"""

    trading_allowed: bool = Field(..., description="Whether trading is allowed")
    breaker_status: str = Field(..., description="Current breaker status")
    active_breakers: Dict[str, Any] = Field(
        default_factory=dict, description="Active circuit breakers"
    )
    position_sizing_multiplier: float = Field(
        ..., description="Position sizing multiplier"
    )


class TradeOrderRequest(BaseModel):
    """Trade order request model"""

    symbol: str = Field(..., description="Symbol to trade")
    trade_type: str = Field(..., description="Trade type: buy or sell")
    order_type: str = Field(..., description="Order type: market or limit")
    quantity: float = Field(..., gt=0, description="Quantity to trade")
    limit_price: Optional[float] = Field(
        None, description="Limit price for limit orders"
    )
    stop_price: Optional[float] = Field(None, description="Stop price for stop orders")
    strategy: Optional[str] = Field(None, description="Strategy name")
    notes: Optional[str] = Field(None, description="Additional notes")


class OrderCancelRequest(BaseModel):
    """Order cancellation request model"""

    trade_id: int = Field(..., description="Trade ID to cancel")


class TradeResponse(BaseModel):
    """Trade response model"""

    id: int
    symbol: str
    trade_type: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    created_at: str
    executed_at: Optional[str] = None
    notes: Optional[str] = None


class PositionResponse(BaseModel):
    """Position response model"""

    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_percentage: float
    asset_type: Optional[str] = None


class TradingStatsResponse(BaseModel):
    """Trading statistics response model"""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_loss: float
    average_profit_loss: float
    largest_win: float
    largest_loss: float
    total_commission: float


class TradingAccountResponse(BaseModel):
    """Trading account response model"""

    account_id: str = Field(..., description="Account identifier")
    account_type: str = Field(..., description="Account type: paper or live")
    buying_power: float = Field(..., description="Available buying power")
    cash_balance: float = Field(..., description="Cash balance")
    portfolio_value: float = Field(..., description="Total portfolio value")
    day_trade_count: int = Field(0, description="Day trade count (rolling 5 days)")
    pattern_day_trader: bool = Field(False, description="Pattern day trader flag")
    trading_blocked: bool = Field(False, description="Whether trading is blocked")
    last_equity_close: float = Field(0.0, description="Previous day equity close")
    created_at: str = Field(..., description="Account creation timestamp")


class BatchDataResponse(BaseModel):
    """Batch data response for efficient data fetching"""

    portfolio: Dict[str, Any] = Field(..., description="Portfolio summary")
    positions: List[PositionResponse] = Field(..., description="Current positions")
    recent_orders: List[TradeResponse] = Field(..., description="Recent orders")
    account: TradingAccountResponse = Field(..., description="Account info")


class SyncModesResponse(BaseModel):
    """Response for trading mode sync operation"""

    success: bool = Field(..., description="Whether sync was successful")
    message: str = Field(..., description="Status message")
    paper_data_count: int = Field(0, description="Paper trading data count")
    live_data_count: int = Field(0, description="Live trading data count")

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from uuid import UUID

class RecommendationResponse(BaseModel):
    """Schema for AI investment recommendations"""
    symbol: str
    action: str  # "buy" or "sell"
    quantity: float
    price: float
    confidence: float  # 0.0 to 1.0
    strategy: str
    reason: str
    timestamp: datetime
    
    @validator('action')
    def validate_action(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Action must be "buy" or "sell"')
        return v.lower()
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    class Config:
        orm_mode = True

class CreateTradeRequest(BaseModel):
    """Schema for creating a trade from a recommendation"""
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    trade_type: str = Field(..., regex='^(buy|sell)$')
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "quantity": 5.0,
                "price": 150.0,
                "trade_type": "buy"
            }
        }

class TradeResponse(BaseModel):
    """Schema for trade information"""
    id: int
    symbol: str
    quantity: float
    price: float
    trade_type: str
    order_type: str
    status: str
    total_amount: float
    created_at: datetime
    executed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class RebalanceResponse(BaseModel):
    """Schema for portfolio rebalance response"""
    trades: List[TradeResponse]
    trade_count: int
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "trades": [
                    {
                        "id": 1,
                        "symbol": "SPY",
                        "quantity": 2.0,
                        "price": 400.0,
                        "trade_type": "buy",
                        "order_type": "market",
                        "status": "pending",
                        "total_amount": 800.0,
                        "created_at": "2023-01-01T12:00:00Z"
                    }
                ],
                "trade_count": 1,
                "message": "Generated 1 trades to rebalance your portfolio."
            }
        }

class StrategyInfoResponse(BaseModel):
    """Schema for trading strategy information"""
    id: str
    name: str
    description: str
    risk_level: str  # low, moderate, high
    recommended_for: List[str]
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v.lower() not in ['low', 'moderate', 'high']:
            raise ValueError('Risk level must be "low", "moderate", or "high"')
        return v.lower()
    
    class Config:
        orm_mode = True

# AI Portfolio Management Schemas

class PortfolioOptimizationRequest(BaseModel):
    """Schema for portfolio optimization request"""
    method: str = Field("efficient_frontier", description="Optimization method to use")
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0, description="User's risk tolerance (0.0 to 1.0)")
    lookback_days: int = Field(365, ge=60, le=1825, description="Historical data lookback period in days")
    min_allocation: float = Field(0.05, ge=0.0, le=0.2, description="Minimum allocation per asset")
    max_allocation: float = Field(0.3, ge=0.05, le=0.5, description="Maximum allocation per asset")
    
    @validator('method')
    def validate_method(cls, v):
        if v not in ['efficient_frontier', 'black_litterman', 'risk_parity']:
            raise ValueError('Method must be "efficient_frontier", "black_litterman", or "risk_parity"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "method": "efficient_frontier",
                "risk_tolerance": 0.6,
                "lookback_days": 365,
                "min_allocation": 0.05,
                "max_allocation": 0.3
            }
        }

class PortfolioOptimizationResponse(BaseModel):
    """Schema for portfolio optimization result"""
    target_allocation: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    optimization_method: str
    confidence_score: float
    trade_count: int
    created_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "target_allocation": {
                    "SPY": 0.30,
                    "VTI": 0.25,
                    "QQQ": 0.15,
                    "AGG": 0.15,
                    "VEA": 0.15
                },
                "expected_return": 0.089,
                "expected_risk": 0.15,
                "sharpe_ratio": 0.46,
                "optimization_method": "efficient_frontier",
                "confidence_score": 0.85,
                "trade_count": 5,
                "created_at": "2025-03-05T10:30:00Z"
            }
        }

class MarketTimingRequest(BaseModel):
    """Schema for market timing request"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Symbol to analyze")
    prediction_horizon: int = Field(7, ge=1, le=30, description="Prediction horizon in days")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "prediction_horizon": 7
            }
        }

class MarketTimingResponse(BaseModel):
    """Schema for market timing signal"""
    symbol: str
    signal_type: str  # "buy", "sell", or "hold"
    strength: float  # 0.0 to 1.0
    time_window: str  # "immediate", "today", "this_week"
    prediction_horizon: int
    confidence: float
    signals: Dict[str, Optional[float]]
    market_conditions: Dict[str, Any]
    created_at: str
    
    @validator('signal_type')
    def validate_signal_type(cls, v):
        if v not in ['buy', 'sell', 'hold']:
            raise ValueError('Signal type must be "buy", "sell", or "hold"')
        return v
    
    @validator('time_window')
    def validate_time_window(cls, v):
        if v not in ['immediate', 'today', 'this_week']:
            raise ValueError('Time window must be "immediate", "today", or "this_week"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "signal_type": "buy",
                "strength": 0.75,
                "time_window": "today",
                "prediction_horizon": 7,
                "confidence": 0.8,
                "signals": {
                    "rsi": 30.5,
                    "macd": 0.5,
                    "bollinger": 0.2,
                    "nn_prediction": 0.6
                },
                "market_conditions": {
                    "regime": "bull",
                    "volatility": 0.14,
                    "momentum": 0.02
                },
                "created_at": "2025-03-05T10:30:00Z"
            }
        }

class RebalanceRequest(BaseModel):
    """Schema for portfolio rebalance request with AI optimization"""
    optimization_method: str = Field("efficient_frontier", description="Optimization method to use")
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0, description="User's risk tolerance (0.0 to 1.0)")
    consider_timing: bool = Field(True, description="Whether to consider market timing signals")
    max_trades: int = Field(20, ge=1, le=50, description="Maximum number of trades to generate")
    min_trade_impact: float = Field(0.02, ge=0.001, le=0.1, description="Minimum portfolio impact to generate a trade")
    
    @validator('optimization_method')
    def validate_method(cls, v):
        if v not in ['efficient_frontier', 'black_litterman', 'risk_parity']:
            raise ValueError('Method must be "efficient_frontier", "black_litterman", or "risk_parity"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "optimization_method": "efficient_frontier",
                "risk_tolerance": 0.6,
                "consider_timing": True,
                "max_trades": 10,
                "min_trade_impact": 0.02
            }
        }

class RebalanceResponse(BaseModel):
    """Enhanced schema for portfolio rebalance response"""
    success: bool
    message: str
    trade_count: int
    optimization_details: Optional[PortfolioOptimizationResponse] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully created 5 rebalancing trades",
                "trade_count": 5,
                "optimization_details": {
                    "target_allocation": {
                        "SPY": 0.30,
                        "VTI": 0.25,
                        "QQQ": 0.15,
                        "AGG": 0.15,
                        "VEA": 0.15
                    },
                    "expected_return": 0.089,
                    "expected_risk": 0.15,
                    "sharpe_ratio": 0.46,
                    "optimization_method": "efficient_frontier",
                    "confidence_score": 0.85,
                    "trade_count": 5,
                    "created_at": "2025-03-05T10:30:00Z"
                }
            }
        }

class ScheduleOptimizationRequest(BaseModel):
    """Schema for scheduling recurring portfolio optimization"""
    schedule: str = Field("weekly", description="Frequency for recurring optimization")
    optimization_method: str = Field("efficient_frontier", description="Optimization method to use")
    auto_execute: bool = Field(False, description="Whether to automatically execute trades")
    
    @validator('schedule')
    def validate_schedule(cls, v):
        if v not in ['daily', 'weekly', 'monthly']:
            raise ValueError('Schedule must be "daily", "weekly", or "monthly"')
        return v
    
    @validator('optimization_method')
    def validate_method(cls, v):
        if v not in ['efficient_frontier', 'black_litterman', 'risk_parity']:
            raise ValueError('Method must be "efficient_frontier", "black_litterman", or "risk_parity"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "schedule": "weekly",
                "optimization_method": "efficient_frontier",
                "auto_execute": False
            }
        }

class ScheduleOptimizationResponse(BaseModel):
    """Schema for scheduling recurring portfolio optimization response"""
    success: bool
    schedule: str
    optimization_method: str
    auto_execute: bool
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "schedule": "weekly",
                "optimization_method": "efficient_frontier",
                "auto_execute": False,
                "message": "Successfully scheduled recurring portfolio optimization"
            }
        }
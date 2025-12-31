from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v.lower() not in ["buy", "sell"]:
            raise ValueError('Action must be "buy" or "sell"')
        return v.lower()

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

    model_config = {"from_attributes": True}


class CreateTradeRequest(BaseModel):
    """Schema for creating a trade from a recommendation"""

    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    trade_type: str = Field(..., pattern="^(buy|sell)$")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "quantity": 5.0,
                "price": 150.0,
                "trade_type": "buy",
            }
        }
    }


class TradeResponse(BaseModel):
    """Schema for the result of creating a trade"""

    trade_id: str
    symbol: str
    quantity: float
    price: float
    trade_type: str
    status: str
    timestamp: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "trade_id": "a1b2c3d4",
                "symbol": "AAPL",
                "quantity": 5.0,
                "price": 150.0,
                "trade_type": "buy",
                "status": "pending",
                "timestamp": "2025-03-01T12:00:00",
            }
        },
    }


class PortfolioAnalysisRequest(BaseModel):
    """Schema for portfolio analysis request"""

    symbols: List[str] = Field(..., min_items=1)

    model_config = {
        "json_schema_extra": {"example": {"symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"]}}
    }


class PortfolioAnalysisResponse(BaseModel):
    """Schema for portfolio analysis response"""

    symbols: List[str]
    risk_score: float
    diversification_score: float
    sector_allocation: Dict[str, float]
    recommendations: List[Dict[str, Any]]
    timestamp: datetime

    model_config = {"from_attributes": True}


class ModelConfigRequest(BaseModel):
    """Schema for AI model configuration request"""

    strategy: str = Field(..., min_length=1)
    confidence_threshold: float = Field(..., ge=0.0, le=1.0)
    risk_tolerance: str = Field(..., pattern="^(low|medium|high)$")
    preferences: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "strategy": "growth",
                "confidence_threshold": 0.7,
                "risk_tolerance": "medium",
                "preferences": {
                    "sectors": ["technology", "healthcare"],
                    "exclude": ["tobacco", "gambling"],
                },
            }
        }
    }


class ModelConfigResponse(BaseModel):
    """Schema for AI model configuration response"""

    strategy: str
    confidence_threshold: float
    risk_tolerance: str
    preferences: Dict[str, Any]
    active: bool
    ai_model_id: str

    model_config = {"from_attributes": True}


class PredictionRequest(BaseModel):
    """Schema for market prediction request"""

    symbol: str = Field(..., min_length=1, max_length=10)
    timeframe: str = Field(..., pattern="^(day|week|month)$")

    model_config = {
        "json_schema_extra": {"example": {"symbol": "AAPL", "timeframe": "week"}}
    }


class PredictionResponse(BaseModel):
    """Schema for market prediction response"""

    symbol: str
    timeframe: str
    prediction: float  # percentage change
    confidence: float
    direction: str  # up, down, sideways
    supporting_data: Dict[str, Any]
    timestamp: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "timeframe": "week",
                "prediction": 2.5,
                "confidence": 0.85,
                "direction": "up",
                "supporting_data": {
                    "technical_indicators": {"rsi": 65, "macd": "bullish"},
                    "sentiment": "positive",
                },
                "timestamp": "2025-03-01T12:00:00",
            }
        },
    }


class RebalanceRequest(BaseModel):
    """Schema for portfolio rebalance request"""

    account_id: Optional[int] = None
    strategy: Optional[str] = Field(None, min_length=1)
    target_allocation: Optional[Dict[str, float]] = None

    @field_validator("target_allocation")
    @classmethod
    def validate_allocation(cls, v):
        if v is not None:
            total = sum(v.values())
            if not (99.0 <= total <= 101.0):  # Allow for minor rounding errors
                raise ValueError(f"Target allocation must sum to 100%, got {total}%")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "account_id": 12345,
                "strategy": "income",
                "target_allocation": {
                    "AAPL": 25.0,
                    "MSFT": 25.0,
                    "GOOGL": 25.0,
                    "AMZN": 25.0,
                },
            }
        }
    }


class RebalanceResponse(BaseModel):
    """Schema for portfolio rebalance response"""

    account_id: int
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    trades_required: List[Dict[str, Any]]
    estimated_cost: float

    model_config = {"from_attributes": True}


class AlgorithmicTradingRequest(BaseModel):
    """Schema for automated trading algorithm request"""

    algorithm: str = Field(..., min_length=1)
    symbols: List[str] = Field(..., min_items=1)
    parameters: Dict[str, Any] = {}
    live_mode: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "algorithm": "mean_reversion",
                "symbols": ["AAPL", "MSFT", "AMZN"],
                "parameters": {
                    "lookback_period": 20,
                    "entry_threshold": 2.0,
                    "exit_threshold": 0.5,
                },
                "live_mode": False,
            }
        }
    }


class StrategyInfoResponse(BaseModel):
    """Schema for AI trading strategy information"""

    strategy_id: str
    name: str
    description: str
    risk_level: str  # low, medium, high
    performance_metrics: Dict[str, Any]
    suitable_market_conditions: List[str]
    parameters: Dict[str, Any]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "strategy_id": "mean_reversion_v2",
                "name": "Mean Reversion Strategy",
                "description": "A strategy that buys oversold assets and sells overbought ones",
                "risk_level": "medium",
                "performance_metrics": {
                    "win_rate": 0.65,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": 0.15,
                },
                "suitable_market_conditions": [
                    "range-bound",
                    "low volatility",
                    "normal",
                ],
                "parameters": {
                    "lookback_period": {"default": 20, "range": [10, 50]},
                    "entry_threshold": {"default": 2.0, "range": [1.0, 3.0]},
                    "exit_threshold": {"default": 0.5, "range": [0.2, 1.0]},
                },
            }
        },
    }


class PortfolioOptimizationRequest(BaseModel):
    """Schema for portfolio optimization request"""

    account_id: Optional[int] = None
    objective: str = Field(..., pattern="^(max_returns|min_risk|balanced)$")
    constraints: Optional[Dict[str, Any]] = None
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "account_id": 12345,
                "objective": "balanced",
                "constraints": {
                    "max_position_size": 0.2,
                    "min_position_size": 0.05,
                    "sector_constraints": {"technology": 0.3, "healthcare": 0.2},
                },
                "risk_tolerance": 0.7,
            }
        }
    }


class PortfolioOptimizationResponse(BaseModel):
    """Schema for portfolio optimization response"""

    account_id: int
    objective: str
    optimized_allocation: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    implementation_plan: List[Dict[str, Any]]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "account_id": 12345,
                "objective": "balanced",
                "optimized_allocation": {
                    "AAPL": 0.15,
                    "MSFT": 0.20,
                    "AMZN": 0.10,
                    "GOOGL": 0.15,
                    "BRK.B": 0.10,
                    "JNJ": 0.10,
                    "PG": 0.10,
                    "CASH": 0.10,
                },
                "expected_return": 0.12,
                "expected_risk": 0.18,
                "sharpe_ratio": 0.67,
                "implementation_plan": [
                    {
                        "action": "buy",
                        "symbol": "MSFT",
                        "quantity": 5,
                        "estimated_cost": 1500.0,
                    },
                    {
                        "action": "sell",
                        "symbol": "AAPL",
                        "quantity": 3,
                        "estimated_proceeds": 600.0,
                    },
                ],
            }
        },
    }


class MarketTimingRequest(BaseModel):
    """Schema for market timing request"""

    symbol: str = Field(..., min_length=1, max_length=10)
    amount: float = Field(..., gt=0)
    direction: str = Field(..., pattern="^(entry|exit)$")
    time_horizon: str = Field(..., pattern="^(short|medium|long)$")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "amount": 10000.0,
                "direction": "entry",
                "time_horizon": "medium",
            }
        }
    }


class MarketTimingResponse(BaseModel):
    """Schema for market timing response"""

    symbol: str
    recommendation: str  # now, wait, gradual, etc.
    confidence: float
    timing_window: Dict[str, datetime]
    expected_improvement: float
    rationale: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "symbol": "AAPL",
                "recommendation": "wait",
                "confidence": 0.85,
                "timing_window": {
                    "optimal_entry": "2025-04-25T10:00:00",
                    "window_start": "2025-04-24T14:00:00",
                    "window_end": "2025-04-27T16:00:00",
                },
                "expected_improvement": 2.5,
                "rationale": "Market volatility expected to decrease next week with improved entry points",
            }
        },
    }


class ScheduleOptimizationRequest(BaseModel):
    """Schema for investment schedule optimization request"""

    total_amount: float = Field(..., gt=0)
    time_period: int = Field(..., gt=0)  # in days
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    strategy: Optional[str] = Field(None, min_length=1)
    risk_profile: str = Field(..., pattern="^(conservative|moderate|aggressive)$")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_amount": 50000.0,
                "time_period": 180,
                "symbol": "AAPL",
                "strategy": "dollar_cost_average",
                "risk_profile": "moderate",
            }
        }
    }


class ScheduleOptimizationResponse(BaseModel):
    """Schema for investment schedule optimization response"""

    success: bool
    schedule: str  # daily, weekly, monthly, etc.
    optimization_method: str
    auto_execute: bool
    message: str
    details: Optional[Dict[str, Any]] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "success": True,
                "schedule": "weekly",
                "optimization_method": "mean_variance",
                "auto_execute": True,
                "message": "Successfully scheduled recurring portfolio optimization",
                "details": {
                    "next_run": "2025-04-26T10:00:00",
                    "frequency": "Every Monday at 10:00 AM",
                    "estimated_trades_per_cycle": 3,
                },
            }
        },
    }

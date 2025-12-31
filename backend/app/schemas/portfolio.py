from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    total_value: float
    cash_balance: float
    invested_amount: float
    total_return: float
    total_return_percentage: float
    auto_rebalance: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    asset_type: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_percentage: float
    target_allocation_percentage: Optional[float]
    current_allocation_percentage: Optional[float]

    class Config:
        from_attributes = True


class PortfolioSummaryResponse(BaseModel):
    portfolio: PortfolioResponse
    holdings: List[HoldingResponse]
    total_positions: int
    largest_position: Optional[HoldingResponse]
    best_performer: Optional[HoldingResponse]
    worst_performer: Optional[HoldingResponse]


class PortfolioUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cash_balance: Optional[float] = None
    auto_rebalance: Optional[bool] = None


# Aliases for compatibility
PortfolioUpdate = PortfolioUpdateRequest


class PositionResponse(BaseModel):
    """Response model for a single position."""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    weight: float

    class Config:
        from_attributes = True


class PerformanceMetrics(BaseModel):
    """Performance metrics for a portfolio."""
    total_return: float
    total_return_percent: float
    daily_return: Optional[float] = None
    daily_return_percent: Optional[float] = None
    weekly_return: Optional[float] = None
    monthly_return: Optional[float] = None
    ytd_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None


class PortfolioPerformanceResponse(BaseModel):
    """Portfolio performance response."""
    portfolio_id: int
    total_value: float
    cash_balance: float
    invested_value: float
    metrics: PerformanceMetrics
    updated_at: datetime


class RiskMetrics(BaseModel):
    """Risk metrics for a portfolio."""
    volatility: Optional[float] = None
    beta: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    value_at_risk: Optional[float] = None
    risk_score: Optional[float] = None


class RiskAnalysisResponse(BaseModel):
    """Risk analysis response for a portfolio."""
    portfolio_id: int
    risk_level: str
    metrics: RiskMetrics
    recommendations: List[str] = []
    analyzed_at: datetime

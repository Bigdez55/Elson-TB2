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

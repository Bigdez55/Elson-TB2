from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class QuoteResponse(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    price: float
    volume: int
    change: Optional[float] = None
    change_percent: Optional[float] = None
    previous_close: Optional[float] = None
    source: str
    timestamp: Optional[datetime] = None


class MultipleQuotesResponse(BaseModel):
    quotes: List[QuoteResponse]
    timestamp: datetime


class AssetResponse(BaseModel):
    id: int
    symbol: str
    name: str
    asset_type: str
    exchange: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    is_tradable: bool

    class Config:
        from_attributes = True


class MarketDataResponse(BaseModel):
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    change: Optional[float]
    change_percentage: Optional[float]
    timestamp: datetime
    timeframe: str
    source: str

    class Config:
        from_attributes = True

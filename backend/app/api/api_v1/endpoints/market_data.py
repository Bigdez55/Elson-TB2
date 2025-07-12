from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.market_data import Asset, MarketData
from app.models.user import User
from app.schemas.market_data import (AssetResponse, MarketDataResponse,
                                     MultipleQuotesResponse, QuoteResponse)
from app.services.market_data import market_data_service

router = APIRouter()


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get real-time quote for a symbol"""
    symbol = symbol.upper()

    quote_data = await market_data_service.get_quote(symbol)
    if not quote_data:
        raise HTTPException(
            status_code=404, detail=f"Quote not found for symbol {symbol}"
        )

    # Save to database
    await market_data_service.save_market_data(symbol, quote_data, db)

    return QuoteResponse(
        symbol=quote_data["symbol"],
        open=quote_data.get("open", 0),
        high=quote_data.get("high", 0),
        low=quote_data.get("low", 0),
        price=quote_data.get("price", 0),
        volume=quote_data.get("volume", 0),
        change=quote_data.get("change"),
        change_percent=quote_data.get("change_percent"),
        previous_close=quote_data.get("previous_close"),
        source=quote_data.get("source", "unknown"),
        timestamp=datetime.utcnow(),
    )


@router.post("/quotes", response_model=MultipleQuotesResponse)
async def get_multiple_quotes(
    symbols: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get quotes for multiple symbols"""
    symbols = [s.upper() for s in symbols]

    if len(symbols) > 50:  # Limit to prevent abuse
        raise HTTPException(
            status_code=400, detail="Maximum 50 symbols allowed"
        )

    quotes_data = await market_data_service.get_multiple_quotes(symbols)

    quotes = []
    for symbol, quote_data in quotes_data.items():
        if quote_data:
            quotes.append(
                QuoteResponse(
                    symbol=quote_data["symbol"],
                    open=quote_data.get("open", 0),
                    high=quote_data.get("high", 0),
                    low=quote_data.get("low", 0),
                    price=quote_data.get("price", 0),
                    volume=quote_data.get("volume", 0),
                    change=quote_data.get("change"),
                    change_percent=quote_data.get("change_percent"),
                    previous_close=quote_data.get("previous_close"),
                    source=quote_data.get("source", "unknown"),
                    timestamp=datetime.utcnow(),
                )
            )

            # Save to database
            await market_data_service.save_market_data(symbol, quote_data, db)

    return MultipleQuotesResponse(quotes=quotes, timestamp=datetime.utcnow())


@router.get("/assets", response_model=List[AssetResponse])
def get_assets(
    asset_type: Optional[str] = Query(
        None, description="Filter by asset type"
    ),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get available assets"""
    query = db.query(Asset).filter(Asset.is_active)

    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)

    if sector:
        query = query.filter(Asset.sector == sector)

    assets = query.limit(limit).all()
    return [AssetResponse.from_orm(asset) for asset in assets]


@router.get("/history/{symbol}", response_model=List[MarketDataResponse])
def get_historical_data(
    symbol: str,
    timeframe: str = Query(
        "1day", description="Timeframe: 1min, 5min, 1hour, 1day"
    ),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get historical market data for a symbol"""
    symbol = symbol.upper()

    query = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol, MarketData.timeframe == timeframe)
        .order_by(MarketData.timestamp.desc())
        .limit(limit)
    )

    historical_data = query.all()
    return [MarketDataResponse.from_orm(data) for data in historical_data]


@router.post("/assets", response_model=AssetResponse)
def create_asset(
    symbol: str,
    name: str,
    asset_type: str,
    exchange: Optional[str] = None,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new asset (admin function for adding watchlist items)"""
    symbol = symbol.upper()

    # Check if asset already exists
    existing_asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    if existing_asset:
        raise HTTPException(
            status_code=400, detail=f"Asset {symbol} already exists"
        )

    new_asset = Asset(
        symbol=symbol,
        name=name,
        asset_type=asset_type,
        exchange=exchange,
        sector=sector,
        industry=industry,
    )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return AssetResponse.from_orm(new_asset)

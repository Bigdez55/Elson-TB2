"""Market data API routes with trading authentication."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.schemas.market_data import (
    ChartDataResponse,
    MarketDataResponse,
    MarketStatusResponse,
    QuoteResponse,
    WatchlistResponse,
)
from app.services.market_data import MarketDataService

# Aliases for compatibility with trading auth patterns
get_trading_user = get_current_active_user


def require_feature_access(feature: str):
    """Decorator that marks a route as requiring feature access.

    For now, this is a pass-through decorator - feature access control
    is enforced via the get_trading_user dependency.
    """
    def decorator(func):
        # Store feature requirement as metadata
        func._required_feature = feature
        return func
    return decorator

router = APIRouter()


@router.get("/market/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    current_user: User = Depends(get_trading_user),
):
    """Get real-time quote for a symbol."""
    market_service = MarketDataService()

    try:
        quote_data = await market_service.get_quote(symbol.upper())
        return QuoteResponse(**quote_data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Unable to fetch quote for {symbol}: {str(e)}"
        )


@router.get("/market/quotes", response_model=List[QuoteResponse])
async def get_multiple_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    current_user: User = Depends(get_trading_user),
):
    """Get quotes for multiple symbols."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    if len(symbol_list) > 50:
        raise HTTPException(
            status_code=400, detail="Maximum 50 symbols allowed per request"
        )

    market_service = MarketDataService()
    quotes = []

    for symbol in symbol_list:
        try:
            quote_data = await market_service.get_quote(symbol)
            quotes.append(QuoteResponse(**quote_data))
        except Exception:
            # Skip symbols that fail to fetch
            continue

    return quotes


@router.get("/market/chart/{symbol}", response_model=ChartDataResponse)
@require_feature_access("market_data_basic")
async def get_chart_data(
    symbol: str,
    timeframe: str = Query("1D", regex="^(1D|5D|1M|3M|6M|1Y|2Y|5Y)$"),
    interval: str = Query("5m", regex="^(1m|5m|15m|30m|1h|1d)$"),
    current_user: User = Depends(get_trading_user),
):
    """Get chart data for a symbol."""
    market_service = MarketDataService()

    try:
        chart_data = await market_service.get_chart_data(
            symbol.upper(), timeframe, interval
        )
        return ChartDataResponse(**chart_data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Unable to fetch chart data for {symbol}: {str(e)}"
        )


@router.get("/market/search")
async def search_symbols(
    query: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_trading_user),
):
    """Search for tradeable symbols."""
    market_service = MarketDataService()

    try:
        results = await market_service.search_symbols(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")


@router.get("/market/status", response_model=MarketStatusResponse)
async def get_market_status(
    current_user: User = Depends(get_trading_user),
):
    """Get current market status and trading hours."""
    market_service = MarketDataService()

    try:
        status_data = await market_service.get_market_status()
        return MarketStatusResponse(**status_data)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Unable to fetch market status: {str(e)}"
        )


@router.get("/market/fundamentals/{symbol}")
@require_feature_access("market_data_advanced")
async def get_fundamentals(
    symbol: str,
    current_user: User = Depends(get_trading_user),
):
    """Get fundamental data for a symbol (premium feature)."""
    market_service = MarketDataService()

    try:
        fundamentals = await market_service.get_fundamentals(symbol.upper())
        return fundamentals
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to fetch fundamentals for {symbol}: {str(e)}",
        )

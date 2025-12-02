"""Market data API routes.

This module provides endpoints for retrieving market data including:
- Real-time stock quotes 
- Historical stock data
- Market status information
- Trading hours
- Streaming market data
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import logging

from app.models.user import User
from app.core.auth import get_current_active_user, get_current_active_user_optional
from app.services.market_data_streaming import (
    get_streaming_service,
    StreamingQuote
)
from app.services.market_data import MarketDataService

# Set up logging
logger = logging.getLogger(__name__)

# Create router with tags
router = APIRouter(tags=["market-data"])

@router.get("/streaming/quote/{symbol}")
async def get_streaming_quote(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
) -> StreamingQuote:
    """Get the latest streaming quote for a symbol."""
    # Get streaming service
    streaming_service = get_streaming_service()
    
    # Normalize symbol
    symbol = symbol.upper()
    
    # Get latest quote
    quote = await streaming_service.get_latest_quote(symbol)
    
    if not quote:
        raise HTTPException(
            status_code=404,
            detail=f"No streaming quote available for {symbol}"
        )
    
    return quote

@router.get("/streaming/status")
async def get_streaming_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get the status of the streaming service."""
    # Get streaming service
    streaming_service = get_streaming_service()
    
    # Return status
    return streaming_service.get_status()

# Get market data service (will be initialized by dependency)
async def get_market_data_service():
    """Get initialized market data service instance."""
    service = MarketDataService()
    await service.setup()
    try:
        yield service
    finally:
        await service.close()

@router.get("/quotes/{symbol}", response_model=Dict)
async def get_quote(
    symbol: str = Path(..., description="Stock symbol to get quote for"),
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    market_data: MarketDataService = Depends(get_market_data_service),
    current_user: Optional[User] = Depends(get_current_active_user_optional)
):
    """Get real-time quote for a stock symbol."""
    try:
        quote = await market_data.get_quote(symbol, force_refresh)
        logger.info(f"Quote request for {symbol} from user {current_user.id if current_user else 'anonymous'}")
        return quote
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting quote: {str(e)}")

@router.post("/quotes/batch", response_model=Dict[str, Dict])
async def get_batch_quotes(
    symbols: List[str],
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    market_data: MarketDataService = Depends(get_market_data_service),
    current_user: Optional[User] = Depends(get_current_active_user_optional)
):
    """Get quotes for multiple symbols in one request."""
    try:
        # Limit number of symbols per request
        if len(symbols) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols per request")
            
        quotes = await market_data.get_batch_quotes(symbols, force_refresh)
        logger.info(f"Batch quote request for {len(symbols)} symbols from user {current_user.id if current_user else 'anonymous'}")
        return quotes
    except Exception as e:
        logger.error(f"Error getting batch quotes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting batch quotes: {str(e)}")

@router.get("/historical/{symbol}", response_model=Dict)
async def get_historical_data(
    symbol: str = Path(..., description="Stock symbol to get data for"),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval (1d, 1h, etc.)"),
    force_refresh: bool = Query(False, description="Force refresh data from source"),
    market_data: MarketDataService = Depends(get_market_data_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get historical price data for a stock symbol."""
    try:
        # Convert dates to datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = None
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.min.time())
            
        historical_data = await market_data.get_historical_data(
            symbol, start_datetime, end_datetime, interval, force_refresh
        )
        logger.info(f"Historical data request for {symbol} from user {current_user.id}")
        return historical_data
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting historical data: {str(e)}")

@router.get("/hours/{market}", response_model=Dict)
async def get_market_hours(
    market: str = Path("US", description="Market to get hours for"),
    market_data: MarketDataService = Depends(get_market_data_service),
    current_user: Optional[User] = Depends(get_current_active_user_optional)
):
    """Get market hours and trading status."""
    try:
        hours = await market_data.get_market_hours(market)
        return hours
    except Exception as e:
        logger.error(f"Error getting market hours for {market}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting market hours: {str(e)}")

@router.get("/health", response_model=Dict)
async def get_market_data_health(
    market_data: MarketDataService = Depends(get_market_data_service),
    current_user: User = Depends(get_current_active_user)
):
    """Get health metrics for the market data service."""
    # Check if user has admin role
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
        
    try:
        metrics = await market_data.get_data_quality_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting market data health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting health metrics: {str(e)}")

@router.post("/cache/clear", response_model=Dict)
async def clear_market_data_cache(
    pattern: Optional[str] = None,
    market_data: MarketDataService = Depends(get_market_data_service),
    current_user: User = Depends(get_current_active_user)
):
    """Clear market data cache entries."""
    # Check if user has admin role
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
        
    try:
        count = await market_data.clear_cache(pattern)
        return {"success": True, "cleared_entries": count}
    except Exception as e:
        logger.error(f"Error clearing market data cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
"""
Market data routes for the API.

This module provides API endpoints for accessing market data from
various sources including stock quotes, historical prices, and other
financial data through the integrated API providers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.routes.deps import get_current_user, get_current_active_user, get_db
from app.services.market_data import MarketDataService
from app.services.market_integration import get_market_integration_service, MarketIntegrationService
from app.models.user import User
from app.services.external_api.integration import (
    get_stock_quote, get_historical_data, get_company_profile,
    get_provider_health, get_available_providers
)
from app.core.config import settings

router = APIRouter(
    prefix="/market-data",
    tags=["market-data"],
)

# Initialize integration service
integration_service = None


async def get_integration_service(db: Session = Depends(get_db)):
    """Get or initialize the market integration service."""
    global integration_service
    if integration_service is None:
        integration_service = get_market_integration_service(db=db)
    return integration_service


@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str = Path(..., description="Stock symbol"),
    force_refresh: bool = Query(False, description="Force refresh from source"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    integration: MarketIntegrationService = Depends(get_integration_service)
):
    """Get real-time quote for a symbol."""
    try:
        # Get quote using the market_data property of the integration service
        quote = await integration.market_data.get_quote(symbol, force_refresh)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/{symbol}")
async def get_historical(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval (1d, 1w, 1m)"),
    force_refresh: bool = Query(False, description="Force refresh from source"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    integration: MarketIntegrationService = Depends(get_integration_service)
):
    """Get historical price data for a symbol."""
    try:
        # Convert start_date string to datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Convert end_date string to datetime or use current date
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        
        # Get historical data using the market_data property of the integration service
        data = await integration.market_data.get_historical_data(
            symbol=symbol,
            start_date=start_dt,
            end_date=end_dt,
            interval=interval,
            force_refresh=force_refresh
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/health")
async def provider_health(
    current_user: User = Depends(get_current_active_user)
):
    """Get health status of all data providers."""
    try:
        health = await get_provider_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/available")
async def available_providers(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available data providers."""
    try:
        providers = await get_available_providers()
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Direct external API endpoints

@router.get("/external/quote/{symbol}")
async def external_quote(
    symbol: str = Path(..., description="Stock symbol"),
    current_user: User = Depends(get_current_active_user)
):
    """Get a stock quote directly from external API."""
    try:
        quote = await get_stock_quote(symbol)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/external/historical/{symbol}")
async def external_historical(
    symbol: str = Path(..., description="Stock symbol"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("daily", description="Data interval (daily, weekly, monthly)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get historical price data directly from external API."""
    try:
        data = await get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
            interval=interval
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/external/company/{symbol}")
async def external_company_profile(
    symbol: str = Path(..., description="Stock symbol"),
    current_user: User = Depends(get_current_active_user)
):
    """Get company profile data directly from external API."""
    try:
        profile = await get_company_profile(symbol)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New endpoints that directly use the market integration service

@router.get("/batch-quotes")
async def batch_quotes(
    symbols: str = Query(..., description="Comma-separated list of stock symbols"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    integration: MarketIntegrationService = Depends(get_integration_service)
):
    """Get real-time quotes for multiple symbols at once."""
    try:
        # Split the comma-separated string into a list
        symbol_list = [s.strip() for s in symbols.split(",")]
        
        # Use the market_integration method for batch quotes
        quotes = await integration.get_market_data_for_symbols(symbol_list)
        return quotes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integration-status")
async def integration_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    integration: MarketIntegrationService = Depends(get_integration_service)
):
    """Get status of market integration service."""
    try:
        status = await integration.get_integration_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconcile-orders")
async def reconcile_orders(
    max_age_days: int = Query(30, ge=1, le=90, description="Maximum age of orders to reconcile"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    integration: MarketIntegrationService = Depends(get_integration_service)
):
    """Reconcile pending orders with broker system."""
    try:
        updated_count, total_count = await integration.reconcile_orders(max_age_days)
        return {
            "updated_count": updated_count,
            "total_count": total_count,
            "success": True,
            "message": f"Reconciled {updated_count} of {total_count} orders"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
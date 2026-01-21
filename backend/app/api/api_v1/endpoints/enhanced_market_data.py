"""
Enhanced Market Data API endpoints with improved caching and multiple providers.
"""

from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_active_user
from app.models.user import User
from app.services.enhanced_market_data import enhanced_market_data_service

logger = structlog.get_logger()

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_enhanced_quote(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get real-time quote with enhanced caching and failover.

    Uses multiple providers with intelligent failover and caching
    for optimal performance and reliability.
    """
    try:
        symbol = symbol.upper().strip()

        quote = await enhanced_market_data_service.get_quote(symbol)

        if not quote:
            raise HTTPException(
                status_code=404, detail=f"Quote not found for symbol {symbol}"
            )

        logger.info(
            "Enhanced quote retrieved",
            user_id=current_user.id,
            symbol=symbol,
            provider=quote.get("provider"),
        )

        return quote

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving enhanced quote",
            user_id=current_user.id,
            symbol=symbol,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve quote")


@router.get("/quotes")
async def get_multiple_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols (max 20)"),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get quotes for multiple symbols efficiently.

    Processes symbols in batches for optimal performance.
    """
    try:
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

        if len(symbol_list) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 symbols allowed per request",
            )

        # Get quotes for all symbols
        quotes = await enhanced_market_data_service.get_multiple_quotes(symbol_list)

        # Count successful quotes
        successful_quotes = sum(1 for q in quotes.values() if q is not None)

        logger.info(
            "Multiple quotes retrieved",
            user_id=current_user.id,
            symbols_requested=len(symbol_list),
            successful_quotes=successful_quotes,
        )

        return {
            "quotes": quotes,
            "summary": {
                "total_requested": len(symbol_list),
                "successful": successful_quotes,
                "failed": len(symbol_list) - successful_quotes,
            },
            "timestamp": (
                quotes[next(iter(quotes.keys()))]["timestamp"]
                if quotes and any(quotes.values())
                else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving multiple quotes",
            user_id=current_user.id,
            symbols=symbols,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve quotes")


@router.get("/historical/{symbol}")
async def get_enhanced_historical_data(
    symbol: str,
    period: str = Query(
        "1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"
    ),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get historical data with enhanced caching and multiple providers.

    Supports various time periods with intelligent caching.
    """
    try:
        symbol = symbol.upper().strip()

        # Validate period
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}",
            )

        historical_data = await enhanced_market_data_service.get_historical_data(
            symbol, period
        )

        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"Historical data not found for {symbol}",
            )

        # Calculate basic statistics
        prices = [float(d["close"]) for d in historical_data if d["close"] is not None]

        if prices:
            stats = {
                "count": len(prices),
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                "price_change_percent": (
                    (prices[-1] - prices[0]) / prices[0] * 100
                    if len(prices) > 1 and prices[0] != 0
                    else 0
                ),
            }
        else:
            stats = {}

        logger.info(
            "Enhanced historical data retrieved",
            user_id=current_user.id,
            symbol=symbol,
            period=period,
            data_points=len(historical_data),
        )

        return {
            "symbol": symbol,
            "period": period,
            "data": historical_data,
            "statistics": stats,
            "data_points": len(historical_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving enhanced historical data",
            user_id=current_user.id,
            symbol=symbol,
            period=period,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve historical data"
        )


@router.get("/search")
async def search_symbols(
    query: str = Query(..., description="Search term for symbol or company name"),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """
    Search for symbols by company name or symbol.

    Returns list of matching symbols with metadata.
    """
    try:
        if len(query.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search query must be at least 2 characters",
            )

        results = await enhanced_market_data_service.search_symbols(query)

        logger.info(
            "Symbol search performed",
            user_id=current_user.id,
            query=query,
            results_count=len(results),
        )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in symbol search",
            user_id=current_user.id,
            query=query,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to search symbols")


@router.get("/health")
async def market_data_health_check(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Health check for market data providers.

    Returns status of all configured providers and overall system health.
    """
    try:
        health_status = await enhanced_market_data_service.health_check()

        logger.info(
            "Market data health check performed",
            user_id=current_user.id,
            overall_status=health_status["overall_status"],
        )

        return health_status

    except Exception as e:
        logger.error(
            "Error in market data health check",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to check market data health"
        )


@router.get("/cache-stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get market data cache statistics.

    Useful for monitoring performance and cache efficiency.
    """
    try:
        cache_stats = enhanced_market_data_service.get_cache_stats()

        logger.info(
            "Cache statistics retrieved",
            user_id=current_user.id,
            cache_size=cache_stats["cache_size"],
        )

        return cache_stats

    except Exception as e:
        logger.error(
            "Error retrieving cache statistics",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve cache statistics"
        )


@router.post("/clear-cache")
async def clear_market_data_cache(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """
    Clear the market data cache.

    Forces fresh data retrieval from providers.
    """
    try:
        enhanced_market_data_service.cache.clear_expired()
        enhanced_market_data_service.cache._cache.clear()

        logger.info("Market data cache cleared", user_id=current_user.id)

        return {"message": "Market data cache cleared successfully"}

    except Exception as e:
        logger.error(
            "Error clearing market data cache",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to clear cache")

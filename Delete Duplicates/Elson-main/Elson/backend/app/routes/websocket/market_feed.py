"""Market data WebSocket endpoints.

This module provides WebSocket endpoints for real-time market data streaming.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.bootstrap import decode_jwt_token
from app.core.config import settings
from app.services.market_data_streaming import (
    get_streaming_service, 
    MarketDataStreamingService,
    StreamingQuote
)
from app.routes.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.websocket("/ws/market/feed")
async def market_data_feed(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """WebSocket endpoint for real-time market data feed.
    
    This endpoint allows clients to subscribe to real-time market data for specific symbols.
    Clients can send subscription messages to subscribe to symbols and will receive
    real-time updates as they occur.
    
    Messages from client to server:
    
    Subscribe to symbols:
    {
        "action": "subscribe",
        "symbols": ["AAPL", "MSFT", "GOOGL"]
    }
    
    Unsubscribe from symbols:
    {
        "action": "unsubscribe",
        "symbols": ["AAPL", "MSFT"]
    }
    
    Ping (to keep connection alive):
    {
        "action": "ping"
    }
    
    Messages from server to client:
    
    Market data updates:
    {
        "symbol": "AAPL",
        "price": 150.25,
        "bid": 150.20,
        "ask": 150.30,
        "volume": 1000,
        "timestamp": "2023-05-01T12:34:56.789Z",
        "source": "alpaca"
    }
    
    Subscription confirmation:
    {
        "type": "subscribed",
        "symbols": ["AAPL", "MSFT", "GOOGL"]
    }
    
    Unsubscription confirmation:
    {
        "type": "unsubscribed",
        "symbols": ["AAPL", "MSFT"]
    }
    
    Error message:
    {
        "type": "error",
        "message": "Invalid subscription request"
    }
    
    Pong response:
    {
        "type": "pong",
        "timestamp": "2023-05-01T12:34:56.789Z"
    }
    """
    # Check authentication if token provided
    user_id = None
    if token:
        try:
            # Decode token
            payload = decode_jwt_token(token)
            user_id = payload.get("sub")
        except Exception as e:
            await websocket.close(code=1008, reason="Invalid authentication token")
            logger.warning(f"WebSocket connection rejected due to invalid token: {str(e)}")
            return
    
    # Get streaming service
    streaming_service = get_streaming_service()
    
    # Start streaming service if not already running
    if not streaming_service.stream_active:
        await streaming_service.start()
    
    try:
        # Handle the WebSocket connection
        await streaming_service.handle_client_websocket(websocket)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        await websocket.close(code=1011, reason="Server error")

@router.get("/api/v1/market/streaming/status", tags=["Market Data"])
async def streaming_status(
    current_user = Depends(get_current_user)
):
    """Get status of the market data streaming service.
    
    Returns information about active connections, subscriptions, and message statistics.
    """
    streaming_service = get_streaming_service()
    return streaming_service.get_status()

@router.post("/api/v1/market/streaming/start", tags=["Market Data"])
async def start_streaming(current_user = Depends(get_current_user)):
    """Start the market data streaming service.
    
    This endpoint is for administrative purposes to manually start the streaming service.
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
        
    streaming_service = get_streaming_service()
    
    if streaming_service.stream_active:
        return {"status": "already_running"}
    
    await streaming_service.start()
    return {"status": "started"}

@router.post("/api/v1/market/streaming/stop", tags=["Market Data"])
async def stop_streaming(current_user = Depends(get_current_user)):
    """Stop the market data streaming service.
    
    This endpoint is for administrative purposes to manually stop the streaming service.
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
        
    streaming_service = get_streaming_service()
    
    if not streaming_service.stream_active:
        return {"status": "already_stopped"}
    
    await streaming_service.stop()
    return {"status": "stopped"}

@router.get("/api/v1/market/streaming/quote/{symbol}", tags=["Market Data"])
async def get_streaming_quote(
    symbol: str,
    current_user = Depends(get_current_user)
):
    """Get the latest streaming quote for a symbol.
    
    Returns the most recent quote from the streaming service if available
    and not older than 5 seconds. Otherwise returns an error.
    """
    from app.core.caching import get_cache, set_cache, CACHE_TTL_VERY_SHORT
    from app.core.metrics import record_metric
    import time
    
    start_time = time.time()
    cache_key = f"market_quote:{symbol.upper()}"
    
    # Try to get from cache first
    cached_quote = await get_cache(cache_key)
    if cached_quote:
        # Record cache hit metric
        record_metric("market_quote_cache_hit", 1, {"symbol": symbol})
        record_metric("market_quote_response_time", (time.time() - start_time) * 1000, 
                     {"source": "cache", "symbol": symbol})
        return cached_quote
    
    # Cache miss, get from streaming service
    streaming_service = get_streaming_service()
    
    # Ensure service is running
    if not streaming_service.stream_active:
        raise HTTPException(status_code=503, detail="Streaming service not running")
    
    # Get the latest quote
    quote = await streaming_service.get_latest_quote(symbol.upper())
    
    if not quote:
        raise HTTPException(status_code=404, detail="No recent quote available")
    
    # Cache the result (with very short TTL for real-time data)
    await set_cache(cache_key, quote, ttl=CACHE_TTL_VERY_SHORT)
    
    # Record cache miss metric
    record_metric("market_quote_cache_miss", 1, {"symbol": symbol})
    record_metric("market_quote_response_time", (time.time() - start_time) * 1000, 
                 {"source": "streaming", "symbol": symbol})
    
    return quote

@router.post("/api/v1/market/streaming/quotes", tags=["Market Data"])
async def get_streaming_quotes_bulk(
    symbols: List[str],
    current_user = Depends(get_current_user)
):
    """Get the latest streaming quotes for multiple symbols in a single request.
    
    This is an optimized bulk endpoint that fetches quotes for multiple symbols
    at once, with improved caching and performance.
    
    Returns:
        A dictionary mapping symbols to their latest quotes
    """
    from app.core.caching import get_cache, set_cache, CACHE_TTL_VERY_SHORT
    from app.core.metrics import record_metric
    import time
    
    start_time = time.time()
    
    # Validate and normalize symbols
    if not symbols:
        raise HTTPException(status_code=400, detail="No symbols provided")
    
    # Limit the number of symbols per request
    if len(symbols) > 50:
        raise HTTPException(status_code=400, detail="Too many symbols (max 50)")
    
    # Normalize symbols
    symbols = [s.upper() for s in symbols if s]
    
    # Get streaming service
    streaming_service = get_streaming_service()
    
    # Ensure service is running
    if not streaming_service.stream_active:
        raise HTTPException(status_code=503, detail="Streaming service not running")
    
    # Process each symbol
    result = {}
    cache_hits = 0
    cache_misses = 0
    
    # First try to get from cache
    for symbol in symbols:
        cache_key = f"market_quote:{symbol}"
        cached_quote = await get_cache(cache_key)
        
        if cached_quote:
            result[symbol] = cached_quote
            cache_hits += 1
        else:
            # Get fresh quote for this symbol
            quote = await streaming_service.get_latest_quote(symbol)
            
            if quote:
                result[symbol] = quote.dict() if hasattr(quote, 'dict') else quote
                await set_cache(cache_key, result[symbol], ttl=CACHE_TTL_VERY_SHORT)
                cache_misses += 1
    
    # Record metrics
    processing_time = (time.time() - start_time) * 1000
    record_metric("market_quote_batch_size", len(symbols))
    record_metric("market_quote_batch_hits", cache_hits)
    record_metric("market_quote_batch_misses", cache_misses)
    record_metric("market_quote_batch_time", processing_time)
    
    return {
        "quotes": result,
        "timestamp": datetime.now().isoformat(),
        "symbols_requested": len(symbols),
        "symbols_found": len(result)
    }
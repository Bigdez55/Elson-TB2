"""Market data WebSocket endpoints.

This module provides WebSocket endpoints for real-time market data streaming.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.core.auth import get_current_user, get_current_user_ws
from app.services.market_data_streaming_enhanced import get_streaming_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/market/feed")
async def market_data_feed(websocket: WebSocket, token: Optional[str] = None):
    """Enhanced WebSocket endpoint for authenticated real-time market data.

    Requires trading-enabled user authentication via JWT token.
    Provides real-time market data streaming with subscription access.

    Authentication:
    - Pass JWT token via query parameter: /ws/market/feed?token=<jwt_token>
    - Token must contain trading_enabled=true claim
    - Advanced features require appropriate subscription tier

    Messages from client to server:

    Subscribe to symbols:
    {
        "action": "subscribe",
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "level": "basic"  // "basic" or "advanced" (Level II data)
    }

    Unsubscribe from symbols:
    {
        "action": "unsubscribe",
        "symbols": ["AAPL", "MSFT"]
    }

    Ping (heartbeat):
    {
        "action": "ping"
    }

    Messages from server to client:

    Market data updates:
    {
        "type": "quote",
        "symbol": "AAPL",
        "price": 150.25,
        "bid": 150.20,
        "ask": 150.30,
        "bidSize": 100,
        "askSize": 200,
        "volume": 1000,
        "dayChange": 2.50,
        "dayChangePercent": 1.69,
        "timestamp": "2023-05-01T12:34:56.789Z",
        "source": "alpaca"
    }

    Level II data (advanced subscription only):
    {
        "type": "level2",
        "symbol": "AAPL",
        "bids": [[150.20, 100], [150.19, 200]],
        "asks": [[150.21, 150], [150.22, 300]],
        "timestamp": "2023-05-01T12:34:56.789Z"
    }

    Trade updates:
    {
        "type": "trade",
        "symbol": "AAPL",
        "price": 150.25,
        "size": 100,
        "timestamp": "2023-05-01T12:34:56.789Z"
    }

    Subscription confirmation:
    {
        "type": "subscribed",
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "level": "basic"
    }

    Error message:
    {
        "type": "error",
        "message": "Insufficient subscription tier for Level II data",
        "code": "SUBSCRIPTION_REQUIRED"
    }

    Pong response:
    {
        "type": "pong",
        "timestamp": "2023-05-01T12:34:56.789Z"
    }
    """
    await websocket.accept()

    # Authenticate user
    user_data = None
    if token:
        try:
            from sqlalchemy.orm import sessionmaker

            from app.db.database import engine

            Session = sessionmaker(bind=engine)
            db = Session()

            try:
                user_data = await get_current_user_ws(token, db)
                logger.info(f"WebSocket authenticated user: {user_data['email']}")
            finally:
                db.close()

        except Exception as e:
            await websocket.close(code=1008, reason="Authentication failed")
            logger.warning(f"WebSocket authentication failed: {str(e)}")
            return
    else:
        await websocket.close(code=1008, reason="Authentication token required")
        return

    # Validate trading permissions
    if not user_data.get("trading_enabled", False):
        await websocket.close(code=1008, reason="Trading access required")
        return

    # Get streaming service
    streaming_service = get_streaming_service()

    # Start streaming service if not already running
    if not streaming_service.stream_active:
        await streaming_service.start()

    # Track user subscriptions and permissions
    user_subscriptions = set()
    subscription_tier = user_data.get("subscription_tier", "free")

    try:
        while True:
            # Receive message from client
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON format"})
                )
                continue
            except Exception:
                break

            action = data.get("action")

            if action == "ping":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

            elif action == "subscribe":
                symbols = data.get("symbols", [])
                level = data.get("level", "basic")

                # Validate subscription level access
                if level == "advanced" and subscription_tier == "free":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Level II data requires premium subscription",
                                "code": "SUBSCRIPTION_REQUIRED",
                            }
                        )
                    )
                    continue

                # Limit symbols based on subscription
                max_symbols = 50 if subscription_tier in ["premium", "family"] else 10
                if len(symbols) > max_symbols:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": f"Maximum {max_symbols} symbols allowed for {subscription_tier} tier",
                                "code": "SYMBOL_LIMIT_EXCEEDED",
                            }
                        )
                    )
                    continue

                # Subscribe to symbols
                valid_symbols = []
                for symbol in symbols:
                    symbol = symbol.upper()
                    if symbol not in user_subscriptions:
                        user_subscriptions.add(symbol)
                        # Add to streaming service subscription
                        await streaming_service.subscribe_symbol(
                            symbol, websocket, level
                        )
                        valid_symbols.append(symbol)

                if valid_symbols:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "subscribed",
                                "symbols": valid_symbols,
                                "level": level,
                                "total_subscriptions": len(user_subscriptions),
                            }
                        )
                    )

            elif action == "unsubscribe":
                symbols = data.get("symbols", [])
                unsubscribed = []

                for symbol in symbols:
                    symbol = symbol.upper()
                    if symbol in user_subscriptions:
                        user_subscriptions.remove(symbol)
                        await streaming_service.unsubscribe_symbol(symbol, websocket)
                        unsubscribed.append(symbol)

                if unsubscribed:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "unsubscribed",
                                "symbols": unsubscribed,
                                "total_subscriptions": len(user_subscriptions),
                            }
                        )
                    )

            else:
                await websocket.send_text(
                    json.dumps(
                        {"type": "error", "message": f"Unknown action: {action}"}
                    )
                )

    except WebSocketDisconnect:
        logger.info(
            f"WebSocket client disconnected (user: {user_data.get('email', 'unknown')})"
        )
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Server error")
        except Exception:
            pass
    finally:
        # Clean up subscriptions
        for symbol in user_subscriptions:
            try:
                await streaming_service.unsubscribe_symbol(symbol, websocket)
            except Exception:
                pass


@router.get("/api/v1/market/streaming/status", tags=["Market Data"])
async def streaming_status(current_user=Depends(get_current_user)):
    """Get status of the market data streaming service.

    Returns information about active connections, subscriptions, and message statistics.
    """
    streaming_service = get_streaming_service()
    return streaming_service.get_status()


@router.post("/api/v1/market/streaming/start", tags=["Market Data"])
async def start_streaming(current_user=Depends(get_current_user)):
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
async def stop_streaming(current_user=Depends(get_current_user)):
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
async def get_streaming_quote(symbol: str, current_user=Depends(get_current_user)):
    """Get the latest streaming quote for a symbol.

    Returns the most recent quote from the streaming service if available
    and not older than 5 seconds. Otherwise returns an error.
    """
    import time

    from app.core.caching import CACHE_TTL_VERY_SHORT, get_cache, set_cache
    from app.core.metrics import record_metric

    start_time = time.time()
    cache_key = f"market_quote:{symbol.upper()}"

    # Try to get from cache first
    cached_quote = await get_cache(cache_key)
    if cached_quote:
        # Record cache hit metric
        record_metric("market_quote_cache_hit", 1, {"symbol": symbol})
        record_metric(
            "market_quote_response_time",
            (time.time() - start_time) * 1000,
            {"source": "cache", "symbol": symbol},
        )
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
    record_metric(
        "market_quote_response_time",
        (time.time() - start_time) * 1000,
        {"source": "streaming", "symbol": symbol},
    )

    return quote


@router.post("/api/v1/market/streaming/quotes", tags=["Market Data"])
async def get_streaming_quotes_bulk(
    symbols: List[str], current_user=Depends(get_current_user)
):
    """Get the latest streaming quotes for multiple symbols in a single request.

    This is an optimized bulk endpoint that fetches quotes for multiple symbols
    at once, with improved caching and performance.

    Returns:
        A dictionary mapping symbols to their latest quotes
    """
    import time

    from app.core.caching import CACHE_TTL_VERY_SHORT, get_cache, set_cache
    from app.core.metrics import record_metric

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
                result[symbol] = quote.dict() if hasattr(quote, "dict") else quote
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
        "symbols_found": len(result),
    }

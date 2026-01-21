"""
Market streaming WebSocket endpoints for real-time data.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.responses import JSONResponse

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.market_streaming import personal_market_streaming

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def market_data_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data streaming.

    Clients can send JSON messages with the following actions:
    - {"action": "subscribe", "symbols": ["AAPL", "GOOGL"]} - Subscribe to symbols
    - {"action": "unsubscribe", "symbols": ["AAPL"]} - Unsubscribe from symbols
    - {"action": "ping"} - Ping for connection check
    - {"action": "status"} - Get connection status

    The server will send back:
    - {"type": "connected"} - Initial connection confirmation
    - {"type": "quote", "data": {...}} - Real-time quote data
    - {"type": "subscribed", "symbols": [...]} - Subscription confirmation
    - {"type": "unsubscribed", "symbols": [...]} - Unsubscription confirmation
    - {"type": "pong"} - Ping response
    - {"type": "status", ...} - Status information
    - {"type": "error", "message": "..."} - Error messages
    """
    await personal_market_streaming.handle_websocket_connection(websocket)


@router.get("/status")
async def get_streaming_status() -> Dict[str, Any]:
    """
    Get the current status of the market streaming service.

    Returns information about active connections, subscriptions, and service health.
    """
    return personal_market_streaming.get_status()


@router.post("/start")
async def start_streaming(
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """
    Start the market streaming service.

    Requires authentication. Only authenticated users can control the streaming service.
    """
    try:
        await personal_market_streaming.start_streaming()
        return JSONResponse(
            content={
                "message": "Market streaming service started",
                "status": "success",
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error starting streaming service: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start streaming service")


@router.post("/stop")
async def stop_streaming(
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """
    Stop the market streaming service.

    Requires authentication. Only authenticated users can control the streaming service.
    """
    try:
        await personal_market_streaming.stop_streaming()
        return JSONResponse(
            content={
                "message": "Market streaming service stopped",
                "status": "success",
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error stopping streaming service: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop streaming service")


@router.get("/quote/{symbol}")
async def get_latest_quote(symbol: str, max_age: int = 30) -> Dict[str, Any]:
    """
    Get the latest cached quote for a symbol.

    Args:
        symbol: The stock symbol to get quote for
        max_age: Maximum age of the quote in seconds (default: 30)

    Returns:
        Latest quote data if available and fresh enough, otherwise 404
    """
    quote = await personal_market_streaming.get_latest_quote(symbol.upper(), max_age)
    if quote:
        return {"symbol": symbol.upper(), "quote": quote.model_dump()}
    else:
        raise HTTPException(
            status_code=404, detail=f"No recent quote available for {symbol}"
        )


@router.post("/quote/{symbol}/refresh")
async def refresh_quote(
    symbol: str, current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Force an immediate refresh of quote data for a symbol.

    Args:
        symbol: The stock symbol to refresh

    Returns:
        Updated quote data
    """
    quote = await personal_market_streaming.force_update_symbol(symbol.upper())
    if quote:
        return {
            "symbol": symbol.upper(),
            "quote": quote.model_dump(),
            "refreshed": True,
        }
    else:
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh quote for {symbol}"
        )


@router.get("/subscriptions")
async def get_active_subscriptions() -> Dict[str, Any]:
    """
    Get all currently active symbol subscriptions.

    Returns:
        List of symbols that clients are currently subscribed to
    """
    status = personal_market_streaming.get_status()
    return {
        "subscribed_symbols": status["subscribed_symbols"],
        "subscription_count": status["subscription_count"],
        "connected_clients": status["connected_clients"],
    }

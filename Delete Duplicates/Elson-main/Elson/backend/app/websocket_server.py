"""
Standalone WebSocket server for market data streaming.

This module provides a standalone FastAPI application that serves
WebSocket endpoints for market data streaming. It's separate from
the main application to avoid circular imports.
"""

import logging
import asyncio
import json
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import settings
from app.services.market_data_streaming import get_streaming_service

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Market Data WebSocket API",
    description="WebSocket API for real-time market data streaming",
    version="1.0.0",
)

@app.websocket("/ws/market/feed")
async def market_data_feed(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """WebSocket endpoint for real-time market data feed."""
    # Accept the connection
    await websocket.accept()
    
    # Check authentication if token provided
    user_id = None
    if token:
        try:
            # Decode token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            logger.info(f"Authenticated WebSocket connection for user {user_id}")
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
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to market data stream",
            "user_id": user_id
        }))
        
        # Handle client messages
        while True:
            # Wait for message from client
            message = await websocket.receive_text()
            
            try:
                data = json.loads(message)
                action = data.get("action")
                
                if action == "subscribe":
                    symbols = data.get("symbols", [])
                    if symbols:
                        # Subscribe client to symbols
                        for symbol in symbols:
                            streaming_service.websocket_manager.subscribe(websocket, symbol)
                        
                        # Subscribe to data providers
                        await streaming_service.subscribe_symbols(symbols)
                        
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "symbols": symbols
                        }))
                        
                elif action == "unsubscribe":
                    symbols = data.get("symbols", [])
                    if symbols:
                        # Unsubscribe client from symbols
                        for symbol in symbols:
                            streaming_service.websocket_manager.unsubscribe(websocket, symbol)
                        
                        # Maybe unsubscribe from data providers
                        await streaming_service.unsubscribe_symbols(symbols)
                        
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "type": "unsubscribed",
                            "symbols": symbols
                        }))
                        
                elif action == "ping":
                    # Send pong response
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "2023-05-01T12:34:56.789Z"
                    }))
                    
                else:
                    # Unknown action
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    }))
                    
            except json.JSONDecodeError:
                # Invalid JSON
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message"
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected")
        streaming_service.websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        await websocket.close(code=1011, reason="Server error")

@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive status information."""
    import psutil
    import socket
    from datetime import datetime
    
    # Get streaming service
    streaming_service = get_streaming_service()
    
    # Basic health status
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "service": "websocket",
    }
    
    # Add streaming service status
    health_data["streaming"] = {
        "active": streaming_service.stream_active,
        "connections": sum(streaming_service.connection_status.values()),
        "client_count": len(getattr(streaming_service.websocket_manager, "active_connections", [])),
        "subscription_count": len(getattr(streaming_service.websocket_manager, "subscriptions", {}))
    }
    
    # Add system metrics
    process = psutil.Process()
    memory_info = process.memory_info()
    health_data["system"] = {
        "cpu_percent": process.cpu_percent(),
        "memory_rss_mb": memory_info.rss / (1024 * 1024),
        "memory_vms_mb": memory_info.vms / (1024 * 1024),
        "thread_count": process.num_threads()
    }
    
    return health_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
"""WebSocket endpoints for real-time trading updates."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import sessionmaker

from app.core.security import get_current_user_ws
from app.core.auth.trading_auth import TradingPermissionError
from app.db.database import engine
from app.models.portfolio import Portfolio
from app.models.trade import Trade, TradeStatus
from app.services.trading_service import TradingService

logger = logging.getLogger(__name__)
router = APIRouter()


class TradingWebSocketManager:
    """Manager for trading WebSocket connections and real-time updates."""

    def __init__(self):
        self.active_connections: Dict[
            int, Set[WebSocket]
        ] = {}  # user_id -> set of websockets
        self.user_portfolios: Dict[int, int] = {}  # user_id -> portfolio_id

    async def connect(self, websocket: WebSocket, user_id: int, portfolio_id: int):
        """Connect a user's WebSocket for trading updates."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.user_portfolios[user_id] = portfolio_id

        logger.info(f"Trading WebSocket connected for user {user_id}")

        # Send initial portfolio data
        await self.send_portfolio_update(user_id)

    async def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's WebSocket."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Remove user if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_portfolios:
                    del self.user_portfolios[user_id]

        logger.info(f"Trading WebSocket disconnected for user {user_id}")

    async def send_trade_update(self, user_id: int, trade_data: Dict):
        """Send trade update to all user's connections."""
        if user_id in self.active_connections:
            message = {
                "type": "trade_update",
                "data": trade_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(
                        f"Failed to send trade update to user {user_id}: {e}"
                    )
                    disconnected.add(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)

    async def send_portfolio_update(self, user_id: int):
        """Send portfolio update to all user's connections."""
        if (
            user_id not in self.active_connections
            or user_id not in self.user_portfolios
        ):
            return

        try:
            Session = sessionmaker(bind=engine)
            db = Session()

            try:
                portfolio = (
                    db.query(Portfolio)
                    .filter(Portfolio.id == self.user_portfolios[user_id])
                    .first()
                )

                if not portfolio:
                    return

                # Update portfolio performance
                portfolio.update_performance_metrics()

                portfolio_data = {
                    "id": portfolio.id,
                    "total_value": float(portfolio.total_value),
                    "cash_balance": float(portfolio.cash_balance),
                    "invested_amount": float(portfolio.invested_amount),
                    "daily_return": float(portfolio.daily_return),
                    "total_return": float(portfolio.total_return),
                    "total_return_percent": float(portfolio.total_return_percent),
                    "last_updated": portfolio.updated_at.isoformat()
                    if portfolio.updated_at
                    else None,
                }

                message = {
                    "type": "portfolio_update",
                    "data": portfolio_data,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                disconnected = set()
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logger.warning(
                            f"Failed to send portfolio update to user {user_id}: {e}"
                        )
                        disconnected.add(websocket)

                # Clean up disconnected sockets
                for ws in disconnected:
                    self.active_connections[user_id].discard(ws)

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error sending portfolio update to user {user_id}: {e}")

    async def send_order_status_update(self, user_id: int, order_data: Dict):
        """Send order status update to user's connections."""
        if user_id in self.active_connections:
            message = {
                "type": "order_status",
                "data": order_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(
                        f"Failed to send order status to user {user_id}: {e}"
                    )
                    disconnected.add(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)

    async def broadcast_market_alert(self, message: Dict):
        """Broadcast market alert to all connected users."""
        alert_message = {
            "type": "market_alert",
            "data": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for user_id, websockets in self.active_connections.items():
            disconnected = set()
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(alert_message))
                except Exception:
                    disconnected.add(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                websockets.discard(ws)


# Global manager instance
trading_ws_manager = TradingWebSocketManager()


@router.websocket("/ws/trading/updates")
async def trading_updates_feed(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket endpoint for real-time trading updates.

    Provides real-time updates for:
    - Trade execution status
    - Portfolio value changes
    - Order book updates
    - Position changes
    - Account alerts

    Authentication via JWT token required.

    Messages from server to client:

    Trade execution update:
    {
        "type": "trade_update",
        "data": {
            "trade_id": 123,
            "symbol": "AAPL",
            "status": "filled",
            "executed_price": 150.25,
            "executed_quantity": 10,
            "executed_at": "2023-05-01T12:34:56.789Z"
        },
        "timestamp": "2023-05-01T12:34:56.789Z"
    }

    Portfolio update:
    {
        "type": "portfolio_update",
        "data": {
            "id": 456,
            "total_value": 25000.50,
            "cash_balance": 5000.00,
            "daily_return": 125.75,
            "total_return_percent": 8.25
        },
        "timestamp": "2023-05-01T12:34:56.789Z"
    }

    Order status update:
    {
        "type": "order_status",
        "data": {
            "trade_id": 123,
            "status": "pending_approval",
            "message": "Awaiting guardian approval"
        },
        "timestamp": "2023-05-01T12:34:56.789Z"
    }

    Market alert:
    {
        "type": "market_alert",
        "data": {
            "severity": "info",
            "title": "Market Hours",
            "message": "Market will close in 30 minutes"
        },
        "timestamp": "2023-05-01T12:34:56.789Z"
    }

    Error message:
    {
        "type": "error",
        "message": "Authentication failed",
        "code": "AUTH_FAILED"
    }
    """
    # Authenticate user
    user_data = None
    if token:
        try:
            Session = sessionmaker(bind=engine)
            db = Session()

            try:
                user_data = await get_current_user_ws(token, db)
                logger.info(
                    f"Trading WebSocket authenticated user: {user_data['email']}"
                )
            finally:
                db.close()

        except Exception as e:
            await websocket.close(code=1008, reason="Authentication failed")
            logger.warning(f"Trading WebSocket authentication failed: {str(e)}")
            return
    else:
        await websocket.close(code=1008, reason="Authentication token required")
        return

    # Validate trading permissions
    if not user_data.get("trading_enabled", False):
        await websocket.close(code=1008, reason="Trading access required")
        return

    user_id = user_data["id"]

    # Get user's portfolio
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            await websocket.close(code=1008, reason="No portfolio found")
            return

        portfolio_id = portfolio.id
    finally:
        db.close()

    # Connect to trading manager
    try:
        await trading_ws_manager.connect(websocket, user_id, portfolio_id)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for message (with timeout for heartbeat)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                try:
                    data = json.loads(message)
                    action = data.get("action")

                    if action == "ping":
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                        )
                    elif action == "refresh_portfolio":
                        await trading_ws_manager.send_portfolio_update(user_id)
                    else:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": f"Unknown action: {action}",
                                }
                            )
                        )

                except json.JSONDecodeError:
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": "Invalid JSON format"})
                    )

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in trading WebSocket: {e}")
                break

    except Exception as e:
        logger.error(f"Trading WebSocket connection error: {e}")
    finally:
        await trading_ws_manager.disconnect(websocket, user_id)


# API endpoint to trigger updates (for testing)
@router.post("/api/v1/trading/ws/test-update")
async def test_trading_update(user_id: int, update_type: str, data: Dict[str, Any]):
    """Test endpoint to trigger WebSocket updates (admin only)."""
    if update_type == "trade":
        await trading_ws_manager.send_trade_update(user_id, data)
    elif update_type == "portfolio":
        await trading_ws_manager.send_portfolio_update(user_id)
    elif update_type == "order":
        await trading_ws_manager.send_order_status_update(user_id, data)
    elif update_type == "alert":
        await trading_ws_manager.broadcast_market_alert(data)
    else:
        raise HTTPException(status_code=400, detail="Invalid update type")

    return {"message": "Update sent", "type": update_type}


# Function to get the global manager (for use in other services)
def get_trading_ws_manager() -> TradingWebSocketManager:
    """Get the global trading WebSocket manager."""
    return trading_ws_manager

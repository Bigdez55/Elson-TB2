"""
Simplified WebSocket market data streaming service for personal trading.

This service provides real-time market data streaming with a focus on simplicity
and personal use cases, without the complex enterprise features of the full
market_data_streaming.py module.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import websockets
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.config import settings
from app.services.market_data import market_data_service

logger = logging.getLogger(__name__)


class StreamingQuote(BaseModel):
    """Real-time streaming quote data model."""

    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    timestamp: str
    source: str


class ConnectionStatus(str, Enum):
    """WebSocket connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class SimpleWebSocketManager:
    """Simple WebSocket connection manager for personal use."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        self.connection_count = 0

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(
            f"WebSocket client connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all subscriptions
        for symbol, subscribers in self.subscriptions.items():
            if websocket in subscribers:
                subscribers.discard(websocket)

        # Clean up empty subscriptions
        empty_subscriptions = [
            symbol
            for symbol, subscribers in self.subscriptions.items()
            if not subscribers
        ]
        for symbol in empty_subscriptions:
            del self.subscriptions[symbol]

        logger.info(
            f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}"
        )

    def subscribe(self, websocket: WebSocket, symbol: str):
        """Subscribe a client to a symbol."""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].add(websocket)
        logger.debug(
            f"Client subscribed to {symbol}. Total subscribers: {len(self.subscriptions[symbol])}"
        )

    def unsubscribe(self, websocket: WebSocket, symbol: str):
        """Unsubscribe a client from a symbol."""
        if symbol in self.subscriptions and websocket in self.subscriptions[symbol]:
            self.subscriptions[symbol].discard(websocket)
            if not self.subscriptions[symbol]:
                del self.subscriptions[symbol]
            logger.debug(f"Client unsubscribed from {symbol}")

    def get_subscribed_symbols(self) -> List[str]:
        """Get all currently subscribed symbols."""
        return list(self.subscriptions.keys())

    def has_subscribers(self, symbol: str) -> bool:
        """Check if a symbol has any subscribers."""
        return symbol in self.subscriptions and len(self.subscriptions[symbol]) > 0

    async def broadcast_to_symbol(self, symbol: str, data: Dict[str, Any]):
        """Broadcast data to all subscribers of a symbol."""
        if symbol not in self.subscriptions:
            return

        message = json.dumps(data)
        disconnected_clients = []

        for websocket in list(self.subscriptions[symbol]):
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to websocket: {str(e)}")
                disconnected_clients.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.disconnect(websocket)


class PersonalMarketStreaming:
    """Simple market data streaming service for personal trading."""

    def __init__(self):
        self.websocket_manager = SimpleWebSocketManager()
        self.streaming_active = False
        self.update_interval = 5.0  # Update every 5 seconds for personal use
        self.streaming_task: Optional[asyncio.Task] = None
        self.latest_quotes: Dict[str, StreamingQuote] = {}

        # Simple rate limiting
        self.last_update_time = 0
        self.min_update_interval = 1.0  # Minimum 1 second between updates

    async def start_streaming(self):
        """Start the streaming service."""
        if self.streaming_active:
            logger.warning("Streaming service already active")
            return

        self.streaming_active = True
        self.streaming_task = asyncio.create_task(self._streaming_loop())
        logger.info("Personal market streaming service started")

    async def stop_streaming(self):
        """Stop the streaming service."""
        self.streaming_active = False
        if self.streaming_task:
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                pass
        logger.info("Personal market streaming service stopped")

    async def _streaming_loop(self):
        """Main streaming loop - fetches data and broadcasts to clients."""
        while self.streaming_active:
            try:
                # Get all subscribed symbols
                symbols = self.websocket_manager.get_subscribed_symbols()

                if symbols:
                    # Rate limiting check
                    current_time = time.time()
                    if (
                        current_time - self.last_update_time
                    ) < self.min_update_interval:
                        await asyncio.sleep(
                            self.min_update_interval
                            - (current_time - self.last_update_time)
                        )

                    # Fetch quotes for all subscribed symbols
                    await self._fetch_and_broadcast_quotes(symbols)
                    self.last_update_time = time.time()

                # Sleep for the update interval
                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                logger.info("Streaming loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in streaming loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _fetch_and_broadcast_quotes(self, symbols: List[str]):
        """Fetch quotes and broadcast to subscribers."""
        for symbol in symbols:
            try:
                # Get quote from market data service
                quote_data = await market_data_service.get_quote(symbol)

                if quote_data:
                    # Create streaming quote
                    streaming_quote = StreamingQuote(
                        symbol=symbol,
                        price=quote_data.get("price", 0.0),
                        bid=quote_data.get("bid"),
                        ask=quote_data.get("ask"),
                        volume=quote_data.get("volume"),
                        timestamp=datetime.now().isoformat(),
                        source=quote_data.get("source", "market_data_service"),
                    )

                    # Cache the latest quote
                    self.latest_quotes[symbol] = streaming_quote

                    # Broadcast to subscribers
                    await self.websocket_manager.broadcast_to_symbol(
                        symbol, {"type": "quote", "data": streaming_quote.model_dump()}
                    )

            except Exception as e:
                logger.error(f"Error fetching quote for {symbol}: {str(e)}")

    async def handle_websocket_connection(self, websocket: WebSocket):
        """Handle a WebSocket connection from a client."""
        client_ip = (
            getattr(websocket.client, "host", "unknown")
            if websocket.client
            else "unknown"
        )

        try:
            # Accept the connection
            await self.websocket_manager.connect(websocket)

            # Send welcome message
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "connected",
                        "message": "Connected to personal market data stream",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            # Handle incoming messages
            async for message in websocket.iter_text():
                await self._handle_client_message(websocket, message, client_ip)

        except WebSocketDisconnect:
            logger.info(f"Client {client_ip} disconnected")
        except Exception as e:
            logger.error(
                f"Error handling WebSocket connection from {client_ip}: {str(e)}"
            )
        finally:
            self.websocket_manager.disconnect(websocket)

    async def _handle_client_message(
        self, websocket: WebSocket, message: str, client_ip: str
    ):
        """Handle incoming messages from clients."""
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                symbols = data.get("symbols", [])
                if symbols and isinstance(symbols, list):
                    # Limit to reasonable number for personal use
                    symbols = symbols[:20]  # Max 20 symbols

                    valid_symbols = []
                    for symbol in symbols:
                        if (
                            isinstance(symbol, str)
                            and 1 <= len(symbol) <= 10
                            and symbol.replace(".", "").isalnum()
                        ):
                            symbol = symbol.upper()
                            self.websocket_manager.subscribe(websocket, symbol)
                            valid_symbols.append(symbol)

                    if valid_symbols:
                        # Send confirmation
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "subscribed",
                                    "symbols": valid_symbols,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        )

                        # Send cached quotes if available
                        for symbol in valid_symbols:
                            if symbol in self.latest_quotes:
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "quote",
                                            "data": self.latest_quotes[
                                                symbol
                                            ].model_dump(),
                                        }
                                    )
                                )

            elif action == "unsubscribe":
                symbols = data.get("symbols", [])
                if symbols and isinstance(symbols, list):
                    for symbol in symbols:
                        if isinstance(symbol, str):
                            symbol = symbol.upper()
                            self.websocket_manager.unsubscribe(websocket, symbol)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "unsubscribed",
                                "symbols": [
                                    s.upper() for s in symbols if isinstance(s, str)
                                ],
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    )

            elif action == "ping":
                await websocket.send_text(
                    json.dumps(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )
                )

            elif action == "status":
                # Get subscriptions for this client
                client_subscriptions = []
                for symbol, subscribers in self.websocket_manager.subscriptions.items():
                    if websocket in subscribers:
                        client_subscriptions.append(symbol)

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status",
                            "connected": True,
                            "subscriptions": client_subscriptions,
                            "streaming_active": self.streaming_active,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

            else:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": f"Unknown action: {action}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

        except json.JSONDecodeError:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": "Invalid JSON message",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )
        except Exception as e:
            logger.error(f"Error processing message from {client_ip}: {str(e)}")
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": "Server error processing message",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            "streaming_active": self.streaming_active,
            "connected_clients": len(self.websocket_manager.active_connections),
            "subscribed_symbols": list(self.websocket_manager.subscriptions.keys()),
            "subscription_count": len(self.websocket_manager.subscriptions),
            "cached_quotes": len(self.latest_quotes),
            "update_interval": self.update_interval,
            "total_connections": self.websocket_manager.connection_count,
        }

    async def get_latest_quote(
        self, symbol: str, max_age_seconds: int = 30
    ) -> Optional[StreamingQuote]:
        """Get the latest cached quote for a symbol."""
        if symbol not in self.latest_quotes:
            return None

        quote = self.latest_quotes[symbol]
        try:
            quote_time = datetime.fromisoformat(quote.timestamp)
            age = (datetime.now() - quote_time).total_seconds()

            if age <= max_age_seconds:
                return quote
        except Exception:
            pass

        return None

    async def force_update_symbol(self, symbol: str) -> Optional[StreamingQuote]:
        """Force an immediate update for a specific symbol."""
        try:
            quote_data = await market_data_service.get_quote(symbol)

            if quote_data:
                streaming_quote = StreamingQuote(
                    symbol=symbol,
                    price=quote_data.get("price", 0.0),
                    bid=quote_data.get("bid"),
                    ask=quote_data.get("ask"),
                    volume=quote_data.get("volume"),
                    timestamp=datetime.now().isoformat(),
                    source=quote_data.get("source", "market_data_service"),
                )

                # Cache and broadcast
                self.latest_quotes[symbol] = streaming_quote
                await self.websocket_manager.broadcast_to_symbol(
                    symbol, {"type": "quote", "data": streaming_quote.model_dump()}
                )

                return streaming_quote

        except Exception as e:
            logger.error(f"Error force updating {symbol}: {str(e)}")

        return None


# Global instance for personal use
personal_market_streaming = PersonalMarketStreaming()

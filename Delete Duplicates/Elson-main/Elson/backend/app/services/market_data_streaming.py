"""Market data streaming service.

This module provides WebSocket-based real-time market data streaming using 
direct connections to data providers rather than polling.
"""

import logging
import asyncio
import json
import time
import random
from typing import Dict, List, Set, Optional, Any, Callable, Awaitable
from enum import Enum
from datetime import datetime
import aiohttp
import websockets
from fastapi import WebSocket
from pydantic import BaseModel

from app.core.config import settings
from app.core.metrics import metrics
from app.core.alerts import AlertCategory, AlertSeverity
import app.services.market_data as market_data

logger = logging.getLogger(__name__)

class StreamSource(str, Enum):
    """Available streaming data sources."""
    ALPACA = "alpaca"
    POLYGON = "polygon"
    WEBSOCKET_HUB = "websocket_hub" # Local redistribution hub

class StreamingQuote(BaseModel):
    """Real-time streaming quote data model."""
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    timestamp: str
    trade_id: Optional[str] = None
    source: str
    
    model_config = {
        "arbitrary_types_allowed": True
    }

class WebSocketManager:
    """WebSocket connection manager for client connections."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        self.subscription_counts: Dict[str, int] = {}
        
        # Batch processing queues
        self.broadcast_queue: Dict[str, List[Any]] = {}
        self.batch_task = None
        self.batch_interval = 0.1  # 100ms batching interval
        self.batch_size = 100  # Maximum messages per batch per symbol 
        self.batch_task_running = False
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total connections: {len(self.active_connections)}")
        metrics.gauge("market_websocket.connections", len(self.active_connections))
        
        # Start batch processing task if not running
        self._ensure_batch_task_running()
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client and remove subscriptions."""
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            # Already removed
            pass
        
        # Remove from all subscriptions
        symbols_to_clean = []
        for symbol, subscribers in self.subscriptions.items():
            if websocket in subscribers:
                subscribers.remove(websocket)
                self.subscription_counts[symbol] = len(subscribers)
                
                # Track empty subscriptions for cleanup
                if not subscribers:
                    symbols_to_clean.append(symbol)
        
        # Clean up empty subscriptions
        for symbol in symbols_to_clean:
            del self.subscriptions[symbol]
            del self.subscription_counts[symbol]
            
            # Also clean up any pending broadcasts
            if symbol in self.broadcast_queue:
                del self.broadcast_queue[symbol]
            
        logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")
        metrics.gauge("market_websocket.connections", len(self.active_connections))
    
    def subscribe(self, websocket: WebSocket, symbol: str):
        """Subscribe a client to a symbol."""
        # Initialize subscription set if needed
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
            self.subscription_counts[symbol] = 0
            
        # Add client to subscription
        self.subscriptions[symbol].add(websocket)
        self.subscription_counts[symbol] = len(self.subscriptions[symbol])
        
        logger.debug(f"Client subscribed to {symbol}. Total subscribers: {self.subscription_counts[symbol]}")
        metrics.gauge(f"market_websocket.subscribers.{symbol}", self.subscription_counts[symbol])
    
    def unsubscribe(self, websocket: WebSocket, symbol: str):
        """Unsubscribe a client from a symbol."""
        if symbol in self.subscriptions and websocket in self.subscriptions[symbol]:
            self.subscriptions[symbol].remove(websocket)
            self.subscription_counts[symbol] = len(self.subscriptions[symbol])
            
            # Clean up empty subscriptions
            if not self.subscriptions[symbol]:
                del self.subscriptions[symbol]
                del self.subscription_counts[symbol]
                
                # Also clean up any pending broadcasts
                if symbol in self.broadcast_queue:
                    del self.broadcast_queue[symbol]
                
            logger.debug(f"Client unsubscribed from {symbol}. Remaining subscribers: {self.subscription_counts.get(symbol, 0)}")
            metrics.gauge(f"market_websocket.subscribers.{symbol}", self.subscription_counts.get(symbol, 0))
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get all currently subscribed symbols."""
        return list(self.subscriptions.keys())
    
    def has_subscribers(self, symbol: str) -> bool:
        """Check if a symbol has any subscribers."""
        return symbol in self.subscriptions and len(self.subscriptions[symbol]) > 0
    
    def _ensure_batch_task_running(self):
        """Ensure the batch processing task is running."""
        if not self.batch_task_running:
            import asyncio
            try:
                # Only create task if there is a running loop
                loop = asyncio.get_running_loop()
                self.batch_task = asyncio.create_task(self._process_broadcast_queue())
                self.batch_task_running = True
            except RuntimeError:
                # No running event loop, can happen during tests
                # We'll just mark it as not running and it will be started when needed
                self.batch_task_running = False
    
    async def _process_broadcast_queue(self):
        """Process the broadcast queue periodically."""
        try:
            self.batch_task_running = True
            
            while True:
                start_time = time.time()
                queue_size = sum(len(queue) for queue in self.broadcast_queue.values())
                
                if queue_size > 0:
                    # Process each symbol's queue
                    processed_count = 0
                    error_count = 0
                    
                    # Make a copy of the keys to avoid modification during iteration
                    symbols = list(self.broadcast_queue.keys())
                    
                    for symbol in symbols:
                        # Skip if no subscribers
                        if not self.has_subscribers(symbol):
                            if symbol in self.broadcast_queue:
                                del self.broadcast_queue[symbol]
                            continue
                            
                        # Get the queue for this symbol
                        if symbol not in self.broadcast_queue:
                            continue
                            
                        queue = self.broadcast_queue[symbol]
                        if not queue:
                            continue
                            
                        # Take up to batch_size messages
                        batch = queue[:self.batch_size]
                        self.broadcast_queue[symbol] = queue[self.batch_size:]
                        
                        # Get the latest message only (for high-frequency updates)
                        if len(batch) > 5 and all(isinstance(m, dict) and "symbol" in m for m in batch):
                            # For market data updates, just send the latest one
                            batch = [batch[-1]]
                            
                        # Send to all subscribers
                        websockets = self.subscriptions[symbol]
                        if not websockets:
                            continue
                            
                        # Process each message in the batch
                        for data in batch:
                            # JSON serialize the data
                            if isinstance(data, dict) or isinstance(data, list):
                                message = json.dumps(data)
                            elif isinstance(data, BaseModel):
                                message = json.dumps(data.model_dump())
                            else:
                                message = str(data)
                                
                            # Send to all subscribers
                            for websocket in list(websockets):  # Copy to avoid modification during iteration
                                try:
                                    await websocket.send_text(message)
                                    processed_count += 1
                                except Exception as e:
                                    error_count += 1
                                    logger.error(f"Error sending to websocket: {str(e)}")
                                    # Don't disconnect here - let the connection error handler handle it
                    
                    # Clean up empty queues
                    empty_queues = [s for s, q in self.broadcast_queue.items() if not q]
                    for symbol in empty_queues:
                        del self.broadcast_queue[symbol]
                        
                    # Log performance metrics
                    processing_time = (time.time() - start_time) * 1000  # ms
                    if processed_count > 0:
                        logger.debug(f"Broadcast batch: {processed_count} messages, {error_count} errors, {processing_time:.1f}ms")
                        metrics.gauge("market_websocket.broadcast_queue_size", queue_size)
                        metrics.histogram("market_websocket.broadcast_batch_time", processing_time)
                        metrics.increment("market_websocket.broadcast_messages", processed_count)
                        metrics.increment("market_websocket.broadcast_errors", error_count)
                
                # Sleep for the batch interval
                await asyncio.sleep(self.batch_interval)
                
        except asyncio.CancelledError:
            logger.info("Broadcast queue processor task cancelled")
            
        except Exception as e:
            logger.error(f"Error in broadcast queue processor: {str(e)}")
            
        finally:
            self.batch_task_running = False
            self.batch_task = None
            
            # Try to restart if we have active connections
            if self.active_connections:
                logger.info("Restarting broadcast queue processor")
                self._ensure_batch_task_running()
    
    async def broadcast(self, symbol: str, data: Any):
        """Queue data for broadcast to all subscribers of a symbol."""
        if not self.has_subscribers(symbol):
            return
            
        # Add to the queue
        if symbol not in self.broadcast_queue:
            self.broadcast_queue[symbol] = []
            
        self.broadcast_queue[symbol].append(data)
        
        # Start batch processing task if not running
        self._ensure_batch_task_running()
    
    async def broadcast_immediate(self, symbol: str, data: Any):
        """Broadcast data immediately to all subscribers of a symbol.
        
        This bypasses the queue for urgent messages.
        """
        if symbol not in self.subscriptions:
            return
            
        # Get all websockets subscribed to this symbol
        websockets = self.subscriptions[symbol]
        
        # JSON serialize the data
        if isinstance(data, dict) or isinstance(data, list):
            message = json.dumps(data)
        elif isinstance(data, BaseModel):
            message = json.dumps(data.model_dump())
        else:
            message = str(data)
        
        # Send to all subscribers
        for websocket in list(websockets):  # Copy to avoid modification during iteration
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to websocket: {str(e)}")
                # Don't disconnect here - let the connection error handler handle it

class MarketDataStreamingService:
    """Real-time market data streaming service using WebSockets."""
    
    def __init__(
        self,
        websocket_manager: Optional[WebSocketManager] = None,
        sources: Optional[List[StreamSource]] = None,
        api_keys: Optional[Dict[str, str]] = None
    ):
        """Initialize the streaming service."""
        self.websocket_manager = websocket_manager or WebSocketManager()
        self.sources = sources or [
            StreamSource.ALPACA,
            StreamSource.POLYGON
        ]
        
        # API keys
        self.api_keys = api_keys or {}
        self.alpaca_api_key = self.api_keys.get("alpaca_key_id", settings.ALPACA_API_KEY_ID)
        self.alpaca_secret_key = self.api_keys.get("alpaca_secret_key", settings.ALPACA_API_SECRET)
        self.polygon_api_key = self.api_keys.get("polygon", settings.POLYGON_API_KEY)
        
        # WebSocket connections to data providers
        self.provider_connections: Dict[StreamSource, Any] = {}
        self.connection_status: Dict[StreamSource, bool] = {
            source: False for source in StreamSource
        }
        
        # Active subscriptions to upstream data sources
        self.active_provider_subscriptions: Dict[StreamSource, Set[str]] = {
            source: set() for source in StreamSource
        }
        
        # Stream status
        self.stream_active = False
        self.stream_task = None
        self.last_message_time: Dict[StreamSource, float] = {
            source: 0 for source in StreamSource
        }
        
        # Stream latency and performance metrics
        self.message_counts: Dict[StreamSource, int] = {
            source: 0 for source in StreamSource
        }
        self.error_counts: Dict[StreamSource, int] = {
            source: 0 for source in StreamSource
        }
        
        # Cached latest quotes
        self.latest_quotes: Dict[str, StreamingQuote] = {}
        
        logger.info(f"Market data streaming service initialized with sources: {self.sources}")
    
    async def _connect_to_alpaca(self) -> bool:
        """Connect to Alpaca WebSocket API."""
        if not self.alpaca_api_key or not self.alpaca_secret_key:
            logger.warning("Alpaca API keys not configured, cannot connect to Alpaca WebSocket")
            return False
            
        try:
            # Alpaca WebSocket URL
            ws_url = "wss://stream.data.alpaca.markets/v2/iex"
            
            # Connect to WebSocket
            self.provider_connections[StreamSource.ALPACA] = await websockets.connect(ws_url)
            
            # Authentication message
            auth_message = {
                "action": "auth",
                "key": self.alpaca_api_key,
                "secret": self.alpaca_secret_key
            }
            
            await self.provider_connections[StreamSource.ALPACA].send(json.dumps(auth_message))
            
            # Wait for auth response
            response = await self.provider_connections[StreamSource.ALPACA].recv()
            auth_response = json.loads(response)
            
            if auth_response[0].get('T') == 'success' and auth_response[0].get('msg') == 'authenticated':
                logger.info("Successfully authenticated with Alpaca WebSocket API")
                self.connection_status[StreamSource.ALPACA] = True
                metrics.gauge("market_streaming.alpaca_connected", 1)
                return True
            else:
                logger.error(f"Alpaca WebSocket authentication failed: {auth_response}")
                metrics.gauge("market_streaming.alpaca_connected", 0)
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Alpaca WebSocket: {str(e)}")
            self.error_counts[StreamSource.ALPACA] += 1
            metrics.gauge("market_streaming.alpaca_connected", 0)
            metrics.increment("market_streaming.connection_error")
            return False
    
    async def _connect_to_polygon(self) -> bool:
        """Connect to Polygon WebSocket API."""
        if not self.polygon_api_key:
            logger.warning("Polygon API key not configured, cannot connect to Polygon WebSocket")
            return False
            
        try:
            # Polygon WebSocket URL
            ws_url = f"wss://socket.polygon.io/stocks"
            
            # Connect to WebSocket
            self.provider_connections[StreamSource.POLYGON] = await websockets.connect(ws_url)
            
            # Authentication message
            auth_message = {
                "action": "auth",
                "params": self.polygon_api_key
            }
            
            await self.provider_connections[StreamSource.POLYGON].send(json.dumps(auth_message))
            
            # Wait for auth response
            response = await self.provider_connections[StreamSource.POLYGON].recv()
            auth_response = json.loads(response)
            
            if "status" in auth_response and auth_response["status"] == "connected":
                logger.info("Successfully authenticated with Polygon WebSocket API")
                self.connection_status[StreamSource.POLYGON] = True
                metrics.gauge("market_streaming.polygon_connected", 1)
                return True
            else:
                logger.error(f"Polygon WebSocket authentication failed: {auth_response}")
                metrics.gauge("market_streaming.polygon_connected", 0)
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Polygon WebSocket: {str(e)}")
            self.error_counts[StreamSource.POLYGON] += 1
            metrics.gauge("market_streaming.polygon_connected", 0)
            metrics.increment("market_streaming.connection_error")
            return False
    
    async def _subscribe_to_alpaca(self, symbols: List[str]) -> bool:
        """Subscribe to symbols on Alpaca WebSocket."""
        if not self.connection_status[StreamSource.ALPACA]:
            logger.warning("Not connected to Alpaca, cannot subscribe")
            return False
            
        try:
            # Subscribe message
            subscribe_message = {
                "action": "subscribe",
                "trades": symbols,
                "quotes": symbols
            }
            
            await self.provider_connections[StreamSource.ALPACA].send(json.dumps(subscribe_message))
            
            # Update active subscriptions
            self.active_provider_subscriptions[StreamSource.ALPACA].update(symbols)
            
            logger.info(f"Subscribed to {len(symbols)} symbols on Alpaca: {symbols}")
            metrics.gauge("market_streaming.alpaca_subscriptions", 
                         len(self.active_provider_subscriptions[StreamSource.ALPACA]))
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to Alpaca WebSocket: {str(e)}")
            self.error_counts[StreamSource.ALPACA] += 1
            metrics.increment("market_streaming.subscription_error")
            return False
    
    async def _subscribe_to_polygon(self, symbols: List[str]) -> bool:
        """Subscribe to symbols on Polygon WebSocket."""
        if not self.connection_status[StreamSource.POLYGON]:
            logger.warning("Not connected to Polygon, cannot subscribe")
            return False
            
        try:
            # Format symbols for Polygon (T.AAPL, T.MSFT, etc.)
            formatted_symbols = [f"T.{symbol}" for symbol in symbols]
            
            # Subscribe message
            subscribe_message = {
                "action": "subscribe",
                "params": ",".join(formatted_symbols)
            }
            
            await self.provider_connections[StreamSource.POLYGON].send(json.dumps(subscribe_message))
            
            # Update active subscriptions
            self.active_provider_subscriptions[StreamSource.POLYGON].update(symbols)
            
            logger.info(f"Subscribed to {len(symbols)} symbols on Polygon: {symbols}")
            metrics.gauge("market_streaming.polygon_subscriptions", 
                         len(self.active_provider_subscriptions[StreamSource.POLYGON]))
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to Polygon WebSocket: {str(e)}")
            self.error_counts[StreamSource.POLYGON] += 1
            metrics.increment("market_streaming.subscription_error")
            return False
    
    async def _unsubscribe_from_alpaca(self, symbols: List[str]) -> bool:
        """Unsubscribe from symbols on Alpaca WebSocket."""
        if not self.connection_status[StreamSource.ALPACA]:
            return False
            
        try:
            # Unsubscribe message
            unsubscribe_message = {
                "action": "unsubscribe",
                "trades": symbols,
                "quotes": symbols
            }
            
            await self.provider_connections[StreamSource.ALPACA].send(json.dumps(unsubscribe_message))
            
            # Update active subscriptions
            for symbol in symbols:
                self.active_provider_subscriptions[StreamSource.ALPACA].discard(symbol)
            
            logger.info(f"Unsubscribed from {len(symbols)} symbols on Alpaca")
            metrics.gauge("market_streaming.alpaca_subscriptions", 
                         len(self.active_provider_subscriptions[StreamSource.ALPACA]))
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from Alpaca WebSocket: {str(e)}")
            self.error_counts[StreamSource.ALPACA] += 1
            return False
    
    async def _unsubscribe_from_polygon(self, symbols: List[str]) -> bool:
        """Unsubscribe from symbols on Polygon WebSocket."""
        if not self.connection_status[StreamSource.POLYGON]:
            return False
            
        try:
            # Format symbols for Polygon (T.AAPL, T.MSFT, etc.)
            formatted_symbols = [f"T.{symbol}" for symbol in symbols]
            
            # Unsubscribe message
            unsubscribe_message = {
                "action": "unsubscribe",
                "params": ",".join(formatted_symbols)
            }
            
            await self.provider_connections[StreamSource.POLYGON].send(json.dumps(unsubscribe_message))
            
            # Update active subscriptions
            for symbol in symbols:
                self.active_provider_subscriptions[StreamSource.POLYGON].discard(symbol)
            
            logger.info(f"Unsubscribed from {len(symbols)} symbols on Polygon")
            metrics.gauge("market_streaming.polygon_subscriptions", 
                         len(self.active_provider_subscriptions[StreamSource.POLYGON]))
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from Polygon WebSocket: {str(e)}")
            self.error_counts[StreamSource.POLYGON] += 1
            return False
    
    def _parse_alpaca_message(self, message: Dict) -> Optional[StreamingQuote]:
        """Parse a message from Alpaca WebSocket."""
        try:
            # Check message type
            msg_type = message.get('T')
            
            if msg_type == 't': # Trade message
                symbol = message.get('S')
                price = float(message.get('p'))
                timestamp = datetime.fromtimestamp(message.get('t') / 1e9).isoformat()
                
                return StreamingQuote(
                    symbol=symbol,
                    price=price,
                    volume=int(message.get('v', 0)),
                    timestamp=timestamp,
                    trade_id=message.get('i'),
                    source='alpaca'
                )
                
            elif msg_type == 'q': # Quote message
                symbol = message.get('S')
                bid = float(message.get('bp', 0))
                ask = float(message.get('ap', 0))
                # Mid price for quotes
                price = (bid + ask) / 2 if bid and ask else None
                timestamp = datetime.fromtimestamp(message.get('t') / 1e9).isoformat()
                
                return StreamingQuote(
                    symbol=symbol,
                    price=price,
                    bid=bid,
                    ask=ask,
                    timestamp=timestamp,
                    source='alpaca'
                )
                
        except Exception as e:
            logger.error(f"Error parsing Alpaca message: {str(e)}, message: {message}")
            return None
            
        return None
    
    def _parse_polygon_message(self, message: Dict) -> Optional[StreamingQuote]:
        """Parse a message from Polygon WebSocket."""
        try:
            # Check event type
            event_type = message.get('ev')
            
            if event_type == 'T': # Trade event
                # Polygon format: T.AAPL -> AAPL
                symbol = message.get('sym')
                if symbol.startswith('T.'):
                    symbol = symbol[2:]
                    
                price = float(message.get('p'))
                timestamp = datetime.fromtimestamp(message.get('t') / 1000).isoformat()
                
                return StreamingQuote(
                    symbol=symbol,
                    price=price,
                    volume=int(message.get('s', 0)),
                    timestamp=timestamp,
                    trade_id=str(message.get('i')),
                    source='polygon'
                )
                
            elif event_type == 'Q': # Quote event
                # Polygon format: Q.AAPL -> AAPL
                symbol = message.get('sym')
                if symbol.startswith('Q.'):
                    symbol = symbol[2:]
                    
                bid = float(message.get('bp', 0))
                ask = float(message.get('ap', 0))
                # Mid price for quotes
                price = (bid + ask) / 2 if bid and ask else None
                timestamp = datetime.fromtimestamp(message.get('t') / 1000).isoformat()
                
                return StreamingQuote(
                    symbol=symbol,
                    price=price,
                    bid=bid,
                    ask=ask,
                    timestamp=timestamp,
                    source='polygon'
                )
                
        except Exception as e:
            logger.error(f"Error parsing Polygon message: {str(e)}, message: {message}")
            return None
            
        return None
    
    async def _process_alpaca_stream(self):
        """Process messages from Alpaca WebSocket."""
        if not self.connection_status[StreamSource.ALPACA]:
            return
            
        try:
            ws = self.provider_connections[StreamSource.ALPACA]
            
            # Read and process messages
            async for message in ws:
                # Update last message time
                self.last_message_time[StreamSource.ALPACA] = time.time()
                
                # Parse message
                try:
                    data = json.loads(message)
                    
                    # Alpaca sends arrays of messages
                    for msg in data:
                        # Skip status messages
                        if msg.get('T') in ['success', 'subscription', 'error']:
                            if msg.get('T') == 'error':
                                logger.error(f"Alpaca WebSocket error: {msg}")
                                self.error_counts[StreamSource.ALPACA] += 1
                            continue
                        
                        # Parse and queue for broadcast
                        quote = self._parse_alpaca_message(msg)
                        if quote and quote.symbol:
                            # Cache latest quote
                            self.latest_quotes[quote.symbol] = quote
                            
                            # Only queue for broadcast if there are subscribers
                            if self.websocket_manager.has_subscribers(quote.symbol):
                                await self.websocket_manager.broadcast(quote.symbol, quote.model_dump())
                            
                            # Track message count
                            self.message_counts[StreamSource.ALPACA] += 1
                            metrics.increment("market_streaming.alpaca_messages")
                            
                except Exception as e:
                    logger.error(f"Error processing Alpaca message: {str(e)}")
                    self.error_counts[StreamSource.ALPACA] += 1
                    metrics.increment("market_streaming.alpaca_errors")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Alpaca WebSocket connection closed")
            self.connection_status[StreamSource.ALPACA] = False
            metrics.gauge("market_streaming.alpaca_connected", 0)
            
        except Exception as e:
            logger.error(f"Error in Alpaca stream processor: {str(e)}")
            self.error_counts[StreamSource.ALPACA] += 1
            self.connection_status[StreamSource.ALPACA] = False
            metrics.gauge("market_streaming.alpaca_connected", 0)
    
    async def _process_polygon_stream(self):
        """Process messages from Polygon WebSocket."""
        if not self.connection_status[StreamSource.POLYGON]:
            return
            
        try:
            ws = self.provider_connections[StreamSource.POLYGON]
            
            # Read and process messages
            async for message in ws:
                # Update last message time
                self.last_message_time[StreamSource.POLYGON] = time.time()
                
                # Parse message
                try:
                    data = json.loads(message)
                    
                    # Polygon may send single messages or arrays
                    messages = data if isinstance(data, list) else [data]
                    
                    for msg in messages:
                        # Skip status messages
                        if msg.get('ev') in ['status', 'connected']:
                            if msg.get('status') == 'error':
                                logger.error(f"Polygon WebSocket error: {msg}")
                                self.error_counts[StreamSource.POLYGON] += 1
                            continue
                        
                        # Parse and queue for broadcast
                        quote = self._parse_polygon_message(msg)
                        if quote and quote.symbol:
                            # Cache latest quote
                            self.latest_quotes[quote.symbol] = quote
                            
                            # Only queue for broadcast if there are subscribers
                            if self.websocket_manager.has_subscribers(quote.symbol):
                                await self.websocket_manager.broadcast(quote.symbol, quote.model_dump())
                            
                            # Track message count
                            self.message_counts[StreamSource.POLYGON] += 1
                            metrics.increment("market_streaming.polygon_messages")
                            
                except Exception as e:
                    logger.error(f"Error processing Polygon message: {str(e)}")
                    self.error_counts[StreamSource.POLYGON] += 1
                    metrics.increment("market_streaming.polygon_errors")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Polygon WebSocket connection closed")
            self.connection_status[StreamSource.POLYGON] = False
            metrics.gauge("market_streaming.polygon_connected", 0)
            
        except Exception as e:
            logger.error(f"Error in Polygon stream processor: {str(e)}")
            self.error_counts[StreamSource.POLYGON] += 1
            self.connection_status[StreamSource.POLYGON] = False
            metrics.gauge("market_streaming.polygon_connected", 0)
    
    async def _heartbeat_check(self):
        """Monitor connection health with heartbeats and exponential backoff reconnection strategy."""
        from app.core.alerts import alert_manager
        
        # Configuration for exponential backoff
        reconnect_backoff = {
            source: 1.0 for source in self.sources  # Initial backoff of 1 second
        }
        max_backoff = 60.0  # Maximum backoff of 60 seconds
        
        # Track consecutive failures for circuit breaking
        consecutive_failures = {
            source: 0 for source in self.sources
        }
        circuit_breaker_threshold = 5  # Break circuit after 5 consecutive failures
        circuit_reset_time = 300  # Reset circuit breaker after 5 minutes
        circuit_breaker_status = {
            source: {
                "tripped": False,
                "trip_time": 0,
            } for source in self.sources
        }
        
        # Connection health metrics
        health_check_interval = 10  # Seconds between checks
        message_timeout = 60  # Seconds of no messages to consider unhealthy
        health_ping_interval = 60  # Send ping to active connections every minute
        last_health_ping = time.time()
        
        logger.info("Starting market data stream heartbeat monitor")
        metrics.gauge("market_streaming.heartbeat_monitor", 1)
        
        while self.stream_active:
            try:
                now = time.time()
                
                # Check connection health for each source
                for source in self.sources:
                    # Skip websocket hub
                    if source == StreamSource.WEBSOCKET_HUB:
                        continue
                    
                    # Check if circuit breaker is tripped and should be reset
                    if circuit_breaker_status[source]["tripped"]:
                        if (now - circuit_breaker_status[source]["trip_time"]) > circuit_reset_time:
                            logger.info(f"Resetting circuit breaker for {source} after {circuit_reset_time} seconds")
                            circuit_breaker_status[source]["tripped"] = False
                            consecutive_failures[source] = 0
                            metrics.gauge(f"market_streaming.circuit_breaker", 0, tags={"source": source.value})
                            
                            # Now we can try to reconnect
                            reconnect_backoff[source] = 1.0  # Reset backoff
                        else:
                            # Circuit breaker still active, skip this source
                            continue
                    
                    # Check if connection is active but hasn't received messages lately
                    if self.connection_status[source]:
                        last_msg_time = self.last_message_time[source]
                        if last_msg_time > 0 and (now - last_msg_time) > message_timeout:
                            # Calculate time since last message
                            message_gap = now - last_msg_time
                            logger.warning(f"No messages from {source} for {message_gap:.1f} seconds, reconnecting")
                            metrics.increment(f"market_streaming.message_timeout", tags={"source": source.value})
                            
                            # Record timeout metric
                            metrics.gauge(f"market_streaming.message_gap", message_gap, tags={"source": source.value})
                            
                            # Mark as disconnected
                            self.connection_status[source] = False
                            metrics.gauge(f"market_streaming.{source.value}_connected", 0)
                            
                            # Try to reconnect
                            success = await self._reconnect_source(source)
                            
                            # Track consecutive failures for circuit breaking
                            if success:
                                consecutive_failures[source] = 0
                                reconnect_backoff[source] = 1.0  # Reset backoff on success
                            else:
                                consecutive_failures[source] += 1
                                
                                # Check if we should trip the circuit breaker
                                if consecutive_failures[source] >= circuit_breaker_threshold:
                                    logger.warning(f"Circuit breaker tripped for {source} after {consecutive_failures[source]} consecutive failures")
                                    circuit_breaker_status[source]["tripped"] = True
                                    circuit_breaker_status[source]["trip_time"] = now
                                    metrics.gauge(f"market_streaming.circuit_breaker", 1, tags={"source": source.value})
                                    
                                    # Send alert for circuit breaker trip
                                    alert_manager.send_alert(
                                        category="MARKET_DATA",
                                        severity="ERROR",
                                        title=f"Market data circuit breaker tripped for {source}",
                                        description=f"Connection to {source} failed after {consecutive_failures[source]} consecutive attempts",
                                        metadata={
                                            "source": source.value,
                                            "consecutive_failures": consecutive_failures[source],
                                            "trip_time": datetime.now().isoformat(),
                                            "reset_time": datetime.fromtimestamp(now + circuit_reset_time).isoformat()
                                        }
                                    )
                                else:
                                    # Increase backoff on failure with jitter
                                    jitter = 0.1 * reconnect_backoff[source] * (0.5 + random.random())
                                    reconnect_backoff[source] = min(
                                        reconnect_backoff[source] * 1.5 + jitter,
                                        max_backoff
                                    )
                                    logger.info(f"Reconnect failed, next attempt for {source} in {reconnect_backoff[source]:.1f}s")
                        else:
                            # Connection is healthy, check if we need to send periodic health check (ping)
                            if (now - last_health_ping) > health_ping_interval:
                                try:
                                    if source in self.provider_connections and self.provider_connections[source]:
                                        # Different providers have different ping mechanisms
                                        if source == StreamSource.ALPACA:
                                            # Alpaca uses a ping message
                                            await self.provider_connections[source].send(json.dumps({"action": "ping"}))
                                            logger.debug(f"Sent ping to {source}")
                                        elif source == StreamSource.POLYGON:
                                            # Polygon uses a status check
                                            await self.provider_connections[source].send(json.dumps({"action": "status"}))
                                            logger.debug(f"Sent status check to {source}")
                                except Exception as e:
                                    logger.warning(f"Error sending health check to {source}: {str(e)}")
                                    # Don't mark as failed just for a ping failure
                            
                    # Check if connection is not active and we should attempt reconnect
                    elif not self.connection_status[source]:
                        # Only attempt reconnect if circuit breaker is not tripped
                        if not circuit_breaker_status[source]["tripped"]:
                            # Try to reconnect with backoff
                            delay_key = f"reconnect_delay_{source.value}"
                            last_attempt = getattr(self, delay_key, 0)
                            
                            if (now - last_attempt) > reconnect_backoff[source]:
                                logger.info(f"Attempting to reconnect to {source} after {reconnect_backoff[source]:.1f}s backoff")
                                setattr(self, delay_key, now)
                                
                                # Try to reconnect
                                success = await self._reconnect_source(source)
                                
                                # Track consecutive failures for circuit breaking
                                if success:
                                    consecutive_failures[source] = 0
                                    reconnect_backoff[source] = 1.0  # Reset backoff on success
                                else:
                                    consecutive_failures[source] += 1
                                    
                                    # Check if we should trip the circuit breaker
                                    if consecutive_failures[source] >= circuit_breaker_threshold:
                                        logger.warning(f"Circuit breaker tripped for {source} after {consecutive_failures[source]} consecutive failures")
                                        circuit_breaker_status[source]["tripped"] = True
                                        circuit_breaker_status[source]["trip_time"] = now
                                        metrics.gauge(f"market_streaming.circuit_breaker", 1, tags={"source": source.value})
                                        
                                        # Send alert for circuit breaker trip
                                        alert_manager.send_alert(
                                            category="MARKET_DATA",
                                            severity="ERROR",
                                            title=f"Market data circuit breaker tripped for {source}",
                                            description=f"Connection to {source} failed after {consecutive_failures[source]} consecutive attempts",
                                            metadata={
                                                "source": source.value,
                                                "consecutive_failures": consecutive_failures[source],
                                                "trip_time": datetime.now().isoformat(),
                                                "reset_time": datetime.fromtimestamp(now + circuit_reset_time).isoformat()
                                            }
                                        )
                                    else:
                                        # Increase backoff on failure with jitter
                                        jitter = 0.1 * reconnect_backoff[source] * (0.5 + random.random())
                                        reconnect_backoff[source] = min(
                                            reconnect_backoff[source] * 1.5 + jitter,
                                            max_backoff
                                        )
                                        logger.info(f"Reconnect failed, next attempt for {source} in {reconnect_backoff[source]:.1f}s")
                
                # Update health ping time if we sent pings
                if (now - last_health_ping) > health_ping_interval:
                    last_health_ping = now
                
                # Log status periodically
                if int(now) % 300 == 0:  # Every 5 minutes
                    self._log_status()
                    
                    # Also log circuit breaker status
                    tripped_sources = [s.value for s in self.sources if circuit_breaker_status[s]["tripped"]]
                    if tripped_sources:
                        logger.warning(f"Circuit breakers currently tripped for: {', '.join(tripped_sources)}")
                
                # Sleep for the health check interval
                await asyncio.sleep(health_check_interval)
                
            except asyncio.CancelledError:
                logger.info("Heartbeat monitor task cancelled")
                break
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {str(e)}")
                await asyncio.sleep(health_check_interval)  # Sleep on error to avoid tight loops
    
    async def _reconnect_source(self, source: StreamSource) -> bool:
        """Reconnect to a data source with enhanced error recovery.
        
        Args:
            source: The source to reconnect to
            
        Returns:
            bool: True if reconnection was successful, False otherwise
        """
        logger.info(f"Attempting to reconnect to {source}")
        from app.core.alerts import alert_manager
        
        # Track start time for metrics
        start_time = time.time()
        metrics.increment(f"market_streaming.reconnect_attempts", tags={"source": source.value})
        
        # Safety check for rate limiting reconnections
        current_time = time.time()
        rate_limit_key = f"last_reconnect_{source.value}"
        last_attempt = getattr(self, rate_limit_key, 0)
        if (current_time - last_attempt) < 5:  # Minimum 5 second interval between reconnections
            logger.warning(f"Reconnection attempt to {source} too frequent, skipping")
            return False
        
        # Update last attempt time
        setattr(self, rate_limit_key, current_time)
        
        try:
            # Close existing connection if any
            if source in self.provider_connections and self.provider_connections[source]:
                try:
                    logger.debug(f"Closing existing connection to {source}")
                    await self.provider_connections[source].close()
                except Exception as e:
                    logger.warning(f"Error closing connection to {source}: {str(e)}")
            
            # Wait a short time to ensure socket is fully closed
            await asyncio.sleep(0.5)
            
            # Connect to source
            logger.debug(f"Connecting to {source}")
            if source == StreamSource.ALPACA:
                connected = await self._connect_to_alpaca()
            elif source == StreamSource.POLYGON:
                connected = await self._connect_to_polygon()
            else:
                logger.warning(f"Unknown source to reconnect: {source}")
                return False
            
            if connected:
                logger.info(f"Connection to {source} established, resubscribing to symbols")
                # Resubscribe to symbols
                symbols = list(self.active_provider_subscriptions[source])
                
                # Only resubscribe if we have active symbols
                resubscribe_success = True
                if symbols:
                    try:
                        if source == StreamSource.ALPACA:
                            resubscribe_success = await self._subscribe_to_alpaca(symbols)
                        elif source == StreamSource.POLYGON:
                            resubscribe_success = await self._subscribe_to_polygon(symbols)
                    except Exception as e:
                        logger.error(f"Error resubscribing to {source}: {str(e)}")
                        resubscribe_success = False
                
                if not resubscribe_success:
                    logger.error(f"Failed to resubscribe to {source}, but connection is established")
                    # We'll still consider this a success since the connection is active
                    # Stream processors will attempt to resubscribe in their loops
                
                # Start stream processor with proper error handling
                logger.debug(f"Starting stream processor for {source}")
                try:
                    if source == StreamSource.ALPACA:
                        asyncio.create_task(self._process_alpaca_stream())
                    elif source == StreamSource.POLYGON:
                        asyncio.create_task(self._process_polygon_stream())
                except Exception as e:
                    logger.error(f"Error starting stream processor for {source}: {str(e)}")
                    # Don't fail the reconnection just because task creation failed
                    # The heartbeat will detect missing messages and try again
                
                # Record successful reconnection
                metrics.increment(f"market_streaming.reconnect_success", tags={"source": source.value})
                metrics.gauge(f"market_streaming.{source.value}_connected", 1)
                
                # Calculate and record reconnection time
                reconnect_time = (time.time() - start_time) * 1000  # ms
                metrics.histogram(f"market_streaming.reconnect_time", reconnect_time, tags={"source": source.value})
                
                logger.info(f"Successfully reconnected to {source} in {reconnect_time:.1f}ms")
                return True
            else:
                # Connection failed
                logger.error(f"Failed to reconnect to {source}")
                metrics.increment(f"market_streaming.reconnect_failure", tags={"source": source.value})
                
                # Send alert for persistent connection failures
                if self.error_counts[source] % 5 == 0:  # Every 5 failures
                    alert_manager.send_alert(
                        category="MARKET_DATA",
                        severity="WARNING",
                        title=f"Persistent connection failures to {source}",
                        description=f"Failed to reconnect to {source} after {self.error_counts[source]} attempts",
                        metadata={
                            "source": source.value,
                            "error_count": self.error_counts[source],
                            "last_attempt": datetime.now().isoformat()
                        }
                    )
                
                return False
                
        except Exception as e:
            logger.error(f"Error reconnecting to {source}: {str(e)}")
            self.error_counts[source] += 1
            metrics.increment(f"market_streaming.reconnect_error", tags={"source": source.value})
            return False
    
    def _log_status(self):
        """Log current streaming service status."""
        status = {
            "connections": {
                source: self.connection_status[source] for source in self.sources 
                if source != StreamSource.WEBSOCKET_HUB
            },
            "subscriptions": {
                source: len(self.active_provider_subscriptions[source]) for source in self.sources
                if source != StreamSource.WEBSOCKET_HUB
            },
            "message_counts": {
                source: self.message_counts[source] for source in self.sources
                if source != StreamSource.WEBSOCKET_HUB
            },
            "error_counts": {
                source: self.error_counts[source] for source in self.sources
                if source != StreamSource.WEBSOCKET_HUB
            },
            "client_connections": len(self.websocket_manager.active_connections),
            "client_subscriptions": len(self.websocket_manager.subscriptions)
        }
        
        logger.info(f"Streaming service status: {json.dumps(status)}")
    
    async def get_latest_quote(self, symbol: str, max_age_seconds: int = 5) -> Optional[StreamingQuote]:
        """Get the latest streaming quote for a symbol.
        
        Args:
            symbol: Symbol to get quote for
            max_age_seconds: Maximum age of quote in seconds
            
        Returns:
            Latest StreamingQuote or None if not available
        """
        # Check if we have a cached quote
        if symbol in self.latest_quotes:
            quote = self.latest_quotes[symbol]
            
            # Parse timestamp
            try:
                quote_time = datetime.fromisoformat(quote.timestamp)
                age = (datetime.now() - quote_time).total_seconds()
                
                # If quote is fresh enough, return it
                if age <= max_age_seconds:
                    return quote
            except:
                pass
        
        # If no valid cached quote, return None
        return None
    
    async def start(self):
        """Start the streaming service."""
        if self.stream_active:
            logger.warning("Streaming service already started")
            return
            
        logger.info("Starting market data streaming service")
        self.stream_active = True
        
        # Connect to data sources
        connection_tasks = []
        
        if StreamSource.ALPACA in self.sources:
            connection_tasks.append(self._connect_to_alpaca())
            
        if StreamSource.POLYGON in self.sources:
            connection_tasks.append(self._connect_to_polygon())
        
        # Wait for connections to establish
        if connection_tasks:
            await asyncio.gather(*connection_tasks)
        
        # Start stream processors
        if self.connection_status[StreamSource.ALPACA]:
            asyncio.create_task(self._process_alpaca_stream())
            
        if self.connection_status[StreamSource.POLYGON]:
            asyncio.create_task(self._process_polygon_stream())
        
        # Start heartbeat checker
        self.stream_task = asyncio.create_task(self._heartbeat_check())
        
        logger.info("Market data streaming service started")
    
    async def stop(self):
        """Stop the streaming service."""
        if not self.stream_active:
            return
            
        logger.info("Stopping market data streaming service")
        self.stream_active = False
        
        # Cancel heartbeat task
        if self.stream_task:
            self.stream_task.cancel()
        
        # Close provider connections
        for source, connection in self.provider_connections.items():
            if connection:
                try:
                    await connection.close()
                except:
                    pass
        
        # Clear status
        self.connection_status = {source: False for source in StreamSource}
        self.provider_connections = {}
        
        logger.info("Market data streaming service stopped")
    
    async def subscribe_symbols(self, symbols: List[str]) -> bool:
        """Subscribe to streaming data for symbols.
        
        Args:
            symbols: List of symbol tickers to subscribe to
            
        Returns:
            Success status
        """
        if not self.stream_active:
            logger.warning("Streaming service not started, cannot subscribe")
            return False
            
        # Validate symbols
        valid_symbols = [s.upper() for s in symbols if s]
        if not valid_symbols:
            return False
            
        # Subscription tasks
        tasks = []
        
        # Subscribe to Alpaca
        if StreamSource.ALPACA in self.sources and self.connection_status[StreamSource.ALPACA]:
            # Filter out already subscribed symbols
            new_symbols = [s for s in valid_symbols if s not in self.active_provider_subscriptions[StreamSource.ALPACA]]
            if new_symbols:
                tasks.append(self._subscribe_to_alpaca(new_symbols))
        
        # Subscribe to Polygon
        if StreamSource.POLYGON in self.sources and self.connection_status[StreamSource.POLYGON]:
            # Filter out already subscribed symbols
            new_symbols = [s for s in valid_symbols if s not in self.active_provider_subscriptions[StreamSource.POLYGON]]
            if new_symbols:
                tasks.append(self._subscribe_to_polygon(new_symbols))
        
        # Wait for subscriptions to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for errors
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error subscribing to symbols: {str(result)}")
                    return False
            
            return True
        else:
            # If no tasks were created (already subscribed)
            return True
    
    async def unsubscribe_symbols(self, symbols: List[str]) -> bool:
        """Unsubscribe from streaming data for symbols.
        
        Args:
            symbols: List of symbol tickers to unsubscribe from
            
        Returns:
            Success status
        """
        if not self.stream_active:
            return False
            
        # Validate symbols
        valid_symbols = [s.upper() for s in symbols if s]
        if not valid_symbols:
            return False
            
        # Unsubscription tasks
        tasks = []
        
        # Check if any of our clients are still subscribed
        any_client_subscribed = False
        for symbol in valid_symbols:
            if self.websocket_manager.has_subscribers(symbol):
                any_client_subscribed = True
                break
        
        # Only unsubscribe from providers if no clients are subscribed
        if not any_client_subscribed:
            # Unsubscribe from Alpaca
            if StreamSource.ALPACA in self.sources and self.connection_status[StreamSource.ALPACA]:
                # Filter to only subscribed symbols
                symbols_to_unsub = [s for s in valid_symbols if s in self.active_provider_subscriptions[StreamSource.ALPACA]]
                if symbols_to_unsub:
                    tasks.append(self._unsubscribe_from_alpaca(symbols_to_unsub))
            
            # Unsubscribe from Polygon
            if StreamSource.POLYGON in self.sources and self.connection_status[StreamSource.POLYGON]:
                # Filter to only subscribed symbols
                symbols_to_unsub = [s for s in valid_symbols if s in self.active_provider_subscriptions[StreamSource.POLYGON]]
                if symbols_to_unsub:
                    tasks.append(self._unsubscribe_from_polygon(symbols_to_unsub))
            
            # Wait for unsubscriptions to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for errors
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error unsubscribing from symbols: {str(result)}")
                        return False
        
        return True
    
    async def handle_client_websocket(self, websocket: WebSocket):
        """Handle a client WebSocket connection.
        
        Args:
            websocket: WebSocket connection from client
        """
        # Track performance metrics
        start_time = time.time()
        message_count = 0
        error_count = 0
        client_ip = getattr(websocket.client, "host", "unknown")
        
        # Accept connection
        await self.websocket_manager.connect(websocket)
        logger.info(f"Client connected from {client_ip}")
        metrics.increment("market_websocket.client_connect", tags={"source": client_ip})
        
        try:
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connected",
                "message": "Connected to market data stream",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Process messages
            async for message in websocket.iter_text():
                message_count += 1
                
                # Track message processing time
                msg_start_time = time.time()
                
                try:
                    # Parse JSON message
                    data = json.loads(message)
                    action = data.get("action")
                    
                    if action == "subscribe":
                        # Handle subscribe
                        symbols = data.get("symbols", [])
                        if symbols:
                            # Validate symbols (limit to 50 per request for DoS protection)
                            if len(symbols) > 50:
                                logger.warning(f"Client {client_ip} tried to subscribe to {len(symbols)} symbols, limiting to 50")
                                symbols = symbols[:50]
                                metrics.increment("market_websocket.excess_symbols", tags={"source": client_ip})
                            
                            # Subscribe client to symbols
                            valid_symbols = []
                            for symbol in symbols:
                                # Basic symbol validation
                                if isinstance(symbol, str) and 1 <= len(symbol) <= 20 and symbol.isalnum():
                                    symbol = symbol.upper()
                                    self.websocket_manager.subscribe(websocket, symbol)
                                    valid_symbols.append(symbol)
                                else:
                                    logger.warning(f"Invalid symbol format: {symbol}")
                                    metrics.increment("market_websocket.invalid_symbol", tags={"source": client_ip})
                            
                            if valid_symbols:
                                # Subscribe to upstream data sources if needed
                                await self.subscribe_symbols(valid_symbols)
                                
                                # Send confirmation
                                await websocket.send_text(json.dumps({
                                    "type": "subscribed",
                                    "symbols": valid_symbols
                                }))
                                
                                metrics.increment("market_websocket.subscribe", 
                                               value=len(valid_symbols), 
                                               tags={"source": client_ip})
                            
                    elif action == "unsubscribe":
                        # Handle unsubscribe
                        symbols = data.get("symbols", [])
                        if symbols:
                            valid_symbols = []
                            for symbol in symbols:
                                if isinstance(symbol, str):
                                    symbol = symbol.upper()
                                    self.websocket_manager.unsubscribe(websocket, symbol)
                                    valid_symbols.append(symbol)
                            
                            # Unsubscribe from upstream if no clients need the data
                            if valid_symbols:
                                await self.unsubscribe_symbols(valid_symbols)
                                
                                # Send confirmation
                                await websocket.send_text(json.dumps({
                                    "type": "unsubscribed",
                                    "symbols": valid_symbols
                                }))
                                
                                metrics.increment("market_websocket.unsubscribe", 
                                               value=len(valid_symbols), 
                                               tags={"source": client_ip})
                            
                    elif action == "ping":
                        # Respond to ping
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                        metrics.increment("market_websocket.ping", tags={"source": client_ip})
                    
                    elif action == "status":
                        # Return status information about the connection
                        subscribed_symbols = []
                        for symbol, subscribers in self.websocket_manager.subscriptions.items():
                            if websocket in subscribers:
                                subscribed_symbols.append(symbol)
                        
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "connected": True,
                            "subscriptions": subscribed_symbols,
                            "uptime": time.time() - start_time,
                            "message_count": message_count,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                    else:
                        # Unknown action
                        logger.warning(f"Unknown action from client {client_ip}: {action}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Unknown action: {action}"
                        }))
                        metrics.increment("market_websocket.unknown_action", tags={"source": client_ip})
                        
                except json.JSONDecodeError:
                    # Invalid JSON
                    error_count += 1
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }))
                    metrics.increment("market_websocket.invalid_json", tags={"source": client_ip})
                    
                except Exception as e:
                    # Other error
                    error_count += 1
                    logger.error(f"Error processing client message: {str(e)}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Server error processing message"
                    }))
                    metrics.increment("market_websocket.message_error", tags={"source": client_ip})
                
                finally:
                    # Record message processing time
                    processing_time = (time.time() - msg_start_time) * 1000  # ms
                    metrics.histogram("market_websocket.message_processing_time", 
                                     processing_time, 
                                     tags={"source": client_ip, "action": action if 'action' in locals() else "unknown"})
                
        except Exception as e:
            # Connection closed or other error
            logger.info(f"Client WebSocket closed: {str(e)}")
            metrics.increment("market_websocket.connection_error", tags={"source": client_ip})
            
        finally:
            # Always disconnect and clean up
            self.websocket_manager.disconnect(websocket)
            
            # Log connection statistics
            duration = time.time() - start_time
            logger.info(
                f"WebSocket client {client_ip} disconnected after {duration:.1f}s "
                f"({message_count} messages, {error_count} errors)"
            )
            
            metrics.increment("market_websocket.client_disconnect", tags={"source": client_ip})
            metrics.histogram("market_websocket.connection_duration", duration, tags={"source": client_ip})
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the streaming service.
        
        Returns:
            Dictionary with status information
        """
        return {
            "active": self.stream_active,
            "sources": [source for source in self.sources],
            "connections": {
                source.value: self.connection_status[source] 
                for source in self.sources if source != StreamSource.WEBSOCKET_HUB
            },
            "subscriptions": {
                source.value: list(self.active_provider_subscriptions[source])
                for source in self.sources if source != StreamSource.WEBSOCKET_HUB
            },
            "message_counts": {
                source.value: self.message_counts[source]
                for source in self.sources if source != StreamSource.WEBSOCKET_HUB
            },
            "error_counts": {
                source.value: self.error_counts[source]
                for source in self.sources if source != StreamSource.WEBSOCKET_HUB
            },
            "client_connections": len(self.websocket_manager.active_connections),
            "client_subscriptions": len(self.websocket_manager.subscriptions),
            "client_subscription_counts": self.websocket_manager.subscription_counts,
            "cached_quotes": len(self.latest_quotes)
        }

# Singleton instance for the application
_streaming_service = None

def get_streaming_service() -> MarketDataStreamingService:
    """Get the singleton instance of the streaming service."""
    global _streaming_service
    
    if _streaming_service is None:
        _streaming_service = MarketDataStreamingService()
        
    return _streaming_service
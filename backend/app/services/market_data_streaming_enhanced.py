"""Enhanced market data streaming service with WebSocket support."""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

# Setup logging
logger = logging.getLogger(__name__)


class StreamingQuote:
    """Enhanced streaming stock quote data structure."""

    def __init__(
        self,
        symbol: str,
        price: float,
        bid: float = None,
        ask: float = None,
        bid_size: int = None,
        ask_size: int = None,
        volume: int = 0,
        day_change: float = 0.0,
        day_change_percent: float = 0.0,
        timestamp: float = None,
        source: str = "simulation",
    ):
        self.symbol = symbol.upper()
        self.price = price
        self.bid = bid or price * 0.999
        self.ask = ask or price * 1.001
        self.bid_size = bid_size or random.randint(100, 1000)
        self.ask_size = ask_size or random.randint(100, 1000)
        self.volume = volume
        self.day_change = day_change
        self.day_change_percent = day_change_percent
        self.timestamp = timestamp or time.time()
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "quote",
            "symbol": self.symbol,
            "price": round(self.price, 2),
            "bid": round(self.bid, 2),
            "ask": round(self.ask, 2),
            "bidSize": self.bid_size,
            "askSize": self.ask_size,
            "volume": self.volume,
            "dayChange": round(self.day_change, 2),
            "dayChangePercent": round(self.day_change_percent, 2),
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "source": self.source,
        }


class Level2Data:
    """Level II market data structure."""

    def __init__(
        self,
        symbol: str,
        bids: List[List[float]] = None,
        asks: List[List[float]] = None,
        timestamp: float = None,
    ):
        self.symbol = symbol.upper()
        self.bids = bids or []
        self.asks = asks or []
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": "level2",
            "symbol": self.symbol,
            "bids": [[round(price, 2), size] for price, size in self.bids],
            "asks": [[round(price, 2), size] for price, size in self.asks],
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


class EnhancedMarketDataStreamingService:
    """Hybrid service for streaming real-time market data with WebSocket support."""

    def __init__(self):
        """Initialize with configuration."""
        logger.info("Initializing enhanced market data streaming service")
        self.websocket_subscriptions: Dict[WebSocket, Dict[str, str]] = {}
        self.symbol_subscribers: Dict[str, Set[WebSocket]] = {}
        self.latest_quotes: Dict[str, StreamingQuote] = {}
        self.latest_level2: Dict[str, Level2Data] = {}
        self.stream_active = False
        self.simulate_task = None
        self.alpaca_stream_task = None

        # Check if using real market data
        from app.core.config import settings

        self.use_real_data = getattr(settings, "USE_REAL_MARKET_DATA", False)

        # Demo data for simulation mode
        self.demo_symbols = [
            "AAPL",
            "GOOGL",
            "MSFT",
            "TSLA",
            "AMZN",
            "NVDA",
            "META",
            "NFLX",
            "ORCL",
            "CRM",
        ]
        self.base_prices = {
            "AAPL": 150.0,
            "GOOGL": 2500.0,
            "MSFT": 300.0,
            "TSLA": 200.0,
            "AMZN": 3000.0,
            "NVDA": 400.0,
            "META": 250.0,
            "NFLX": 400.0,
            "ORCL": 100.0,
            "CRM": 180.0,
        }

        # Alpaca streaming configuration
        self.alpaca_ws_url = getattr(
            settings, "ALPACA_WS_URL", "wss://stream.data.alpaca.markets/v2/iex"
        )
        self.alpaca_api_key = getattr(settings, "ALPACA_API_KEY", "")
        self.alpaca_secret_key = getattr(settings, "ALPACA_SECRET_KEY", "")

        # Initialize appropriate data source
        if self.use_real_data:
            logger.info("Initializing with real market data from Alpaca")
            self._initialize_real_data()
        else:
            logger.info("Initializing with simulated market data")
            self._initialize_demo_data()

    def _initialize_demo_data(self):
        """Initialize demo market data."""
        for symbol, base_price in self.base_prices.items():
            # Add some random variation to base price
            current_price = base_price * (1 + random.uniform(-0.05, 0.05))
            day_change = current_price - base_price
            day_change_percent = (day_change / base_price) * 100

            quote = StreamingQuote(
                symbol=symbol,
                price=current_price,
                volume=random.randint(1000000, 10000000),
                day_change=day_change,
                day_change_percent=day_change_percent,
            )

            self.latest_quotes[symbol] = quote

            # Generate Level 2 data
            self._generate_level2_data(symbol, current_price)

    def _initialize_real_data(self):
        """Initialize real market data connections."""
        # Initialize with empty quotes - will be populated from real streams
        self.latest_quotes = {}
        self.latest_level2 = {}

        # Real symbols from major exchanges
        self.real_symbols = [
            "AAPL",
            "GOOGL",
            "MSFT",
            "TSLA",
            "AMZN",
            "NVDA",
            "META",
            "NFLX",
            "ORCL",
            "CRM",
            "AMD",
            "INTC",
            "UBER",
            "LYFT",
            "SPOT",
            "ZM",
            "PLTR",
            "SNOW",
            "NET",
            "DDOG",
        ]

    def _generate_level2_data(self, symbol: str, price: float):
        """Generate realistic Level 2 market data."""
        # Generate bid ladder (below current price)
        bids = []
        for i in range(5):
            bid_price = price - (i + 1) * 0.01
            bid_size = random.randint(100, 2000)
            bids.append([bid_price, bid_size])

        # Generate ask ladder (above current price)
        asks = []
        for i in range(5):
            ask_price = price + (i + 1) * 0.01
            ask_size = random.randint(100, 2000)
            asks.append([ask_price, ask_size])

        level2 = Level2Data(symbol=symbol, bids=bids, asks=asks)
        self.latest_level2[symbol] = level2

    async def start(self):
        """Start the streaming service."""
        if self.stream_active:
            return

        logger.info("Starting enhanced market data streaming service")
        self.stream_active = True

        if self.use_real_data:
            # Start real data streaming
            logger.info("Starting real market data streaming from Alpaca")
            self.alpaca_stream_task = asyncio.create_task(self._stream_alpaca_data())
        else:
            # Start simulation
            logger.info("Starting simulated market data streaming")
            self.simulate_task = asyncio.create_task(self._simulate_streaming())

    async def stop(self):
        """Stop the streaming service."""
        if not self.stream_active:
            return

        logger.info("Stopping enhanced market data streaming service")
        self.stream_active = False

        # Cancel background tasks
        for task in [self.simulate_task, self.alpaca_stream_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Clean up all connections
        self.websocket_subscriptions.clear()
        self.symbol_subscribers.clear()

    async def subscribe_symbol(
        self, symbol: str, websocket: WebSocket, level: str = "basic"
    ):
        """Subscribe a WebSocket to a symbol."""
        symbol = symbol.upper()

        if websocket not in self.websocket_subscriptions:
            self.websocket_subscriptions[websocket] = {}

        self.websocket_subscriptions[websocket][symbol] = level

        if symbol not in self.symbol_subscribers:
            self.symbol_subscribers[symbol] = set()

        self.symbol_subscribers[symbol].add(websocket)

        # Send latest quote immediately
        if symbol in self.latest_quotes:
            await self._send_to_websocket(
                websocket, self.latest_quotes[symbol].to_dict()
            )

        # Send Level 2 data if advanced subscription
        if level == "advanced" and symbol in self.latest_level2:
            await self._send_to_websocket(
                websocket, self.latest_level2[symbol].to_dict()
            )

        logger.info(f"WebSocket subscribed to {symbol} at {level} level")

    async def unsubscribe_symbol(self, symbol: str, websocket: WebSocket):
        """Unsubscribe a WebSocket from a symbol."""
        symbol = symbol.upper()

        if websocket in self.websocket_subscriptions:
            self.websocket_subscriptions[websocket].pop(symbol, None)

            # Remove websocket if no more subscriptions
            if not self.websocket_subscriptions[websocket]:
                del self.websocket_subscriptions[websocket]

        if symbol in self.symbol_subscribers:
            self.symbol_subscribers[symbol].discard(websocket)

            # Remove symbol if no more subscribers
            if not self.symbol_subscribers[symbol]:
                del self.symbol_subscribers[symbol]

        logger.info(f"WebSocket unsubscribed from {symbol}")

    async def get_latest_quote(self, symbol: str) -> Optional[StreamingQuote]:
        """Get the latest quote for a symbol."""
        return self.latest_quotes.get(symbol.upper())

    async def _simulate_streaming(self):
        """Simulate real-time market data updates."""
        logger.info("Starting market data simulation")

        while self.stream_active:
            try:
                # Update each demo symbol
                for symbol in self.demo_symbols:
                    if symbol in self.latest_quotes:
                        await self._update_symbol_data(symbol)

                # Wait before next update (simulate real-time frequency)
                await asyncio.sleep(random.uniform(0.5, 2.0))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market data simulation: {e}")
                await asyncio.sleep(1.0)

    async def _stream_alpaca_data(self):
        """Stream real market data from Alpaca."""
        logger.info("Starting Alpaca real-time data stream")

        if not self.alpaca_api_key or not self.alpaca_secret_key:
            logger.warning(
                "Alpaca API credentials not configured, falling back to simulation"
            )
            await self._simulate_streaming()
            return

        try:
            import json

            import websockets

            auth_message = {
                "action": "auth",
                "key": self.alpaca_api_key,
                "secret": self.alpaca_secret_key,
            }

            # Connect to Alpaca WebSocket
            async with websockets.connect(self.alpaca_ws_url) as websocket:
                # Authenticate
                await websocket.send(json.dumps(auth_message))
                auth_response = await websocket.recv()
                logger.info(f"Alpaca auth response: {auth_response}")

                # Subscribe to all real symbols
                subscribe_message = {
                    "action": "subscribe",
                    "quotes": self.real_symbols,
                    "trades": self.real_symbols,
                }
                await websocket.send(json.dumps(subscribe_message))

                # Process incoming messages
                while self.stream_active:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        await self._process_alpaca_message(json.loads(message))
                    except asyncio.TimeoutError:
                        # Send heartbeat
                        await websocket.ping()
                    except Exception as e:
                        logger.error(f"Error processing Alpaca message: {e}")
                        break

        except ImportError:
            logger.warning(
                "websockets library not available, falling back to simulation"
            )
            await self._simulate_streaming()
        except Exception as e:
            logger.error(f"Error connecting to Alpaca stream: {e}")
            logger.info("Falling back to simulation mode")
            await self._simulate_streaming()

    async def _process_alpaca_message(self, message):
        """Process incoming message from Alpaca stream."""
        if isinstance(message, list):
            for item in message:
                await self._process_single_alpaca_message(item)
        else:
            await self._process_single_alpaca_message(message)

    async def _process_single_alpaca_message(self, data):
        """Process a single message from Alpaca."""
        try:
            msg_type = data.get("T")  # Message type
            symbol = data.get("S")  # Symbol

            if msg_type == "q" and symbol:  # Quote message
                quote = StreamingQuote(
                    symbol=symbol,
                    price=(data.get("bp", 0) + data.get("ap", 0)) / 2,  # Mid price
                    bid=data.get("bp", 0),
                    ask=data.get("ap", 0),
                    bid_size=data.get("bs", 0),
                    ask_size=data.get("as", 0),
                    timestamp=data.get("t", time.time()) / 1000,  # Convert from ms
                    source="alpaca",
                )

                self.latest_quotes[symbol] = quote
                await self._broadcast_quote_update(symbol, quote)

            elif msg_type == "t" and symbol:  # Trade message
                # Update quote with trade price
                trade_price = data.get("p", 0)
                if symbol in self.latest_quotes:
                    # Update existing quote with trade info
                    existing_quote = self.latest_quotes[symbol]
                    updated_quote = StreamingQuote(
                        symbol=symbol,
                        price=trade_price,
                        bid=existing_quote.bid,
                        ask=existing_quote.ask,
                        bid_size=existing_quote.bid_size,
                        ask_size=existing_quote.ask_size,
                        volume=existing_quote.volume + data.get("s", 0),
                        timestamp=data.get("t", time.time()) / 1000,
                        source="alpaca",
                    )

                    self.latest_quotes[symbol] = updated_quote
                    await self._broadcast_quote_update(symbol, updated_quote)

        except Exception as e:
            logger.error(f"Error processing Alpaca message: {e}")

    async def _update_symbol_data(self, symbol: str):
        """Update data for a specific symbol."""
        if symbol not in self.latest_quotes:
            return

        current_quote = self.latest_quotes[symbol]
        base_price = self.base_prices[symbol]

        # Simulate price movement (random walk with mean reversion)
        price_change_percent = random.uniform(-0.002, 0.002)  # ±0.2% per update

        # Add mean reversion tendency
        distance_from_base = (current_quote.price - base_price) / base_price
        reversion_factor = -distance_from_base * 0.1  # Pull back towards base

        final_change = price_change_percent + reversion_factor
        new_price = current_quote.price * (1 + final_change)

        # Calculate day change
        day_change = new_price - base_price
        day_change_percent = (day_change / base_price) * 100

        # Create updated quote
        updated_quote = StreamingQuote(
            symbol=symbol,
            price=new_price,
            volume=current_quote.volume + random.randint(100, 1000),
            day_change=day_change,
            day_change_percent=day_change_percent,
        )

        self.latest_quotes[symbol] = updated_quote

        # Update Level 2 data occasionally
        if random.random() < 0.3:  # 30% chance
            self._generate_level2_data(symbol, new_price)

        # Broadcast to subscribed WebSockets
        await self._broadcast_quote_update(symbol, updated_quote)

    async def _broadcast_quote_update(self, symbol: str, quote: StreamingQuote):
        """Broadcast quote update to all subscribers."""
        if symbol not in self.symbol_subscribers:
            return

        quote_data = quote.to_dict()
        disconnected_sockets = set()

        for websocket in self.symbol_subscribers[symbol]:
            try:
                await self._send_to_websocket(websocket, quote_data)
            except Exception as e:
                logger.warning(f"Failed to send quote update: {e}")
                disconnected_sockets.add(websocket)

        # Clean up disconnected sockets
        for ws in disconnected_sockets:
            await self._cleanup_websocket(ws)

    async def _send_to_websocket(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a WebSocket with error handling."""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            raise

    async def _cleanup_websocket(self, websocket: WebSocket):
        """Clean up a disconnected WebSocket."""
        # Remove from all subscriptions
        if websocket in self.websocket_subscriptions:
            symbols = list(self.websocket_subscriptions[websocket].keys())
            for symbol in symbols:
                await self.unsubscribe_symbol(symbol, websocket)

    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        available_symbols = (
            self.real_symbols if self.use_real_data else self.demo_symbols
        )

        return {
            "active": self.stream_active,
            "mode": "real_data" if self.use_real_data else "simulation",
            "total_websocket_connections": len(self.websocket_subscriptions),
            "subscribed_symbols": list(self.symbol_subscribers.keys()),
            "total_subscriptions": sum(
                len(subs) for subs in self.symbol_subscribers.values()
            ),
            "available_symbols": available_symbols,
            "latest_quote_count": len(self.latest_quotes),
            "data_source": "alpaca" if self.use_real_data else "simulation",
        }


# Global service instance
_streaming_service_instance = None


def get_streaming_service() -> EnhancedMarketDataStreamingService:
    """Get the global streaming service instance."""
    global _streaming_service_instance
    if _streaming_service_instance is None:
        _streaming_service_instance = EnhancedMarketDataStreamingService()
    return _streaming_service_instance

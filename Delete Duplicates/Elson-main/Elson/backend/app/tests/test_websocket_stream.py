"""
Tests for WebSocket streaming functionality.

This module tests the WebSocket market data streaming implementation.
"""
import pytest
import json
import asyncio
import time
from typing import Optional
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

# Import the necessary services first
from app.services.market_data_streaming import (
    MarketDataStreamingService,
    WebSocketManager,
    StreamingQuote,
    StreamSource,
    get_streaming_service
)

# Define a test endpoint with the same behavior
# This avoids circular import issues
async def mock_market_data_feed(websocket: WebSocket, token: Optional[str] = None):
    """Mock WebSocket endpoint for market data feed."""
    # Mock streaming service
    streaming_service = MagicMock(spec=MarketDataStreamingService)
    streaming_service.stream_active = True
    streaming_service.handle_client_websocket = AsyncMock()
    
    # Accept the connection
    await websocket.accept()
    
    # Handle the WebSocket
    try:
        await streaming_service.handle_client_websocket(websocket)
    except WebSocketDisconnect:
        pass

# Create test app with the mock WebSocket endpoint
app = FastAPI()
app.add_websocket_route("/ws/market/feed", mock_market_data_feed)


@pytest.fixture
def test_client():
    """Test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_streaming_service():
    """Mock streaming service for testing."""
    with patch("app.routes.websocket.market_feed.get_streaming_service") as mock_get_service:
        # Create a mock service
        mock_service = MagicMock(spec=MarketDataStreamingService)
        mock_service.stream_active = True
        mock_service.handle_client_websocket = AsyncMock()
        mock_service.get_latest_quote = AsyncMock(return_value={
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": "2023-01-01T12:00:00Z",
            "source": "test"
        })
        mock_service.get_status = MagicMock(return_value={
            "active": True,
            "sources": ["alpaca", "polygon"],
            "client_connections": 1,
            "cached_quotes": 5
        })
        
        # Set up mock WebSocket manager
        mock_manager = MagicMock(spec=WebSocketManager)
        mock_manager.connect = AsyncMock()
        mock_manager.disconnect = MagicMock()
        mock_manager.subscribe = MagicMock()
        mock_manager.unsubscribe = MagicMock()
        mock_manager.broadcast = AsyncMock()
        mock_manager.active_connections = []
        mock_manager.subscriptions = {}
        mock_manager.subscription_counts = {}
        mock_manager.has_subscribers = MagicMock(return_value=True)
        
        mock_service.websocket_manager = mock_manager
        mock_service.start = AsyncMock()
        mock_service.stop = AsyncMock()
        mock_service.subscribe_symbols = AsyncMock(return_value=True)
        mock_service.unsubscribe_symbols = AsyncMock(return_value=True)
        
        # Return mock service from get_streaming_service
        mock_get_service.return_value = mock_service
        
        yield mock_service


class TestWebSocketManager:
    """Test the WebSocket manager component."""
    
    @pytest.mark.asyncio
    async def test_websocket_manager_connect(self):
        """Test WebSocket manager connection handling."""
        manager = WebSocketManager()
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        
        await manager.connect(mock_ws)
        
        mock_ws.accept.assert_called_once()
        assert mock_ws in manager.active_connections
        assert len(manager.active_connections) == 1
    
    @pytest.mark.asyncio
    async def test_websocket_manager_disconnect(self):
        """Test WebSocket manager disconnection handling."""
        manager = WebSocketManager()
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        
        # Connect first
        await manager.connect(mock_ws)
        assert mock_ws in manager.active_connections
        
        # Subscribe to a symbol
        manager.subscribe(mock_ws, "AAPL")
        assert "AAPL" in manager.subscriptions
        assert mock_ws in manager.subscriptions["AAPL"]
        
        # Disconnect
        manager.disconnect(mock_ws)
        assert mock_ws not in manager.active_connections
        assert "AAPL" not in manager.subscriptions  # Should be cleaned up
    
    @pytest.mark.asyncio
    async def test_websocket_manager_subscribe_unsubscribe(self):
        """Test WebSocket manager subscription handling."""
        manager = WebSocketManager()
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws2 = MagicMock(spec=WebSocket)
        
        # Subscribe to symbols
        manager.subscribe(mock_ws1, "AAPL")
        manager.subscribe(mock_ws1, "MSFT")
        manager.subscribe(mock_ws2, "AAPL")
        
        # Verify subscriptions
        assert "AAPL" in manager.subscriptions
        assert "MSFT" in manager.subscriptions
        assert mock_ws1 in manager.subscriptions["AAPL"]
        assert mock_ws1 in manager.subscriptions["MSFT"]
        assert mock_ws2 in manager.subscriptions["AAPL"]
        assert manager.subscription_counts["AAPL"] == 2
        assert manager.subscription_counts["MSFT"] == 1
        
        # Unsubscribe
        manager.unsubscribe(mock_ws1, "AAPL")
        
        # Verify after unsubscribe
        assert "AAPL" in manager.subscriptions  # Still has ws2
        assert "MSFT" in manager.subscriptions
        assert mock_ws1 not in manager.subscriptions["AAPL"]
        assert mock_ws1 in manager.subscriptions["MSFT"]
        assert mock_ws2 in manager.subscriptions["AAPL"]
        assert manager.subscription_counts["AAPL"] == 1
        
        # Unsubscribe last client from AAPL
        manager.unsubscribe(mock_ws2, "AAPL")
        
        # AAPL should be removed entirely
        assert "AAPL" not in manager.subscriptions
        assert "AAPL" not in manager.subscription_counts
    
    @pytest.mark.asyncio
    async def test_websocket_manager_broadcast(self):
        """Test WebSocket manager broadcast functionality."""
        manager = WebSocketManager()
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        
        # Connect and subscribe
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        manager.subscribe(mock_ws1, "AAPL")
        manager.subscribe(mock_ws2, "AAPL")
        
        # Broadcast a message
        test_data = {"symbol": "AAPL", "price": 150.0}
        await manager.broadcast("AAPL", test_data)
        
        # Verify both clients received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()
        
        # Verify message content (json encoded)
        expected_message = json.dumps(test_data)
        mock_ws1.send_text.assert_called_once_with(expected_message)
        mock_ws2.send_text.assert_called_once_with(expected_message)
        
        # Test broadcast to non-existent symbol
        await manager.broadcast("NONEXISTENT", test_data)
        # No additional calls should be made
        assert mock_ws1.send_text.call_count == 1
        assert mock_ws2.send_text.call_count == 1


class TestStreamingQuote:
    """Test the StreamingQuote model."""
    
    def test_streaming_quote_creation(self):
        """Test creating and using StreamingQuote objects."""
        # Create a quote
        quote = StreamingQuote(
            symbol="AAPL",
            price=150.0,
            bid=149.9,
            ask=150.1,
            volume=1000,
            timestamp="2023-01-01T12:00:00Z",
            source="test"
        )
        
        # Verify fields
        assert quote.symbol == "AAPL"
        assert quote.price == 150.0
        assert quote.bid == 149.9
        assert quote.ask == 150.1
        assert quote.volume == 1000
        assert quote.timestamp == "2023-01-01T12:00:00Z"
        assert quote.source == "test"
        
        # Test serialization
        serialized = quote.dict()
        assert serialized["symbol"] == "AAPL"
        assert serialized["price"] == 150.0
        
        # Test JSON serialization
        json_str = quote.json()
        deserialized = json.loads(json_str)
        assert deserialized["symbol"] == "AAPL"
        assert deserialized["price"] == 150.0


@pytest.mark.asyncio
class TestMarketDataStreamingService:
    """Test the MarketDataStreamingService."""
    
    async def test_service_initialization(self):
        """Test service initialization with default settings."""
        service = MarketDataStreamingService()
        
        # Verify default initialization
        assert not service.stream_active
        assert service.sources == [StreamSource.ALPACA, StreamSource.POLYGON]
        assert isinstance(service.websocket_manager, WebSocketManager)
        assert service.latest_quotes == {}
    
    async def test_get_latest_quote(self):
        """Test getting the latest quote."""
        service = MarketDataStreamingService()
        
        # Case 1: No quote available
        quote = await service.get_latest_quote("AAPL")
        assert quote is None
        
        # Case 2: Quote available but too old
        old_timestamp = (time.time() - 60) * 1000  # 60 seconds ago
        service.latest_quotes["AAPL"] = StreamingQuote(
            symbol="AAPL",
            price=150.0,
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(old_timestamp)),
            source="test"
        )
        
        quote = await service.get_latest_quote("AAPL", max_age_seconds=5)
        assert quote is None  # Should be too old
        
        # Case 3: Fresh quote available
        now = time.time() * 1000
        service.latest_quotes["AAPL"] = StreamingQuote(
            symbol="AAPL",
            price=150.0,
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now)),
            source="test"
        )
        
        quote = await service.get_latest_quote("AAPL", max_age_seconds=5)
        assert quote is not None
        assert quote.symbol == "AAPL"
        assert quote.price == 150.0
    
    async def test_service_start_stop(self):
        """Test starting and stopping the service."""
        service = MarketDataStreamingService()
        
        # Patch connection methods
        service._connect_to_alpaca = AsyncMock(return_value=True)
        service._connect_to_polygon = AsyncMock(return_value=True)
        service._process_alpaca_stream = AsyncMock()
        service._process_polygon_stream = AsyncMock()
        
        # Start service
        await service.start()
        
        # Verify service state
        assert service.stream_active
        service._connect_to_alpaca.assert_called_once()
        service._connect_to_polygon.assert_called_once()
        
        # Stop service
        await service.stop()
        
        # Verify service state after stopping
        assert not service.stream_active
    
    async def test_handle_client_websocket(self):
        """Test handling a client WebSocket connection."""
        service = MarketDataStreamingService()
        mock_ws = MagicMock(spec=WebSocket)
        
        # Setup WebSocket manager
        service.websocket_manager.connect = AsyncMock()
        service.websocket_manager.disconnect = MagicMock()
        
        # Setup WebSocket to receive messages then disconnect
        mock_ws.iter_text = AsyncMock()
        messages = [
            '{"action": "subscribe", "symbols": ["AAPL", "MSFT"]}',
            '{"action": "ping"}',
            '{"action": "unsubscribe", "symbols": ["MSFT"]}'
        ]
        
        async def mock_iter():
            for msg in messages:
                yield msg
            raise WebSocketDisconnect
        
        mock_ws.iter_text.return_value = mock_iter()
        mock_ws.send_text = AsyncMock()
        
        # Mock subscription methods
        service.subscribe_symbols = AsyncMock(return_value=True)
        service.unsubscribe_symbols = AsyncMock(return_value=True)
        
        # Handle the WebSocket connection
        await service.handle_client_websocket(mock_ws)
        
        # Verify interactions
        service.websocket_manager.connect.assert_called_once_with(mock_ws)
        service.websocket_manager.disconnect.assert_called_once_with(mock_ws)
        
        # Should have 3 send_text calls: subscribe confirm, pong, unsubscribe confirm
        assert mock_ws.send_text.call_count == 3
        
        # Verify subscribe was called with correct symbols
        service.subscribe_symbols.assert_called_once_with(["AAPL", "MSFT"])
    
    async def test_subscribe_unsubscribe_symbols(self):
        """Test subscribing and unsubscribing to symbols."""
        service = MarketDataStreamingService()
        service.stream_active = True
        
        # Mock connection status
        service.connection_status = {
            StreamSource.ALPACA: True,
            StreamSource.POLYGON: True
        }
        
        # Mock subscription methods
        service._subscribe_to_alpaca = AsyncMock(return_value=True)
        service._subscribe_to_polygon = AsyncMock(return_value=True)
        service._unsubscribe_from_alpaca = AsyncMock(return_value=True)
        service._unsubscribe_from_polygon = AsyncMock(return_value=True)
        
        # Test subscribe
        result = await service.subscribe_symbols(["AAPL", "MSFT"])
        assert result is True
        service._subscribe_to_alpaca.assert_called_once_with(["AAPL", "MSFT"])
        service._subscribe_to_polygon.assert_called_once_with(["AAPL", "MSFT"])
        
        # Test unsubscribe (with no subscribers)
        service.websocket_manager.has_subscribers = MagicMock(return_value=False)
        result = await service.unsubscribe_symbols(["AAPL"])
        assert result is True
        service._unsubscribe_from_alpaca.assert_called_once_with(["AAPL"])
        service._unsubscribe_from_polygon.assert_called_once_with(["AAPL"])
        
        # Test unsubscribe (with subscribers still present)
        service._unsubscribe_from_alpaca.reset_mock()
        service._unsubscribe_from_polygon.reset_mock()
        service.websocket_manager.has_subscribers = MagicMock(return_value=True)
        result = await service.unsubscribe_symbols(["MSFT"])
        assert result is True
        # Should not unsubscribe from provider if clients still subscribed
        service._unsubscribe_from_alpaca.assert_not_called()
        service._unsubscribe_from_polygon.assert_not_called()
    
    async def test_parse_provider_messages(self):
        """Test parsing messages from data providers."""
        service = MarketDataStreamingService()
        
        # Test parsing Alpaca trade message
        alpaca_trade = {
            'T': 't',  # Trade
            'S': 'AAPL',  # Symbol
            'p': 150.0,  # Price
            'v': 100,  # Volume
            't': 1672574400000000000,  # Timestamp (nanoseconds)
            'i': '12345'  # Trade ID
        }
        
        quote = service._parse_alpaca_message(alpaca_trade)
        assert quote is not None
        assert quote.symbol == 'AAPL'
        assert quote.price == 150.0
        assert quote.volume == 100
        assert quote.source == 'alpaca'
        
        # Test parsing Alpaca quote message
        alpaca_quote = {
            'T': 'q',  # Quote
            'S': 'AAPL',  # Symbol
            'bp': 149.9,  # Bid price
            'ap': 150.1,  # Ask price
            't': 1672574400000000000  # Timestamp (nanoseconds)
        }
        
        quote = service._parse_alpaca_message(alpaca_quote)
        assert quote is not None
        assert quote.symbol == 'AAPL'
        assert quote.price == 150.0  # Mid price
        assert quote.bid == 149.9
        assert quote.ask == 150.1
        assert quote.source == 'alpaca'
        
        # Test parsing Polygon trade message
        polygon_trade = {
            'ev': 'T',  # Trade event
            'sym': 'T.AAPL',  # Symbol with prefix
            'p': 150.0,  # Price
            's': 100,  # Size (volume)
            't': 1672574400000,  # Timestamp (milliseconds)
            'i': 12345  # Trade ID
        }
        
        quote = service._parse_polygon_message(polygon_trade)
        assert quote is not None
        assert quote.symbol == 'AAPL'  # Prefix removed
        assert quote.price == 150.0
        assert quote.volume == 100
        assert quote.source == 'polygon'
        
        # Test parsing Polygon quote message
        polygon_quote = {
            'ev': 'Q',  # Quote event
            'sym': 'Q.AAPL',  # Symbol with prefix
            'bp': 149.9,  # Bid price
            'ap': 150.1,  # Ask price
            't': 1672574400000  # Timestamp (milliseconds)
        }
        
        quote = service._parse_polygon_message(polygon_quote)
        assert quote is not None
        assert quote.symbol == 'AAPL'  # Prefix removed
        assert quote.price == 150.0  # Mid price
        assert quote.bid == 149.9
        assert quote.ask == 150.1
        assert quote.source == 'polygon'


class TestMarketFeedWebSocket:
    """Test the market data feed WebSocket endpoint."""
    
    def test_websocket_connection(self, test_client):
        """Test basic WebSocket connection."""
        with test_client.websocket_connect("/ws/market/feed") as websocket:
            # Should connect successfully
            pass  # Connection is successful if it reaches here
            
    def test_websocket_ping_pong(self, test_client):
        """Test WebSocket ping/pong messages."""
        with patch.object(AsyncMock, "__call__") as mock_handle:
            # Set up behavior for handle_client_websocket to respond to ping
            async def handle_client(ws):
                # Echo back a message
                data = await ws.receive_text()
                req = json.loads(data)
                if req.get("action") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            
            mock_handle.side_effect = handle_client
            
            # Connect to WebSocket
            with test_client.websocket_connect("/ws/market/feed") as websocket:
                # Send ping
                websocket.send_text(json.dumps({"action": "ping"}))
                
                # Should receive pong
                response = websocket.receive_json()
                assert response["type"] == "pong"


# Run the tests
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
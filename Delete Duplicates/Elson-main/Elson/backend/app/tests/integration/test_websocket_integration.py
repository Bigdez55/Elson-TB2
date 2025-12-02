"""
Integration tests for WebSocket market data streaming.

This module tests the integration between WebSocket endpoints
and the market data streaming service.
"""
import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, WebSocket, Depends
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.services.market_data_streaming import (
    MarketDataStreamingService,
    StreamingQuote,
    WebSocketManager
)

# Create a test FastAPI app for the WebSocket testing
test_app = FastAPI()

# Set up WebSocket manager and streaming service for testing
ws_manager = WebSocketManager()
streaming_service = MarketDataStreamingService(websocket_manager=ws_manager)

# Add test quotes
streaming_service.latest_quotes = {
    "AAPL": StreamingQuote(
        symbol="AAPL",
        price=150.0,
        bid=149.5,
        ask=150.5,
        volume=1000,
        timestamp="2023-01-01T12:00:00Z",
        source="test"
    ),
    "MSFT": StreamingQuote(
        symbol="MSFT",
        price=250.0,
        bid=249.5,
        ask=250.5,
        volume=500,
        timestamp="2023-01-01T12:00:00Z",
        source="test"
    )
}

# Set streaming service active
streaming_service.stream_active = True

# Define test API endpoints that don't need authentication
@test_app.get("/api/test/quote/{symbol}")
async def get_test_quote(symbol: str):
    """Test endpoint to get quote without authentication."""
    # Normalize symbol
    symbol = symbol.upper()
    
    # Get quote from test data
    quote = streaming_service.latest_quotes.get(symbol)
    
    if not quote:
        return {"error": "Quote not found"}
        
    return quote

@test_app.get("/api/test/status")
async def get_test_status():
    """Test endpoint to get streaming status without authentication."""
    return {
        "active": streaming_service.stream_active,
        "quotes": len(streaming_service.latest_quotes)
    }

# Test WebSocket endpoint
@test_app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Test WebSocket endpoint."""
    await websocket.accept()
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to test WebSocket"
    })
    
    try:
        while True:
            # Process messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": "2023-01-01T12:00:00Z"
                })
                
            elif action == "quote":
                symbol = message.get("symbol", "").upper()
                quote = streaming_service.latest_quotes.get(symbol)
                
                if quote:
                    await websocket.send_json(quote.model_dump())
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Symbol not found"
                    })
                    
            elif action == "subscribe":
                symbols = message.get("symbols", [])
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })
                
                # Send initial quotes
                for symbol in symbols:
                    quote = streaming_service.latest_quotes.get(symbol.upper())
                    if quote:
                        await websocket.send_json(quote.model_dump())
                        
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })
                
    except WebSocketDisconnect:
        pass

@pytest.fixture
def test_client():
    """Test client for the FastAPI test application."""
    return TestClient(test_app)


class TestApiIntegration:
    """Test integration with REST API endpoints."""
    
    def test_get_quote_api(self, test_client):
        """Test getting a streaming quote via REST API."""
        # Test getting a quote for a symbol that has data
        response = test_client.get("/api/test/quote/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.0
        
    def test_get_streaming_status(self, test_client):
        """Test getting streaming service status."""
        response = test_client.get("/api/test/status")
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is True
        assert data["quotes"] == 2  # We added 2 test quotes

class TestWebSocketIntegration:
    """Test WebSocket client connections and messaging."""
    
    def test_websocket_connection(self, test_client):
        """Test connecting to WebSocket and receiving welcome message."""
        with test_client.websocket_connect("/ws/test") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "message" in data
    
    def test_websocket_ping(self, test_client):
        """Test ping/pong functionality."""
        with test_client.websocket_connect("/ws/test") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"action": "ping"})
            
            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response
    
    def test_websocket_quote_request(self, test_client):
        """Test requesting a quote via WebSocket."""
        with test_client.websocket_connect("/ws/test") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Request quote for AAPL
            websocket.send_json({
                "action": "quote",
                "symbol": "AAPL"
            })
            
            # Receive quote
            response = websocket.receive_json()
            assert response["symbol"] == "AAPL"
            assert response["price"] == 150.0
            
            # Request quote for unknown symbol
            websocket.send_json({
                "action": "quote",
                "symbol": "UNKNOWN"
            })
            
            # Receive error
            response = websocket.receive_json()
            assert response["type"] == "error"
    
    def test_websocket_subscription(self, test_client):
        """Test subscribing to symbols via WebSocket."""
        with test_client.websocket_connect("/ws/test") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Subscribe to symbols
            symbols = ["AAPL", "MSFT"]
            websocket.send_json({
                "action": "subscribe",
                "symbols": symbols
            })
            
            # Receive subscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert response["symbols"] == symbols
            
            # Should receive quotes for subscribed symbols
            for _ in range(len(symbols)):
                quote = websocket.receive_json()
                assert quote["symbol"] in ["AAPL", "MSFT"]
                assert "price" in quote


@pytest.mark.asyncio
class TestDataProcessing:
    """Test processing market data."""
    
    async def test_alpaca_message_parsing(self):
        """Test parsing Alpaca market data messages."""
        # Create test service
        service = MarketDataStreamingService()
        
        # Test Alpaca trade message
        alpaca_trade = {
            'T': 't',
            'S': 'AAPL',
            'p': 150.0,
            'v': 100,
            't': 1672574400000000000,
            'i': '12345'
        }
        
        # Parse message
        quote = service._parse_alpaca_message(alpaca_trade)
        
        # Verify parsing
        assert quote is not None
        assert quote.symbol == "AAPL"
        assert quote.price == 150.0
        assert quote.volume == 100
        assert quote.source == "alpaca"
    
    async def test_polygon_message_parsing(self):
        """Test parsing Polygon market data messages."""
        # Create test service
        service = MarketDataStreamingService()
        
        # Test Polygon trade message
        polygon_trade = {
            'ev': 'T',
            'sym': 'T.MSFT',
            'p': 250.0,
            's': 200,
            't': 1672574400000,
            'i': 67890
        }
        
        # Parse message
        quote = service._parse_polygon_message(polygon_trade)
        
        # Verify parsing
        assert quote is not None
        assert quote.symbol == "MSFT"
        assert quote.price == 250.0
        assert quote.volume == 200
        assert quote.source == "polygon"


# Run the tests
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
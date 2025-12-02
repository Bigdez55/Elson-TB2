"""
Tests for WebSocket client behavior.

This module tests the client-side WebSocket handling functionality.
"""
import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

# Create test app with a WebSocket echo endpoint for client testing
app = FastAPI()

@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    """Echo WebSocket endpoint for testing clients."""
    await websocket.accept()
    try:
        while True:
            # Echo back any received data
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.websocket("/ws/market/test")
async def websocket_market_test(websocket: WebSocket):
    """Test WebSocket endpoint that mimics market data behavior."""
    await websocket.accept()
    
    # Track subscriptions
    subscriptions = set()
    
    try:
        # Send welcome message
        await websocket.send_json({"type": "connected"})
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "ping":
                    # Respond to ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": "2023-01-01T12:00:00Z"
                    })
                
                elif action == "subscribe":
                    # Handle subscription
                    symbols = message.get("symbols", [])
                    for symbol in symbols:
                        subscriptions.add(symbol)
                    
                    # Confirm subscription
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": symbols
                    })
                    
                    # Send initial quotes for subscribed symbols
                    for symbol in symbols:
                        await websocket.send_json({
                            "symbol": symbol,
                            "price": 100.0,
                            "bid": 99.5,
                            "ask": 100.5,
                            "volume": 1000,
                            "timestamp": "2023-01-01T12:00:00Z",
                            "source": "test"
                        })
                
                elif action == "unsubscribe":
                    # Handle unsubscription
                    symbols = message.get("symbols", [])
                    for symbol in symbols:
                        if symbol in subscriptions:
                            subscriptions.remove(symbol)
                    
                    # Confirm unsubscription
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbols": symbols
                    })
                
                else:
                    # Unknown action
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })
            
            except json.JSONDecodeError:
                # Not valid JSON
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    
    except Exception as e:
        print(f"WebSocket error: {e}")


@pytest.fixture
def test_client():
    """Test client for the FastAPI application."""
    return TestClient(app)


class TestWebSocketEcho:
    """Test basic WebSocket functionality with echo service."""
    
    def test_websocket_echo(self, test_client):
        """Test basic WebSocket echo functionality."""
        with test_client.websocket_connect("/ws/echo") as websocket:
            # Send a message
            message = "Hello, WebSocket!"
            websocket.send_text(message)
            
            # Receive the echo response
            response = websocket.receive_text()
            assert response == message
    
    def test_websocket_json_echo(self, test_client):
        """Test WebSocket echo with JSON payloads."""
        with test_client.websocket_connect("/ws/echo") as websocket:
            # Send a JSON message
            data = {"action": "test", "data": "value"}
            websocket.send_json(data)
            
            # Receive the echo response (as text)
            response = websocket.receive_text()
            assert json.loads(response) == data


class TestMarketDataWebSocket:
    """Test market data WebSocket client behavior."""
    
    def test_market_data_connection(self, test_client):
        """Test connecting to market data WebSocket."""
        with test_client.websocket_connect("/ws/market/test") as websocket:
            # Should receive connected message
            response = websocket.receive_json()
            assert response["type"] == "connected"
    
    def test_market_data_ping(self, test_client):
        """Test ping functionality."""
        with test_client.websocket_connect("/ws/market/test") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"action": "ping"})
            
            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response
    
    def test_market_data_subscribe(self, test_client):
        """Test subscription functionality."""
        with test_client.websocket_connect("/ws/market/test") as websocket:
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
            assert set(response["symbols"]) == set(symbols)
            
            # Should receive initial quotes for each symbol
            for _ in range(len(symbols)):
                quote = websocket.receive_json()
                assert quote["symbol"] in symbols
                assert "price" in quote
                assert "timestamp" in quote
    
    def test_market_data_unsubscribe(self, test_client):
        """Test unsubscription functionality."""
        with test_client.websocket_connect("/ws/market/test") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Subscribe first
            symbols = ["AAPL", "MSFT"]
            websocket.send_json({
                "action": "subscribe",
                "symbols": symbols
            })
            
            # Skip subscription confirmation and quotes
            for _ in range(len(symbols) + 1):
                websocket.receive_json()
            
            # Unsubscribe from one symbol
            websocket.send_json({
                "action": "unsubscribe",
                "symbols": ["AAPL"]
            })
            
            # Receive unsubscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "unsubscribed"
            assert response["symbols"] == ["AAPL"]
    
    def test_market_data_error_handling(self, test_client):
        """Test error handling in market data WebSocket."""
        with test_client.websocket_connect("/ws/market/test") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send invalid action
            websocket.send_json({
                "action": "invalid_action"
            })
            
            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "message" in response
            
            # Send invalid JSON
            websocket.send_text("not valid json")
            
            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "message" in response


# Run the tests
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
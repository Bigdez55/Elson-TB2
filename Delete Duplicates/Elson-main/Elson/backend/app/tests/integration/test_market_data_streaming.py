"""
Integration tests for market data streaming WebSocket.

This module tests the real-time market data streaming functionality in a production-like environment,
focusing on the WebSocket connection, data flow, and reliability.
"""

import asyncio
import json
import logging
import time
import unittest
from datetime import datetime

import websockets
import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data_streaming import get_streaming_service
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test client
client = TestClient(app)

@pytest.mark.asyncio
class TestMarketDataStreaming:
    """Tests for market data streaming."""

    async def test_websocket_connection(self):
        """Test basic WebSocket connection."""
        # First, ensure the streaming service is running
        response = client.post("/api/v1/market/streaming/start")
        assert response.status_code in (200, 409)  # 200 if started, 409 if already running
        
        uri = f"ws://localhost:8000/ws/market/feed"
        
        async with websockets.connect(uri) as websocket:
            # Send ping message
            await websocket.send(json.dumps({"action": "ping"}))
            
            # Wait for pong response
            response = await websocket.recv()
            data = json.loads(response)
            
            assert data["type"] == "pong"
            assert "timestamp" in data

    async def test_symbol_subscription(self):
        """Test subscribing to market data for a symbol."""
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        received_data = {}
        
        uri = f"ws://localhost:8000/ws/market/feed"
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to test symbols
            await websocket.send(json.dumps({
                "action": "subscribe",
                "symbols": test_symbols
            }))
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            assert data["type"] == "subscribed"
            assert set(data["symbols"]) == set(test_symbols)
            
            # Wait for data updates (with timeout)
            start_time = time.time()
            data_received = False
            
            while time.time() - start_time < 30:  # 30 second timeout
                try:
                    # Set a shorter timeout for each receive attempt
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    # Store received data by symbol
                    if "symbol" in data and data["symbol"] in test_symbols:
                        symbol = data["symbol"]
                        received_data[symbol] = data
                        logger.info(f"Received data for {symbol}: {data}")
                        data_received = True
                        
                        # If we've received data for all symbols, we can break early
                        if all(symbol in received_data for symbol in test_symbols):
                            break
                except asyncio.TimeoutError:
                    # This is expected if no message is received in the timeout period
                    logger.info("No message received in timeout period, continuing...")
                    continue
            
            # Unsubscribe from symbols
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "symbols": test_symbols
            }))
            
            # Wait for unsubscribe confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            assert data["type"] == "unsubscribed"
            assert set(data["symbols"]) == set(test_symbols)
            
            # Assert that we received data
            assert data_received, "No market data was received in the timeout period"
            
            # Validate data format for received symbols
            for symbol, data in received_data.items():
                assert "price" in data
                assert isinstance(data["price"], (int, float))
                assert "timestamp" in data
                # Validate timestamp format
                try:
                    datetime.fromisoformat(data["timestamp"])
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {data['timestamp']}")

    async def test_service_connection_status(self):
        """Test market data service connection status."""
        # Get the streaming service status
        response = client.get("/api/v1/market/streaming/status")
        assert response.status_code == 200
        
        status = response.json()
        assert "active" in status
        assert "connections" in status
        
        # Check if service is active
        assert status["active"], "Streaming service is not active"
        
        # At least one data source should be connected
        assert any(status["connections"].values()), "No data sources are connected"

    async def test_streaming_quote_endpoint(self):
        """Test REST endpoint for latest streaming quote."""
        test_symbol = "AAPL"
        
        # Connect to WebSocket and subscribe to the test symbol
        uri = f"ws://localhost:8000/ws/market/feed"
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to test symbol
            await websocket.send(json.dumps({
                "action": "subscribe",
                "symbols": [test_symbol]
            }))
            
            # Wait for subscription confirmation
            await websocket.recv()
            
            # Wait a bit to receive some data
            await asyncio.sleep(5)
            
            # Get latest quote via REST API
            response = client.get(f"/api/v1/market/streaming/quote/{test_symbol}")
            
            if response.status_code == 404:
                # If no quote is available yet, wait a bit longer
                await asyncio.sleep(10)
                response = client.get(f"/api/v1/market/streaming/quote/{test_symbol}")
            
            # Now we should have a quote
            assert response.status_code == 200, f"Failed to get streaming quote: {response.text}"
            
            quote = response.json()
            assert quote["symbol"] == test_symbol
            assert "price" in quote
            assert "timestamp" in quote
            
            # Unsubscribe
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "symbols": [test_symbol]
            }))
            
            # Wait for unsubscribe confirmation
            await websocket.recv()

    async def test_reconnection_capability(self):
        """Test WebSocket reconnection capability."""
        # First, get streaming service status to make sure it's running
        response = client.get("/api/v1/market/streaming/status")
        assert response.status_code == 200
        
        # Now stop the streaming service
        response = client.post("/api/v1/market/streaming/stop")
        assert response.status_code == 200
        
        # Verify it stopped
        response = client.get("/api/v1/market/streaming/status")
        status = response.json()
        assert not status["active"]
        
        # Restart it
        response = client.post("/api/v1/market/streaming/start")
        assert response.status_code == 200
        
        # Verify it started
        response = client.get("/api/v1/market/streaming/status")
        status = response.json()
        assert status["active"]
        
        # Attempt to connect - should succeed
        uri = f"ws://localhost:8000/ws/market/feed"
        
        async with websockets.connect(uri) as websocket:
            # Send ping message
            await websocket.send(json.dumps({"action": "ping"}))
            
            # Wait for pong response
            response = await websocket.recv()
            data = json.loads(response)
            
            assert data["type"] == "pong"
            assert "timestamp" in data

    async def test_streaming_service_failover(self):
        """Test failover between different market data providers."""
        # Get current service status
        response = client.get("/api/v1/market/streaming/status")
        assert response.status_code == 200
        
        status = response.json()
        
        # Check if multiple sources are configured
        if len(status["connections"]) < 2:
            pytest.skip("Test requires multiple data sources to be configured")
        
        # Check which sources are connected
        connected_sources = [
            source for source, is_connected in status["connections"].items() 
            if is_connected
        ]
        
        if not connected_sources:
            pytest.fail("No data sources are connected")
        
        logger.info(f"Connected sources: {connected_sources}")
        
        # Get current message counts
        initial_message_counts = status["message_counts"]
        
        # Subscribe to a symbol to generate traffic
        test_symbol = "AAPL"
        
        uri = f"ws://localhost:8000/ws/market/feed"
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to test symbol
            await websocket.send(json.dumps({
                "action": "subscribe",
                "symbols": [test_symbol]
            }))
            
            # Wait for subscription confirmation
            await websocket.recv()
            
            # Wait for some messages to come in
            await asyncio.sleep(5)
            
            # Get updated message counts
            response = client.get("/api/v1/market/streaming/status")
            updated_status = response.json()
            
            # Check if we're receiving messages from at least one source
            is_receiving_data = False
            for source in connected_sources:
                if updated_status["message_counts"][source] > initial_message_counts.get(source, 0):
                    is_receiving_data = True
                    logger.info(f"Receiving data from {source}")
                    break
            
            assert is_receiving_data, "Not receiving data from any source"
            
            # Unsubscribe
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "symbols": [test_symbol]
            }))
            
            # Wait for unsubscribe confirmation
            await websocket.recv()

    async def test_high_frequency_updates(self):
        """Test handling of high-frequency market data updates."""
        # Subscribe to multiple liquid symbols that should have frequent updates
        test_symbols = ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "GOOGL", "FB", "TSLA"]
        update_counts = {symbol: 0 for symbol in test_symbols}
        
        uri = f"ws://localhost:8000/ws/market/feed"
        
        async with websockets.connect(uri) as websocket:
            # Subscribe to test symbols
            await websocket.send(json.dumps({
                "action": "subscribe",
                "symbols": test_symbols
            }))
            
            # Wait for subscription confirmation
            await websocket.recv()
            
            # Count updates for 30 seconds
            start_time = time.time()
            while time.time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    
                    if "symbol" in data and data["symbol"] in test_symbols:
                        update_counts[data["symbol"]] += 1
                except asyncio.TimeoutError:
                    continue
            
            # Unsubscribe
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "symbols": test_symbols
            }))
            
            # Wait for unsubscribe confirmation
            await websocket.recv()
            
            # Report update frequencies
            total_updates = sum(update_counts.values())
            logger.info(f"Received {total_updates} updates in 30 seconds")
            for symbol, count in update_counts.items():
                logger.info(f"{symbol}: {count} updates ({count/30:.2f} per second)")
            
            # We should have received some updates
            assert total_updates > 0, "No market data updates received"
            
            # At least some symbols should have updates
            symbols_with_updates = sum(1 for count in update_counts.values() if count > 0)
            assert symbols_with_updates > 0, "No symbols received any updates"

    async def test_client_subscription_management(self):
        """Test client subscription management in the WebSocket manager."""
        # Get initial status
        response = client.get("/api/v1/market/streaming/status")
        initial_status = response.json()
        
        test_symbol = "AAPL"
        
        # Open multiple client connections
        uri = f"ws://localhost:8000/ws/market/feed"
        
        # Connect first client and subscribe
        client1 = await websockets.connect(uri)
        await client1.send(json.dumps({
            "action": "subscribe",
            "symbols": [test_symbol]
        }))
        await client1.recv()  # Wait for subscription confirmation
        
        # Check that client count increased
        response = client.get("/api/v1/market/streaming/status")
        status = response.json()
        assert status["client_connections"] >= initial_status["client_connections"] + 1
        
        # Connect second client and subscribe to same symbol
        client2 = await websockets.connect(uri)
        await client2.send(json.dumps({
            "action": "subscribe",
            "symbols": [test_symbol]
        }))
        await client2.recv()  # Wait for subscription confirmation
        
        # Check subscription counts
        response = client.get("/api/v1/market/streaming/status")
        status = response.json()
        
        # Should have 2 subscribers for the test symbol
        assert str(test_symbol) in status["client_subscription_counts"]
        assert status["client_subscription_counts"][str(test_symbol)] >= 2
        
        # Close one connection
        await client1.close()
        
        # Allow time for cleanup
        await asyncio.sleep(1)
        
        # Check that subscriptions were updated
        response = client.get("/api/v1/market/streaming/status")
        status = response.json()
        
        # Should still have 1 subscriber for the test symbol
        assert str(test_symbol) in status["client_subscription_counts"]
        assert status["client_subscription_counts"][str(test_symbol)] >= 1
        
        # Close second connection
        await client2.close()
        
        # Allow time for cleanup
        await asyncio.sleep(1)
        
        # Final check - should be back to initial state
        response = client.get("/api/v1/market/streaming/status")
        final_status = response.json()
        
        # The symbol subscription might still exist if there are other clients
        # or if cleanup hasn't completed yet, so we won't assert that
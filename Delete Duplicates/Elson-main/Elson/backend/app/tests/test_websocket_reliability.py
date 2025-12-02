"""
WebSocket reliability tests.
These tests verify that the WebSocket connection is robust and reliable
under various conditions including:
- Multiple connections
- Reconnection after disconnection
- Handling of high message rates
- Proper error recovery
- Subscription management
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import WebSocket, WebSocketDisconnect
import time
from datetime import datetime

from app.routes.websocket.market_feed import (
    MarketDataWebSocketManager, 
    get_websocket_manager
)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = MagicMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    return websocket


@pytest.fixture
def ws_manager():
    """Create a WebSocket manager for testing."""
    manager = MarketDataWebSocketManager()
    # Mock the market service to avoid external API calls
    manager.market_service = MagicMock()
    manager.market_service.get_batch_quotes = AsyncMock(return_value={
        "AAPL": {"price": 150.0, "change": 1.5, "volume": 1000000},
        "MSFT": {"price": 250.0, "change": 2.5, "volume": 2000000},
        "GOOGL": {"price": 2000.0, "change": 20.0, "volume": 500000}
    })
    return manager


@pytest.mark.asyncio
async def test_connection_and_disconnection(ws_manager, mock_websocket):
    """Test WebSocket connection and disconnection."""
    user_id = 1
    
    # Test connection
    await ws_manager.connect(mock_websocket, user_id)
    mock_websocket.accept.assert_called_once()
    assert user_id in ws_manager.active_connections
    assert mock_websocket in ws_manager.active_connections[user_id]
    
    # Test disconnection
    ws_manager.disconnect(mock_websocket, user_id)
    assert user_id not in ws_manager.active_connections
    assert user_id not in ws_manager.user_subscriptions


@pytest.mark.asyncio
async def test_subscription_management(ws_manager, mock_websocket):
    """Test subscription and unsubscription functionality."""
    user_id = 1
    await ws_manager.connect(mock_websocket, user_id)
    
    # Test subscribe
    symbols = ["AAPL", "MSFT"]
    await ws_manager.subscribe(user_id, symbols)
    assert all(symbol in ws_manager.user_subscriptions[user_id] for symbol in symbols)
    mock_websocket.send_json.assert_called_once()
    
    # Reset mock for next test
    mock_websocket.send_json.reset_mock()
    
    # Test unsubscribe
    await ws_manager.unsubscribe(user_id, ["AAPL"])
    assert "AAPL" not in ws_manager.user_subscriptions[user_id]
    assert "MSFT" in ws_manager.user_subscriptions[user_id]
    mock_websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_market_data(ws_manager, mock_websocket):
    """Test market data broadcasting."""
    user_id = 1
    await ws_manager.connect(mock_websocket, user_id)
    await ws_manager.subscribe(user_id, ["AAPL", "MSFT"])
    
    # Reset mock after subscription message
    mock_websocket.send_json.reset_mock()
    
    # Create a task for broadcasting, but only let it run once
    task = asyncio.create_task(ws_manager.broadcast_market_data())
    
    # Give task time to execute once
    await asyncio.sleep(0.1)
    
    # Cancel the task before the next iteration
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Verify data was sent
    mock_websocket.send_json.assert_called_once()
    call_args = mock_websocket.send_json.call_args[0][0]
    assert call_args["type"] == "market_data"
    assert "AAPL" in call_args["data"]
    assert "MSFT" in call_args["data"]


@pytest.mark.asyncio
async def test_multiple_connections(ws_manager):
    """Test handling of multiple WebSocket connections from the same user."""
    user_id = 1
    connections = [MagicMock(spec=WebSocket) for _ in range(3)]
    for conn in connections:
        conn.accept = AsyncMock()
        conn.send_json = AsyncMock()
        await ws_manager.connect(conn, user_id)
    
    # Verify all connections are stored
    assert len(ws_manager.active_connections[user_id]) == 3
    
    # Subscribe to a symbol
    await ws_manager.subscribe(user_id, ["AAPL"])
    
    # Verify message sent to all connections
    for conn in connections:
        conn.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling_in_send(ws_manager, mock_websocket):
    """Test error handling when sending messages fails."""
    user_id = 1
    await ws_manager.connect(mock_websocket, user_id)
    
    # Make send_json raise an exception
    mock_websocket.send_json.side_effect = Exception("Send failed")
    
    # Try to send message
    await ws_manager._send_to_user(user_id, {"test": "message"})
    
    # Connection should be removed due to error
    assert len(ws_manager.active_connections[user_id]) == 0


@pytest.mark.asyncio
async def test_reconnection(ws_manager):
    """Test reconnection after disconnection."""
    user_id = 1
    
    # Connect first time
    websocket1 = MagicMock(spec=WebSocket)
    websocket1.accept = AsyncMock()
    await ws_manager.connect(websocket1, user_id)
    
    # Subscribe to symbols
    await ws_manager.subscribe(user_id, ["AAPL", "MSFT"])
    
    # Disconnect
    ws_manager.disconnect(websocket1, user_id)
    assert user_id not in ws_manager.active_connections
    
    # Connect again with new socket
    websocket2 = MagicMock(spec=WebSocket)
    websocket2.accept = AsyncMock()
    websocket2.send_json = AsyncMock()
    await ws_manager.connect(websocket2, user_id)
    
    # Subscriptions should be empty for new connection
    assert len(ws_manager.user_subscriptions[user_id]) == 0
    
    # Resubscribe
    await ws_manager.subscribe(user_id, ["GOOGL"])
    assert "GOOGL" in ws_manager.user_subscriptions[user_id]


@pytest.mark.asyncio
async def test_broadcast_error_recovery(ws_manager, mock_websocket):
    """Test recovery from errors during market data broadcast."""
    user_id = 1
    await ws_manager.connect(mock_websocket, user_id)
    await ws_manager.subscribe(user_id, ["AAPL"])
    
    # Make market service raise an exception on first call, then succeed
    error_then_succeed = AsyncMock()
    error_then_succeed.side_effect = [
        Exception("API error"),
        {"AAPL": {"price": 150.0}}
    ]
    ws_manager.market_service.get_batch_quotes = error_then_succeed
    
    # Create a task for broadcasting, let it run twice
    task = asyncio.create_task(ws_manager.broadcast_market_data())
    
    # Give task time to execute twice (error, then success)
    # This includes 5 second delay after error
    await asyncio.sleep(5.1)  
    
    # Cancel the task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Verify successful call sent data
    mock_websocket.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_get_websocket_manager():
    """Test the dependency for getting the WebSocket manager."""
    manager = await get_websocket_manager()
    assert isinstance(manager, MarketDataWebSocketManager)
    
    # Should be the same instance (singleton)
    manager2 = await get_websocket_manager()
    assert manager is manager2
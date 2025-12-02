"""
Test for the WebSocketManager class.

This test focuses specifically on the WebSocketManager class functionality.
"""
import pytest
import pytest_asyncio
import json
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock

from app.services.market_data_streaming import WebSocketManager, StreamingQuote


class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self):
        self.messages = []
        self.closed = False
        self.send_text = AsyncMock()
        
    async def accept(self):
        """Accept connection."""
        pass
        
    async def send_json(self, data):
        """Send JSON data."""
        self.messages.append(data)
        
    async def close(self):
        """Close connection."""
        self.closed = True


@pytest.mark.asyncio
class TestWebSocketManager:
    """Test the WebSocketManager component."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def _cleanup_tasks(self):
        """Clean up tasks after each test."""
        yield
        # Get all running tasks and cancel them
        tasks = [task for task in asyncio.all_tasks() 
                if task is not asyncio.current_task()]
        
        for task in tasks:
            task.cancel()
            
        # Wait for all tasks to be cancelled
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def test_connect(self):
        """Test connecting a WebSocket client."""
        manager = WebSocketManager()
        mock_ws = MockWebSocket()
        
        await manager.connect(mock_ws)
        
        assert mock_ws in manager.active_connections
        assert len(manager.active_connections) == 1
    
    async def test_disconnect(self):
        """Test disconnecting a WebSocket client."""
        manager = WebSocketManager()
        mock_ws = MockWebSocket()
        
        # Connect first
        await manager.connect(mock_ws)
        assert mock_ws in manager.active_connections
        
        # Subscribe to a symbol
        manager.subscribe(mock_ws, "AAPL")
        assert "AAPL" in manager.subscriptions
        assert mock_ws in manager.subscriptions["AAPL"]
        
        # Disconnect
        manager.disconnect(mock_ws)
        
        # Check that everything is cleaned up
        assert mock_ws not in manager.active_connections
        assert "AAPL" not in manager.subscriptions
    
    async def test_subscribe_unsubscribe(self):
        """Test subscribing and unsubscribing to symbols."""
        manager = WebSocketManager()
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
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
        assert mock_ws1 not in manager.subscriptions["AAPL"]
        assert mock_ws2 in manager.subscriptions["AAPL"]
        assert manager.subscription_counts["AAPL"] == 1
        
        # Unsubscribe last client from AAPL
        manager.unsubscribe(mock_ws2, "AAPL")
        
        # AAPL should be removed entirely
        assert "AAPL" not in manager.subscriptions
    
    async def test_broadcast(self):
        """Test broadcasting messages to subscribers."""
        manager = WebSocketManager()
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
        # Connect and subscribe
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        
        manager.subscribe(mock_ws1, "AAPL")
        manager.subscribe(mock_ws2, "AAPL")
        manager.subscribe(mock_ws1, "MSFT")
        
        # Broadcast to AAPL - both WS should receive
        test_data = {"symbol": "AAPL", "price": 150.0}
        await manager.broadcast(symbol="AAPL", data=test_data)
        
        # Trigger queue processing
        await asyncio.sleep(0.2)
        
        # Both clients should have received the AAPL message
        assert mock_ws1.send_text.called
        assert mock_ws2.send_text.called
        
        # Broadcast to MSFT - only WS1 should receive
        test_data = {"symbol": "MSFT", "price": 250.0}
        await manager.broadcast_immediate(symbol="MSFT", data=test_data)
        
        # WS1 should have received 2 messages (AAPL and MSFT)
        assert mock_ws1.send_text.call_count == 2
        # WS2 should have received 1 message (AAPL only)
        assert mock_ws2.send_text.call_count == 1
    
    async def test_queue_processing(self):
        """Test the batch queue processing functionality."""
        manager = WebSocketManager()
        
        # Customize batch settings for faster testing
        manager.batch_interval = 0.1  # 100ms
        
        mock_ws = MockWebSocket()
        await manager.connect(mock_ws)
        manager.subscribe(mock_ws, "AAPL")
        
        # Add many messages to the queue - should be batched
        for i in range(10):
            await manager.broadcast("AAPL", {"price": 150.0 + i, "symbol": "AAPL"})
        
        # Wait for batch processing
        await asyncio.sleep(0.3)
        
        # Should have at least one message sent
        assert mock_ws.send_text.called
        
        # The last batch should contain the latest message with price 159.0
        latest_call = mock_ws.send_text.call_args_list[-1][0][0]
        latest_data = json.loads(latest_call)
        assert latest_data["price"] == 159.0
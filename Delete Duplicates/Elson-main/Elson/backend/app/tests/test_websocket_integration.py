"""
Integration tests for the WebSocket implementation in the Elson Wealth App.

This test suite verifies the WebSocket server functionality, connection management,
subscription handling, and data streaming capabilities.
"""

import asyncio
import pytest
import json
import time
import logging
import websockets
import jwt
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for testing
WEBSOCKET_URL = "ws://localhost:8001/ws/market/feed"
TEST_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
TEST_SECRET_KEY = "testsecretkey123456789testsecretkey123456789"  # Match the test environment key
TEST_USER_ID = "test-user-123"

# Helper functions
def generate_test_token(user_id=TEST_USER_ID, expires_in_minutes=30):
    """Generate a JWT token for testing."""
    expiration = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    payload = {
        "sub": user_id,
        "exp": expiration,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm="HS256")

class WebSocketTestClient:
    """Helper class for WebSocket testing."""
    
    def __init__(self, url, token=None):
        """Initialize the WebSocket test client."""
        self.url = url
        self.token = token
        self.connection = None
        self.received_messages = []
        self.connected = False
        self.error = None
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            url = self.url
            if self.token:
                url = f"{self.url}?token={self.token}"
            self.connection = await websockets.connect(url)
            self.connected = True
            # Get welcome message
            welcome = await self.connection.recv()
            self.received_messages.append(json.loads(welcome))
            return True
        except Exception as e:
            self.error = str(e)
            self.connected = False
            return False
    
    async def subscribe(self, symbols):
        """Subscribe to symbols."""
        message = {
            "action": "subscribe",
            "symbols": symbols
        }
        await self.connection.send(json.dumps(message))
        response = await self.connection.recv()
        self.received_messages.append(json.loads(response))
        return json.loads(response)
    
    async def unsubscribe(self, symbols):
        """Unsubscribe from symbols."""
        message = {
            "action": "unsubscribe",
            "symbols": symbols
        }
        await self.connection.send(json.dumps(message))
        response = await self.connection.recv()
        self.received_messages.append(json.loads(response))
        return json.loads(response)
    
    async def ping(self):
        """Send ping message."""
        message = {
            "action": "ping"
        }
        await self.connection.send(json.dumps(message))
        response = await self.connection.recv()
        self.received_messages.append(json.loads(response))
        return json.loads(response)
    
    async def get_status(self):
        """Get connection status."""
        message = {
            "action": "status"
        }
        await self.connection.send(json.dumps(message))
        response = await self.connection.recv()
        self.received_messages.append(json.loads(response))
        return json.loads(response)
    
    async def receive_messages(self, count=1, timeout=5):
        """Receive a specific number of messages."""
        messages = []
        for _ in range(count):
            try:
                # Set a timeout to avoid hanging
                response = await asyncio.wait_for(self.connection.recv(), timeout=timeout)
                message = json.loads(response)
                self.received_messages.append(message)
                messages.append(message)
            except asyncio.TimeoutError:
                break
        return messages
    
    async def close(self):
        """Close the connection."""
        if self.connection:
            await self.connection.close()
            self.connected = False

# Fixtures
@pytest.fixture
async def websocket_client():
    """Create a WebSocket client for testing."""
    client = WebSocketTestClient(WEBSOCKET_URL)
    yield client
    await client.close()

@pytest.fixture
async def authenticated_websocket_client():
    """Create an authenticated WebSocket client for testing."""
    token = generate_test_token()
    client = WebSocketTestClient(WEBSOCKET_URL, token)
    yield client
    await client.close()

# Tests
@pytest.mark.asyncio
async def test_websocket_connection():
    """Test basic WebSocket connection."""
    client = WebSocketTestClient(WEBSOCKET_URL)
    connected = await client.connect()
    
    assert connected, f"Failed to connect: {client.error}"
    assert len(client.received_messages) == 1, "Should receive welcome message"
    assert client.received_messages[0]["type"] == "connected"
    
    await client.close()

@pytest.mark.asyncio
async def test_authenticated_connection():
    """Test authenticated WebSocket connection."""
    token = generate_test_token()
    client = WebSocketTestClient(WEBSOCKET_URL, token)
    connected = await client.connect()
    
    assert connected, f"Failed to connect: {client.error}"
    assert len(client.received_messages) == 1, "Should receive welcome message"
    assert client.received_messages[0]["type"] == "connected"
    assert "user_id" in client.received_messages[0], "User ID should be included in welcome message"
    assert client.received_messages[0]["user_id"] == TEST_USER_ID
    
    await client.close()

@pytest.mark.asyncio
async def test_invalid_authentication():
    """Test invalid authentication is rejected."""
    token = "invalid.token.format"
    client = WebSocketTestClient(WEBSOCKET_URL, token)
    connected = await client.connect()
    
    assert not connected, "Should not connect with invalid token"
    
@pytest.mark.asyncio
async def test_expired_token():
    """Test expired token is rejected."""
    token = generate_test_token(expires_in_minutes=-10)  # Token expired 10 minutes ago
    client = WebSocketTestClient(WEBSOCKET_URL, token)
    connected = await client.connect()
    
    assert not connected, "Should not connect with expired token"

@pytest.mark.asyncio
async def test_symbol_subscription(websocket_client):
    """Test subscribing to symbols."""
    await websocket_client.connect()
    
    # Subscribe to symbols
    response = await websocket_client.subscribe(TEST_SYMBOLS)
    
    assert response["type"] == "subscribed"
    assert sorted(response["symbols"]) == sorted(TEST_SYMBOLS)

@pytest.mark.asyncio
async def test_symbol_unsubscription(websocket_client):
    """Test unsubscribing from symbols."""
    await websocket_client.connect()
    
    # Subscribe to symbols
    await websocket_client.subscribe(TEST_SYMBOLS)
    
    # Unsubscribe from a subset of symbols
    unsubscribe_symbols = TEST_SYMBOLS[:2]  # First two symbols
    response = await websocket_client.unsubscribe(unsubscribe_symbols)
    
    assert response["type"] == "unsubscribed"
    assert sorted(response["symbols"]) == sorted(unsubscribe_symbols)

@pytest.mark.asyncio
async def test_ping_pong(websocket_client):
    """Test ping/pong functionality."""
    await websocket_client.connect()
    
    # Send ping
    response = await websocket_client.ping()
    
    assert response["type"] == "pong"
    assert "timestamp" in response

@pytest.mark.asyncio
async def test_status_request(websocket_client):
    """Test status request functionality."""
    await websocket_client.connect()
    
    # Send status request
    response = await websocket_client.get_status()
    
    assert response["type"] == "status"
    assert "connected" in response
    assert response["connected"] is True
    assert "timestamp" in response

@pytest.mark.asyncio
async def test_invalid_message_format(websocket_client):
    """Test sending an invalid message format."""
    await websocket_client.connect()
    
    # Send invalid JSON
    await websocket_client.connection.send("this is not valid json")
    response = await websocket_client.connection.recv()
    response = json.loads(response)
    
    assert response["type"] == "error"
    assert "message" in response
    assert "Invalid JSON" in response["message"]

@pytest.mark.asyncio
async def test_unknown_action(websocket_client):
    """Test sending an unknown action."""
    await websocket_client.connect()
    
    # Send unknown action
    await websocket_client.connection.send(json.dumps({
        "action": "unknown_action",
        "data": "test"
    }))
    response = await websocket_client.connection.recv()
    response = json.loads(response)
    
    assert response["type"] == "error"
    assert "message" in response
    assert "Unknown action" in response["message"]

@pytest.mark.asyncio
async def test_data_reception(websocket_client):
    """Test receiving market data after subscription."""
    await websocket_client.connect()
    
    # Subscribe to symbols
    await websocket_client.subscribe(TEST_SYMBOLS[:1])  # Just subscribe to one symbol
    
    # Wait for data messages (with timeout)
    start_time = time.time()
    timeout = 10  # 10 seconds timeout
    data_received = False
    
    while time.time() - start_time < timeout and not data_received:
        try:
            message = await asyncio.wait_for(websocket_client.connection.recv(), timeout=1)
            data = json.loads(message)
            
            # Check if this is a market data message (should have symbol field)
            if "symbol" in data and data["symbol"] == TEST_SYMBOLS[0]:
                data_received = True
                break
        except asyncio.TimeoutError:
            # Just continue waiting
            pass
    
    # This test may fail if no market data is available during testing
    # It's a good idea to have a mock data provider for testing
    assert data_received, f"No market data received for {TEST_SYMBOLS[0]} within {timeout} seconds"

@pytest.mark.asyncio
async def test_multiple_connections():
    """Test multiple simultaneous connections."""
    num_clients = 5
    clients = []
    
    # Create and connect multiple clients
    for i in range(num_clients):
        client = WebSocketTestClient(WEBSOCKET_URL)
        connected = await client.connect()
        assert connected, f"Client {i} failed to connect: {client.error}"
        clients.append(client)
    
    # All clients subscribe to same symbol
    for i, client in enumerate(clients):
        response = await client.subscribe([TEST_SYMBOLS[0]])
        assert response["type"] == "subscribed", f"Client {i} failed to subscribe"
    
    # Close all clients
    for client in clients:
        await client.close()

@pytest.mark.asyncio
async def test_connection_sharing():
    """Test that multiple subscriptions on one connection work correctly."""
    client = WebSocketTestClient(WEBSOCKET_URL)
    await client.connect()
    
    # Subscribe to first subset of symbols
    first_symbols = TEST_SYMBOLS[:2]
    response1 = await client.subscribe(first_symbols)
    assert response1["type"] == "subscribed"
    assert sorted(response1["symbols"]) == sorted(first_symbols)
    
    # Subscribe to second subset of symbols
    second_symbols = TEST_SYMBOLS[2:4]
    response2 = await client.subscribe(second_symbols)
    assert response2["type"] == "subscribed"
    assert sorted(response2["symbols"]) == sorted(second_symbols)
    
    # Get status to verify subscriptions
    status = await client.get_status()
    assert "subscriptions" in status
    
    # All subscribed symbols should be in the status
    all_symbols = first_symbols + second_symbols
    for symbol in all_symbols:
        assert symbol in status["subscriptions"], f"Symbol {symbol} missing from subscriptions"
    
    await client.close()

@pytest.mark.asyncio
async def test_reconnection():
    """Test reconnection after abnormal close."""
    # This test is complex as it requires server-side interaction
    # In a real test, you might need to mock the server or use admin tools
    # Here, we'll simulate a connection drop by forcefully closing the socket
    
    client = WebSocketTestClient(WEBSOCKET_URL)
    await client.connect()
    
    # Subscribe to a symbol
    await client.subscribe([TEST_SYMBOLS[0]])
    
    # Force close the connection
    await client.connection.close()
    
    # Reconnect
    reconnected = await client.connect()
    
    assert reconnected, "Failed to reconnect after forced close"
    
    # Re-subscribe
    response = await client.subscribe([TEST_SYMBOLS[0]])
    assert response["type"] == "subscribed"
    
    await client.close()

@pytest.mark.asyncio
async def test_performance():
    """Basic performance test for WebSocket operations."""
    client = WebSocketTestClient(WEBSOCKET_URL)
    await client.connect()
    
    # Measure subscription time
    start_time = time.time()
    await client.subscribe(TEST_SYMBOLS)
    subscription_time = time.time() - start_time
    
    # Measure ping time
    start_time = time.time()
    await client.ping()
    ping_time = time.time() - start_time
    
    # Log performance metrics
    logger.info(f"Subscription time for {len(TEST_SYMBOLS)} symbols: {subscription_time:.4f} seconds")
    logger.info(f"Ping round-trip time: {ping_time:.4f} seconds")
    
    # Assert performance meets requirements
    assert subscription_time < 1.0, f"Subscription time ({subscription_time:.4f}s) exceeds 1.0s limit"
    assert ping_time < 0.2, f"Ping time ({ping_time:.4f}s) exceeds 0.2s limit"
    
    await client.close()

if __name__ == "__main__":
    # This allows running the tests manually for debugging
    import sys
    logging.basicConfig(level=logging.INFO)
    
    async def run_tests():
        client = WebSocketTestClient(WEBSOCKET_URL)
        connected = await client.connect()
        print(f"Connected: {connected}")
        if connected:
            response = await client.subscribe(TEST_SYMBOLS)
            print(f"Subscribe response: {response}")
            
            # Wait for some data
            messages = await client.receive_messages(5, timeout=10)
            print(f"Received {len(messages)} messages")
            for msg in messages:
                print(f"Message: {msg}")
                
            await client.close()
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(run_tests())
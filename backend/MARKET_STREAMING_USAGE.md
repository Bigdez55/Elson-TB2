# Personal Market Data Streaming Service

This document describes the simplified WebSocket market data streaming service designed for personal trading use.

## Overview

The personal market streaming service provides real-time market data updates through WebSocket connections. It's designed to be simple, lightweight, and focused on personal trading needs without the complexity of enterprise-grade features.

## Features

- ✅ Real-time market data streaming via WebSocket
- ✅ Simple subscription management for stock symbols
- ✅ Integration with existing market data service 
- ✅ Basic rate limiting and error handling
- ✅ In-memory caching of latest quotes
- ✅ Auto-start/stop with application lifecycle
- ✅ RESTful API for service control
- ❌ No complex connection management
- ❌ No enterprise failover/clustering
- ❌ No persistent storage of streaming data

## API Endpoints

### WebSocket Connection
```
WS /api/v1/streaming/ws
```

### REST Endpoints
```
GET  /api/v1/streaming/status           # Get service status
POST /api/v1/streaming/start            # Start streaming (requires auth)
POST /api/v1/streaming/stop             # Stop streaming (requires auth)
GET  /api/v1/streaming/quote/{symbol}   # Get latest cached quote
POST /api/v1/streaming/quote/{symbol}/refresh  # Force refresh quote
GET  /api/v1/streaming/subscriptions    # Get active subscriptions
```

## WebSocket Protocol

### Client Messages (JSON)

**Subscribe to symbols:**
```json
{
  "action": "subscribe",
  "symbols": ["AAPL", "GOOGL", "MSFT"]
}
```

**Unsubscribe from symbols:**
```json
{
  "action": "unsubscribe", 
  "symbols": ["AAPL"]
}
```

**Ping for connection check:**
```json
{
  "action": "ping"
}
```

**Get connection status:**
```json
{
  "action": "status"
}
```

### Server Messages (JSON)

**Connection confirmation:**
```json
{
  "type": "connected",
  "message": "Connected to personal market data stream",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Real-time quote update:**
```json
{
  "type": "quote",
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "bid": 150.20,
    "ask": 150.30,
    "volume": 1000000,
    "timestamp": "2024-01-15T10:30:05.123456",
    "source": "yahoo_finance"
  }
}
```

**Subscription confirmation:**
```json
{
  "type": "subscribed",
  "symbols": ["AAPL", "GOOGL"],
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Error message:**
```json
{
  "type": "error",
  "message": "Invalid JSON message",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

## Configuration

The service uses these default settings:
- Update interval: 5 seconds
- Rate limiting: 1 second minimum between updates
- Max symbols per client: 20
- Quote cache TTL: 30 seconds

## Usage Examples

### Python WebSocket Client
```python
import asyncio
import json
import websockets

async def stream_market_data():
    uri = "ws://localhost:8000/api/v1/streaming/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to symbols
        await websocket.send(json.dumps({
            "action": "subscribe",
            "symbols": ["AAPL", "GOOGL"]
        }))
        
        # Listen for updates
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "quote":
                quote = data["data"]
                print(f"{quote['symbol']}: ${quote['price']:.2f}")

asyncio.run(stream_market_data())
```

### JavaScript WebSocket Client
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/streaming/ws');

ws.onopen = () => {
    // Subscribe to symbols
    ws.send(JSON.stringify({
        action: 'subscribe',
        symbols: ['AAPL', 'GOOGL', 'MSFT']
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'quote') {
        const quote = data.data;
        console.log(`${quote.symbol}: $${quote.price.toFixed(2)}`);
    }
};
```

### REST API Usage
```bash
# Check service status
curl http://localhost:8000/api/v1/streaming/status

# Get latest cached quote
curl http://localhost:8000/api/v1/streaming/quote/AAPL

# Force refresh a quote (requires auth)
curl -X POST http://localhost:8000/api/v1/streaming/quote/AAPL/refresh \
     -H "Authorization: Bearer YOUR_TOKEN"
```

## Testing

A test client is included for demonstration:

```bash
# Run interactive demo
python test_streaming_client.py

# Run simple test
python test_streaming_client.py simple
```

## Integration with Trading

The streaming service integrates with the existing market data service and can be used by trading algorithms for real-time price updates:

```python
from app.services.market_streaming import personal_market_streaming

# Get latest streaming quote
quote = await personal_market_streaming.get_latest_quote("AAPL", max_age_seconds=10)
if quote:
    current_price = quote.price
    # Use in trading decision
```

## Monitoring

The service provides basic health monitoring:
- Active client connections
- Symbol subscriptions  
- Update intervals
- Quote cache status

Access monitoring data via:
```python
status = personal_market_streaming.get_status()
print(f"Connected clients: {status['connected_clients']}")
print(f"Subscribed symbols: {status['subscribed_symbols']}")
```

## Performance

For personal use, the service is designed to handle:
- Up to 10 concurrent WebSocket connections
- Up to 50 symbol subscriptions total
- 5-second update intervals
- In-memory caching only

This is sufficient for individual trading needs while keeping the implementation simple and resource-efficient.
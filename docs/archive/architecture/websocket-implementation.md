---
title: "Websocket Implementation"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# WebSocket Implementation for Real-Time Market Data

This document outlines the WebSocket implementation for real-time market data in the Elson Wealth App.

## Overview

The Elson platform provides real-time market data through a WebSocket connection, enabling live updates for prices, quotes, and other market information. The implementation follows best practices for performance, reliability, and resource management.

**Last Updated:** March 2025

**Status:** Production-Ready

All features have been implemented and thoroughly tested, and the system is ready for production deployment. The implementation includes robust error handling, authentication, reconnection logic, and comprehensive testing.

## Architecture

The system is composed of:

1. **Backend WebSocket Server** - FastAPI-based WebSocket endpoints
2. **Market Data Streaming Service** - Connects to external providers (Alpaca, Polygon)
3. **WebSocket Manager** - Handles client connections and subscriptions
4. **Frontend WebSocket Hook** - Manages WebSocket connection in React components

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   External    │     │   Backend     │     │   Frontend    │
│  Data Sources │◄────┤ WebSocket     │◄────┤ WebSocket     │
│ (Alpaca/etc.) │     │ Implementation│     │ Hook          │
└───────────────┘     └───────────────┘     └───────────────┘
```

## Backend Implementation

### WebSocket Manager

The `WebSocketManager` class (`market_data_streaming.py`) handles client connections, subscriptions, and broadcasting. Key features:

- Connection management with connection pooling
- Subscription tracking by symbol
- Batch processing for high-frequency updates
- Message deduplication for high-frequency symbols (only sends latest value)
- Connection health monitoring with auto-reconnect

### MarketDataStreamingService

The `MarketDataStreamingService` class connects to external data providers like Alpaca and Polygon. Features:

- Multiple data source support with failover
- Automatic reconnection with exponential backoff
- Provider-specific message parsing
- Quote caching for fast response times

### WebSocket Routes

The `/ws/market/feed` endpoint (in `market_feed.py`) provides the entry point for clients to connect and receive updates. Features:

- Authentication support
- Subscription/unsubscription protocol
- Heartbeat mechanism (ping/pong)
- Error handling

## Frontend Implementation

### useMarketWebSocket Hook

The `useMarketWebSocket` custom React hook (`useMarketWebSocket.ts`) manages the WebSocket connection on the client side. Key features:

- Connection management with auto-reconnect
- Symbol subscription/unsubscription
- Batch processing to minimize React re-renders
- Multi-level caching (memory and localStorage)
- Connection sharing between components
- Automatic cleanup on unmount

### Components Using WebSockets

Several components utilize the WebSocket hook:

- `LiveQuoteDisplay`: Shows real-time quotes for selected symbols
- `RealTimeTradeForm`: Provides up-to-date prices for placing trades
- `MarketDepth`: Displays order book data
- `TradingDashboard`: Shows market overview

## Protocol

The WebSocket communication follows a standardized protocol:

### Client to Server Messages

```json
// Subscribe to symbols
{
    "action": "subscribe",
    "symbols": ["AAPL", "MSFT", "GOOGL"]
}

// Unsubscribe from symbols
{
    "action": "unsubscribe",
    "symbols": ["AAPL", "MSFT"]
}

// Ping (keep-alive)
{
    "action": "ping"
}
```

### Server to Client Messages

```json
// Market data updates
{
    "symbol": "AAPL",
    "price": 150.25,
    "bid": 150.20,
    "ask": 150.30,
    "volume": 1000,
    "timestamp": "2023-05-01T12:34:56.789Z",
    "source": "alpaca"
}

// Subscription confirmation
{
    "type": "subscribed",
    "symbols": ["AAPL", "MSFT", "GOOGL"]
}

// Pong response
{
    "type": "pong",
    "timestamp": "2023-05-01T12:34:56.789Z"
}

// Error message
{
    "type": "error",
    "message": "Invalid subscription request"
}
```

## Optimizations

The WebSocket implementation includes several optimizations:

1. **Batch Processing** - Updates are batched and sent every 100ms to reduce network traffic and rendering overhead
2. **Message Deduplication** - For high-frequency symbols, only the latest value is sent in each batch
3. **Connection Sharing** - A global WebSocket connection is shared between components
4. **Multi-level Caching** - Data is cached in memory and localStorage for quick access
5. **Selective Updates** - Components only receive updates for their subscribed symbols
6. **Exponential Backoff** - Reconnection attempts use exponential backoff with jitter

## Error Handling

The implementation includes robust error handling:

1. **Connection Loss** - Automatic reconnection with exponential backoff
2. **Message Parsing** - Graceful handling of malformed messages
3. **Provider Failures** - Automatic failover between data providers
4. **Memory Management** - Proper cleanup of resources on unmount

## Testing

The WebSocket implementation is tested using:

1. **Unit Tests** - Testing the `useMarketWebSocket` hook and components
2. **Integration Tests** - Testing the backend WebSocket endpoints
3. **Performance Tests** - Testing high-frequency update handling

## Future Improvements

While the implementation is production-ready, future enhancements could include:

1. **WebSocket Compression** - Implementing message compression for bandwidth optimization
2. **Horizontal Scaling** - Support for horizontal scaling using Redis pub/sub across multiple WebSocket servers
3. **Custom Data Channels** - Support for different data types (news, alerts, etc.) using a topic-based subscription model
4. **Selective History** - Support for retrieving historical data on connection
5. **Enhanced Analytics** - Additional metrics for WebSocket usage patterns and performance

## Testing Tools

The repository includes the following tools for testing WebSocket functionality:

1. **websocket-test.js** - Node.js-based command-line testing tool
2. **websocket-client.html** - Browser-based WebSocket test client
3. **Integration Tests** - Comprehensive test suite for WebSocket functionality

## Deployment Notes

The WebSocket server can be deployed using:

1. Docker: The `docker-compose.yml` file includes configuration for the WebSocket server
2. Kubernetes: The `/infrastructure/kubernetes/production/websocket-deployment.yaml` file contains the K8s deployment configuration
3. Standalone: The `start_websocket.sh` script can be used for standalone deployment

The server should be deployed with at least 2 instances behind a load balancer for high availability.
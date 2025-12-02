---
title: "Openapi"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Elson Wealth Trading Platform API Documentation

## API Overview

The Elson Wealth Trading Platform provides a RESTful API for interacting with user accounts, portfolios, trading functionality, and educational content. This document outlines the available endpoints and their usage.

## Base URL

**Beta Environment:** `https://api-beta.elsonwealth.com/v1`

## Authentication

All API requests require authentication using JSON Web Tokens (JWT). To authenticate:

1. Obtain a token via the `/auth/login` endpoint
2. Include the token in all subsequent requests in the Authorization header:
   `Authorization: Bearer <your_token>`

Tokens expire after 24 hours and must be refreshed using the `/auth/refresh` endpoint.

## Error Handling

Errors follow a standard format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {} // Optional additional information
  }
}
```

Common error codes:
- `AUTHENTICATION_ERROR`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `VALIDATION_ERROR`: Invalid request parameters
- `CIRCUIT_BREAKER_ACTIVE`: Trading restricted due to volatility

## Rate Limiting

Requests are limited to 100 per minute per user. Rate limit information is included in response headers:

- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in the current window
- `X-RateLimit-Reset`: Timestamp when the rate limit resets

## Endpoints

### Authentication

#### POST /auth/login

Authenticate a user and receive a JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-03-24T10:00:00Z",
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "role": "guardian"
  }
}
```

#### POST /auth/refresh

Refresh an existing token.

**Request:**
Authorization header with current token

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-03-25T10:00:00Z"
}
```

### Portfolio Management

#### GET /portfolios

Retrieve a list of user portfolios.

**Response:**
```json
{
  "portfolios": [
    {
      "id": "portfolio123",
      "name": "My First Portfolio",
      "created_at": "2025-01-15T10:30:00Z",
      "balance": 1050.25,
      "performance": {
        "daily": 1.2,
        "weekly": -0.5,
        "monthly": 3.7,
        "yearly": 12.4
      }
    }
  ]
}
```

#### GET /portfolios/{id}

Retrieve detailed information about a specific portfolio.

**Response:**
```json
{
  "id": "portfolio123",
  "name": "My First Portfolio",
  "created_at": "2025-01-15T10:30:00Z",
  "balance": 1050.25,
  "cash_balance": 250.75,
  "performance": {
    "daily": 1.2,
    "weekly": -0.5,
    "monthly": 3.7,
    "yearly": 12.4
  },
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 2,
      "average_price": 175.50,
      "current_price": 180.25,
      "current_value": 360.50,
      "gain_loss": 9.50,
      "gain_loss_percent": 2.7
    }
  ],
  "diversification_score": 45
}
```

### Trading

#### GET /markets/status

Get current market status and volatility information.

**Response:**
```json
{
  "status": "OPEN",
  "volatility_regime": "HIGH",
  "circuit_breaker_status": "RESTRICTED",
  "indices": [
    {
      "symbol": "SPY",
      "price": 478.92,
      "change": -12.34,
      "change_percent": -2.51,
      "volatility": 28.5
    }
  ]
}
```

#### POST /trades

Submit a new trade order.

**Request:**
```json
{
  "portfolio_id": "portfolio123",
  "symbol": "AAPL",
  "order_type": "MARKET",
  "side": "BUY",
  "quantity": 1
}
```

**Response:**
```json
{
  "id": "order789",
  "status": "PENDING",
  "portfolio_id": "portfolio123",
  "symbol": "AAPL",
  "order_type": "MARKET",
  "side": "BUY",
  "quantity": 1,
  "submitted_at": "2025-03-23T15:30:45Z",
  "estimated_cost": 180.25,
  "guardian_approval_required": true
}
```

#### GET /trades/{id}

Get trade order status.

**Response:**
```json
{
  "id": "order789",
  "status": "EXECUTED",
  "portfolio_id": "portfolio123",
  "symbol": "AAPL",
  "order_type": "MARKET",
  "side": "BUY",
  "quantity": 1,
  "submitted_at": "2025-03-23T15:30:45Z",
  "executed_at": "2025-03-23T15:31:12Z",
  "execution_price": 180.25,
  "total_cost": 180.25
}
```

### Education

#### GET /education/modules

Get available educational modules.

**Response:**
```json
{
  "modules": [
    {
      "id": "mod001",
      "title": "Introduction to Stock Markets",
      "description": "Learn the basics of how stock markets work",
      "difficulty": "BEGINNER",
      "duration_minutes": 15,
      "completed": false
    }
  ]
}
```

### Recurring Investments

#### GET /recurring-investments

Get user's recurring investment plans.

**Response:**
```json
{
  "recurring_investments": [
    {
      "id": "recur123",
      "portfolio_id": "portfolio123",
      "symbol": "SPY",
      "amount": 50.00,
      "frequency": "WEEKLY",
      "day": "MONDAY",
      "active": true,
      "next_execution": "2025-03-30T09:30:00Z"
    }
  ]
}
```

#### POST /recurring-investments

Create a new recurring investment plan.

**Request:**
```json
{
  "portfolio_id": "portfolio123",
  "symbol": "SPY",
  "amount": 50.00,
  "frequency": "WEEKLY",
  "day": "MONDAY"
}
```

**Response:**
```json
{
  "id": "recur123",
  "portfolio_id": "portfolio123",
  "symbol": "SPY",
  "amount": 50.00,
  "frequency": "WEEKLY",
  "day": "MONDAY",
  "active": true,
  "created_at": "2025-03-23T16:45:12Z",
  "next_execution": "2025-03-30T09:30:00Z"
}
```

### WebSockets

WebSocket connections are available for real-time data:

**Connection URL:** `wss://ws-beta.elsonwealth.com/v1/market`

**Authentication:** Pass the JWT token as a query parameter
`wss://ws-beta.elsonwealth.com/v1/market?token=your_jwt_token`

**Available Channels:**
- `market.prices`: Real-time market price updates
- `market.volatility`: Real-time volatility metrics
- `portfolio.updates`: Real-time portfolio value updates
- `trades.status`: Real-time trade status updates

**Subscription Message:**
```json
{
  "action": "subscribe",
  "channels": ["market.prices"],
  "symbols": ["AAPL", "MSFT", "SPY"]
}
```

## Beta Limitations

During the beta phase, the following limitations apply:

1. Paper trading only - no real money transactions
2. Delayed market data (15 minutes)
3. Limited symbol universe (major US stocks and ETFs only)
4. Maximum of 5 portfolios per user
5. Maximum of 10 positions per portfolio

## Support

For API support during the beta, please contact `api-beta-support@elsonwealth.com` or create an issue in the GitHub repository.
# Market Data Integration Tests

This directory contains integration tests for the market data streaming system. These tests verify that our real-time market data streaming system works correctly with external data providers and client applications.

## Overview

The market data integration tests focus on:

1. WebSocket connection establishment and management
2. Symbol subscription and data delivery
3. Service status monitoring and control
4. Failover between different data providers
5. Performance under high-frequency data conditions

## Requirements

To run these tests, you need:

- Python 3.8+
- pytest and pytest-asyncio
- websockets library
- Access to data provider APIs (Alpaca, Polygon)
- Valid API keys configured in the environment

## Running the Tests

### Basic Test Execution

```bash
# Run all market data tests
pytest -xvs test_market_data_streaming.py

# Run a specific test case
pytest -xvs test_market_data_streaming.py::TestMarketDataStreaming::test_websocket_connection
```

### Environment Configuration

The tests support different environments through environment variables:

```bash
# Test against local development environment
export TEST_ENV=local
export TEST_BASE_URL=http://localhost:8000
export TEST_WEBSOCKET_URL=ws://localhost:8000
pytest -xvs test_market_data_streaming.py

# Test against staging environment
export TEST_ENV=staging
export TEST_BASE_URL=https://staging-api.elsonwealth.com
export TEST_WEBSOCKET_URL=wss://staging-api.elsonwealth.com
pytest -xvs test_market_data_streaming.py

# Test against production environment
export TEST_ENV=production
export TEST_BASE_URL=https://api.elsonwealth.com
export TEST_WEBSOCKET_URL=wss://api.elsonwealth.com
export TEST_API_TOKEN=your_token_here
pytest -xvs test_market_data_streaming.py
```

## Using the Test Script

For convenience, use the test script in the scripts directory:

```bash
# Run tests against local environment
../../../scripts/test_market_data_integration.sh local

# Run tests against staging
../../../scripts/test_market_data_integration.sh staging

# Run tests against production
../../../scripts/test_market_data_integration.sh production
```

## Test Cases

### test_websocket_connection

Verifies basic WebSocket connection establishment and the ping/pong mechanism.

### test_symbol_subscription

Tests subscribing to market data for specific symbols, verifies data receipt and format.

### test_service_connection_status

Verifies the service status endpoint and checks connection status to data providers.

### test_streaming_quote_endpoint

Tests the REST endpoint for retrieving the latest streaming quote for a symbol.

### test_reconnection_capability

Verifies the service can recover after being stopped and restarted.

### test_streaming_service_failover

Tests failover between different market data providers when one becomes unavailable.

### test_high_frequency_updates

Verifies the system can handle high-frequency market data updates during periods of market volatility.

### test_client_subscription_management

Tests the WebSocket manager's handling of client subscriptions and connection cleanup.

## Interpreting Test Results

### Success Criteria

A successful test run should show all tests passing. Look for:

- WebSocket connections established successfully
- Provider connections active
- Data flowing from providers to clients
- No unexplained errors or exceptions
- Reasonable latency for data delivery

### Common Failures

If tests fail, check for:

1. **Connection Issues**: Verify network connectivity to providers
2. **Authentication Failures**: Check API keys and authentication tokens
3. **Market Hours**: Some tests may fail outside of market hours when data flow is limited
4. **Provider Outages**: Check provider status pages for any reported issues
5. **Rate Limiting**: Ensure you haven't exceeded provider rate limits

## Adding New Tests

When adding new tests:

1. Follow the asyncio pattern used in existing tests
2. Use descriptive test names that clearly indicate what's being tested
3. Add proper assertions with clear error messages
4. Handle timeouts appropriately (market data may not arrive immediately)
5. Clean up resources (close WebSocket connections) in finally blocks

## Related Documentation

For more information, see:

- [Market Data Integration Testing Guide](/workspaces/Elson/Elson/docs/setup/market-data-integration-testing.md)
- [Production Market Data Test Plan](/workspaces/Elson/Elson/docs/setup/production-market-data-test-plan.md)
- [Market Data Monitoring Guide](/workspaces/Elson/Elson/docs/setup/market-data-monitoring.md)
#!/bin/bash
# Script to test market data integration in various environments
# Usage: ./test_market_data_integration.sh [local|staging|production]

set -e  # Exit on error

# Default to local environment
ENV=${1:-local}
echo "Testing market data integration in $ENV environment"

# Set base URL based on environment
case $ENV in
  local)
    BASE_URL="http://localhost:8000"
    WEBSOCKET_URL="ws://localhost:8000"
    ;;
  staging)
    BASE_URL="https://staging-api.elsonwealth.com"
    WEBSOCKET_URL="wss://staging-api.elsonwealth.com"
    ;;
  production)
    BASE_URL="https://api.elsonwealth.com"
    WEBSOCKET_URL="wss://api.elsonwealth.com"
    ;;
  *)
    echo "Unknown environment: $ENV"
    echo "Usage: ./test_market_data_integration.sh [local|staging|production]"
    exit 1
    ;;
esac

# Check if environment is ready
echo "Checking if $ENV environment is ready..."
if ! curl -s "$BASE_URL/api/v1/health" | grep -q "ok"; then
  echo "Environment $ENV is not ready. Health check failed."
  exit 1
fi

# Get API token for testing (may need to adjust this for your auth system)
get_token() {
  if [ "$ENV" == "local" ]; then
    # For local, we can use a test user
    TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username":"admin@elsonwealth.com","password":"adminpass"}' \
      | jq -r '.access_token')
  else
    # For staging/production, we need to use a service account
    TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/service/token" \
      -H "Content-Type: application/json" \
      -d '{"client_id":"'$SERVICE_CLIENT_ID'","client_secret":"'$SERVICE_CLIENT_SECRET'"}' \
      | jq -r '.access_token')
  fi
  
  if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "Failed to get authentication token"
    exit 1
  fi
  
  echo "$TOKEN"
}

# Run the WebSocket testing
run_websocket_tests() {
  echo "Running WebSocket market data integration tests..."
  
  # Set environment variables for the test
  export TEST_ENV=$ENV
  export TEST_BASE_URL=$BASE_URL
  export TEST_WEBSOCKET_URL=$WEBSOCKET_URL
  export TEST_API_TOKEN=$TOKEN
  
  # Change to the backend directory
  cd "$(dirname "$0")/../Elson/backend"
  
  # Run the pytest
  python -m pytest -xvs app/tests/integration/test_market_data_streaming.py
  
  # Capture the result
  TEST_RESULT=$?
  
  # Unset environment variables
  unset TEST_ENV TEST_BASE_URL TEST_WEBSOCKET_URL TEST_API_TOKEN
  
  return $TEST_RESULT
}

# Test market data consistency
test_data_consistency() {
  echo "Testing market data consistency..."
  
  # Sample a few common symbols
  SYMBOLS=("AAPL" "MSFT" "GOOGL" "AMZN" "FB")
  
  for SYMBOL in "${SYMBOLS[@]}"; do
    echo "Checking $SYMBOL..."
    
    # Get quote from REST API
    REST_QUOTE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "$BASE_URL/api/v1/market/quote/$SYMBOL")
    
    # Get streaming quote (may be null if not available)
    STREAM_QUOTE=$(curl -s -H "Authorization: Bearer $TOKEN" \
      "$BASE_URL/api/v1/market/streaming/quote/$SYMBOL")
    
    # If both quotes are available, compare them
    if [ -n "$REST_QUOTE" ] && [ -n "$STREAM_QUOTE" ] && \
       [ "$REST_QUOTE" != "null" ] && [ "$STREAM_QUOTE" != "null" ]; then
      
      REST_PRICE=$(echo $REST_QUOTE | jq -r '.price')
      STREAM_PRICE=$(echo $STREAM_QUOTE | jq -r '.price')
      
      # Calculate percentage difference
      if [ "$REST_PRICE" != "null" ] && [ "$STREAM_PRICE" != "null" ] && \
         [ "$REST_PRICE" != "0" ]; then
        DIFF=$(echo "scale=4; (($STREAM_PRICE - $REST_PRICE) / $REST_PRICE) * 100" | bc)
        echo "  REST price: $REST_PRICE"
        echo "  Stream price: $STREAM_PRICE"
        echo "  Difference: $DIFF%"
        
        # Check if difference is within acceptable range (5%)
        ABS_DIFF=$(echo "$DIFF" | awk '{print ($1 >= 0) ? $1 : -$1}')
        if (( $(echo "$ABS_DIFF > 5.0" | bc -l) )); then
          echo "  WARNING: Price difference exceeds 5% for $SYMBOL"
        fi
      fi
    else
      echo "  One or both quotes not available for $SYMBOL"
    fi
  done
}

# Test WebSocket connection reliability
test_websocket_reliability() {
  echo "Testing WebSocket connection reliability..."
  
  # Install wscat if needed
  if ! command -v wscat &> /dev/null; then
    echo "Installing wscat..."
    npm install -g wscat
  fi
  
  # Connect to WebSocket and measure connection time
  echo "Connecting to WebSocket at $WEBSOCKET_URL/ws/market/feed..."
  START_TIME=$(date +%s.%N)
  
  # Try to establish connection
  CONNECTION_RESULT=$(wscat -c "$WEBSOCKET_URL/ws/market/feed?token=$TOKEN" \
    --execute '{"action":"ping"}' 2>&1)
  
  END_TIME=$(date +%s.%N)
  ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)
  
  echo "Connection time: $ELAPSED seconds"
  
  # Check result
  if echo "$CONNECTION_RESULT" | grep -q "Connected"; then
    echo "WebSocket connection successful"
  else
    echo "WebSocket connection failed: $CONNECTION_RESULT"
    return 1
  fi
  
  return 0
}

# Test service status
test_service_status() {
  echo "Testing market data service status..."
  
  # Get service status
  STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/market/streaming/status")
  
  # Check if service is active
  IS_ACTIVE=$(echo $STATUS | jq -r '.active')
  if [ "$IS_ACTIVE" == "true" ]; then
    echo "Market data streaming service is active"
  else
    echo "WARNING: Market data streaming service is not active"
  fi
  
  # Check connection status
  echo "Connection status:"
  CONNECTIONS=$(echo $STATUS | jq -r '.connections')
  echo "$CONNECTIONS" | jq '.'
  
  # Check if any source is connected
  ANY_CONNECTED=$(echo $CONNECTIONS | jq 'any(values)')
  if [ "$ANY_CONNECTED" == "true" ]; then
    echo "At least one data source is connected"
  else
    echo "WARNING: No data sources are connected"
    return 1
  fi
  
  # Print subscription counts
  echo "Client subscriptions: $(echo $STATUS | jq -r '.client_subscriptions')"
  
  # Print message counts
  echo "Message counts:"
  echo $STATUS | jq -r '.message_counts'
  
  return 0
}

# Main testing flow
main() {
  echo "Starting market data integration tests in $ENV environment"
  
  # Get token
  TOKEN=$(get_token)
  echo "Authentication token obtained"
  
  # Run basic service status check
  test_service_status
  
  # Run data consistency test
  test_data_consistency
  
  # Test WebSocket reliability
  test_websocket_reliability
  
  # Run WebSocket integration tests
  run_websocket_tests
  
  echo "All tests completed!"
}

# Run the main function
main
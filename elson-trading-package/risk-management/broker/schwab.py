"""Schwab broker implementation.

This module implements the Schwab broker API integration.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings
from app.core.metrics import metrics
from app.core.secrets import get_secret
from app.models.trade import OrderSide, OrderType, Trade, TradeStatus
from app.services.broker.base import BaseBroker, BrokerError
from app.services.broker.config import schwab as schwab_config

logger = logging.getLogger(__name__)


class SchwabBroker(BaseBroker):
    """Broker implementation for Charles Schwab API."""

    def __init__(
        self,
        db=None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        secret: Optional[str] = None,
        sandbox: bool = False,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """Initialize with API credentials.

        Args:
            db: Database session
            api_key: Schwab API key (will use env var if not provided)
            api_secret: Schwab API secret (will use env var if not provided)
            secret: Alternative name for api_secret (for compatibility)
            sandbox: Whether to use sandbox environment
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.db = db
        self.api_key = api_key or get_secret("SCHWAB_API_KEY")
        # Support both api_secret and secret parameter names for compatibility
        self.api_secret = api_secret or secret or get_secret("SCHWAB_SECRET")
        self.sandbox = sandbox

        # Initialize metrics counters
        self.request_count = 0
        self.error_count = 0
        self.api_latency = 0

        # Get configuration based on environment
        self.config = (
            schwab_config.get_sandbox_config()
            if sandbox
            else schwab_config.get_production_config()
        )

        # Override config with constructor arguments if provided
        if timeout is not None:
            self.config["timeout"] = timeout
        if max_retries is not None:
            self.config["retry_config"]["max_retries"] = max_retries

        # Set base URL
        self.base_url = self.config["api_base_url"]

        # Set up session with retries
        self.session = self._create_session()

        # Set up authentication and token management
        self.token_expiry = 0
        self.access_token = None

        # First-time authentication
        self._refresh_auth_token()

        logger.info(f"Initialized Schwab broker (sandbox={sandbox})")
        metrics.increment("broker.schwab.initialized", tags={"sandbox": str(sandbox)})

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        # Configure retry strategy from config
        retry_config = self.config["retry_config"]
        retry_strategy = Retry(
            total=retry_config["max_retries"],
            backoff_factor=retry_config["backoff_factor"],
            status_forcelist=retry_config["status_forcelist"],
            allowed_methods=retry_config["allowed_methods"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _refresh_auth_token(self) -> None:
        """Refresh the OAuth access token."""
        auth_config = self.config["auth_config"]
        token_url = auth_config["token_url"]

        try:
            # In a real implementation, this would use OAuth2 flow
            # For testing purposes, we're simulating the token acquisition

            # Payload for token request
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret,
            }

            start_time = time.time()

            response = self.session.post(
                token_url, data=payload, timeout=self.config["timeout"]
            )

            request_time = time.time() - start_time
            # Use record_metric instead of timing
            metrics.record_metric("broker.schwab.auth.latency", request_time * 1000)

            if not response.ok:
                error_message = f"Failed to refresh authentication token: {response.status_code} {response.text}"
                logger.error(error_message)
                metrics.record_metric("broker.schwab.auth.error", 1)
                raise BrokerError(message=error_message, error_code="AUTH_FAILURE")

            # Parse response and extract token information
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", auth_config["token_expiry"])

            # Set token expiry with a safety margin (refresh 5 minutes before expiry)
            self.token_expiry = time.time() + expires_in - 300

            # Update session headers with new token
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )

            logger.info("Successfully refreshed authentication token")
            metrics.record_metric("broker.schwab.auth.success", 1)

        except requests.RequestException as e:
            error_message = f"Authentication token refresh request failed: {str(e)}"
            logger.error(error_message)
            metrics.record_metric("broker.schwab.auth.error", 1)
            raise BrokerError(message=error_message, error_code="AUTH_REQUEST_FAILED")
        except Exception as e:
            error_message = (
                f"Unexpected error during authentication token refresh: {str(e)}"
            )
            logger.error(error_message, exc_info=True)
            metrics.record_metric("broker.schwab.auth.error", 1)
            raise BrokerError(message=error_message, error_code="AUTH_UNEXPECTED_ERROR")

    def _check_token_expiry(self) -> None:
        """Check if the token needs to be refreshed and refresh if needed."""
        if time.time() >= self.token_expiry:
            logger.info("Authentication token expired or near expiry, refreshing")
            self._refresh_auth_token()

    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle error responses from the API with detailed logging and metrics."""
        try:
            error_data = response.json()
            error_message = error_data.get(
                "message", error_data.get("errorMessage", "Unknown error")
            )
            error_code = error_data.get(
                "error_code", error_data.get("errorCode", str(response.status_code))
            )

            # Map known error codes to descriptive messages
            error_description = schwab_config.ERROR_CODES.get(error_code, error_message)

            # Log detailed error information
            logger.error(f"Schwab API Error: {error_code} - {error_message}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response body: {json.dumps(error_data, indent=2)}")

            # Update metrics based on error type
            metrics.increment("broker.schwab.error", tags={"error_code": error_code})

            # Check for rate limit errors
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(
                    f"Rate limit exceeded, retry after {retry_after} seconds"
                )
                metrics.increment("broker.schwab.rate_limit_exceeded")

                # Add specific rate limit information to the error
                raise BrokerError(
                    message=f"Rate limit exceeded: {error_description}",
                    error_code="RATE_LIMIT_EXCEEDED",
                    broker_response=error_data,
                    metadata={"retry_after": retry_after},
                )

            # Raise appropriate error
            raise BrokerError(
                message=f"Schwab API Error: {error_description}",
                error_code=error_code,
                broker_response=error_data,
            )

        except json.JSONDecodeError:
            # Handle non-JSON error responses
            error_message = response.text or f"HTTP Error: {response.status_code}"
            error_code = str(response.status_code)

            logger.error(
                f"Schwab API Error (non-JSON): {response.status_code} - {error_message[:200]}"
            )
            metrics.increment("broker.schwab.error", tags={"error_code": error_code})

            raise BrokerError(
                message=f"Schwab API Error: {error_message}", error_code=error_code
            )

    def _api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Schwab API with error handling, retries, and metrics.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            headers: Additional headers
            timeout: Request timeout override

        Returns:
            API response as dictionary

        Raises:
            BrokerError: If the API request fails
        """
        # Check token expiry and refresh if needed
        self._check_token_expiry()

        url = f"{self.base_url}{endpoint}"
        request_timeout = timeout or self.config["timeout"]
        request_headers = headers or {}

        # Add request ID for tracking
        request_id = f"req_{int(time.time() * 1000)}_{self.request_count}"
        request_headers["X-Request-ID"] = request_id

        # Increment request counter for metrics
        self.request_count += 1

        # Start timing request
        start_time = time.time()

        try:
            # Log request details
            if self.sandbox or settings.LOG_LEVEL == "DEBUG":
                logger.debug(f"API Request [{request_id}]: {method} {url}")
                if params:
                    logger.debug(f"Request params: {params}")
                if data:
                    logger.debug(f"Request data: {json.dumps(data, indent=2)}")

            # Make the request
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=request_timeout,
            )

            # Calculate request duration for metrics
            request_duration = time.time() - start_time
            self.api_latency += request_duration

            # Record metrics
            metrics.timing(
                "broker.schwab.request_latency",
                request_duration * 1000,
                tags={"method": method, "endpoint": endpoint},
            )

            # Log response status
            if self.sandbox or settings.LOG_LEVEL == "DEBUG":
                logger.debug(f"Response status [{request_id}]: {response.status_code}")

            # Handle non-successful responses
            if not response.ok:
                self.error_count += 1
                self._handle_error_response(response)

            # Parse and return successful response
            response_data = response.json()

            # Log detailed response for debugging
            if self.sandbox and settings.LOG_LEVEL == "DEBUG":
                logger.debug(
                    f"Response data [{request_id}]: {json.dumps(response_data, indent=2)}"
                )

            metrics.increment(
                "broker.schwab.request.success",
                tags={"method": method, "endpoint": endpoint},
            )
            return response_data

        except requests.exceptions.Timeout:
            self.error_count += 1
            error_message = (
                f"API request timed out after {request_timeout}s: {method} {url}"
            )
            logger.error(error_message)
            metrics.increment(
                "broker.schwab.request.timeout",
                tags={"method": method, "endpoint": endpoint},
            )
            raise BrokerError(message=error_message, error_code="REQUEST_TIMEOUT")

        except requests.exceptions.ConnectionError as e:
            self.error_count += 1
            error_message = f"API connection error: {str(e)}"
            logger.error(error_message)
            metrics.increment(
                "broker.schwab.request.connection_error",
                tags={"method": method, "endpoint": endpoint},
            )
            raise BrokerError(message=error_message, error_code="CONNECTION_ERROR")

        except requests.RequestException as e:
            self.error_count += 1
            error_message = f"API request failed: {str(e)}"
            logger.error(error_message)
            metrics.increment(
                "broker.schwab.request.error",
                tags={"method": method, "endpoint": endpoint},
            )
            raise BrokerError(message=error_message, error_code="REQUEST_ERROR")

        except json.JSONDecodeError as e:
            self.error_count += 1
            error_message = f"Failed to parse API response: {str(e)}"
            logger.error(error_message)
            logger.debug(f"Raw response: {response.text[:500]}")
            metrics.increment(
                "broker.schwab.request.json_error",
                tags={"method": method, "endpoint": endpoint},
            )
            raise BrokerError(message=error_message, error_code="RESPONSE_PARSE_ERROR")

        except Exception as e:
            self.error_count += 1
            error_message = f"Unexpected error during API request: {str(e)}"
            logger.error(error_message, exc_info=True)
            metrics.increment(
                "broker.schwab.request.unexpected_error",
                tags={"method": method, "endpoint": endpoint},
            )
            raise BrokerError(message=error_message, error_code="UNEXPECTED_ERROR")

    # Implementation of BaseBroker interface methods

    def execute_trade(self, trade: Trade) -> Dict[str, Any]:
        """Execute a trade and return execution details."""
        logger.info(
            f"Executing trade: {trade.symbol} {trade.side} {trade.quantity or trade.investment_amount}"
        )

        # Convert trade model to Schwab API format
        order_data = self._prepare_order_data(trade)

        try:
            # Submit order to Schwab API
            response = self._api_request(
                method="POST", endpoint=schwab_config.ORDER_ENDPOINT, data=order_data
            )

            # Parse response and extract order ID
            order_id = response.get("order_id")
            if not order_id:
                raise BrokerError(
                    message="No order ID returned from Schwab API",
                    broker_response=response,
                )

            # Map broker status to internal status
            status = self._map_broker_status(response.get("status", "PENDING"))

            # Log successful order placement
            logger.info(
                f"Successfully placed order {order_id} for {trade.symbol}, status: {status}"
            )
            metrics.increment(
                "broker.schwab.trade.executed",
                tags={"symbol": trade.symbol, "side": trade.side.value},
            )

            # Return execution details
            return {
                "broker_order_id": order_id,
                "status": status,
                "submitted_at": datetime.now().isoformat(),
                "broker_response": response,
            }

        except BrokerError as e:
            # Log the error with details
            logger.error(
                f"Failed to execute trade for {trade.symbol}: {e.message} (code: {e.error_code})"
            )
            metrics.increment(
                "broker.schwab.trade.failed",
                tags={"symbol": trade.symbol, "side": trade.side.value},
            )

            # Re-raise the error
            raise

    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get account information."""
        logger.info(f"Retrieving account information for account {account_id}")

        try:
            response = self._api_request(
                method="GET", endpoint=f"{schwab_config.ACCOUNT_ENDPOINT}/{account_id}"
            )

            # Transform the response to a standardized format
            account_info = {
                "account_id": account_id,
                "balance": response.get("balance"),
                "buying_power": response.get("buying_power"),
                "cash": response.get("cash"),
                "currency": response.get("currency", "USD"),
                "status": response.get("status"),
                "broker_response": response,
            }

            logger.info(f"Successfully retrieved account information for {account_id}")
            metrics.increment("broker.schwab.account_info.success")

            return account_info

        except BrokerError as e:
            logger.error(
                f"Failed to retrieve account information for {account_id}: {e.message}"
            )
            metrics.increment("broker.schwab.account_info.failed")
            raise

    def get_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get current positions for an account."""
        logger.info(f"Retrieving positions for account {account_id}")

        try:
            response = self._api_request(
                method="GET",
                endpoint=f"{schwab_config.ACCOUNT_ENDPOINT}/{account_id}{schwab_config.POSITIONS_ENDPOINT}",
            )

            # Transform positions to standardized format
            positions = []
            for position in response.get("positions", []):
                positions.append(
                    {
                        "symbol": position.get("symbol"),
                        "quantity": position.get("quantity"),
                        "market_value": position.get("market_value"),
                        "cost_basis": position.get("cost_basis"),
                        "unrealized_pl": position.get("unrealized_pl"),
                        "unrealized_pl_percent": position.get("unrealized_pl_percent"),
                        "asset_type": position.get("asset_type"),
                    }
                )

            logger.info(
                f"Retrieved {len(positions)} positions for account {account_id}"
            )
            metrics.increment("broker.schwab.positions.success")
            metrics.gauge("broker.schwab.positions.count", len(positions))

            return positions

        except BrokerError as e:
            logger.error(
                f"Failed to retrieve positions for account {account_id}: {e.message}"
            )
            metrics.increment("broker.schwab.positions.failed")
            raise

    def get_trade_status(self, broker_order_id: str) -> Dict[str, Any]:
        """Get the current status of a trade."""
        logger.info(f"Checking status for order {broker_order_id}")

        try:
            response = self._api_request(
                method="GET",
                endpoint=f"{schwab_config.ORDER_ENDPOINT}/{broker_order_id}",
            )

            # Map status to internal format
            status = self._map_broker_status(response.get("status", "UNKNOWN"))

            # Format response
            result = {
                "broker_order_id": broker_order_id,
                "status": status,
                "filled_quantity": response.get("filled_quantity", 0),
                "filled_price": response.get("filled_price"),
                "filled_at": response.get("filled_at"),
                "message": response.get("message"),
                "broker_response": response,
            }

            logger.info(f"Order {broker_order_id} status: {status}")
            metrics.increment("broker.schwab.order_status.success")

            return result

        except BrokerError as e:
            logger.error(
                f"Failed to retrieve status for order {broker_order_id}: {e.message}"
            )
            metrics.increment("broker.schwab.order_status.failed")
            raise

    def cancel_trade(self, broker_order_id: str) -> bool:
        """Cancel a pending trade."""
        logger.info(f"Cancelling order {broker_order_id}")

        try:
            response = self._api_request(
                method="DELETE",
                endpoint=f"{schwab_config.ORDER_ENDPOINT}/{broker_order_id}",
            )

            is_canceled = response.get("canceled", False)

            if is_canceled:
                logger.info(f"Successfully canceled order {broker_order_id}")
                metrics.increment("broker.schwab.cancel_order.success")
            else:
                logger.warning(
                    f"Failed to cancel order {broker_order_id}, response: {response}"
                )
                metrics.increment("broker.schwab.cancel_order.failed")

            return is_canceled

        except BrokerError as e:
            # Check if error is because order is already executed
            if "ALREADY_FILLED" in e.error_code or "ALREADY_EXECUTED" in e.error_code:
                logger.info(
                    f"Cannot cancel order {broker_order_id} as it is already executed"
                )
                metrics.increment("broker.schwab.cancel_order.already_executed")
                return False

            # Order might already be canceled
            if "ALREADY_CANCELED" in e.error_code:
                logger.info(f"Order {broker_order_id} is already canceled")
                metrics.increment("broker.schwab.cancel_order.already_canceled")
                return True

            # Log other errors
            logger.warning(f"Failed to cancel order {broker_order_id}: {e.message}")
            metrics.increment("broker.schwab.cancel_order.error")
            return False

    def get_order_history(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get order history for an account."""
        logger.info(f"Retrieving order history for account {account_id}")

        # Set default date range if not provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Format dates for API
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        try:
            response = self._api_request(
                method="GET",
                endpoint=f"{schwab_config.ACCOUNT_ENDPOINT}/{account_id}/orders",
                params=params,
            )

            # Transform orders to standardized format
            orders = []
            for order in response.get("orders", []):
                # Map broker status to internal status
                status = self._map_broker_status(order.get("status"))

                orders.append(
                    {
                        "broker_order_id": order.get("id"),
                        "symbol": order.get("symbol"),
                        "quantity": order.get("quantity"),
                        "side": order.get("side"),
                        "type": order.get("type"),
                        "status": status,
                        "submitted_at": order.get("created_at"),
                        "filled_at": order.get("filled_at"),
                        "filled_price": order.get("filled_price"),
                        "filled_quantity": order.get("filled_quantity"),
                    }
                )

            logger.info(f"Retrieved {len(orders)} orders for account {account_id}")
            metrics.increment("broker.schwab.order_history.success")
            metrics.gauge("broker.schwab.order_history.count", len(orders))

            return orders

        except BrokerError as e:
            logger.error(
                f"Failed to retrieve order history for account {account_id}: {e.message}"
            )
            metrics.increment("broker.schwab.order_history.failed")
            raise

    def get_trade_execution(self, broker_order_id: str) -> Dict[str, Any]:
        """Get detailed execution information for a completed trade."""
        logger.info(f"Retrieving execution details for order {broker_order_id}")

        try:
            response = self._api_request(
                method="GET",
                endpoint=f"{schwab_config.ORDER_ENDPOINT}/{broker_order_id}{schwab_config.EXECUTIONS_ENDPOINT}",
            )

            executions = response.get("executions", [])

            # If no executions, return pending status
            if not executions:
                logger.info(f"No executions found for order {broker_order_id}")
                return {
                    "broker_order_id": broker_order_id,
                    "status": "PENDING",
                    "filled_quantity": 0,
                    "average_price": None,
                    "executions": [],
                }

            # Calculate average price for all executions
            total_qty = sum(execution.get("quantity", 0) for execution in executions)
            weighted_price = sum(
                execution.get("price", 0) * execution.get("quantity", 0)
                for execution in executions
            )

            average_price = weighted_price / total_qty if total_qty > 0 else None

            logger.info(
                f"Retrieved {len(executions)} executions for order {broker_order_id}"
            )
            metrics.increment("broker.schwab.trade_execution.success")

            return {
                "broker_order_id": broker_order_id,
                "status": "FILLED" if total_qty > 0 else "PENDING",
                "filled_quantity": total_qty,
                "average_price": average_price,
                "executions": executions,
            }

        except BrokerError as e:
            logger.error(
                f"Failed to retrieve execution details for order {broker_order_id}: {e.message}"
            )
            metrics.increment("broker.schwab.trade_execution.failed")
            raise

    # Optional methods implementation

    def get_market_hours(self, market: str = "EQUITY") -> Dict[str, Any]:
        """Get market hours information."""
        logger.info(f"Retrieving market hours for {market}")

        try:
            response = self._api_request(
                method="GET",
                endpoint=schwab_config.MARKET_HOURS_ENDPOINT,
                params={"markets": market},
            )

            market_data = response.get(market, {})

            result = {
                "market": market,
                "is_open": market_data.get("is_open", False),
                "opens_at": market_data.get("opens_at"),
                "closes_at": market_data.get("closes_at"),
                "extended_opens_at": market_data.get("extended", {}).get("opens_at"),
                "extended_closes_at": market_data.get("extended", {}).get("closes_at"),
                "next_open_date": market_data.get("next_open_date"),
                "next_close_date": market_data.get("next_close_date"),
            }

            logger.info(
                f"Market {market} is {'open' if result['is_open'] else 'closed'}"
            )
            metrics.increment("broker.schwab.market_hours.success")

            return result

        except BrokerError as e:
            logger.error(f"Failed to retrieve market hours for {market}: {e.message}")
            metrics.increment("broker.schwab.market_hours.failed")
            raise

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get a quote for a symbol."""
        logger.info(f"Retrieving quote for {symbol}")

        try:
            response = self._api_request(
                method="GET",
                endpoint=schwab_config.QUOTES_ENDPOINT,
                params={"symbols": symbol},
            )

            quotes = response.get("quotes", [])

            # If no quotes returned
            if not quotes:
                logger.warning(f"No quote data returned for symbol {symbol}")
                metrics.increment("broker.schwab.quote.empty")
                raise BrokerError(
                    message=f"No quote data available for symbol: {symbol}",
                    error_code="QUOTE_NOT_FOUND",
                )

            # Extract first quote (should be the only one)
            quote = quotes[0]

            result = {
                "symbol": symbol,
                "bid_price": quote.get("bid_price"),
                "ask_price": quote.get("ask_price"),
                "last_price": quote.get("last_price"),
                "change_percent": quote.get("change_percent"),
                "change": quote.get("change"),
                "volume": quote.get("volume"),
                "timestamp": quote.get("timestamp"),
            }

            logger.info(
                f"Retrieved quote for {symbol}: last price {result['last_price']}"
            )
            metrics.increment("broker.schwab.quote.success")

            return result

        except BrokerError as e:
            logger.error(f"Failed to retrieve quote for {symbol}: {e.message}")
            metrics.increment("broker.schwab.quote.failed")
            raise

    def place_bracket_order(
        self, trade: Trade, take_profit_price: float, stop_loss_price: float
    ) -> Dict[str, Any]:
        """Place a bracket order (entry + take profit + stop loss)."""
        logger.info(
            f"Placing bracket order for {trade.symbol}: "
            f"entry at market, TP at {take_profit_price}, SL at {stop_loss_price}"
        )

        # Check if broker supports bracket orders
        if not schwab_config.SUPPORTS_BRACKET_ORDERS:
            raise BrokerError(
                message="Bracket orders not supported by Schwab broker",
                error_code="FEATURE_NOT_SUPPORTED",
            )

        # Prepare order data with bracket parameters
        order_data = self._prepare_order_data(trade)

        # Add bracket parameters
        order_data["bracket"] = {
            "take_profit": {"limit_price": str(take_profit_price)},
            "stop_loss": {"stop_price": str(stop_loss_price)},
        }

        try:
            # Submit order to Schwab API
            response = self._api_request(
                method="POST", endpoint=schwab_config.ORDER_ENDPOINT, data=order_data
            )

            # Extract order IDs (main order and bracket orders)
            order_id = response.get("order_id")
            bracket_order_ids = response.get("bracket_order_ids", {})

            if not order_id:
                raise BrokerError(
                    message="No order ID returned from Schwab API for bracket order",
                    broker_response=response,
                )

            # Map status to internal format
            status = self._map_broker_status(response.get("status", "PENDING"))

            logger.info(
                f"Successfully placed bracket order {order_id} for {trade.symbol}"
            )
            metrics.increment("broker.schwab.bracket_order.success")

            return {
                "broker_order_id": order_id,
                "status": status,
                "submitted_at": datetime.now().isoformat(),
                "take_profit_order_id": bracket_order_ids.get("take_profit"),
                "stop_loss_order_id": bracket_order_ids.get("stop_loss"),
                "broker_response": response,
            }

        except BrokerError as e:
            logger.error(
                f"Failed to place bracket order for {trade.symbol}: {e.message}"
            )
            metrics.increment("broker.schwab.bracket_order.failed")
            raise

    def place_trailing_stop(
        self, trade: Trade, trail_amount: float, trail_type: str = "percent"
    ) -> Dict[str, Any]:
        """Place a trailing stop order."""
        logger.info(
            f"Placing trailing stop order for {trade.symbol}: "
            f"trail amount {trail_amount}, type {trail_type}"
        )

        # Check if broker supports trailing stops
        if not schwab_config.SUPPORTS_TRAILING_STOPS:
            raise BrokerError(
                message="Trailing stop orders not supported by Schwab broker",
                error_code="FEATURE_NOT_SUPPORTED",
            )

        # Prepare basic order data
        order_data = self._prepare_order_data(trade)

        # Override order type
        order_data["type"] = "trailing_stop"

        # Add trailing stop parameters
        if trail_type == "percent":
            order_data["trail_percent"] = str(trail_amount)
        else:
            order_data["trail_price"] = str(trail_amount)

        try:
            # Submit order to Schwab API
            response = self._api_request(
                method="POST", endpoint=schwab_config.ORDER_ENDPOINT, data=order_data
            )

            # Extract order ID
            order_id = response.get("order_id")

            if not order_id:
                raise BrokerError(
                    message="No order ID returned from Schwab API for trailing stop order",
                    broker_response=response,
                )

            # Map status to internal format
            status = self._map_broker_status(response.get("status", "PENDING"))

            logger.info(
                f"Successfully placed trailing stop order {order_id} for {trade.symbol}"
            )
            metrics.increment("broker.schwab.trailing_stop.success")

            return {
                "broker_order_id": order_id,
                "status": status,
                "submitted_at": datetime.now().isoformat(),
                "broker_response": response,
            }

        except BrokerError as e:
            logger.error(
                f"Failed to place trailing stop order for {trade.symbol}: {e.message}"
            )
            metrics.increment("broker.schwab.trailing_stop.failed")
            raise

    # Helper methods

    def _prepare_order_data(self, trade: Trade) -> Dict[str, Any]:
        """Translate trade model to Schwab API format."""
        # Get mappings from config
        order_type_map = schwab_config.ORDER_TYPE_MAP
        order_side_map = schwab_config.ORDER_SIDE_MAP

        # Map order type to Schwab API format
        order_type = order_type_map.get(trade.order_type.value.lower(), "market")

        # Map order side to Schwab API format
        order_side = order_side_map.get(trade.side.value.lower(), "buy")

        # Prepare order data
        order_data = {
            "symbol": trade.symbol,
            "side": order_side,
            "type": order_type,
            "time_in_force": schwab_config.DEFAULT_TIME_IN_FORCE,
            "account_id": trade.account_id,
        }

        # Handle fractional shares (investment amount) vs. quantity
        if trade.is_fractional and trade.investment_amount:
            # Check if broker supports fractional shares
            if not schwab_config.SUPPORTS_FRACTIONAL:
                raise BrokerError(
                    message="Fractional shares not supported by Schwab broker",
                    error_code="FRACTIONAL_NOT_SUPPORTED",
                )
            order_data["dollar_amount"] = str(trade.investment_amount)
        else:
            order_data["quantity"] = str(trade.quantity)

        # Add limit price for limit orders
        if (
            trade.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]
            and trade.limit_price
        ):
            order_data["limit_price"] = str(trade.limit_price)

        # Add stop price for stop orders
        if (
            trade.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]
            and trade.stop_price
        ):
            order_data["stop_price"] = str(trade.stop_price)

        # Add extended hours flag if specified
        if trade.extended_hours:
            # Check if broker supports extended hours trading
            if not schwab_config.SUPPORTS_EXTENDED_HOURS:
                raise BrokerError(
                    message="Extended hours trading not supported by Schwab broker",
                    error_code="EXTENDED_HOURS_NOT_SUPPORTED",
                )
            order_data["extended_hours"] = True

        return order_data

    def _map_broker_status(self, broker_status: str) -> str:
        """Map broker-specific status to application status."""
        # Use status map from config
        return schwab_config.STATUS_MAP.get(broker_status.upper(), TradeStatus.UNKNOWN)

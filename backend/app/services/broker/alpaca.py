"""Alpaca broker implementation.

This module implements the Alpaca broker API integration.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings
from app.core.secrets import get_secret, validate_broker_credentials, mask_secret
from app.models.trade import Trade, TradeStatus, OrderType, OrderSide
from app.services.broker.base import BaseBroker, BrokerError

logger = logging.getLogger(__name__)

# Constants for API endpoints
PAPER_API_BASE_URL = "https://paper-api.alpaca.markets/v2"
LIVE_API_BASE_URL = "https://api.alpaca.markets/v2"
ORDERS_ENDPOINT = "/orders"
ACCOUNT_ENDPOINT = "/account"
POSITIONS_ENDPOINT = "/positions"
ASSETS_ENDPOINT = "/assets"
BARS_ENDPOINT = "/bars"


class AlpacaBroker(BaseBroker):
    """Broker implementation for Alpaca API."""

    def __init__(
        self,
        db=None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        use_paper: bool = False,
    ):
        """Initialize with API credentials.

        Args:
            db: Database session
            api_key: Alpaca API key (will use env var if not provided)
            api_secret: Alpaca API secret (will use env var if not provided)
            use_paper: Whether to use paper trading API
        """
        self.db = db
        self.api_key = api_key or get_secret("ALPACA_API_KEY")
        self.api_secret = api_secret or get_secret("ALPACA_API_SECRET")
        self.use_paper = use_paper

        # Validate credentials
        if not self.api_key or not self.api_secret:
            raise BrokerError(
                message="Missing Alpaca API credentials. Please set ALPACA_API_KEY and ALPACA_API_SECRET.",
                error_code="MISSING_CREDENTIALS",
            )

        # Validate broker credentials are complete
        if not validate_broker_credentials("alpaca"):
            raise BrokerError(
                message="Invalid or incomplete Alpaca API credentials",
                error_code="INVALID_CREDENTIALS",
            )

        # Use paper or live URL based on settings
        self.base_url = PAPER_API_BASE_URL if use_paper else LIVE_API_BASE_URL

        # Set up session with retries
        self.session = self._create_session()

        # Set up authentication
        self._configure_auth()

        # Log initialization with masked credentials for security
        logger.info(
            f"Initialized Alpaca broker (paper={use_paper}, "
            f"api_key={mask_secret(self.api_key)}, "
            f"base_url={self.base_url})"
        )

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _configure_auth(self) -> None:
        """Configure authentication for API requests."""
        # Alpaca uses API key authentication headers
        self.session.headers.update(
            {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = str(error_data.get("code", response.status_code))
        except Exception:
            error_message = response.text or f"HTTP Error: {response.status_code}"
            error_code = str(response.status_code)

        raise BrokerError(
            message=f"Alpaca API Error: {error_message}",
            error_code=error_code,
            broker_response=error_data if "error_data" in locals() else None,
        )

    def _api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Alpaca API with error handling and retries."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=30,
            )

            # Log request details for debugging
            if self.use_paper:
                logger.debug(f"API Request: {method} {url}")
                logger.debug(f"Request data: {data}")
                logger.debug(f"Response status: {response.status_code}")

            # Handle error responses
            if not response.ok:
                self._handle_error_response(response)

            # For DELETE requests that return empty responses
            if method == "DELETE" and response.status_code == 204:
                return {"success": True}

            # Parse response
            return response.json()

        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise BrokerError(message=f"API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            raise BrokerError(message=f"Failed to parse API response: {str(e)}")

    # BaseBroker interface implementation

    def execute_trade(self, trade: Trade) -> Dict[str, Any]:
        """Execute a trade and return execution details."""
        # Safety checks for live trading
        if not self.use_paper:
            self._validate_live_trade(trade)

        # Translate trade model to Alpaca API format
        order_data = self._prepare_order_data(trade)

        # Log order for auditing (mask sensitive data)
        logger.info(
            f"Submitting {'paper' if self.use_paper else 'live'} order: "
            f"symbol={trade.symbol}, side={trade.side}, "
            f"qty={trade.quantity}, type={trade.order_type}"
        )

        # Submit order to Alpaca API
        response = self._api_request(
            method="POST", endpoint=ORDERS_ENDPOINT, data=order_data
        )

        # Return execution details
        return {
            "broker_order_id": response.get("id"),
            "status": self._map_broker_status(response.get("status", "new")),
            "submitted_at": response.get("created_at"),
            "broker_response": response,
        }

    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get account information."""
        # Alpaca only supports a single account per API key
        response = self._api_request(method="GET", endpoint=ACCOUNT_ENDPOINT)

        return {
            "account_id": response.get("id"),
            "balance": float(response.get("equity", 0)),
            "buying_power": float(response.get("buying_power", 0)),
            "cash": float(response.get("cash", 0)),
            "currency": response.get("currency", "USD"),
            "status": response.get("status"),
            "pattern_day_trader": response.get("pattern_day_trader", False),
            "trade_suspended_by_user": response.get("trade_suspended_by_user", False),
            "trading_blocked": response.get("trading_blocked", False),
            "broker_response": response,
        }

    def get_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get current positions for an account."""
        # Alpaca only supports a single account per API key
        response = self._api_request(method="GET", endpoint=POSITIONS_ENDPOINT)

        positions = []
        for position in response:
            positions.append(
                {
                    "symbol": position.get("symbol"),
                    "quantity": float(position.get("qty", 0)),
                    "market_value": float(position.get("market_value", 0)),
                    "cost_basis": float(position.get("cost_basis", 0)),
                    "unrealized_pl": float(position.get("unrealized_pl", 0)),
                    "unrealized_pl_percent": float(position.get("unrealized_plpc", 0))
                    * 100,
                    "asset_type": "equity",  # Alpaca primarily supports equities
                    "average_entry_price": float(position.get("avg_entry_price", 0)),
                    "side": position.get("side"),
                    "exchange": position.get("exchange"),
                }
            )

        return positions

    def get_trade_status(self, broker_order_id: str) -> Dict[str, Any]:
        """Get the current status of a trade."""
        response = self._api_request(
            method="GET", endpoint=f"{ORDERS_ENDPOINT}/{broker_order_id}"
        )

        return {
            "broker_order_id": broker_order_id,
            "status": self._map_broker_status(response.get("status", "unknown")),
            "filled_quantity": float(response.get("filled_qty", 0)),
            "filled_price": float(response.get("filled_avg_price", 0))
            if response.get("filled_avg_price")
            else None,
            "filled_at": response.get("filled_at"),
            "message": "",
            "broker_response": response,
        }

    def cancel_trade(self, broker_order_id: str) -> bool:
        """Cancel a pending trade."""
        try:
            response = self._api_request(
                method="DELETE", endpoint=f"{ORDERS_ENDPOINT}/{broker_order_id}"
            )

            return response.get("success", False)
        except BrokerError as e:
            # Order might already be executed or canceled
            logger.warning(f"Failed to cancel order {broker_order_id}: {str(e)}")
            return False

    def get_order_history(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get order history for an account."""
        params = {"status": "all", "limit": 100}

        if start_date:
            params["after"] = start_date.isoformat()

        if end_date:
            params["until"] = end_date.isoformat()

        response = self._api_request(
            method="GET", endpoint=ORDERS_ENDPOINT, params=params
        )

        orders = []
        for order in response:
            orders.append(
                {
                    "broker_order_id": order.get("id"),
                    "symbol": order.get("symbol"),
                    "quantity": float(order.get("qty", 0)),
                    "side": order.get("side"),
                    "type": order.get("type"),
                    "status": self._map_broker_status(order.get("status")),
                    "submitted_at": order.get("created_at"),
                    "filled_at": order.get("filled_at"),
                    "filled_price": float(order.get("filled_avg_price", 0))
                    if order.get("filled_avg_price")
                    else None,
                    "filled_quantity": float(order.get("filled_qty", 0)),
                }
            )

        return orders

    def get_trade_execution(self, broker_order_id: str) -> Dict[str, Any]:
        """Get detailed execution information for a completed trade."""
        # Alpaca doesn't have a separate executions endpoint, so we use the order detail
        response = self._api_request(
            method="GET", endpoint=f"{ORDERS_ENDPOINT}/{broker_order_id}"
        )

        # If order is filled, return details
        if response.get("status") == "filled":
            return {
                "broker_order_id": broker_order_id,
                "status": "FILLED",
                "filled_quantity": float(response.get("filled_qty", 0)),
                "average_price": float(response.get("filled_avg_price", 0)),
                # Alpaca doesn't provide individual executions, so we simulate one
                "executions": [
                    {
                        "price": float(response.get("filled_avg_price", 0)),
                        "quantity": float(response.get("filled_qty", 0)),
                        "timestamp": response.get("filled_at"),
                    }
                ],
            }
        else:
            return {
                "broker_order_id": broker_order_id,
                "status": self._map_broker_status(response.get("status", "unknown")),
                "filled_quantity": float(response.get("filled_qty", 0)),
                "average_price": float(response.get("filled_avg_price", 0))
                if response.get("filled_avg_price")
                else None,
                "executions": [],
            }

    # Optional methods implementation

    def get_market_hours(self, market: str = "EQUITY") -> Dict[str, Any]:
        """Get market hours information."""
        # Alpaca doesn't have a dedicated market hours endpoint
        # We use the clock endpoint instead
        response = self._api_request(method="GET", endpoint="/clock")

        return {
            "market": "US_EQUITY",
            "is_open": response.get("is_open", False),
            "opens_at": response.get("next_open"),
            "closes_at": response.get("next_close"),
            "extended_opens_at": None,  # Alpaca doesn't provide extended hours info via this endpoint
            "extended_closes_at": None,
            "next_open_date": response.get("next_open"),
            "next_close_date": response.get("next_close"),
        }

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get a quote for a symbol."""
        # Alpaca's quotes require a different API
        response = self._api_request(
            method="GET", endpoint=f"/stocks/{symbol}/quotes/latest"
        )

        quote = response.get("quote", {})

        return {
            "symbol": symbol,
            "bid_price": float(quote.get("bp", 0)),
            "ask_price": float(quote.get("ap", 0)),
            "bid_size": int(quote.get("bs", 0)),
            "ask_size": int(quote.get("as", 0)),
            "last_price": float(
                quote.get("ap", 0)
            ),  # Use ask as last price approximation
            "timestamp": quote.get("t"),
        }

    def place_bracket_order(
        self, trade: Trade, take_profit_price: float, stop_loss_price: float
    ) -> Dict[str, Any]:
        """Place a bracket order (entry + take profit + stop loss)."""
        # Alpaca supports bracket orders natively
        order_data = self._prepare_order_data(trade)

        # Add bracket order details
        order_data["order_class"] = "bracket"
        order_data["take_profit"] = {"limit_price": str(take_profit_price)}
        order_data["stop_loss"] = {
            "stop_price": str(stop_loss_price),
            "limit_price": str(stop_loss_price * 0.99)
            if trade.side == OrderSide.BUY
            else str(stop_loss_price * 1.01),
        }

        # Submit order to Alpaca API
        response = self._api_request(
            method="POST", endpoint=ORDERS_ENDPOINT, data=order_data
        )

        # Return execution details
        return {
            "broker_order_id": response.get("id"),
            "status": self._map_broker_status(response.get("status", "new")),
            "submitted_at": response.get("created_at"),
            "take_profit_id": response.get("legs", [{}])[0].get("id")
            if response.get("legs")
            else None,
            "stop_loss_id": response.get("legs", [{}])[1].get("id")
            if response.get("legs") and len(response.get("legs")) > 1
            else None,
            "broker_response": response,
        }

    def place_trailing_stop(
        self, trade: Trade, trail_amount: float, trail_type: str = "percent"
    ) -> Dict[str, Any]:
        """Place a trailing stop order."""
        # Alpaca supports trailing stops natively
        order_data = self._prepare_order_data(trade)

        # Add trailing stop details
        order_data["type"] = "trailing_stop"

        if trail_type == "percent":
            order_data["trail_percent"] = str(trail_amount)
        else:
            order_data["trail_price"] = str(trail_amount)

        # Submit order to Alpaca API
        response = self._api_request(
            method="POST", endpoint=ORDERS_ENDPOINT, data=order_data
        )

        # Return execution details
        return {
            "broker_order_id": response.get("id"),
            "status": self._map_broker_status(response.get("status", "new")),
            "submitted_at": response.get("created_at"),
            "broker_response": response,
        }

    # Helper methods

    def _validate_live_trade(self, trade: Trade) -> None:
        """Validate trade before executing in live environment.

        Args:
            trade: The trade to validate

        Raises:
            BrokerError: If trade validation fails
        """
        # Basic validation
        if not trade.symbol:
            raise BrokerError(
                message="Trade symbol is required", error_code="INVALID_SYMBOL"
            )

        if not trade.side or trade.side not in [OrderSide.BUY, OrderSide.SELL]:
            raise BrokerError(message="Invalid trade side", error_code="INVALID_SIDE")

        if not trade.order_type:
            raise BrokerError(
                message="Order type is required", error_code="INVALID_ORDER_TYPE"
            )

        # Quantity/amount validation
        if trade.is_fractional and trade.investment_amount:
            if trade.investment_amount <= 0:
                raise BrokerError(
                    message="Investment amount must be positive",
                    error_code="INVALID_AMOUNT",
                )
        else:
            if not trade.quantity or trade.quantity <= 0:
                raise BrokerError(
                    message="Trade quantity must be positive",
                    error_code="INVALID_QUANTITY",
                )

        # Price validation for limit orders
        if trade.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if not trade.limit_price or trade.limit_price <= 0:
                raise BrokerError(
                    message="Limit price is required for limit orders",
                    error_code="INVALID_LIMIT_PRICE",
                )

        # Stop price validation for stop orders
        if trade.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if not trade.stop_price or trade.stop_price <= 0:
                raise BrokerError(
                    message="Stop price is required for stop orders",
                    error_code="INVALID_STOP_PRICE",
                )

        # Risk limits for live trading
        if not self.use_paper:
            # Maximum position size check (example: $50,000 per position)
            max_position_value = 50000.0

            if trade.is_fractional and trade.investment_amount:
                position_value = trade.investment_amount
            else:
                # Estimate position value (would need current price in real implementation)
                position_value = trade.quantity * (
                    trade.limit_price or 100.0
                )  # Conservative estimate

            if position_value > max_position_value:
                raise BrokerError(
                    message=f"Position size ${position_value:,.2f} exceeds maximum allowed ${max_position_value:,.2f}",
                    error_code="POSITION_SIZE_LIMIT_EXCEEDED",
                )

        logger.info(f"Live trade validation passed for {trade.symbol}")

    def _prepare_order_data(self, trade: Trade) -> Dict[str, Any]:
        """Translate trade model to Alpaca API format."""
        # Map order type to Alpaca API format
        order_type_map = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP: "stop",
            OrderType.STOP_LIMIT: "stop_limit",
        }

        # Map order side to Alpaca API format
        order_side_map = {OrderSide.BUY: "buy", OrderSide.SELL: "sell"}

        # Prepare order data
        order_data = {
            "symbol": trade.symbol,
            "side": order_side_map.get(trade.side),
            "type": order_type_map.get(trade.order_type),
            "time_in_force": "day",  # Default to day orders
        }

        # Handle fractional shares (investment amount) vs. quantity
        if trade.is_fractional and trade.investment_amount:
            # Alpaca supports both fractional qty and notional value
            if float(trade.quantity) > 0:
                order_data["qty"] = str(trade.quantity)
            else:
                order_data["notional"] = str(trade.investment_amount)
        else:
            order_data["qty"] = str(trade.quantity)

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

        return order_data

    def _map_broker_status(self, broker_status: str) -> str:
        """Map broker-specific status to application status."""
        status_map = {
            "filled": TradeStatus.FILLED,
            "partially_filled": TradeStatus.PARTIALLY_FILLED,
            "new": TradeStatus.PENDING,
            "accepted": TradeStatus.PENDING,
            "pending_new": TradeStatus.PENDING,
            "accepted_for_bidding": TradeStatus.PENDING,
            "stopped": TradeStatus.CANCELED,
            "rejected": TradeStatus.REJECTED,
            "suspended": TradeStatus.PENDING,
            "canceled": TradeStatus.CANCELED,
            "cancelled": TradeStatus.CANCELLED,  # Support both spellings
            "pending_cancel": TradeStatus.PENDING_CANCEL,
            "pending_replace": TradeStatus.PENDING,
            "replaced": TradeStatus.PENDING,
            "done_for_day": TradeStatus.FILLED,
            "expired": TradeStatus.EXPIRED,
        }

        return status_map.get(broker_status.lower(), TradeStatus.UNKNOWN)

    # Additional safety and monitoring methods for live trading

    def get_account_buying_power(self, account_id: str) -> float:
        """Get current buying power for risk management.

        Args:
            account_id: Account identifier (not used by Alpaca)

        Returns:
            Current buying power in USD
        """
        account_info = self.get_account_info(account_id)
        return account_info.get("buying_power", 0.0)

    def check_trade_affordability(self, trade: Trade) -> bool:
        """Check if account has sufficient buying power for trade.

        Args:
            trade: The trade to check

        Returns:
            True if trade is affordable
        """
        try:
            buying_power = self.get_account_buying_power("")

            if trade.is_fractional and trade.investment_amount:
                required_amount = trade.investment_amount
            else:
                # Estimate required amount (would need current price in real implementation)
                estimated_price = trade.limit_price or 100.0  # Conservative estimate
                required_amount = trade.quantity * estimated_price

            return buying_power >= required_amount

        except Exception as e:
            logger.error(f"Error checking trade affordability: {str(e)}")
            return False

    def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a specific symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Position information or None if no position
        """
        try:
            positions = self.get_positions("")
            for position in positions:
                if position.get("symbol") == symbol:
                    return position
            return None
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {str(e)}")
            return None

    def is_market_open(self) -> bool:
        """Check if market is currently open.

        Returns:
            True if market is open
        """
        try:
            market_info = self.get_market_hours()
            return market_info.get("is_open", False)
        except Exception as e:
            logger.warning(f"Could not determine market status: {str(e)}")
            return False  # Conservative approach - assume closed if unknown

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that a symbol is tradeable on Alpaca.

        Args:
            symbol: Stock symbol to validate

        Returns:
            True if symbol is valid and tradeable
        """
        try:
            response = self._api_request(
                method="GET", endpoint=f"{ASSETS_ENDPOINT}/{symbol}"
            )

            # Check if asset is tradeable
            return (
                response.get("tradable", False)
                and response.get("status") == "active"
                and not response.get("fractionable", True)
                is False  # Allow fractional trading
            )

        except BrokerError:
            # Symbol not found or not tradeable
            return False
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {str(e)}")
            return False

    def get_daily_trade_count(self) -> int:
        """Get number of trades executed today for PDT monitoring.

        Returns:
            Number of trades executed today
        """
        try:
            from datetime import datetime, timezone

            today = datetime.now(timezone.utc).date()
            orders = self.get_order_history(
                account_id="",
                start_date=datetime.combine(
                    today, datetime.min.time().replace(tzinfo=timezone.utc)
                ),
            )

            # Count filled orders
            filled_orders = [
                order
                for order in orders
                if order.get("status")
                in [TradeStatus.FILLED, TradeStatus.PARTIALLY_FILLED]
            ]

            return len(filled_orders)

        except Exception as e:
            logger.error(f"Error getting daily trade count: {str(e)}")
            return 0

    def check_pattern_day_trader_compliance(self, account_id: str) -> Dict[str, Any]:
        """Check PDT compliance for the account.

        Args:
            account_id: Account identifier

        Returns:
            PDT compliance information
        """
        try:
            account_info = self.get_account_info(account_id)
            daily_trades = self.get_daily_trade_count()

            is_pdt = account_info.get("pattern_day_trader", False)
            account_value = account_info.get("balance", 0.0)

            return {
                "is_pattern_day_trader": is_pdt,
                "account_value": account_value,
                "daily_trade_count": daily_trades,
                "pdt_compliant": account_value >= 25000.0 if is_pdt else True,
                "day_trades_remaining": max(0, 3 - daily_trades)
                if not is_pdt and account_value < 25000.0
                else None,
            }

        except Exception as e:
            logger.error(f"Error checking PDT compliance: {str(e)}")
            return {
                "is_pattern_day_trader": False,
                "account_value": 0.0,
                "daily_trade_count": 0,
                "pdt_compliant": False,
                "day_trades_remaining": 0,
            }

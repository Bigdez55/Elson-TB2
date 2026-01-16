"""Alpaca broker implementation.

This module implements the Alpaca broker API integration using the ApiBaseBroker.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from app.core.config import settings
from app.core.exception_handlers import BrokerError, handle_errors
from app.core.secrets import get_secret
from app.models.trade import OrderSide, OrderType, Trade, TradeStatus
from app.services.broker.api_broker_base import ApiBaseBroker

logger = logging.getLogger(__name__)

# Constants for API endpoints
PAPER_API_BASE_URL = "https://paper-api.alpaca.markets/v2"
LIVE_API_BASE_URL = "https://api.alpaca.markets/v2"
ORDERS_ENDPOINT = "/orders"
ACCOUNT_ENDPOINT = "/account"
POSITIONS_ENDPOINT = "/positions"
ASSETS_ENDPOINT = "/assets"
BARS_ENDPOINT = "/bars"


class AlpacaBroker(ApiBaseBroker):
    """Broker implementation for Alpaca API."""

    def __init__(
        self,
        db=None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        use_paper: Optional[bool] = None,
    ):
        """Initialize with API credentials.

        Args:
            db: Database session
            api_key: Alpaca API key (will use env var if not provided)
            api_secret: Alpaca API secret (will use env var if not provided)
            use_paper: Whether to use paper trading API (defaults to settings.ALPACA_PAPER_TRADING)
        """
        # Determine environment
        self.use_paper = (
            use_paper if use_paper is not None else settings.ALPACA_PAPER_TRADING
        )

        # Determine base URL
        base_url = PAPER_API_BASE_URL if self.use_paper else LIVE_API_BASE_URL

        # Initialize base class
        super().__init__(
            db=db, api_base_url=base_url, timeout=30, metrics_prefix="broker.alpaca"
        )

        # Store API credentials
        self.api_key = api_key or get_secret("ALPACA_API_KEY_ID")
        self.api_secret = api_secret or get_secret("ALPACA_API_SECRET")

        logger.info(f"Initialized Alpaca broker (paper={self.use_paper})")

    def _configure_auth(self) -> None:
        """Configure authentication for API requests."""
        # Alpaca uses API key authentication headers
        self.api.configure_session_headers(
            {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _handle_error_response(self, response):
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

    # Order type mapping
    def _map_order_type(self, order_type: OrderType, to_api: bool = True) -> str:
        """Map between platform order types and Alpaca order types."""
        if to_api:
            order_type_map = {
                OrderType.MARKET: "market",
                OrderType.LIMIT: "limit",
                OrderType.STOP: "stop",
                OrderType.STOP_LIMIT: "stop_limit",
            }
            return order_type_map.get(order_type, "market")
        else:
            order_type_map = {
                "market": OrderType.MARKET,
                "limit": OrderType.LIMIT,
                "stop": OrderType.STOP,
                "stop_limit": OrderType.STOP_LIMIT,
            }
            return order_type_map.get(order_type, OrderType.MARKET)

    # Order side mapping
    def _map_order_side(self, order_side: OrderSide, to_api: bool = True) -> str:
        """Map between platform order sides and Alpaca order sides."""
        if to_api:
            order_side_map = {OrderSide.BUY: "buy", OrderSide.SELL: "sell"}
            return order_side_map.get(order_side, "buy")
        else:
            order_side_map = {"buy": OrderSide.BUY, "sell": OrderSide.SELL}
            return order_side_map.get(order_side, OrderSide.BUY)

    # Order status mapping
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
            "pending_cancel": TradeStatus.PENDING_CANCEL,
            "pending_replace": TradeStatus.PENDING,
            "replaced": TradeStatus.PENDING,
            "done_for_day": TradeStatus.FILLED,
            "expired": TradeStatus.EXPIRED,
        }

        return status_map.get(broker_status.lower(), TradeStatus.UNKNOWN)

    def _prepare_order_data(self, trade: Trade) -> Dict[str, Any]:
        """Translate trade model to Alpaca API format."""
        # Map order type to Alpaca API format
        order_type = self._map_order_type(trade.order_type)

        # Map order side to Alpaca API format
        order_side = self._map_order_side(trade.side)

        # Prepare order data
        order_data = {
            "symbol": trade.symbol,
            "side": order_side,
            "type": order_type,
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

    # BaseBroker interface implementation

    def execute_trade(self, trade: Trade) -> Dict[str, Any]:
        """Execute a trade and return execution details."""
        # Translate trade model to Alpaca API format
        order_data = self._prepare_order_data(trade)

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

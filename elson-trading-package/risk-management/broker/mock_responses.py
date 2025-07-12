"""Mock API responses for broker testing.

This module provides mock responses for testing broker API integrations
without requiring actual API connections.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MockResponseGenerator:
    """Generator for mock broker API responses."""

    def __init__(self, broker_type: str = "generic"):
        """Initialize with broker type.

        Args:
            broker_type: Type of broker to generate responses for
                (generic, schwab, or alpaca)
        """
        self.broker_type = broker_type.lower()
        self.current_time = datetime.now().isoformat()

        # Dictionary to store any created orders
        self.orders = {}

        # Dictionary to store any created accounts
        self.accounts = {}

        # Dictionary to store any created positions
        self.positions = {}

        # Initialize with default account
        self._create_default_account()

    def _create_default_account(self):
        """Create a default account for testing."""
        account_id = "test-account-123"

        self.accounts[account_id] = {
            "id": account_id,
            "status": "ACTIVE",
            "currency": "USD",
            "balance": 10000.0,
            "buying_power": 20000.0,
            "cash": 10000.0,
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        }

        # Add some positions
        self.positions[account_id] = [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "market_value": 1750.0,
                "cost_basis": 1500.0,
                "unrealized_pl": 250.0,
                "unrealized_pl_percent": 16.67,
                "asset_type": "equity",
            },
            {
                "symbol": "MSFT",
                "quantity": 5,
                "market_value": 1800.0,
                "cost_basis": 1600.0,
                "unrealized_pl": 200.0,
                "unrealized_pl_percent": 12.5,
                "asset_type": "equity",
            },
            {
                "symbol": "AMZN",
                "quantity": 2,
                "market_value": 7000.0,
                "cost_basis": 6800.0,
                "unrealized_pl": 200.0,
                "unrealized_pl_percent": 2.94,
                "asset_type": "equity",
            },
        ]

    def generate_account_info(self, account_id: str) -> Dict[str, Any]:
        """Generate mock account information.

        Args:
            account_id: Account ID to generate info for

        Returns:
            Mock account information
        """
        # Return existing account if it exists
        if account_id in self.accounts:
            return self.accounts[account_id]

        # Generate generic account info
        account_info = {
            "id": account_id,
            "status": "ACTIVE",
            "currency": "USD",
            "balance": 10000.0,
            "buying_power": 20000.0,
            "cash": 10000.0,
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        }

        # Add broker-specific fields
        if self.broker_type == "alpaca":
            account_info.update(
                {
                    "pattern_day_trader": False,
                    "trade_suspended_by_user": False,
                    "trading_blocked": False,
                    "account_blocked": False,
                    "account_number": f"AP{account_id[-6:]}",
                    "shorting_enabled": True,
                }
            )
        elif self.broker_type == "schwab":
            account_info.update(
                {
                    "account_number": f"SC{account_id[-6:]}",
                    "account_type": "INDIVIDUAL",
                    "day_trader_status": "NON_PATTERN",
                    "option_level": "LEVEL_2",
                    "margin_enabled": True,
                }
            )

        # Store account
        self.accounts[account_id] = account_info

        return account_info

    def generate_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Generate mock positions for an account.

        Args:
            account_id: Account ID to generate positions for

        Returns:
            List of mock positions
        """
        # Return existing positions if they exist
        if account_id in self.positions:
            return self.positions[account_id]

        # Generate empty positions list
        return []

    def generate_order_response(
        self, order_data: Dict[str, Any], account_id: str
    ) -> Dict[str, Any]:
        """Generate mock order response.

        Args:
            order_data: Order request data
            account_id: Account ID for the order

        Returns:
            Mock order response
        """
        symbol = order_data.get("symbol", "UNKNOWN")
        side = order_data.get("side", "buy")
        order_type = order_data.get("type", "market")
        quantity = order_data.get("quantity", order_data.get("qty", "0"))

        # Generate order ID based on timestamp
        order_id = f"order-{datetime.now().strftime('%Y%m%d%H%M%S')}-{symbol}"

        # Create generic response
        response = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Add broker-specific fields
        if self.broker_type == "alpaca":
            response.update(
                {
                    "status": "new",
                    "qty": quantity,
                    "filled_qty": "0",
                    "filled_avg_price": None,
                    "order_class": order_data.get("order_class", "simple"),
                    "order_type": order_type,
                    "time_in_force": order_data.get("time_in_force", "day"),
                    "extended_hours": False,
                    "client_order_id": f"client-{order_id}",
                }
            )
        elif self.broker_type == "schwab":
            response.update(
                {
                    "order_id": order_id,
                    "account_id": account_id,
                    "order_status": "PENDING",
                    "execution_status": "PENDING",
                    "order_type": order_type.upper(),
                    "time_in_force": order_data.get("time_in_force", "DAY"),
                    "quantity": quantity,
                    "filled_quantity": "0",
                    "remaining_quantity": quantity,
                }
            )

        # Add limit price if present
        if "limit_price" in order_data:
            response["limit_price"] = order_data["limit_price"]

        # Add stop price if present
        if "stop_price" in order_data:
            response["stop_price"] = order_data["stop_price"]

        # Store the order
        self.orders[order_id] = response

        return response

    def generate_order_status(
        self, order_id: str, status: str = "PENDING"
    ) -> Dict[str, Any]:
        """Generate mock order status.

        Args:
            order_id: Order ID to generate status for
            status: Status of the order (PENDING, FILLED, REJECTED, etc.)

        Returns:
            Mock order status
        """
        # Return existing order if it exists
        if order_id in self.orders:
            order = self.orders[order_id].copy()

            # Update status
            if self.broker_type == "alpaca":
                order["status"] = status.lower()
            else:
                order["status"] = status

            # If filled, add fill details
            if status.upper() == "FILLED":
                order["filled_at"] = datetime.now().isoformat()

                if self.broker_type == "alpaca":
                    order["filled_qty"] = order["qty"]
                    order["filled_avg_price"] = "175.50"
                else:
                    order["filled_quantity"] = order["quantity"]
                    order["filled_price"] = "175.50"

            return order

        # Generate generic response for unknown order
        return {"id": order_id, "status": "UNKNOWN", "message": "Order not found"}

    def generate_order_history(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Generate mock order history.

        Args:
            account_id: Account ID to generate history for
            start_date: Start date for history
            end_date: End date for history

        Returns:
            List of mock orders
        """
        # Use stored orders if they exist
        orders = [
            order
            for order in self.orders.values()
            if order.get("account_id") == account_id
        ]

        # If no stored orders, generate some sample orders
        if not orders:
            orders = [
                {
                    "id": f"order-20230101-AAPL",
                    "symbol": "AAPL",
                    "side": "buy",
                    "type": "market",
                    "quantity": "10",
                    "status": "FILLED",
                    "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
                    "filled_at": (datetime.now() - timedelta(days=30)).isoformat(),
                    "filled_quantity": "10",
                    "filled_price": "150.00",
                    "account_id": account_id,
                },
                {
                    "id": f"order-20230201-MSFT",
                    "symbol": "MSFT",
                    "side": "buy",
                    "type": "limit",
                    "quantity": "5",
                    "status": "FILLED",
                    "created_at": (datetime.now() - timedelta(days=20)).isoformat(),
                    "filled_at": (datetime.now() - timedelta(days=20)).isoformat(),
                    "filled_quantity": "5",
                    "filled_price": "320.00",
                    "limit_price": "320.00",
                    "account_id": account_id,
                },
                {
                    "id": f"order-20230301-GOOGL",
                    "symbol": "GOOGL",
                    "side": "buy",
                    "type": "market",
                    "quantity": "3",
                    "status": "FILLED",
                    "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "filled_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "filled_quantity": "3",
                    "filled_price": "125.00",
                    "account_id": account_id,
                },
            ]

        # Filter by date if provided
        if start_date:
            orders = [
                order
                for order in orders
                if datetime.fromisoformat(order["created_at"].split("T")[0])
                >= start_date
            ]

        if end_date:
            orders = [
                order
                for order in orders
                if datetime.fromisoformat(order["created_at"].split("T")[0]) <= end_date
            ]

        return orders

    def generate_quote(self, symbol: str) -> Dict[str, Any]:
        """Generate mock quote data.

        Args:
            symbol: Symbol to generate quote for

        Returns:
            Mock quote data
        """
        # Generate random price based on symbol
        price_seed = sum(ord(c) for c in symbol) % 1000
        last_price = price_seed / 10.0

        # Create generic response
        response = {
            "symbol": symbol,
            "bid_price": last_price - 0.01,
            "ask_price": last_price + 0.01,
            "last_price": last_price,
            "volume": 10000 + (price_seed % 90000),
            "timestamp": datetime.now().isoformat(),
        }

        # Add broker-specific fields
        if self.broker_type == "alpaca":
            response.update(
                {
                    "quote": {
                        "t": int(datetime.now().timestamp() * 1000),
                        "bp": last_price - 0.01,
                        "ap": last_price + 0.01,
                        "bs": 100,
                        "as": 100,
                        "bx": "V",
                        "ax": "V",
                    }
                }
            )
        elif self.broker_type == "schwab":
            response.update(
                {
                    "quotes": [
                        {
                            "symbol": symbol,
                            "bid_price": last_price - 0.01,
                            "ask_price": last_price + 0.01,
                            "last_price": last_price,
                            "change": 0.5,
                            "change_percent": 0.25,
                            "volume": 10000 + (price_seed % 90000),
                            "timestamp": datetime.now().isoformat(),
                        }
                    ]
                }
            )

        return response

    def generate_market_hours(self, market: str = "EQUITY") -> Dict[str, Any]:
        """Generate mock market hours.

        Args:
            market: Market to generate hours for

        Returns:
            Mock market hours
        """
        now = datetime.now()
        next_open = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)
        next_close = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)

        # Adjust for weekend
        if now.weekday() >= 5:  # Saturday or Sunday
            days_to_monday = (7 - now.weekday()) % 7
            next_open = (now + timedelta(days=days_to_monday)).replace(
                hour=9, minute=30, second=0, microsecond=0
            )
            next_close = (now + timedelta(days=days_to_monday)).replace(
                hour=16, minute=0, second=0, microsecond=0
            )

        # Determine if market is open
        is_open = (
            now.weekday() < 5
            and now.time() >= next_open.time()  # Monday through Friday
            and now.time() < next_close.time()
        )

        # Create generic response
        response = {
            "market": market,
            "is_open": is_open,
            "opens_at": next_open.isoformat(),
            "closes_at": next_close.isoformat(),
            "next_open_date": next_open.isoformat(),
            "next_close_date": next_close.isoformat(),
        }

        # Add broker-specific fields
        if self.broker_type == "alpaca":
            response = {
                "is_open": is_open,
                "next_open": next_open.isoformat(),
                "next_close": next_close.isoformat(),
                "timestamp": datetime.now().isoformat(),
            }
        elif self.broker_type == "schwab":
            response.update(
                {
                    "EQUITY": {
                        "is_open": is_open,
                        "opens_at": next_open.isoformat(),
                        "closes_at": next_close.isoformat(),
                        "extended": {
                            "opens_at": next_open.replace(hour=4, minute=0).isoformat(),
                            "closes_at": next_close.replace(
                                hour=20, minute=0
                            ).isoformat(),
                        },
                    }
                }
            )

        return response


# Convenience functions
def get_mock_generator(broker_type: str = "generic") -> MockResponseGenerator:
    """Get a mock response generator for the specified broker type.

    Args:
        broker_type: Type of broker (generic, schwab, or alpaca)

    Returns:
        MockResponseGenerator instance
    """
    return MockResponseGenerator(broker_type)


def generate_mock_response(
    broker_type: str, response_type: str, **kwargs
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Generate a mock response.

    Args:
        broker_type: Type of broker (generic, schwab, or alpaca)
        response_type: Type of response to generate
        **kwargs: Additional parameters for the generator

    Returns:
        Mock response
    """
    generator = get_mock_generator(broker_type)

    if response_type == "account_info":
        return generator.generate_account_info(
            account_id=kwargs.get("account_id", "test-account-123")
        )
    elif response_type == "positions":
        return generator.generate_positions(
            account_id=kwargs.get("account_id", "test-account-123")
        )
    elif response_type == "order":
        return generator.generate_order_response(
            order_data=kwargs.get("order_data", {}),
            account_id=kwargs.get("account_id", "test-account-123"),
        )
    elif response_type == "order_status":
        return generator.generate_order_status(
            order_id=kwargs.get("order_id", "test-order-123"),
            status=kwargs.get("status", "PENDING"),
        )
    elif response_type == "order_history":
        return generator.generate_order_history(
            account_id=kwargs.get("account_id", "test-account-123"),
            start_date=kwargs.get("start_date"),
            end_date=kwargs.get("end_date"),
        )
    elif response_type == "quote":
        return generator.generate_quote(symbol=kwargs.get("symbol", "AAPL"))
    elif response_type == "market_hours":
        return generator.generate_market_hours(market=kwargs.get("market", "EQUITY"))
    else:
        raise ValueError(f"Unknown response type: {response_type}")


def save_mock_responses(broker_type: str, output_dir: str) -> None:
    """Save a set of mock responses to files.

    Args:
        broker_type: Type of broker (generic, schwab, or alpaca)
        output_dir: Directory to save responses to
    """
    generator = get_mock_generator(broker_type)

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate and save responses
    responses = {
        "account_info.json": generator.generate_account_info(
            account_id="test-account-123"
        ),
        "positions.json": generator.generate_positions(account_id="test-account-123"),
        "order_market_buy.json": generator.generate_order_response(
            order_data={
                "symbol": "AAPL",
                "side": "buy",
                "type": "market",
                "quantity": "10",
            },
            account_id="test-account-123",
        ),
        "order_limit_buy.json": generator.generate_order_response(
            order_data={
                "symbol": "MSFT",
                "side": "buy",
                "type": "limit",
                "quantity": "5",
                "limit_price": "300.00",
            },
            account_id="test-account-123",
        ),
        "order_status_pending.json": generator.generate_order_status(
            order_id="test-order-123", status="PENDING"
        ),
        "order_status_filled.json": generator.generate_order_status(
            order_id="test-order-123", status="FILLED"
        ),
        "order_history.json": generator.generate_order_history(
            account_id="test-account-123"
        ),
        "quote_aapl.json": generator.generate_quote(symbol="AAPL"),
        "market_hours.json": generator.generate_market_hours(),
    }

    # Save responses to files
    for filename, response in responses.items():
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w") as f:
            json.dump(response, f, indent=2)

    logger.info(f"Saved mock responses for {broker_type} to {output_dir}")

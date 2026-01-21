"""Tests for broker API integration.

This module tests the broker API integration with mock responses.
Note: These tests require real API credentials and network access.
"""

import os
import unittest.mock as mock
from datetime import datetime, timedelta

import pytest

from app.models.trade import OrderSide, OrderType, Trade, TradeStatus
from app.services.broker.base import BaseBroker, BrokerError
from app.services.broker.factory import BrokerType, get_broker
from app.services.broker.mock_responses import generate_mock_response


# Skip these tests if no API credentials are configured
SCHWAB_CREDENTIALS_AVAILABLE = bool(os.getenv("SCHWAB_API_KEY"))
ALPACA_CREDENTIALS_AVAILABLE = bool(os.getenv("ALPACA_API_KEY"))

skip_schwab = pytest.mark.skipif(
    not SCHWAB_CREDENTIALS_AVAILABLE,
    reason="Schwab API credentials not configured"
)
skip_alpaca = pytest.mark.skipif(
    not ALPACA_CREDENTIALS_AVAILABLE,
    reason="Alpaca API credentials not configured"
)


class TestBrokerAPI:
    """Test broker API integration."""

    @pytest.fixture
    def mock_schwab_api(self):
        """Mock Schwab API responses."""
        with mock.patch(
            "app.services.broker.schwab.SchwabBroker._api_request"
        ) as mock_api:
            # Configure the mock to return different responses based on call
            mock_api.side_effect = self._mock_schwab_api_side_effect
            yield mock_api

    @pytest.fixture
    def mock_alpaca_api(self):
        """Mock Alpaca API responses."""
        with mock.patch(
            "app.services.broker.alpaca.AlpacaBroker._api_request"
        ) as mock_api:
            # Configure the mock to return different responses based on call
            mock_api.side_effect = self._mock_alpaca_api_side_effect
            yield mock_api

    def _mock_schwab_api_side_effect(self, method, endpoint, **kwargs):
        """Generate appropriate mock response based on request."""
        if endpoint == "/accounts/test-account-123":
            return generate_mock_response(
                "schwab", "account_info", account_id="test-account-123"
            )
        elif endpoint == "/accounts/test-account-123/positions":
            return generate_mock_response(
                "schwab", "positions", account_id="test-account-123"
            )
        elif endpoint == "/trading/orders" and method == "POST":
            return generate_mock_response(
                "schwab",
                "order",
                order_data=kwargs.get("data", {}),
                account_id="test-account-123",
            )
        elif endpoint.startswith("/trading/orders/") and method == "GET":
            order_id = endpoint.split("/")[-1]
            if order_id == "test-filled-order":
                return generate_mock_response(
                    "schwab", "order_status", order_id=order_id, status="FILLED"
                )
            else:
                return generate_mock_response(
                    "schwab", "order_status", order_id=order_id, status="PENDING"
                )
        elif endpoint.startswith("/trading/orders/") and method == "DELETE":
            return {"canceled": True}
        elif endpoint == "/accounts/test-account-123/orders":
            return generate_mock_response(
                "schwab",
                "order_history",
                account_id="test-account-123",
                start_date=kwargs.get("params", {}).get("start_date"),
                end_date=kwargs.get("params", {}).get("end_date"),
            )
        elif endpoint == "/market/quotes":
            symbol = kwargs.get("params", {}).get("symbols", "AAPL")
            return generate_mock_response("schwab", "quote", symbol=symbol)
        elif endpoint == "/market/hours":
            return generate_mock_response("schwab", "market_hours")
        else:
            raise ValueError(f"Unexpected API call: {method} {endpoint}")

    def _mock_alpaca_api_side_effect(self, method, endpoint, **kwargs):
        """Generate appropriate mock response based on request."""
        if endpoint == "/account":
            return generate_mock_response(
                "alpaca", "account_info", account_id="test-account-123"
            )
        elif endpoint == "/positions":
            return generate_mock_response(
                "alpaca", "positions", account_id="test-account-123"
            )
        elif endpoint == "/orders" and method == "POST":
            return generate_mock_response(
                "alpaca",
                "order",
                order_data=kwargs.get("data", {}),
                account_id="test-account-123",
            )
        elif endpoint.startswith("/orders/") and method == "GET":
            order_id = endpoint.split("/")[-1]
            if "executions" in endpoint:
                # This is a call to get executions
                if order_id == "test-filled-order":
                    status = "filled"
                else:
                    status = "pending"

                return {
                    "executions": [
                        {
                            "price": 175.50,
                            "quantity": 10,
                            "timestamp": datetime.now().isoformat(),
                        }
                    ]
                    if status == "filled"
                    else []
                }
            else:
                # This is a call to get order status
                if order_id == "test-filled-order":
                    return generate_mock_response(
                        "alpaca", "order_status", order_id=order_id, status="filled"
                    )
                else:
                    return generate_mock_response(
                        "alpaca", "order_status", order_id=order_id, status="new"
                    )
        elif endpoint.startswith("/orders/") and method == "DELETE":
            return {"success": True}
        elif endpoint == "/orders" and method == "GET":
            return generate_mock_response(
                "alpaca",
                "order_history",
                account_id="test-account-123",
                start_date=kwargs.get("params", {}).get("after"),
                end_date=kwargs.get("params", {}).get("until"),
            )
        elif endpoint.startswith("/stocks/") and "quotes" in endpoint:
            symbol = endpoint.split("/")[2]
            return generate_mock_response("alpaca", "quote", symbol=symbol)
        elif endpoint == "/clock":
            return generate_mock_response("alpaca", "market_hours")
        else:
            raise ValueError(f"Unexpected API call: {method} {endpoint}")

    @skip_schwab
    def test_schwab_broker_basic_functionality(self, mock_schwab_api):
        """Test basic functionality of the Schwab broker implementation."""
        broker = get_broker(BrokerType.SCHWAB)

        # Test get_account_info
        account_info = broker.get_account_info("test-account-123")
        assert account_info["account_id"] == "test-account-123"
        assert "balance" in account_info
        assert "buying_power" in account_info

        # Test get_positions
        positions = broker.get_positions("test-account-123")
        assert len(positions) > 0
        assert "symbol" in positions[0]
        assert "quantity" in positions[0]

        # Test get_quote
        quote = broker.get_quote("AAPL")
        assert quote["symbol"] == "AAPL"
        assert "bid_price" in quote
        assert "ask_price" in quote

        # Test get_market_hours
        hours = broker.get_market_hours()
        assert "is_open" in hours
        assert "opens_at" in hours
        assert "closes_at" in hours

    @skip_schwab
    def test_schwab_broker_order_execution(self, mock_schwab_api):
        """Test order execution with the Schwab broker implementation."""
        broker = get_broker(BrokerType.SCHWAB)

        # Create a trade
        trade = Trade(
            id=1,
            account_id="test-account-123",
            symbol="AAPL",
            quantity=10,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
        )

        # Execute the trade
        result = broker.execute_trade(trade)
        assert "broker_order_id" in result
        assert result["status"] == TradeStatus.PENDING

        # Check order status
        order_status = broker.get_trade_status(result["broker_order_id"])
        assert order_status["broker_order_id"] == result["broker_order_id"]
        assert order_status["status"] in [TradeStatus.PENDING, TradeStatus.FILLED]

        # Test cancel order
        cancel_result = broker.cancel_trade(result["broker_order_id"])
        assert cancel_result is True

        # Test get order history
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        order_history = broker.get_order_history(
            "test-account-123", start_date=start_date, end_date=end_date
        )
        assert len(order_history) > 0
        assert "broker_order_id" in order_history[0]
        assert "symbol" in order_history[0]

        # Test get trade execution for filled order
        execution = broker.get_trade_execution("test-filled-order")
        assert execution["status"] == "FILLED"
        assert execution["filled_quantity"] > 0

    @skip_alpaca
    def test_alpaca_broker_basic_functionality(self, mock_alpaca_api):
        """Test basic functionality of the Alpaca broker implementation."""
        broker = get_broker(BrokerType.ALPACA)

        # Test get_account_info
        account_info = broker.get_account_info("test-account-123")
        assert account_info["account_id"] is not None
        assert "balance" in account_info
        assert "buying_power" in account_info

        # Test get_positions
        positions = broker.get_positions("test-account-123")
        assert len(positions) > 0
        assert "symbol" in positions[0]
        assert "quantity" in positions[0]

        # Test get_quote
        quote = broker.get_quote("AAPL")
        assert quote["symbol"] == "AAPL"
        assert "bid_price" in quote
        assert "ask_price" in quote

        # Test get_market_hours
        hours = broker.get_market_hours()
        assert "is_open" in hours
        assert "opens_at" in hours or "next_open" in hours

    @skip_alpaca
    def test_alpaca_broker_order_execution(self, mock_alpaca_api):
        """Test order execution with the Alpaca broker implementation."""
        broker = get_broker(BrokerType.ALPACA)

        # Create a trade
        trade = Trade(
            id=1,
            account_id="test-account-123",
            symbol="AAPL",
            quantity=10,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
        )

        # Execute the trade
        result = broker.execute_trade(trade)
        assert "broker_order_id" in result
        assert result["status"] == TradeStatus.PENDING

        # Check order status
        order_status = broker.get_trade_status(result["broker_order_id"])
        assert order_status["broker_order_id"] == result["broker_order_id"]
        assert order_status["status"] in [TradeStatus.PENDING, TradeStatus.FILLED]

        # Test cancel order
        cancel_result = broker.cancel_trade(result["broker_order_id"])
        assert cancel_result is True

        # Test get order history
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        order_history = broker.get_order_history(
            "test-account-123", start_date=start_date, end_date=end_date
        )
        assert len(order_history) > 0
        assert "broker_order_id" in order_history[0]
        assert "symbol" in order_history[0]

        # Test get trade execution for filled order
        execution = broker.get_trade_execution("test-filled-order")
        assert execution["status"] == "FILLED"
        assert execution["filled_quantity"] > 0
        assert execution["average_price"] is not None
        assert len(execution["executions"]) > 0

    @skip_alpaca
    def test_alpaca_broker_advanced_orders(self, mock_alpaca_api):
        """Test advanced order types with the Alpaca broker implementation."""
        broker = get_broker(BrokerType.ALPACA)

        # Create a trade
        trade = Trade(
            id=1,
            account_id="test-account-123",
            symbol="AAPL",
            quantity=10,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
        )

        # Test bracket order
        result = broker.place_bracket_order(
            trade, take_profit_price=200.0, stop_loss_price=180.0
        )
        assert "broker_order_id" in result
        assert result["status"] == TradeStatus.PENDING
        assert "take_profit_id" in result
        assert "stop_loss_id" in result

        # Test trailing stop order
        result = broker.place_trailing_stop(
            trade, trail_amount=10.0, trail_type="percent"
        )
        assert "broker_order_id" in result
        assert result["status"] == TradeStatus.PENDING

    @skip_schwab
    def test_error_handling(self, mock_schwab_api):
        """Test error handling in broker implementations."""
        broker = get_broker(BrokerType.SCHWAB)

        # Mock API to raise an exception
        mock_schwab_api.side_effect = Exception("API error")

        # Test exception handling
        with pytest.raises(BrokerError):
            broker.get_account_info("test-account-123")

    def test_fractional_share_orders(self, mock_alpaca_api):
        """Test fractional share orders with the Alpaca broker implementation."""
        broker = get_broker(BrokerType.ALPACA)

        # Create a fractional trade using investment amount
        trade = Trade(
            id=1,
            account_id="test-account-123",
            symbol="AAPL",
            quantity=0,
            investment_amount=1000.0,
            is_fractional=True,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
        )

        # Execute the trade
        result = broker.execute_trade(trade)
        assert "broker_order_id" in result
        assert result["status"] == TradeStatus.PENDING

        # Create a fractional trade using fractional quantity
        trade = Trade(
            id=2,
            account_id="test-account-123",
            symbol="MSFT",
            quantity=2.5,
            is_fractional=True,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
        )

        # Execute the trade
        result = broker.execute_trade(trade)
        assert "broker_order_id" in result
        assert result["status"] == TradeStatus.PENDING

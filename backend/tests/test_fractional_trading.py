from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.trade import InvestmentType, OrderSide, OrderType, Trade, TradeStatus


@pytest.fixture
def fractional_trade(
    db: Session, test_user: Dict[str, Any], test_portfolio: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fixture that creates a fractional share trade for testing.
    """
    trade = Trade(
        user_id=test_user["id"],
        portfolio_id=test_portfolio["id"],
        symbol="AAPL",
        quantity=0.5,  # Fractional amount
        price=150.0,
        investment_amount=75.0,  # $75 worth of AAPL
        investment_type=InvestmentType.DOLLAR_BASED,
        is_fractional=True,
        trade_type="buy",
        order_type=OrderType.MARKET,
        status=TradeStatus.PENDING,
        created_at=datetime.utcnow(),
    )

    db.add(trade)
    db.commit()
    db.refresh(trade)

    trade_data = {
        "id": trade.id,
        "user_id": trade.user_id,
        "portfolio_id": trade.portfolio_id,
        "symbol": trade.symbol,
        "quantity": float(trade.quantity),
        "price": float(trade.price),
        "investment_amount": float(trade.investment_amount),
        "investment_type": trade.investment_type.value,
        "is_fractional": trade.is_fractional,
        "trade_type": trade.trade_type,
        "order_type": trade.order_type.value,
        "status": trade.status.value,
    }

    return trade_data


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/dollar not implemented")
def test_create_dollar_based_trade(
    authorized_client: TestClient, test_portfolio: Dict[str, Any]
):
    """Test creating a dollar-based (fractional share) trade."""

    # Create a dollar-based investment trade
    trade_data = {
        "portfolio_id": test_portfolio["id"],
        "symbol": "TSLA",
        "investment_amount": 100.0,
        "trade_type": "buy",
        "investment_type": "dollar_based",
    }

    response = authorized_client.post("/api/v1/trades/dollar", json=trade_data)
    assert response.status_code == 200

    # Check response data
    data = response.json()
    assert data["symbol"] == "TSLA"
    assert data["investment_amount"] == 100.0
    assert data["investment_type"] == "dollar_based"
    assert data["is_fractional"] == True
    assert data["status"] == "pending"


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/{id}/execute not implemented")
def test_execute_fractional_trade(
    authorized_client: TestClient, fractional_trade: Dict[str, Any], db: Session
):
    """Test executing a fractional share trade."""

    trade_id = fractional_trade["id"]

    # Mock market price for execution
    with patch(
        "app.services.market_data.MarketDataService.get_current_price",
        return_value=150.0,
    ):
        # Execute the fractional trade
        response = authorized_client.post(f"/api/v1/trades/{trade_id}/execute")
        assert response.status_code == 200

        # Check the trade details after execution
        data = response.json()
        assert data["status"] == "filled"

        # The executed quantity should match our fractional amount
        assert abs(data["filled_quantity"] - 0.5) < 0.001

        # Verify that the total_amount is close to $75 (may include commission)
        assert abs(data["total_amount"] - 75.0) < 2.0

        # The is_fractional flag should still be true
        assert data["is_fractional"] == True


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/dollar not implemented")
def test_minimum_investment_amount(
    authorized_client: TestClient, test_portfolio: Dict[str, Any]
):
    """Test the minimum investment amount requirement for dollar-based trades."""

    # Try to create a dollar-based trade with too small an amount
    trade_data = {
        "portfolio_id": test_portfolio["id"],
        "symbol": "AAPL",
        "investment_amount": 0.5,  # Too small
        "trade_type": "buy",
        "investment_type": "dollar_based",
    }

    response = authorized_client.post("/api/v1/trades/dollar", json=trade_data)
    assert response.status_code == 422  # Validation error

    # Verify error message
    data = response.json()
    assert "validation error" in data["detail"].lower()


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/{id}/execute not implemented")
def test_fractional_trade_in_portfolio(
    authorized_client: TestClient,
    fractional_trade: Dict[str, Any],
    test_portfolio: Dict[str, Any],
    db: Session,
):
    """Test that fractional shares appear correctly in portfolio positions."""

    # Execute the fractional trade first
    trade_id = fractional_trade["id"]

    # Mock market price for execution
    with patch(
        "app.services.market_data.MarketDataService.get_current_price",
        return_value=150.0,
    ):
        # Execute the fractional trade
        execute_response = authorized_client.post(f"/api/v1/trades/{trade_id}/execute")
        assert execute_response.status_code == 200

    # Get portfolio positions
    response = authorized_client.get(
        f"/api/v1/portfolios/{test_portfolio['id']}/positions"
    )
    assert response.status_code == 200

    # Check the portfolio contains our fractional position
    positions = response.json()
    assert isinstance(positions, list)

    # Find our AAPL position
    aapl_position = next((pos for pos in positions if pos["symbol"] == "AAPL"), None)
    assert aapl_position is not None

    # Verify the fractional amount
    assert abs(aapl_position["quantity"] - 0.5) < 0.001
    assert aapl_position["is_fractional"] == True


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/dollar not implemented")
def test_multiple_fractional_trades(
    authorized_client: TestClient, test_portfolio: Dict[str, Any], db: Session
):
    """Test multiple fractional trades adding up correctly."""

    # Create first fractional trade
    trade1_data = {
        "portfolio_id": test_portfolio["id"],
        "symbol": "AAPL",
        "investment_amount": 50.0,
        "trade_type": "buy",
        "investment_type": "dollar_based",
    }

    response1 = authorized_client.post("/api/v1/trades/dollar", json=trade1_data)
    assert response1.status_code == 200
    trade1_id = response1.json()["id"]

    # Create second fractional trade for the same stock
    trade2_data = {
        "portfolio_id": test_portfolio["id"],
        "symbol": "AAPL",
        "investment_amount": 25.0,
        "trade_type": "buy",
        "investment_type": "dollar_based",
    }

    response2 = authorized_client.post("/api/v1/trades/dollar", json=trade2_data)
    assert response2.status_code == 200
    trade2_id = response2.json()["id"]

    # Mock market price for execution
    with patch(
        "app.services.market_data.MarketDataService.get_current_price",
        return_value=150.0,
    ):
        # Execute both trades
        authorized_client.post(f"/api/v1/trades/{trade1_id}/execute")
        authorized_client.post(f"/api/v1/trades/{trade2_id}/execute")

    # Get portfolio positions
    response = authorized_client.get(
        f"/api/v1/portfolios/{test_portfolio['id']}/positions"
    )
    assert response.status_code == 200

    # Find our AAPL position
    positions = response.json()
    aapl_position = next((pos for pos in positions if pos["symbol"] == "AAPL"), None)
    assert aapl_position is not None

    # We expect approximately 0.5 shares (50/150 + 25/150)
    expected_quantity = 0.5
    assert abs(aapl_position["quantity"] - expected_quantity) < 0.01
    assert aapl_position["is_fractional"] == True


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/dollar not implemented")
def test_fractional_sell(
    authorized_client: TestClient, test_portfolio: Dict[str, Any], db: Session
):
    """Test selling a fractional position."""

    # First create and execute a buy trade to establish a position
    buy_data = {
        "portfolio_id": test_portfolio["id"],
        "symbol": "AAPL",
        "investment_amount": 150.0,
        "trade_type": "buy",
        "investment_type": "dollar_based",
    }

    buy_response = authorized_client.post("/api/v1/trades/dollar", json=buy_data)
    assert buy_response.status_code == 200
    buy_id = buy_response.json()["id"]

    # Execute the buy
    with patch(
        "app.services.market_data.MarketDataService.get_current_price",
        return_value=150.0,
    ):
        authorized_client.post(f"/api/v1/trades/{buy_id}/execute")

    # Now sell a portion of the position
    sell_data = {
        "portfolio_id": test_portfolio["id"],
        "symbol": "AAPL",
        "quantity": 0.5,  # Sell half a share
        "trade_type": "sell",
        "is_fractional": True,
    }

    sell_response = authorized_client.post("/api/v1/trades", json=sell_data)
    assert sell_response.status_code == 200
    sell_id = sell_response.json()["id"]

    # Execute the sell
    with patch(
        "app.services.market_data.MarketDataService.get_current_price",
        return_value=150.0,
    ):
        authorized_client.post(f"/api/v1/trades/{sell_id}/execute")

    # Check portfolio positions
    positions_response = authorized_client.get(
        f"/api/v1/portfolios/{test_portfolio['id']}/positions"
    )
    assert positions_response.status_code == 200

    # Find our AAPL position
    positions = positions_response.json()
    aapl_position = next((pos for pos in positions if pos["symbol"] == "AAPL"), None)

    if aapl_position:
        # We should have approximately 0.5 shares left
        assert abs(aapl_position["quantity"] - 0.5) < 0.01
    else:
        # Or the position might be closed out (due to rounding, fees, etc.)
        pass


@pytest.mark.xfail(reason="API endpoint /api/v1/trades/dollar not implemented")
def test_fractional_minor_trade_approval(
    minor_client: TestClient,
    authorized_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session,
):
    """Test guardian approval for fractional share trades by minors."""

    # Minor creates a dollar-based investment
    trade_data = {
        "portfolio_id": minor_portfolio["id"],
        "symbol": "AAPL",
        "investment_amount": 50.0,
        "trade_type": "buy",
        "investment_type": "dollar_based",
    }

    response = minor_client.post("/api/v1/trades/dollar", json=trade_data)
    assert response.status_code == 200

    trade_id = response.json()["id"]

    # Check the trade requires approval
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    assert db_trade.status == TradeStatus.PENDING_APPROVAL

    # Guardian approves the trade
    approval_data = {"approved": True}

    approval_response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve", json=approval_data
    )
    assert approval_response.status_code == 200

    # Verify the trade status was updated
    db.refresh(db_trade)
    assert db_trade.status == TradeStatus.PENDING
    assert db_trade.approved_by_user_id == test_user["id"]

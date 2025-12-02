import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models.portfolio import Portfolio
from app.models.trade import Trade


@pytest.fixture
def test_portfolio(db: Session, test_user):
    """Fixture that creates a test portfolio"""
    portfolio = Portfolio(
        name="Trading Test Portfolio",
        description="A portfolio for testing trades",
        user_id=test_user["id"],
        cash_balance=100000.00,
        risk_score=7
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "user_id": str(portfolio.user_id),
        "cash_balance": portfolio.cash_balance
    }


@pytest.fixture
def test_trade(db: Session, test_portfolio):
    """Fixture that creates a test trade"""
    trade = Trade(
        portfolio_id=uuid.UUID(test_portfolio["id"]),
        symbol="AAPL",
        side="buy",
        quantity=10,
        price=150.00,
        type="market",
        status="filled"
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return {
        "id": str(trade.id),
        "portfolio_id": str(trade.portfolio_id),
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": trade.quantity,
        "price": trade.price,
        "type": trade.type,
        "status": trade.status
    }


def test_place_market_order(authorized_client: TestClient, test_portfolio, db: Session):
    data = {
        "symbol": "MSFT",
        "side": "buy",
        "quantity": 5
    }
    response = authorized_client.post(f"/api/v1/portfolios/{test_portfolio['id']}/trades/market", json=data)
    assert response.status_code == 201
    
    # Check response data
    trade_data = response.json()
    assert trade_data["symbol"] == data["symbol"]
    assert trade_data["side"] == data["side"]
    assert trade_data["quantity"] == data["quantity"]
    assert trade_data["type"] == "market"
    assert trade_data["status"] == "pending"
    assert "id" in trade_data
    
    # Verify trade was created in database
    db_trade = db.query(Trade).filter(Trade.id == uuid.UUID(trade_data["id"])).first()
    assert db_trade is not None
    assert db_trade.symbol == data["symbol"]
    assert db_trade.side == data["side"]
    assert db_trade.quantity == data["quantity"]


def test_place_limit_order(authorized_client: TestClient, test_portfolio, db: Session):
    data = {
        "symbol": "AMZN",
        "side": "buy",
        "quantity": 2,
        "limit_price": 3200.00,
        "time_in_force": "day"
    }
    response = authorized_client.post(f"/api/v1/portfolios/{test_portfolio['id']}/trades/limit", json=data)
    assert response.status_code == 201
    
    # Check response data
    trade_data = response.json()
    assert trade_data["symbol"] == data["symbol"]
    assert trade_data["limit_price"] == data["limit_price"]
    assert trade_data["type"] == "limit"
    assert "time_in_force" in trade_data


def test_place_stop_order(authorized_client: TestClient, test_portfolio, db: Session):
    data = {
        "symbol": "TSLA",
        "side": "sell",
        "quantity": 3,
        "stop_price": 800.00,
        "time_in_force": "gtc"
    }
    response = authorized_client.post(f"/api/v1/portfolios/{test_portfolio['id']}/trades/stop", json=data)
    assert response.status_code == 201
    
    # Check response data
    trade_data = response.json()
    assert trade_data["symbol"] == data["symbol"]
    assert trade_data["stop_price"] == data["stop_price"]
    assert trade_data["type"] == "stop"


def test_get_trades(authorized_client: TestClient, test_portfolio, test_trade):
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades")
    assert response.status_code == 200
    
    trades = response.json()
    assert "items" in trades
    assert len(trades["items"]) >= 1
    
    # Check if test trade is in the list
    trade_ids = [t["id"] for t in trades["items"]]
    assert test_trade["id"] in trade_ids


def test_get_trade_by_id(authorized_client: TestClient, test_portfolio, test_trade):
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades/{test_trade['id']}")
    assert response.status_code == 200
    
    trade_data = response.json()
    assert trade_data["id"] == test_trade["id"]
    assert trade_data["symbol"] == test_trade["symbol"]
    assert trade_data["side"] == test_trade["side"]
    assert trade_data["quantity"] == test_trade["quantity"]


def test_get_nonexistent_trade(authorized_client: TestClient, test_portfolio):
    non_existent_id = str(uuid.uuid4())
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades/{non_existent_id}")
    assert response.status_code == 404


def test_cancel_trade(authorized_client: TestClient, db: Session, test_portfolio):
    # Create a pending trade
    pending_trade = Trade(
        portfolio_id=uuid.UUID(test_portfolio["id"]),
        symbol="GOOGL",
        side="buy",
        quantity=1,
        price=2500.00,
        type="limit",
        status="pending"
    )
    db.add(pending_trade)
    db.commit()
    db.refresh(pending_trade)
    
    # Cancel the trade
    response = authorized_client.delete(f"/api/v1/portfolios/{test_portfolio['id']}/trades/{pending_trade.id}")
    assert response.status_code == 200
    
    # Verify trade status was updated
    db_trade = db.query(Trade).filter(Trade.id == pending_trade.id).first()
    assert db_trade.status == "canceled"


def test_cannot_cancel_filled_trade(authorized_client: TestClient, test_portfolio, test_trade):
    # Try to cancel a filled trade
    response = authorized_client.delete(f"/api/v1/portfolios/{test_portfolio['id']}/trades/{test_trade['id']}")
    assert response.status_code == 400
    assert "cannot be canceled" in response.json()["detail"].lower()


def test_update_trade_notes(authorized_client: TestClient, db: Session, test_trade):
    data = {
        "notes": "Updated notes on this trade - bought due to technical breakout"
    }
    response = authorized_client.patch(
        f"/api/v1/portfolios/{test_trade['portfolio_id']}/trades/{test_trade['id']}",
        json=data
    )
    assert response.status_code == 200
    
    # Verify notes were updated in database
    db_trade = db.query(Trade).filter(Trade.id == uuid.UUID(test_trade["id"])).first()
    assert db_trade.notes == data["notes"]


def test_trade_performance(authorized_client: TestClient, test_portfolio, test_trade):
    response = authorized_client.get(
        f"/api/v1/portfolios/{test_portfolio['id']}/trades/{test_trade['id']}/performance"
    )
    assert response.status_code == 200
    
    performance_data = response.json()
    assert performance_data["id"] == test_trade["id"]
    assert performance_data["symbol"] == test_trade["symbol"]
    assert "current_price" in performance_data
    assert "percent_return" in performance_data


def test_trade_statistics(authorized_client: TestClient, test_portfolio):
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trade-statistics")
    assert response.status_code == 200
    
    stats = response.json()
    assert "portfolio_id" in stats
    assert stats["portfolio_id"] == test_portfolio["id"]
    assert "trade_count" in stats
    assert "win_rate" in stats


def test_trade_filtering(authorized_client: TestClient, db: Session, test_portfolio):
    # Create multiple trades for filtering testing
    symbols = ["AAPL", "MSFT", "AMZN", "TSLA", "GOOGL"]
    sides = ["buy", "sell", "buy", "sell", "buy"]
    statuses = ["filled", "filled", "pending", "canceled", "filled"]
    
    for i in range(5):
        trade = Trade(
            portfolio_id=uuid.UUID(test_portfolio["id"]),
            symbol=symbols[i],
            side=sides[i],
            quantity=i + 1,
            price=100.00 * (i + 1),
            type="market",
            status=statuses[i]
        )
        db.add(trade)
    db.commit()
    
    # Test filtering by symbol
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades?symbol=AAPL")
    assert response.status_code == 200
    trades = response.json()
    assert all(t["symbol"] == "AAPL" for t in trades["items"])
    
    # Test filtering by status
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades?status=pending")
    assert response.status_code == 200
    trades = response.json()
    assert all(t["status"] == "pending" for t in trades["items"])
    
    # Test filtering by side
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades?side=sell")
    assert response.status_code == 200
    trades = response.json()
    assert all(t["side"] == "sell" for t in trades["items"])


def test_trade_sorting(authorized_client: TestClient, test_portfolio):
    # Test sorting by price ascending
    response = authorized_client.get(
        f"/api/v1/portfolios/{test_portfolio['id']}/trades?sort_by=price&sort_direction=asc"
    )
    assert response.status_code == 200
    trades = response.json()
    
    if len(trades["items"]) > 1:
        prices = [t["price"] for t in trades["items"]]
        assert all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
    
    # Test sorting by quantity descending
    response = authorized_client.get(
        f"/api/v1/portfolios/{test_portfolio['id']}/trades?sort_by=quantity&sort_direction=desc"
    )
    assert response.status_code == 200
    trades = response.json()
    
    if len(trades["items"]) > 1:
        quantities = [t["quantity"] for t in trades["items"]]
        assert all(quantities[i] >= quantities[i+1] for i in range(len(quantities)-1))


def test_unauthorized_trade_access(client: TestClient, test_portfolio, test_trade):
    # Try without authentication
    response = client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades")
    assert response.status_code == 401
    
    response = client.get(f"/api/v1/portfolios/{test_portfolio['id']}/trades/{test_trade['id']}")
    assert response.status_code == 401
    
    response = client.post(f"/api/v1/portfolios/{test_portfolio['id']}/trades/market", 
                           json={"symbol": "AAPL", "side": "buy", "quantity": 1})
    assert response.status_code == 401
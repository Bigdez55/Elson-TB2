import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models.portfolio import Portfolio
from app.models.user import User


@pytest.fixture
def test_portfolio(db: Session, test_user):
    """Fixture that creates a test portfolio"""
    portfolio = Portfolio(
        name="Test Portfolio",
        description="A test portfolio",
        user_id=test_user["id"],
        cash_balance=50000.00,
        risk_score=7
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return {
        "id": str(portfolio.id),
        "name": portfolio.name,
        "description": portfolio.description,
        "user_id": str(portfolio.user_id),
        "cash_balance": portfolio.cash_balance,
        "risk_score": portfolio.risk_score
    }


def test_create_portfolio(authorized_client: TestClient, db: Session):
    data = {
        "name": "New Portfolio",
        "description": "My new investment portfolio",
        "initial_cash": 100000.00,
        "risk_profile": {
            "risk_tolerance": "medium_high",
            "investment_horizon": "long_term",
            "objective": "growth"
        }
    }
    response = authorized_client.post("/api/v1/portfolios", json=data)
    assert response.status_code == 201
    
    # Check response data
    portfolio_data = response.json()
    assert portfolio_data["name"] == data["name"]
    assert portfolio_data["description"] == data["description"]
    assert portfolio_data["cash_balance"] == data["initial_cash"]
    assert "id" in portfolio_data
    
    # Verify portfolio was created in database
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == uuid.UUID(portfolio_data["id"])).first()
    assert db_portfolio is not None
    assert db_portfolio.name == data["name"]
    assert db_portfolio.cash_balance == data["initial_cash"]


def test_get_portfolios(authorized_client: TestClient, test_portfolio):
    response = authorized_client.get("/api/v1/portfolios")
    assert response.status_code == 200
    
    portfolios = response.json()
    assert "items" in portfolios
    assert len(portfolios["items"]) >= 1
    
    # Check if test portfolio is in the list
    portfolio_ids = [p["id"] for p in portfolios["items"]]
    assert test_portfolio["id"] in portfolio_ids


def test_get_portfolio_by_id(authorized_client: TestClient, test_portfolio):
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}")
    assert response.status_code == 200
    
    portfolio_data = response.json()
    assert portfolio_data["id"] == test_portfolio["id"]
    assert portfolio_data["name"] == test_portfolio["name"]
    assert portfolio_data["description"] == test_portfolio["description"]
    assert portfolio_data["cash_balance"] == test_portfolio["cash_balance"]


def test_get_nonexistent_portfolio(authorized_client: TestClient):
    non_existent_id = str(uuid.uuid4())
    response = authorized_client.get(f"/api/v1/portfolios/{non_existent_id}")
    assert response.status_code == 404


def test_get_other_user_portfolio(authorized_client: TestClient, db: Session, test_superuser):
    # Create a portfolio for a different user
    other_user = db.query(User).filter(User.email == test_superuser["email"]).first()
    other_portfolio = Portfolio(
        name="Other User Portfolio",
        description="A portfolio belonging to another user",
        user_id=other_user.id,
        cash_balance=75000.00
    )
    db.add(other_portfolio)
    db.commit()
    db.refresh(other_portfolio)
    
    # Try to access other user's portfolio
    response = authorized_client.get(f"/api/v1/portfolios/{other_portfolio.id}")
    assert response.status_code == 403


def test_update_portfolio(authorized_client: TestClient, test_portfolio, db: Session):
    data = {
        "name": "Updated Portfolio Name",
        "description": "Updated portfolio description",
        "risk_profile": {
            "risk_tolerance": "high",
            "investment_horizon": "long_term",
            "objective": "aggressive_growth"
        }
    }
    response = authorized_client.put(f"/api/v1/portfolios/{test_portfolio['id']}", json=data)
    assert response.status_code == 200
    
    # Check response
    portfolio_data = response.json()
    assert portfolio_data["name"] == data["name"]
    assert portfolio_data["description"] == data["description"]
    assert portfolio_data["risk_score"] > test_portfolio["risk_score"]  # Risk score should increase
    
    # Verify changes in database
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == uuid.UUID(test_portfolio["id"])).first()
    assert db_portfolio.name == data["name"]
    assert db_portfolio.description == data["description"]


def test_delete_portfolio(authorized_client: TestClient, test_portfolio, db: Session):
    response = authorized_client.delete(f"/api/v1/portfolios/{test_portfolio['id']}")
    assert response.status_code == 200
    
    # Verify portfolio was deleted from database
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == uuid.UUID(test_portfolio["id"])).first()
    assert db_portfolio is None


def test_unauthorized_access(client: TestClient, test_portfolio):
    # Try without authentication
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 401
    
    response = client.get(f"/api/v1/portfolios/{test_portfolio['id']}")
    assert response.status_code == 401
    
    response = client.post("/api/v1/portfolios", json={"name": "Unauthorized Portfolio"})
    assert response.status_code == 401


def test_create_portfolio_validation(authorized_client: TestClient):
    # Test with missing required fields
    data = {
        "name": "Missing Fields Portfolio"
        # missing description and initial_cash
    }
    response = authorized_client.post("/api/v1/portfolios", json=data)
    assert response.status_code == 422
    
    # Test with negative cash balance
    data = {
        "name": "Negative Cash Portfolio",
        "description": "A portfolio with negative cash",
        "initial_cash": -1000.00
    }
    response = authorized_client.post("/api/v1/portfolios", json=data)
    assert response.status_code == 422
    
    # Test with invalid risk score
    data = {
        "name": "Invalid Risk Portfolio",
        "description": "A portfolio with invalid risk score",
        "initial_cash": 10000.00,
        "risk_score": 15  # Risk score should be 1-10
    }
    response = authorized_client.post("/api/v1/portfolios", json=data)
    assert response.status_code == 422


def test_portfolio_performance(authorized_client: TestClient, test_portfolio):
    response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio['id']}/performance")
    assert response.status_code == 200
    
    performance_data = response.json()
    assert "portfolio_id" in performance_data
    assert performance_data["portfolio_id"] == test_portfolio["id"]
    assert "data_points" in performance_data
    assert "benchmarks" in performance_data


def test_portfolio_pagination(authorized_client: TestClient, db: Session, test_user):
    # Create multiple portfolios for pagination testing
    for i in range(5):
        portfolio = Portfolio(
            name=f"Pagination Test Portfolio {i}",
            description=f"Testing portfolio pagination {i}",
            user_id=test_user["id"],
            cash_balance=10000.00 * (i + 1)
        )
        db.add(portfolio)
    db.commit()
    
    # Test pagination limit
    response = authorized_client.get("/api/v1/portfolios?limit=3")
    assert response.status_code == 200
    portfolios = response.json()
    assert len(portfolios["items"]) == 3
    
    # Test pagination offset
    response = authorized_client.get("/api/v1/portfolios?offset=3&limit=10")
    assert response.status_code == 200
    portfolios = response.json()
    assert len(portfolios["items"]) >= 3  # At least 3 portfolios (1 original + 5 new - 3 offset)
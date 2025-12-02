import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Dict, List, Any

from app.models.user import User, UserRole
from app.models.account import Account, AccountType
from app.models.trade import Trade, TradeStatus


def test_create_minor_account(authorized_client: TestClient, test_user: Dict[str, Any]):
    """Test creating a new minor account."""
    # Generate a birthdate for someone under 18
    minor_birthdate = date.today() - timedelta(days=10*365)  # 10 years old
    
    minor_data = {
        "email": "new_minor@example.com",
        "first_name": "New",
        "last_name": "Minor",
        "birthdate": minor_birthdate.isoformat()
    }
    
    response = authorized_client.post("/api/v1/family/minor", json=minor_data)
    assert response.status_code == 200
    
    # Check the response data
    data = response.json()
    assert data["email"] == minor_data["email"]
    assert data["first_name"] == minor_data["first_name"]
    assert data["last_name"] == minor_data["last_name"]
    assert data["guardian_id"] == test_user["id"]
    assert "account_id" in data
    

def test_create_minor_invalid_age(authorized_client: TestClient):
    """Test creating a minor account with invalid age (over 18)."""
    # Generate a birthdate for someone over 18
    adult_birthdate = date.today() - timedelta(days=19*365)  # 19 years old
    
    minor_data = {
        "email": "not_minor@example.com",
        "first_name": "Not",
        "last_name": "Minor",
        "birthdate": adult_birthdate.isoformat()
    }
    
    response = authorized_client.post("/api/v1/family/minor", json=minor_data)
    assert response.status_code == 400
    assert "Minor must be under 18 years old" in response.json()["detail"]


def test_create_minor_unauthorized(minor_client: TestClient):
    """Test that minors cannot create other minor accounts."""
    minor_birthdate = date.today() - timedelta(days=10*365)
    
    minor_data = {
        "email": "another_minor@example.com",
        "first_name": "Another",
        "last_name": "Minor",
        "birthdate": minor_birthdate.isoformat()
    }
    
    response = minor_client.post("/api/v1/family/minor", json=minor_data)
    assert response.status_code == 403
    assert "Only adult users can create minor accounts" in response.json()["detail"]


def test_get_my_minors(
    authorized_client: TestClient, 
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any]
):
    """Test getting all minors under a guardian."""
    response = authorized_client.get("/api/v1/family/minors")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least our test_minor
    
    # Find our test minor in the list
    minor_found = False
    for minor in data:
        if minor["id"] == test_minor["id"]:
            minor_found = True
            assert minor["email"] == test_minor["email"]
            assert minor["first_name"] == test_minor["first_name"]
            assert minor["last_name"] == test_minor["last_name"]
            assert minor["guardian_id"] == test_user["id"]
            assert minor["account_id"] == test_minor["account_id"]
    
    assert minor_found, "Test minor not found in response"


def test_get_my_minors_unauthorized(minor_client: TestClient):
    """Test that minors cannot view the list of minors."""
    response = minor_client.get("/api/v1/family/minors")
    assert response.status_code == 403
    assert "Only adult users can view their minor accounts" in response.json()["detail"]


def test_get_my_guardian(
    minor_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any]
):
    """Test a minor getting their guardian info."""
    response = minor_client.get("/api/v1/family/guardian")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == test_user["id"]
    assert data["email"] == test_user["email"]
    assert data["first_name"] == test_user["first_name"]
    assert data["last_name"] == test_user["last_name"]


def test_get_my_guardian_unauthorized(authorized_client: TestClient):
    """Test that adults cannot view guardian info (as they don't have one)."""
    response = authorized_client.get("/api/v1/family/guardian")
    assert response.status_code == 403
    assert "Only minor users can view their guardian" in response.json()["detail"]


def test_get_pending_trades(
    authorized_client: TestClient, 
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    pending_minor_trades: List[Dict[str, Any]]
):
    """Test getting pending trades from minors that need approval."""
    response = authorized_client.get("/api/v1/family/trades/pending")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(pending_minor_trades)
    
    # Verify all pending trades are in the response
    trade_ids = [trade["trade_id"] for trade in data]
    for trade in pending_minor_trades:
        assert trade["id"] in trade_ids
        
    # Check details of a trade
    first_trade = data[0]
    assert first_trade["minor_id"] == test_minor["id"]
    assert first_trade["status"] == "pending_approval"


def test_get_pending_trades_unauthorized(minor_client: TestClient):
    """Test that minors cannot view pending trades."""
    response = minor_client.get("/api/v1/family/trades/pending")
    assert response.status_code == 403
    assert "Only adult users can view pending minor trades" in response.json()["detail"]


def test_approve_minor_trade(
    authorized_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    pending_minor_trades: List[Dict[str, Any]],
    db: Session
):
    """Test approving a minor's trade request."""
    trade_id = pending_minor_trades[0]["id"]
    
    approval_data = {
        "approved": True
    }
    
    response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve", 
        json=approval_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["trade_id"] == trade_id
    assert data["status"] == "pending"  # Changed from pending_approval to pending
    assert data["approved_at"] is not None
    
    # Verify database state was updated
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    assert db_trade.status == TradeStatus.PENDING
    assert db_trade.approved_by_user_id == test_user["id"]
    assert db_trade.approved_at is not None


def test_reject_minor_trade(
    authorized_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    pending_minor_trades: List[Dict[str, Any]],
    db: Session
):
    """Test rejecting a minor's trade request."""
    trade_id = pending_minor_trades[1]["id"]
    
    rejection_data = {
        "approved": False,
        "rejection_reason": "Too risky for your portfolio"
    }
    
    response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve", 
        json=rejection_data
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["trade_id"] == trade_id
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == rejection_data["rejection_reason"]
    
    # Verify database state was updated
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    assert db_trade.status == TradeStatus.REJECTED
    assert db_trade.rejection_reason == rejection_data["rejection_reason"]


def test_approve_trade_missing_reason(authorized_client: TestClient, pending_minor_trades: List[Dict[str, Any]]):
    """Test rejecting a trade without providing a reason."""
    trade_id = pending_minor_trades[2]["id"]
    
    rejection_data = {
        "approved": False,
        # Missing rejection_reason
    }
    
    response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve", 
        json=rejection_data
    )
    assert response.status_code == 422  # Validation error
    
    
def test_approve_trade_not_guardian(superuser_client: TestClient, pending_minor_trades: List[Dict[str, Any]]):
    """Test that non-guardian adults cannot approve trades for minors they don't have a relationship with."""
    trade_id = pending_minor_trades[0]["id"]
    
    approval_data = {
        "approved": True
    }
    
    response = superuser_client.post(
        f"/api/v1/family/trade/{trade_id}/approve", 
        json=approval_data
    )
    assert response.status_code == 403
    assert "You are not the guardian for this minor" in response.json()["detail"]


def test_approve_trade_unauthorized(minor_client: TestClient, pending_minor_trades: List[Dict[str, Any]]):
    """Test that minors cannot approve trades."""
    trade_id = pending_minor_trades[0]["id"]
    
    approval_data = {
        "approved": True
    }
    
    response = minor_client.post(
        f"/api/v1/family/trade/{trade_id}/approve", 
        json=approval_data
    )
    assert response.status_code == 403
    assert "Only adult users can approve minor trades" in response.json()["detail"]
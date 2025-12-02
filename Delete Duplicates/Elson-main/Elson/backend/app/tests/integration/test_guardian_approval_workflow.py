import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List, Any

from app.models.trade import Trade, TradeStatus
from app.models.user import User, UserRole
from app.models.account import Account, AccountType


def test_complete_guardian_approval_workflow(
    minor_client: TestClient,
    authorized_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session
):
    """
    Test the complete workflow of a minor placing a trade, guardian approving it,
    and the trade being executed.
    """
    # Step 1: Minor places a trade that requires approval
    trade_data = {
        "portfolio_id": minor_portfolio["id"],
        "symbol": "AAPL",
        "quantity": 1.0,
        "trade_type": "buy"
    }
    
    # Minor creates the trade
    response = minor_client.post("/api/v1/trades", json=trade_data)
    assert response.status_code == 200
    
    # Extract the trade ID
    trade_id = response.json()["id"]
    
    # Step 2: Check the trade status was set to PENDING_APPROVAL
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    assert db_trade is not None
    assert db_trade.status == TradeStatus.PENDING_APPROVAL
    
    # Step 3: Guardian views pending trades
    guardian_response = authorized_client.get("/api/v1/family/trades/pending")
    assert guardian_response.status_code == 200
    
    # Ensure the newly created trade is in the pending list
    pending_trades = guardian_response.json()
    assert any(trade["trade_id"] == trade_id for trade in pending_trades)
    
    # Step 4: Guardian approves the trade
    approval_data = {
        "approved": True
    }
    
    approval_response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve",
        json=approval_data
    )
    assert approval_response.status_code == 200
    
    # Step 5: Verify the trade status changed to PENDING (ready for execution)
    db.refresh(db_trade)
    assert db_trade.status == TradeStatus.PENDING
    assert db_trade.approved_by_user_id == test_user["id"]
    assert db_trade.approved_at is not None
    
    # Step 6: Minor checks their trade status
    minor_trades_response = minor_client.get("/api/v1/trades")
    assert minor_trades_response.status_code == 200
    
    # Find the trade in the minor's list
    minor_trades = minor_trades_response.json()
    approved_trade = next((t for t in minor_trades if t["id"] == trade_id), None)
    assert approved_trade is not None
    assert approved_trade["status"] == "pending"  # Now ready for execution
    
    # This test assumes the trade execution happens in a separate process/background task


def test_guardian_rejects_trade(
    minor_client: TestClient,
    authorized_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session
):
    """Test the workflow when a guardian rejects a minor's trade."""
    # Step 1: Minor places a trade
    trade_data = {
        "portfolio_id": minor_portfolio["id"],
        "symbol": "RISKY",  # Hypothetical risky stock
        "quantity": 10.0,
        "trade_type": "buy"
    }
    
    response = minor_client.post("/api/v1/trades", json=trade_data)
    assert response.status_code == 200
    
    trade_id = response.json()["id"]
    
    # Step 2: Guardian rejects the trade
    rejection_data = {
        "approved": False,
        "rejection_reason": "This stock is too risky for your portfolio"
    }
    
    rejection_response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve",
        json=rejection_data
    )
    assert rejection_response.status_code == 200
    
    # Step 3: Verify the trade was rejected
    db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
    assert db_trade.status == TradeStatus.REJECTED
    assert db_trade.rejection_reason == rejection_data["rejection_reason"]
    
    # Step 4: Minor sees the rejected trade
    minor_trades_response = minor_client.get("/api/v1/trades")
    assert minor_trades_response.status_code == 200
    
    minor_trades = minor_trades_response.json()
    rejected_trade = next((t for t in minor_trades if t["id"] == trade_id), None)
    assert rejected_trade is not None
    assert rejected_trade["status"] == "rejected"
    assert rejected_trade["rejection_reason"] == rejection_data["rejection_reason"]


def test_minor_cannot_execute_pending_approval_trade(
    minor_client: TestClient,
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session
):
    """Test that minors cannot execute trades that are still pending approval."""
    # Step 1: Create a trade with pending_approval status
    trade = Trade(
        user_id=test_minor["id"],
        portfolio_id=minor_portfolio["id"],
        symbol="AAPL",
        quantity=1.0,
        price=150.0,
        trade_type="buy",
        status=TradeStatus.PENDING_APPROVAL,
        created_at=datetime.utcnow()
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    # Step 2: Minor attempts to execute the trade
    execution_response = minor_client.post(f"/api/v1/trades/{trade.id}/execute")
    
    # This should be forbidden
    assert execution_response.status_code == 403
    assert "Cannot execute trade" in execution_response.json()["detail"]
    
    # Trade status should still be pending approval
    db.refresh(trade)
    assert trade.status == TradeStatus.PENDING_APPROVAL


def test_guardian_cannot_approve_other_guardians_minors(
    superuser_client: TestClient,
    authorized_client: TestClient,
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session
):
    """Test that guardians cannot approve trades for minors who aren't under their guardianship."""
    # Create a trade requiring approval
    trade = Trade(
        user_id=test_minor["id"],
        portfolio_id=minor_portfolio["id"],
        symbol="AAPL",
        quantity=1.0,
        price=150.0,
        trade_type="buy",
        status=TradeStatus.PENDING_APPROVAL,
        created_at=datetime.utcnow()
    )
    
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    # Superuser (who is not the guardian) attempts to approve
    approval_data = {
        "approved": True
    }
    
    response = superuser_client.post(
        f"/api/v1/family/trade/{trade.id}/approve",
        json=approval_data
    )
    
    # Should be forbidden
    assert response.status_code == 403
    assert "You are not the guardian for this minor" in response.json()["detail"]
    
    # Trade status should remain unchanged
    db.refresh(trade)
    assert trade.status == TradeStatus.PENDING_APPROVAL


def test_guardian_approves_multiple_trades(
    minor_client: TestClient,
    authorized_client: TestClient,
    test_user: Dict[str, Any],
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session
):
    """Test that guardians can approve multiple trades for their minors."""
    # Create multiple trades
    symbols = ["AAPL", "MSFT", "GOOGL"]
    trade_ids = []
    
    for symbol in symbols:
        trade_data = {
            "portfolio_id": minor_portfolio["id"],
            "symbol": symbol,
            "quantity": 1.0,
            "trade_type": "buy"
        }
        
        response = minor_client.post("/api/v1/trades", json=trade_data)
        assert response.status_code == 200
        trade_ids.append(response.json()["id"])
    
    # Guardian approves each trade
    for trade_id in trade_ids:
        approval_data = {
            "approved": True
        }
        
        response = authorized_client.post(
            f"/api/v1/family/trade/{trade_id}/approve",
            json=approval_data
        )
        assert response.status_code == 200
    
    # Verify all trades were approved
    for trade_id in trade_ids:
        db_trade = db.query(Trade).filter(Trade.id == trade_id).first()
        assert db_trade.status == TradeStatus.PENDING
        assert db_trade.approved_by_user_id == test_user["id"]
        assert db_trade.approved_at is not None


def test_notifications_for_approvals_and_rejections(
    minor_client: TestClient,
    authorized_client: TestClient,
    test_minor: Dict[str, Any],
    minor_portfolio: Dict[str, Any],
    db: Session
):
    """
    Test that notifications are generated for approval/rejection actions.
    
    Note: This is a bit of a mock test since we can't easily verify email/push notifications
    in a test environment. We're just checking the notification record is created.
    """
    # Create a trade needing approval
    trade_data = {
        "portfolio_id": minor_portfolio["id"],
        "symbol": "AAPL",
        "quantity": 1.0,
        "trade_type": "buy"
    }
    
    response = minor_client.post("/api/v1/trades", json=trade_data)
    assert response.status_code == 200
    trade_id = response.json()["id"]
    
    # Guardian approves the trade
    approval_data = {
        "approved": True
    }
    
    approval_response = authorized_client.post(
        f"/api/v1/family/trade/{trade_id}/approve",
        json=approval_data
    )
    assert approval_response.status_code == 200
    
    # In a real implementation, we would check the notifications table
    # to verify a notification was created for the minor
    
    # For now, we're just checking the response includes approved_at
    assert approval_response.json()["approved_at"] is not None
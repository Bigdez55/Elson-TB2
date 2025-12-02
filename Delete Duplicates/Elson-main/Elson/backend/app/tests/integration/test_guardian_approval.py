"""Integration tests for guardian approval workflow.

This test suite verifies the integration between the guardian and minor
functionality, including trade approval workflows and permissions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.main import app
from app.models.user import User, UserRole
from app.models.account import Account, AccountType
from app.models.trade import Trade, TradeStatus, OrderType
from app.core.config import settings
from app.services.notifications import NotificationService


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_notification_service():
    """Create a mock notification service."""
    return MagicMock(spec=NotificationService)


@pytest.fixture
def test_guardian():
    """Create a test guardian user."""
    return User(
        id=1,
        email="guardian@example.com",
        first_name="Guardian",
        last_name="Parent",
        role=UserRole.ADULT,
        hashed_password="hashed_password",
        is_active=True
    )


@pytest.fixture
def test_minor():
    """Create a test minor user."""
    return User(
        id=2,
        email="minor@example.com",
        first_name="Minor",
        last_name="Child",
        role=UserRole.MINOR,
        hashed_password="hashed_password",
        is_active=True,
        birthdate=datetime.now() - timedelta(days=365 * 12)  # 12 years old
    )


@pytest.fixture
def test_custodial_account(test_minor, test_guardian):
    """Create a test custodial account linking the minor and guardian."""
    return Account(
        id=1,
        account_type=AccountType.CUSTODIAL,
        user_id=test_minor.id,
        guardian_id=test_guardian.id,
        status="active",
        account_number="CUST123456"
    )


@pytest.fixture
def test_pending_trade(test_minor):
    """Create a test trade pending guardian approval."""
    return Trade(
        id=1,
        user_id=test_minor.id,
        portfolio_id=1,
        symbol="AAPL",
        quantity=10,
        price=150.0,
        trade_type="buy",
        order_type=OrderType.MARKET,
        status=TradeStatus.PENDING_APPROVAL,
        created_at=datetime.now(),
        requested_by_user_id=test_minor.id
    )


class TestGuardianApprovalWorkflow:
    """Test cases for the guardian approval workflow."""

    def test_minor_trade_requires_approval(self, mock_db, test_minor, test_guardian, test_custodial_account):
        """Test that trades from minors are automatically marked for approval."""
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_minor,  # For user lookup
            None,        # For guardian lookup to force the code path we want to test
            test_custodial_account  # For account lookup
        ]
        
        # Create trading service with mocked dependencies
        from app.services.trading import TradingService
        trading_service = TradingService(db=mock_db)
        
        # Create trade data
        trade_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "price": 150.0,
            "portfolio_id": 1,
            "trade_type": "buy",
            "order_type": "market"
        }
        
        # Mock the _create_trade_record method to return a trade with PENDING_APPROVAL status
        trading_service._create_trade_record = MagicMock(return_value=Trade(
            id=1,
            user_id=test_minor.id,
            portfolio_id=1,
            symbol="AAPL",
            quantity=10,
            price=150.0,
            trade_type="buy",
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING_APPROVAL,
            created_at=datetime.now(),
            requested_by_user_id=test_minor.id
        ))
        
        # Mock the _check_if_requires_approval method
        trading_service._check_if_requires_approval = MagicMock(return_value=True)
        
        # Call create_trade
        result = trading_service.create_trade(test_minor.id, trade_data)
        
        # Verify result has requires_approval flag
        assert result.get("requires_approval") is True
        assert result.get("status") == "pending_approval"

    def test_guardian_can_approve_trade(self, mock_db, test_guardian, test_minor, test_pending_trade):
        """Test that guardians can approve trades from their minors."""
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_pending_trade,  # For trade lookup
            test_custodial_account  # For guardian verification
        ]
        
        # Create trading service with mocked dependencies
        from app.services.trading import TradingService
        trading_service = TradingService(db=mock_db)
        
        # Mock the _validate_and_execute_trade method
        trading_service._validate_and_execute_trade = MagicMock(return_value={
            "trade_id": test_pending_trade.id,
            "status": "filled",
            "message": "Trade executed successfully"
        })
        
        # Call approve_trade
        result = trading_service.approve_trade(
            trade_id=test_pending_trade.id,
            guardian_id=test_guardian.id,
            approved=True
        )
        
        # Verify trade was approved and executed
        assert result.get("status") == "filled"
        assert result.get("message") == "Trade executed successfully"
        assert mock_db.commit.called

    def test_guardian_can_reject_trade(self, mock_db, test_guardian, test_minor, test_pending_trade):
        """Test that guardians can reject trades from their minors."""
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_pending_trade,  # For trade lookup
            test_custodial_account  # For guardian verification
        ]
        
        # Create trading service with mocked dependencies
        from app.services.trading import TradingService
        trading_service = TradingService(db=mock_db)
        
        # Call approve_trade with approved=False
        result = trading_service.approve_trade(
            trade_id=test_pending_trade.id,
            guardian_id=test_guardian.id,
            approved=False,
            rejection_reason="Too expensive"
        )
        
        # Verify trade was rejected
        assert result.get("status") == "rejected"
        assert result.get("rejection_reason") == "Too expensive"
        assert mock_db.commit.called

    def test_non_guardian_cannot_approve_trade(self, mock_db, test_pending_trade):
        """Test that non-guardians cannot approve trades."""
        # Create a non-guardian user
        non_guardian = User(
            id=3,
            email="non_guardian@example.com",
            first_name="Not",
            last_name="Guardian",
            role=UserRole.ADULT,
            hashed_password="hashed_password",
            is_active=True
        )
        
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_pending_trade,  # For trade lookup
            None  # No guardian relationship found
        ]
        
        # Create trading service with mocked dependencies
        from app.services.trading import TradingService
        trading_service = TradingService(db=mock_db)
        
        # Call approve_trade with a non-guardian user
        with pytest.raises(Exception) as excinfo:
            trading_service.approve_trade(
                trade_id=test_pending_trade.id,
                guardian_id=non_guardian.id,
                approved=True
            )
        
        # Verify permission error
        assert "permission" in str(excinfo.value).lower()
        assert not mock_db.commit.called

    def test_notifications_sent_for_approval_workflow(self, mock_db, mock_notification_service, test_guardian, test_minor, test_pending_trade):
        """Test that notifications are sent during the approval workflow."""
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_pending_trade,  # For trade lookup
            test_custodial_account  # For guardian verification
        ]
        
        # Create trading service with mocked dependencies and notification service
        from app.services.trading import TradingService
        trading_service = TradingService(
            db=mock_db,
            notification_service=mock_notification_service
        )
        
        # Mock the _validate_and_execute_trade method
        trading_service._validate_and_execute_trade = MagicMock(return_value={
            "trade_id": test_pending_trade.id,
            "status": "filled",
            "message": "Trade executed successfully"
        })
        
        # Call approve_trade
        trading_service.approve_trade(
            trade_id=test_pending_trade.id,
            guardian_id=test_guardian.id,
            approved=True
        )
        
        # Verify notification was sent
        assert mock_notification_service.send_trade_approved_notification.called
        
        # Reset mocks and test rejection
        mock_notification_service.reset_mock()
        mock_db.reset_mock()
        
        # Setup mock database queries again
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_pending_trade,  # For trade lookup
            test_custodial_account  # For guardian verification
        ]
        
        # Call approve_trade with approved=False
        trading_service.approve_trade(
            trade_id=test_pending_trade.id,
            guardian_id=test_guardian.id,
            approved=False,
            rejection_reason="Too expensive"
        )
        
        # Verify rejection notification was sent
        assert mock_notification_service.send_trade_rejected_notification.called
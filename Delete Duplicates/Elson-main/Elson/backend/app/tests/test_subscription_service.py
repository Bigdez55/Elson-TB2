import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionPayment, PaymentStatus, PaymentMethod
from app.models.user import User, SubscriptionPlan, BillingCycle, UserRole
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionPaymentCreate,
    PaymentMethodCreate, CreditCardInfo, BankAccountInfo
)
from app.services.subscription_service import SubscriptionService

# Mock data for testing
def create_test_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.ADULT
    )

def create_test_subscription(user_id=1):
    return Subscription(
        id=1,
        user_id=user_id,
        plan=SubscriptionPlan.PREMIUM,
        billing_cycle=BillingCycle.MONTHLY,
        price=9.99,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        auto_renew=True,
        is_active=True
    )

def create_test_payment(subscription_id=1):
    return SubscriptionPayment(
        id=1,
        subscription_id=subscription_id,
        amount=9.99,
        status=PaymentStatus.SUCCEEDED,
        payment_date=datetime.utcnow()
    )

class TestSubscriptionService:
    def test_get_subscription(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mock query
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = test_subscription
        
        # Call method
        result = SubscriptionService.get_subscription(mock_db, 1)
        
        # Assert
        assert result == test_subscription
        mock_db.query.assert_called_once_with(Subscription)
        mock_query.filter.assert_called_once()
    
    def test_get_active_subscription(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mocks for the query chain
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.first.return_value = test_subscription
        
        # Call method
        result = SubscriptionService.get_active_subscription(mock_db, 1)
        
        # Assert
        assert result == test_subscription
        mock_db.query.assert_called_once_with(Subscription)
        mock_query.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()
        mock_order_by.first.assert_called_once()
    
    def test_create_subscription(self, mocker):
        # Setup mock DB
        mock_db = MagicMock(spec=Session)
        
        # Create subscription data
        subscription_data = SubscriptionCreate(
            user_id=1,
            plan=SubscriptionPlan.PREMIUM,
            billing_cycle=BillingCycle.MONTHLY,
            price=9.99,
            auto_renew=True
        )
        
        # Call method
        result = SubscriptionService.create_subscription(mock_db, subscription_data)
        
        # Assert
        assert result is not None
        assert result.user_id == 1
        assert result.plan == SubscriptionPlan.PREMIUM
        assert result.billing_cycle == BillingCycle.MONTHLY
        assert result.price == 9.99
        assert result.auto_renew is True
        
        # Verify DB calls
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_subscription(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mock query to return the test subscription
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = test_subscription
        
        # Create update data
        update_data = SubscriptionUpdate(plan=SubscriptionPlan.FAMILY)
        
        # Call method
        result = SubscriptionService.update_subscription(mock_db, 1, update_data)
        
        # Assert
        assert result is not None
        assert result.plan == SubscriptionPlan.FAMILY
        
        # Verify DB calls
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_cancel_subscription_immediate(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mock query
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = test_subscription
        
        # Call method
        result = SubscriptionService.cancel_subscription(mock_db, 1, immediate=True)
        
        # Assert
        assert result is not None
        assert result.is_active is False
        assert result.canceled_at is not None
        
        # Verify DB calls
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_cancel_subscription_end_of_period(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mock query
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = test_subscription
        
        # Call method
        result = SubscriptionService.cancel_subscription(mock_db, 1, immediate=False)
        
        # Assert
        assert result is not None
        assert result.is_active is True  # Still active until end of period
        assert result.auto_renew is False  # But won't renew
        assert result.canceled_at is not None
        
        # Verify DB calls
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_change_plan(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mock query
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = test_subscription
        
        # Call method
        result = SubscriptionService.change_plan(
            mock_db, 
            1, 
            new_plan=SubscriptionPlan.FAMILY,
            new_billing_cycle=BillingCycle.ANNUALLY,
            prorate=True
        )
        
        # Assert
        assert result is not None
        assert result.plan == SubscriptionPlan.FAMILY
        assert result.billing_cycle == BillingCycle.ANNUALLY
        
        # Verify DB calls
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @patch('app.services.subscription_service.encryptor')
    def test_process_payment_credit_card(self, mock_encryptor, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_subscription = create_test_subscription()
        
        # Configure mock query
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = test_subscription
        
        # Configure encryptor mock
        mock_encryptor.encrypt.return_value = "encrypted_data"
        
        # Create payment method data
        payment_method = PaymentMethodCreate(
            type=PaymentMethod.CREDIT_CARD,
            credit_card=CreditCardInfo(
                card_number="4242424242424242",
                expiry_month=12,
                expiry_year=2025,
                cvc="123",
                cardholder_name="Test User"
            )
        )
        
        # Call method
        success, message, payment = SubscriptionService.process_payment(
            mock_db, 1, payment_method
        )
        
        # Assert
        assert success is True
        assert "processed successfully" in message
        assert payment is not None
        assert test_subscription.encrypted_payment_details == "encrypted_data"
        assert test_subscription.payment_method_type == PaymentMethod.CREDIT_CARD
        
        # Verify DB calls
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_check_feature_access_free_feature(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_user = create_test_user()
        
        # Configure user query
        mock_user_query = mock_db.query.return_value
        mock_user_filter = mock_user_query.filter.return_value
        mock_user_filter.first.return_value = test_user
        
        # Call method for a free feature
        has_access, required_plan = SubscriptionService.check_feature_access(
            mock_db, 1, "paper_trading"
        )
        
        # Assert
        assert has_access is True
        assert required_plan is None
    
    def test_check_feature_access_premium_feature(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_user = create_test_user()
        test_subscription = create_test_subscription(user_id=test_user.id)
        
        # Configure user query
        mock_user_query = mock_db.query.return_value
        mock_user_filter = mock_user_query.filter.return_value
        mock_user_filter.first.return_value = test_user
        
        # Configure subscription query for active subscription check
        with patch.object(SubscriptionService, 'get_active_subscription', return_value=test_subscription):
            # Call method for a premium feature
            has_access, required_plan = SubscriptionService.check_feature_access(
                mock_db, 1, "fractional_shares"
            )
            
            # Assert
            assert has_access is True
            assert required_plan == SubscriptionPlan.PREMIUM
    
    def test_check_feature_access_family_feature(self, mocker):
        # Setup mock DB and objects
        mock_db = MagicMock(spec=Session)
        test_user = create_test_user()
        
        # Create a premium subscription (not family)
        test_subscription = create_test_subscription(user_id=test_user.id)
        test_subscription.plan = SubscriptionPlan.PREMIUM
        
        # Configure user query
        mock_user_query = mock_db.query.return_value
        mock_user_filter = mock_user_query.filter.return_value
        mock_user_filter.first.return_value = test_user
        
        # Configure subscription query for active subscription check
        with patch.object(SubscriptionService, 'get_active_subscription', return_value=test_subscription):
            # Call method for a family feature
            has_access, required_plan = SubscriptionService.check_feature_access(
                mock_db, 1, "custodial_accounts"
            )
            
            # Assert
            assert has_access is False
            assert required_plan == SubscriptionPlan.FAMILY
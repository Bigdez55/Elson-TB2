import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.subscription_service import SubscriptionService
from app.services.stripe_service import StripeService
from app.models.subscription import Subscription, SubscriptionPayment, PaymentStatus, PaymentMethod
from app.models.user import User, SubscriptionPlan, BillingCycle
from app.schemas.subscription import SubscriptionCreate, PaymentMethodCreate

@pytest.fixture
def mock_stripe_paypal_order():
    return {
        "id": "cs_test_paypal_123456789",
        "url": "https://checkout.stripe.com/pay/cs_test_paypal_123456789",
        "expires_at": int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
    }

@pytest.fixture
def mock_stripe_checkout_session():
    return {
        "id": "cs_test_paypal_123456789",
        "object": "checkout.session",
        "payment_method_types": ["paypal"],
        "mode": "subscription",
        "subscription": "sub_test_123456789",
        "customer": "cus_test_123456789",
        "customer_details": {
            "email": "test@example.com"
        },
        "amount_total": 1999,  # $19.99 in cents
        "metadata": {
            "subscription_id": "1",
            "user_id": "1",
            "plan": "family",
            "billing_cycle": "monthly"
        }
    }

@pytest.fixture
def mock_user(db: Session):
    user = User(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        stripe_customer_id="cus_test_123456789"
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def mock_subscription(db: Session, mock_user):
    subscription = Subscription(
        id=1,
        user_id=mock_user.id,
        plan=SubscriptionPlan.FAMILY,
        billing_cycle=BillingCycle.MONTHLY,
        price=19.99,
        auto_renew=True,
        start_date=datetime.utcnow(),
        is_active=True
    )
    db.add(subscription)
    db.commit()
    return subscription

class TestPayPalIntegration:
    
    @patch('app.services.stripe_service.stripe.checkout.Session.create')
    def test_create_paypal_order(self, mock_stripe_create, mock_stripe_paypal_order):
        # Mock Stripe checkout session creation
        mock_stripe_create.return_value = MagicMock(
            id=mock_stripe_paypal_order["id"],
            url=mock_stripe_paypal_order["url"],
            expires_at=mock_stripe_paypal_order["expires_at"]
        )
        
        # Call the service method
        result = StripeService.create_paypal_order(
            customer_id="cus_test_123456789",
            price_id="price_test_123456789",
            return_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            metadata={"subscription_id": "1", "user_id": "1"}
        )
        
        # Assert the correct data was returned
        assert result["id"] == mock_stripe_paypal_order["id"]
        assert result["url"] == mock_stripe_paypal_order["url"]
        assert result["expires_at"] == mock_stripe_paypal_order["expires_at"]
        
        # Assert Stripe was called with the correct parameters
        mock_stripe_create.assert_called_once()
        call_kwargs = mock_stripe_create.call_args[1]
        assert call_kwargs["payment_method_types"] == ["paypal"]
        assert call_kwargs["customer"] == "cus_test_123456789"
        assert call_kwargs["mode"] == "subscription"
    
    @patch('app.services.subscription_service.StripeService.create_paypal_order')
    def test_process_payment_with_paypal(self, mock_create_paypal_order, db, mock_user, mock_subscription, mock_stripe_paypal_order):
        # Mock the PayPal order creation
        mock_create_paypal_order.return_value = mock_stripe_paypal_order
        
        # Create payment method for PayPal
        payment_method = PaymentMethodCreate(
            type=PaymentMethod.PAYPAL,
            save_for_future=True
        )
        
        # Process the payment
        success, message, payment, additional_data = SubscriptionService.process_payment(
            db=db,
            subscription_id=mock_subscription.id,
            payment_method=payment_method
        )
        
        # Assert the result
        assert success is True
        assert "PayPal checkout initiated" in message
        assert payment is not None
        assert additional_data is not None
        assert "redirect_url" in additional_data
        assert additional_data["redirect_url"] == mock_stripe_paypal_order["url"]
        
        # Verify the subscription was updated
        updated_subscription = db.query(Subscription).filter(Subscription.id == mock_subscription.id).first()
        assert updated_subscription.payment_method_type == PaymentMethod.PAYPAL
        
        # Verify payment record was created
        payment_record = db.query(SubscriptionPayment).filter(
            SubscriptionPayment.subscription_id == mock_subscription.id
        ).first()
        assert payment_record is not None
        assert payment_record.status == PaymentStatus.PENDING
        
    @patch('app.core.encryption.AES256Encryptor.encrypt')
    @patch('stripe.Subscription.retrieve')
    def test_process_paypal_webhook(self, mock_stripe_retrieve, mock_encrypt, db, mock_user, mock_subscription, mock_stripe_checkout_session):
        # Mock the encryption function
        mock_encrypt.return_value = "encrypted_data"
        
        # Mock Stripe subscription retrieval
        mock_stripe_retrieve.return_value = {
            "id": "sub_test_123456789",
            "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp())
        }
        
        # Process the webhook
        event_data = {"object": mock_stripe_checkout_session}
        success, message = StripeService.process_paypal_webhook(db, event_data)
        
        # Assert the result
        assert success is True
        assert "PayPal subscription processed successfully" in message
        
        # Verify the subscription was updated
        updated_subscription = db.query(Subscription).filter(Subscription.id == mock_subscription.id).first()
        assert updated_subscription.provider_subscription_id == "sub_test_123456789"
        assert updated_subscription.payment_method_type == "paypal"
        assert updated_subscription.is_active is True
        
        # Verify payment record was created
        payment_record = db.query(SubscriptionPayment).filter(
            SubscriptionPayment.subscription_id == mock_subscription.id
        ).first()
        assert payment_record is not None
        assert payment_record.status == PaymentStatus.SUCCEEDED
        assert payment_record.amount == 19.99
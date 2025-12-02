import unittest
from unittest.mock import patch, MagicMock
import pytest
import stripe
from fastapi import HTTPException

from app.services.stripe_service import StripeService
from app.schemas.subscription import CreditCardInfo


class TestStripeService:
    """Tests for the StripeService class"""
    
    @patch('app.services.stripe_service.stripe.Customer.create')
    def test_create_customer(self, mock_create_customer):
        """Test creating a Stripe customer"""
        # Setup mock
        mock_customer = {
            'id': 'cus_test123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        mock_create_customer.return_value = mock_customer
        
        # Call the service
        result = StripeService.create_customer(
            user_id=123,
            email='test@example.com',
            name='Test User'
        )
        
        # Assertions
        assert result == mock_customer
        mock_create_customer.assert_called_once_with(
            email='test@example.com',
            name='Test User',
            metadata={'user_id': '123'}
        )
    
    @patch('app.services.stripe_service.stripe.Customer.create')
    def test_create_customer_error(self, mock_create_customer):
        """Test handling Stripe errors when creating customer"""
        # Setup mock to raise an error
        mock_create_customer.side_effect = stripe.error.StripeError("Test error")
        
        # Call the service and expect exception
        with pytest.raises(HTTPException) as exc_info:
            StripeService.create_customer(
                user_id=123,
                email='test@example.com'
            )
        
        # Assertions
        assert exc_info.value.status_code == 500
        assert "Payment service error" in exc_info.value.detail
    
    @patch('app.services.stripe_service.stripe.PaymentMethod.create')
    @patch('app.services.stripe_service.stripe.PaymentMethod.attach')
    def test_create_payment_method(self, mock_attach, mock_create_pm):
        """Test creating a payment method"""
        # Setup mocks
        mock_payment_method = {
            'id': 'pm_test123',
            'type': 'card',
            'card': {
                'last4': '4242',
                'brand': 'visa'
            }
        }
        mock_create_pm.return_value = mock_payment_method
        
        # Create card info
        card_info = CreditCardInfo(
            card_number="4242424242424242",
            expiry_month=12,
            expiry_year=2025,
            cvc="123",
            cardholder_name="Test User"
        )
        
        # Call service without customer ID
        result = StripeService.create_payment_method(card_info)
        
        # Assertions for creation
        assert result == mock_payment_method
        mock_create_pm.assert_called_once_with(
            type="card",
            card={
                "number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123"
            },
            billing_details={
                "name": "Test User"
            }
        )
        # Attachment should not be called
        mock_attach.assert_not_called()
        
        # Reset mocks
        mock_create_pm.reset_mock()
        
        # Call service with customer ID
        result = StripeService.create_payment_method(card_info, customer_id="cus_test123")
        
        # Assertions for attachment
        mock_attach.assert_called_once_with(
            mock_payment_method.get('id'),
            customer="cus_test123"
        )
    
    @patch('app.services.stripe_service.stripe.Subscription.create')
    @patch('app.services.stripe_service.stripe.Customer.modify')
    def test_create_subscription(self, mock_modify, mock_create_sub):
        """Test creating a subscription"""
        # Setup mocks
        mock_subscription = {
            'id': 'sub_test123',
            'customer': 'cus_test123',
            'items': {
                'data': [
                    {'id': 'si_test', 'price': {'id': 'price_test'}}
                ]
            },
            'current_period_end': 1672531200,  # 2023-01-01
            'status': 'active'
        }
        mock_create_sub.return_value = mock_subscription
        
        # Call service
        result = StripeService.create_subscription(
            customer_id="cus_test123",
            price_id="price_test",
            payment_method_id="pm_test123",
            metadata={"order_id": "12345"}
        )
        
        # Assertions
        assert result == mock_subscription
        mock_modify.assert_called_once_with(
            "cus_test123",
            invoice_settings={
                "default_payment_method": "pm_test123"
            }
        )
        mock_create_sub.assert_called_once_with(
            customer="cus_test123",
            items=[{"price": "price_test"}],
            expand=["latest_invoice.payment_intent"],
            metadata={"order_id": "12345"}
        )
    
    @patch('app.services.stripe_service.stripe.Webhook.construct_event')
    def test_handle_webhook_event(self, mock_construct):
        """Test handling a webhook event"""
        # Setup mock
        mock_event = {
            'id': 'evt_test123',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_test123'
                }
            }
        }
        mock_construct.return_value = mock_event
        
        # Call service
        result = StripeService.handle_webhook_event(
            payload=b'{"test": "data"}',
            sig_header="test_signature",
            webhook_secret="test_secret"
        )
        
        # Assertions
        assert result == mock_event
        mock_construct.assert_called_once_with(
            b'{"test": "data"}', "test_signature", "test_secret"
        )
    
    @patch('app.services.stripe_service.stripe.Webhook.construct_event')
    def test_handle_webhook_invalid_signature(self, mock_construct):
        """Test handling webhook with invalid signature"""
        # Setup mock to raise an error
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid", "test")
        
        # Call service and expect exception
        with pytest.raises(HTTPException) as exc_info:
            StripeService.handle_webhook_event(
                payload=b'{"test": "data"}',
                sig_header="invalid_signature",
                webhook_secret="test_secret"
            )
        
        # Assertions
        assert exc_info.value.status_code == 400
        assert "Invalid signature" in exc_info.value.detail
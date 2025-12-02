import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User, UserRole, SubscriptionPlan, BillingCycle
from app.models.subscription import Subscription, SubscriptionPayment, PaymentStatus, PaymentMethod
from app.services.subscription_service import PRICING
from app.core.security import create_access_token
from app.schemas.subscription import PaymentMethodCreate, CreditCardInfo

# Test client
client = TestClient(app)

# Helper functions
def create_test_user(db: Session) -> User:
    """Create a test user in the database"""
    user = User(
        email="test@example.com", 
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.ADULT,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_admin(db: Session) -> User:
    """Create a test admin user in the database"""
    admin = User(
        email="admin@example.com", 
        hashed_password="hashed_password",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

def create_test_subscription(db: Session, user_id: int) -> Subscription:
    """Create a test subscription in the database"""
    now = datetime.utcnow()
    subscription = Subscription(
        user_id=user_id,
        plan=SubscriptionPlan.PREMIUM,
        billing_cycle=BillingCycle.MONTHLY,
        price=PRICING[SubscriptionPlan.PREMIUM][BillingCycle.MONTHLY],
        start_date=now,
        end_date=now + timedelta(days=30),
        auto_renew=True,
        is_active=True
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

def get_auth_headers(user_id: int) -> dict:
    """Get authentication headers for a user"""
    access_token = create_access_token(
        data={"sub": str(user_id)}
    )
    return {"Authorization": f"Bearer {access_token}"}

class TestSubscriptionAPI:
    def test_get_user_subscriptions(self, db: Session):
        # Create test user and subscription
        user = create_test_user(db)
        subscription = create_test_subscription(db, user.id)
        
        # Make request
        response = client.get(
            "/api/v1/subscriptions/",
            headers=get_auth_headers(user.id)
        )
        
        # Assert
        assert response.status_code == 200
        subscriptions = response.json()
        assert len(subscriptions) == 1
        assert subscriptions[0]["id"] == subscription.id
        assert subscriptions[0]["user_id"] == user.id
        assert subscriptions[0]["plan"] == "premium"
        
    def test_get_active_subscription(self, db: Session):
        # Create test user and subscription
        user = create_test_user(db)
        subscription = create_test_subscription(db, user.id)
        
        # Make request
        response = client.get(
            "/api/v1/subscriptions/active",
            headers=get_auth_headers(user.id)
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription.id
        assert data["user_id"] == user.id
        assert data["plan"] == "premium"
        assert data["status"] == "Active"
    
    def test_get_subscription_by_id(self, db: Session):
        # Create test user and subscription
        user = create_test_user(db)
        subscription = create_test_subscription(db, user.id)
        
        # Make request
        response = client.get(
            f"/api/v1/subscriptions/{subscription.id}",
            headers=get_auth_headers(user.id)
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription.id
        assert data["user_id"] == user.id
        assert data["plan"] == "premium"
    
    def test_get_subscription_unauthorized(self, db: Session):
        # Create two users
        user1 = create_test_user(db)
        user2 = User(
            email="other@example.com", 
            hashed_password="hashed_password",
            role=UserRole.ADULT,
            is_active=True
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        
        # Create subscription for user1
        subscription = create_test_subscription(db, user1.id)
        
        # Try to access with user2's credentials
        response = client.get(
            f"/api/v1/subscriptions/{subscription.id}",
            headers=get_auth_headers(user2.id)
        )
        
        # Assert
        assert response.status_code == 403
    
    def test_create_subscription_as_admin(self, db: Session):
        # Create admin and regular user
        admin = create_test_admin(db)
        user = create_test_user(db)
        
        # Make request to create subscription for user
        response = client.post(
            "/api/v1/subscriptions/",
            headers=get_auth_headers(admin.id),
            json={
                "user_id": user.id,
                "plan": "premium",
                "billing_cycle": "monthly",
                "price": PRICING[SubscriptionPlan.PREMIUM][BillingCycle.MONTHLY],
                "auto_renew": True
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user.id
        assert data["plan"] == "premium"
        assert data["billing_cycle"] == "monthly"
    
    def test_create_subscription_unauthorized(self, db: Session):
        # Create two regular users
        user1 = create_test_user(db)
        user2 = User(
            email="other@example.com", 
            hashed_password="hashed_password",
            role=UserRole.ADULT,
            is_active=True
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        
        # Try to create subscription for user2 as user1
        response = client.post(
            "/api/v1/subscriptions/",
            headers=get_auth_headers(user1.id),
            json={
                "user_id": user2.id,
                "plan": "premium",
                "billing_cycle": "monthly",
                "price": PRICING[SubscriptionPlan.PREMIUM][BillingCycle.MONTHLY],
                "auto_renew": True
            }
        )
        
        # Assert
        assert response.status_code == 403
    
    def test_subscribe_with_payment(self, db: Session):
        # Create user
        user = create_test_user(db)
        
        # Make request
        response = client.post(
            "/api/v1/subscriptions/subscribe",
            headers=get_auth_headers(user.id),
            json={
                "plan": "premium",
                "billing_cycle": "monthly",
                "price": PRICING[SubscriptionPlan.PREMIUM][BillingCycle.MONTHLY],
                "auto_renew": True,
                "payment_method": {
                    "type": "credit_card",
                    "credit_card": {
                        "card_number": "4242424242424242",
                        "expiry_month": 12,
                        "expiry_year": 2025,
                        "cvc": "123",
                        "cardholder_name": "Test User"
                    },
                    "save_for_future": True
                }
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user.id
        assert data["plan"] == "premium"
        assert data["billing_cycle"] == "monthly"
        assert data["payment_method_type"] == "credit_card"
    
    def test_cancel_subscription(self, db: Session):
        # Create user and subscription
        user = create_test_user(db)
        subscription = create_test_subscription(db, user.id)
        
        # Make request
        response = client.post(
            f"/api/v1/subscriptions/{subscription.id}/cancel",
            headers=get_auth_headers(user.id),
            json={
                "reason": "Testing cancellation",
                "immediate": False
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription.id
        assert data["auto_renew"] is False
        assert data["is_active"] is True  # Still active until end of period
        assert "canceled_at" in data and data["canceled_at"] is not None
    
    def test_change_subscription_plan(self, db: Session):
        # Create user and subscription
        user = create_test_user(db)
        subscription = create_test_subscription(db, user.id)
        
        # Make request
        response = client.post(
            f"/api/v1/subscriptions/{subscription.id}/change-plan",
            headers=get_auth_headers(user.id),
            json={
                "new_plan": "family",
                "new_billing_cycle": "annually",
                "prorate": True
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription.id
        assert data["plan"] == "family"
        assert data["billing_cycle"] == "annually"
        assert data["price"] == PRICING[SubscriptionPlan.FAMILY][BillingCycle.ANNUALLY]
    
    def test_check_feature_access(self, db: Session):
        # Create user and subscription
        user = create_test_user(db)
        subscription = create_test_subscription(db, user.id)
        
        # Make request for premium feature
        response = client.post(
            "/api/v1/subscriptions/check-feature",
            headers=get_auth_headers(user.id),
            json={
                "feature": "fractional_shares"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["feature"] == "fractional_shares"
        assert data["has_access"] is True
        assert data["required_plan"] == "premium"
        
        # Make request for family feature (should not have access)
        response = client.post(
            "/api/v1/subscriptions/check-feature",
            headers=get_auth_headers(user.id),
            json={
                "feature": "custodial_accounts"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["feature"] == "custodial_accounts"
        assert data["has_access"] is False
        assert data["required_plan"] == "family"
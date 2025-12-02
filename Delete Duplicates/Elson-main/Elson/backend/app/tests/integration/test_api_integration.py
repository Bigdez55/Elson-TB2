"""Integration tests for API endpoints.

This module contains integration tests for the API endpoints, testing the
interaction between API routes, services, database models, and authentication.
"""

import pytest
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.core.auth import create_access_token
from app.models.user import User, UserRole
from app.models.portfolio import Portfolio, RiskProfile
from app.db.database import get_db
from app.tests.conftest import override_get_db, test_db, user_factory, portfolio_factory


@pytest.fixture
def client():
    """Create a test client for the API."""
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def admin_token(test_db):
    """Create an admin token for authentication."""
    admin = user_factory(test_db, role=UserRole.ADMIN)
    token_data = {
        "sub": admin.email,
        "user_id": admin.id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return create_access_token(token_data)


@pytest.fixture
def user_token(test_db):
    """Create a user token for authentication."""
    user = user_factory(test_db)
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return create_access_token(token_data)


class TestUserAPI:
    """Integration tests for user API endpoints."""
    
    def test_create_user(self, client):
        """Test creating a new user."""
        user_data = {
            "email": "newuser@example.com",
            "password": "Password123!",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert "id" in data
        
    def test_get_users(self, client, admin_token):
        """Test retrieving all users (admin only)."""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
    def test_get_current_user(self, client, user_token):
        """Test retrieving the current user."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "email" in data
        assert "id" in data
        
    def test_update_user(self, client, user_token, test_db):
        """Test updating user information."""
        # Get the user from the token
        token_parts = user_token.split('.')
        import base64
        import json
        payload = json.loads(base64.b64decode(token_parts[1] + '==').decode('utf-8'))
        user_id = payload["user_id"]
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = client.patch(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]


class TestPortfolioAPI:
    """Integration tests for portfolio API endpoints."""
    
    def test_create_portfolio(self, client, user_token, test_db):
        """Test creating a new portfolio."""
        portfolio_data = {
            "name": "Test Portfolio",
            "description": "A test portfolio",
            "risk_profile": "MODERATE"
        }
        
        response = client.post(
            "/api/v1/portfolios/",
            headers={"Authorization": f"Bearer {user_token}"},
            json=portfolio_data
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == portfolio_data["name"]
        assert data["description"] == portfolio_data["description"]
        assert data["risk_profile"] == portfolio_data["risk_profile"]
        assert "id" in data
        
    def test_get_portfolios(self, client, user_token, test_db):
        """Test retrieving user portfolios."""
        # Get the user from the token
        token_parts = user_token.split('.')
        import base64
        import json
        payload = json.loads(base64.b64decode(token_parts[1] + '==').decode('utf-8'))
        user_id = payload["user_id"]
        
        # Create a portfolio for the user
        portfolio = portfolio_factory(test_db, user_id=user_id)
        
        response = client.get(
            "/api/v1/portfolios/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(p["id"] == portfolio.id for p in data)
        
    def test_get_portfolio(self, client, user_token, test_db):
        """Test retrieving a specific portfolio."""
        # Get the user from the token
        token_parts = user_token.split('.')
        import base64
        import json
        payload = json.loads(base64.b64decode(token_parts[1] + '==').decode('utf-8'))
        user_id = payload["user_id"]
        
        # Create a portfolio for the user
        portfolio = portfolio_factory(test_db, user_id=user_id)
        
        response = client.get(
            f"/api/v1/portfolios/{portfolio.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == portfolio.id
        assert data["name"] == portfolio.name
        
    def test_update_portfolio(self, client, user_token, test_db):
        """Test updating a portfolio."""
        # Get the user from the token
        token_parts = user_token.split('.')
        import base64
        import json
        payload = json.loads(base64.b64decode(token_parts[1] + '==').decode('utf-8'))
        user_id = payload["user_id"]
        
        # Create a portfolio for the user
        portfolio = portfolio_factory(test_db, user_id=user_id)
        
        update_data = {
            "name": "Updated Portfolio",
            "description": "An updated portfolio description",
            "risk_profile": "AGGRESSIVE"
        }
        
        response = client.patch(
            f"/api/v1/portfolios/{portfolio.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["risk_profile"] == update_data["risk_profile"]


class TestAuthentication:
    """Integration tests for authentication endpoints."""
    
    def test_login(self, client, test_db):
        """Test user login."""
        email = "testlogin@example.com"
        password = "Password123!"
        
        # Create a user
        from app.core.security import get_password_hash
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            first_name="Test",
            last_name="Login",
            role=UserRole.ADULT,
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        login_data = {
            "username": email,
            "password": password
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "invalid@example.com",
            "password": "InvalidPassword123!"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
    def test_token_refresh(self, client, user_token):
        """Test refreshing a token."""
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password


def test_create_user(client: TestClient, db: Session):
    data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User"
    }
    response = client.post("/api/v1/users/register", json=data)
    assert response.status_code == 201
    
    # Check response data
    user_data = response.json()
    assert user_data["email"] == data["email"]
    assert user_data["full_name"] == data["full_name"]
    assert "id" in user_data
    assert "password" not in user_data
    
    # Verify user was created in database
    db_user = db.query(User).filter(User.email == data["email"]).first()
    assert db_user is not None
    assert db_user.email == data["email"]
    assert db_user.full_name == data["full_name"]
    assert verify_password(data["password"], db_user.hashed_password)


def test_create_user_existing_email(client: TestClient, test_user):
    data = {
        "email": test_user["email"],  # Using existing email
        "password": "differentpassword",
        "full_name": "Another User"
    }
    response = client.post("/api/v1/users/register", json=data)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_login_user(client: TestClient, test_user):
    data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    response = client.post("/api/v1/auth/login", data=data)
    assert response.status_code == 200
    
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_user_wrong_password(client: TestClient, test_user):
    data = {
        "username": test_user["email"],
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=data)
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_get_users_me(authorized_client: TestClient, test_user):
    response = authorized_client.get("/api/v1/users/me")
    assert response.status_code == 200
    
    user_data = response.json()
    assert user_data["email"] == test_user["email"]
    assert user_data["full_name"] == test_user["full_name"]
    assert user_data["id"] == test_user["id"]
    assert "hashed_password" not in user_data


def test_get_users_me_unauthorized(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_update_user(authorized_client: TestClient, test_user, db: Session):
    data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    response = authorized_client.put("/api/v1/users/me", json=data)
    assert response.status_code == 200
    
    # Check response
    user_data = response.json()
    assert user_data["full_name"] == data["full_name"]
    assert user_data["email"] == data["email"]
    
    # Verify changes in database
    db_user = db.query(User).filter(User.id == test_user["id"]).first()
    assert db_user.full_name == data["full_name"]
    assert db_user.email == data["email"]


def test_change_password(authorized_client: TestClient, test_user, db: Session):
    data = {
        "current_password": test_user["password"],
        "new_password": "newstrongpassword"
    }
    response = authorized_client.put("/api/v1/users/me/password", json=data)
    assert response.status_code == 200
    
    # Verify password was changed in database
    db_user = db.query(User).filter(User.id == test_user["id"]).first()
    assert verify_password(data["new_password"], db_user.hashed_password)
    assert not verify_password(test_user["password"], db_user.hashed_password)


def test_change_password_wrong_current(authorized_client: TestClient, test_user):
    data = {
        "current_password": "wrongpassword",
        "new_password": "newstrongpassword"
    }
    response = authorized_client.put("/api/v1/users/me/password", json=data)
    assert response.status_code == 400
    assert "current password" in response.json()["detail"].lower()


@pytest.mark.parametrize("password", [
    "short",           # Too short
    "nodigits",        # No digits
    "12345678",        # No letters
    "aaaaa12345"       # No uppercase
])
def test_password_validation(client: TestClient, password):
    data = {
        "email": "testvalidation@example.com",
        "password": password,
        "full_name": "Test Validation"
    }
    response = client.post("/api/v1/users/register", json=data)
    assert response.status_code == 422
    

def test_get_all_users_superuser(superuser_client: TestClient, test_user, test_superuser):
    response = superuser_client.get("/api/v1/users/")
    assert response.status_code == 200
    
    users = response.json()
    assert len(users) >= 2  # At least the test user and superuser
    emails = [user["email"] for user in users]
    assert test_user["email"] in emails
    assert test_superuser["email"] in emails


def test_get_all_users_regular_user(authorized_client: TestClient):
    response = authorized_client.get("/api/v1/users/")
    assert response.status_code == 403  # Forbidden for regular users


def test_get_user_by_id_superuser(superuser_client: TestClient, test_user):
    response = superuser_client.get(f"/api/v1/users/{test_user['id']}")
    assert response.status_code == 200
    
    user_data = response.json()
    assert user_data["email"] == test_user["email"]
    assert user_data["id"] == test_user["id"]


def test_get_user_by_id_regular_user(authorized_client: TestClient, test_superuser):
    response = authorized_client.get(f"/api/v1/users/{test_superuser['id']}")
    assert response.status_code == 403  # Forbidden for regular users
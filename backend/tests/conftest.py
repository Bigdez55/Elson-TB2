import asyncio
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base, get_db
from app.main import app
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioType


# Test settings
class TestSettings(Settings):
    DATABASE_URL: str = "sqlite:///./test.db"
    SECRET_KEY: str = "test-secret-key-for-testing-only"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = None


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    return TestSettings()


# Database fixtures
@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# Alias for db_session (some tests use 'db' instead)
@pytest.fixture(scope="function")
def db(db_session):
    return db_session


# FastAPI test client
@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Async test fixtures
@pytest_asyncio.fixture
async def async_client(db_session) -> AsyncGenerator[TestClient, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# User test data
@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "risk_tolerance": "moderate",
        "trading_style": "long_term",
    }


@pytest.fixture
def test_portfolio_data():
    return {
        "name": "Test Portfolio",
        "description": "A test portfolio",
        "cash_balance": 10000.0,
        "auto_rebalance": False,
    }


@pytest.fixture
def test_trade_data():
    return {
        "symbol": "AAPL",
        "trade_type": "BUY",
        "order_type": "MARKET",
        "quantity": 10,
        "portfolio_id": 1,
    }


# Clean up test database after each test session
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    # Clean up test database
    if os.path.exists("./test.db"):
        os.remove("./test.db")


# Test user fixture - creates a user in the database
@pytest.fixture
def test_user(db_session) -> Dict[str, Any]:
    """Create a test user in the database."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        risk_tolerance="moderate",
        trading_style="long_term",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "password": "testpassword123",
    }


# Test portfolio fixture - creates a portfolio for the test user
@pytest.fixture
def test_portfolio(db_session, test_user) -> Dict[str, Any]:
    """Create a test portfolio for the test user."""
    portfolio = Portfolio(
        user_id=test_user["id"],
        owner_id=test_user["id"],
        name="Test Portfolio",
        description="A test portfolio",
        cash_balance=Decimal("100000.00"),
        total_value=Decimal("100000.00"),
        portfolio_type=PortfolioType.PAPER,
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "name": portfolio.name,
        "cash_balance": float(portfolio.cash_balance),
    }


# Authorized client fixture - client with authentication token
@pytest.fixture
def authorized_client(client, test_user) -> TestClient:
    """Create a test client with authentication."""
    # Create access token for the test user
    access_token = create_access_token(data={"sub": test_user["email"]})

    # Add authorization header to client
    client.headers["Authorization"] = f"Bearer {access_token}"

    return client


# Minor user fixtures for family account testing
@pytest.fixture
def test_minor(db_session, test_user) -> Dict[str, Any]:
    """Create a minor user linked to the test user."""
    from app.models.user import UserRole

    minor = User(
        email="minor@example.com",
        hashed_password=get_password_hash("minorpassword123"),
        full_name="Test Minor",
        is_active=True,
        is_verified=True,
        role=UserRole.MINOR,  # Use role enum instead of is_minor
        risk_tolerance="conservative",
        trading_style="long_term",
    )
    db_session.add(minor)
    db_session.commit()
    db_session.refresh(minor)

    return {
        "id": minor.id,
        "email": minor.email,
        "full_name": minor.full_name,
        "guardian_id": test_user["id"],  # Track the guardian relationship in the fixture return
    }


@pytest.fixture
def minor_portfolio(db_session, test_minor) -> Dict[str, Any]:
    """Create a portfolio for the minor user."""
    portfolio = Portfolio(
        user_id=test_minor["id"],
        owner_id=test_minor["id"],
        name="Minor Portfolio",
        description="Portfolio for minor user",
        cash_balance=Decimal("10000.00"),
        total_value=Decimal("10000.00"),
        portfolio_type=PortfolioType.PAPER,
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "name": portfolio.name,
        "cash_balance": float(portfolio.cash_balance),
    }


@pytest.fixture
def minor_client(client, test_minor) -> TestClient:
    """Create a test client for the minor user."""
    access_token = create_access_token(data={"sub": test_minor["email"]})
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client

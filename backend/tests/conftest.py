import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base, get_db
from app.main import app


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

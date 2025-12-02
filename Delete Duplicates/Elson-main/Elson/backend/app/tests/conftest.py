import os
import pytest
from typing import Dict, Generator, Any, List
from datetime import datetime, date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.account import Account, AccountType
from app.models.portfolio import Portfolio
from app.models.trade import Trade, TradeStatus, OrderType, OrderSide
from app.core.security import get_password_hash
from app.core.auth import create_access_token


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db() -> Generator:
    """
    Fixture for the database session that is used in tests.
    Creates tables, yields a session, and drops tables after tests.
    """
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after tests
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db: Session) -> Generator:
    """
    Fixture for the FastAPI test client with a db session dependency override.
    """
    def override_get_db() -> Generator:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db: Session) -> Dict[str, Any]:
    """
    Fixture that creates a test user and returns user data.
    """
    user_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role": UserRole.ADULT,
    }
    
    hashed_password = get_password_hash(user_data["password"])
    db_user = User(
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        hashed_password=hashed_password,
        role=user_data["role"],
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Add id to user_data
    user_data["id"] = db_user.id
    return user_data


@pytest.fixture
def token(test_user: Dict[str, Any]) -> str:
    """
    Fixture that creates a JWT token for the test user.
    """
    return create_access_token(
        subject=test_user["email"]
    )


@pytest.fixture
def authorized_client(client: TestClient, token: str) -> TestClient:
    """
    Fixture for an authorized test client with the JWT token in headers.
    """
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}",
    }
    return client


@pytest.fixture
def test_superuser(db: Session) -> Dict[str, Any]:
    """
    Fixture that creates a test superuser and returns user data.
    """
    user_data = {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "adminpass123",
        "role": UserRole.ADULT,
    }
    
    hashed_password = get_password_hash(user_data["password"])
    db_user = User(
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        hashed_password=hashed_password,
        role=user_data["role"],
        is_active=True,
        is_superuser=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Add id to user_data
    user_data["id"] = db_user.id
    return user_data


@pytest.fixture
def superuser_token(test_superuser: Dict[str, Any]) -> str:
    """
    Fixture that creates a JWT token for the test superuser.
    """
    return create_access_token(
        subject=test_superuser["email"]
    )


@pytest.fixture
def superuser_client(client: TestClient, superuser_token: str) -> TestClient:
    """
    Fixture for an authorized test client with superuser token in headers.
    """
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {superuser_token}",
    }
    return client


@pytest.fixture
def test_minor(db: Session, test_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fixture that creates a test minor user with an associated custodial account.
    Also sets up the guardian relationship.
    """
    # Calculate a valid birthdate for a minor (17 years old)
    minor_birthdate = date.today() - timedelta(days=17*365)
    
    minor_data = {
        "email": "minor@example.com",
        "first_name": "Minor",
        "last_name": "User",
        "password": "minorpass123",
        "role": UserRole.MINOR,
        "birthdate": minor_birthdate,
    }
    
    hashed_password = get_password_hash(minor_data["password"])
    db_minor = User(
        email=minor_data["email"],
        first_name=minor_data["first_name"],
        last_name=minor_data["last_name"],
        hashed_password=hashed_password,
        role=minor_data["role"],
        birthdate=minor_data["birthdate"],
        is_active=True,
    )
    db.add(db_minor)
    db.commit()
    db.refresh(db_minor)
    
    # Add id to minor_data
    minor_data["id"] = db_minor.id
    
    # Create custodial account linking the minor to the guardian
    custodial_account = Account(
        user_id=db_minor.id,
        guardian_id=test_user["id"],
        account_type=AccountType.CUSTODIAL,
        account_number=f"CUST-{db_minor.id}-{datetime.utcnow().strftime('%Y%m%d')}",
        institution="Elson Wealth"
    )
    
    db.add(custodial_account)
    db.commit()
    db.refresh(custodial_account)
    
    # Add account info to minor_data
    minor_data["account_id"] = custodial_account.id
    minor_data["guardian_id"] = test_user["id"]
    
    return minor_data


@pytest.fixture
def minor_token(test_minor: Dict[str, Any]) -> str:
    """
    Fixture that creates a JWT token for the test minor.
    """
    return create_access_token(
        subject=test_minor["email"]
    )


@pytest.fixture
def minor_client(client: TestClient, minor_token: str) -> TestClient:
    """
    Fixture for an authorized test client with the minor's JWT token in headers.
    """
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {minor_token}",
    }
    return client


@pytest.fixture
def test_portfolio(db: Session, test_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fixture that creates a test portfolio for the test user.
    """
    portfolio_data = {
        "name": "Test Portfolio",
        "description": "A test portfolio",
        "cash_balance": 10000.00,
        "total_value": 10000.00,
    }
    
    db_portfolio = Portfolio(
        user_id=test_user["id"],
        name=portfolio_data["name"],
        description=portfolio_data["description"],
        cash_balance=portfolio_data["cash_balance"],
        total_value=portfolio_data["total_value"],
    )
    
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    
    # Add id to portfolio_data
    portfolio_data["id"] = db_portfolio.id
    portfolio_data["user_id"] = test_user["id"]
    
    return portfolio_data


@pytest.fixture
def minor_portfolio(db: Session, test_minor: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fixture that creates a test portfolio for the minor user.
    """
    portfolio_data = {
        "name": "Minor Portfolio",
        "description": "A minor's test portfolio",
        "cash_balance": 1000.00,
        "total_value": 1000.00,
    }
    
    db_portfolio = Portfolio(
        user_id=test_minor["id"],
        name=portfolio_data["name"],
        description=portfolio_data["description"],
        cash_balance=portfolio_data["cash_balance"],
        total_value=portfolio_data["total_value"],
    )
    
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    
    # Add id to portfolio_data
    portfolio_data["id"] = db_portfolio.id
    portfolio_data["user_id"] = test_minor["id"]
    
    return portfolio_data


@pytest.fixture
def pending_minor_trades(db: Session, test_minor: Dict[str, Any], minor_portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fixture that creates a set of pending trades for the minor that require guardian approval.
    """
    trades = []
    
    # Create 3 trades with pending_approval status
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for i, symbol in enumerate(symbols):
        trade_data = {
            "symbol": symbol,
            "quantity": 1.0 + i,
            "price": 100.0 * (i + 1),
            "trade_type": "buy" if i % 2 == 0 else "sell",
            "status": TradeStatus.PENDING_APPROVAL,
        }
        
        db_trade = Trade(
            user_id=test_minor["id"],
            portfolio_id=minor_portfolio["id"],
            symbol=trade_data["symbol"],
            quantity=trade_data["quantity"],
            price=trade_data["price"],
            trade_type=trade_data["trade_type"],
            order_type=OrderType.MARKET,
            status=trade_data["status"],
            created_at=datetime.utcnow(),
        )
        
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)
        
        # Add id to trade_data
        trade_data["id"] = db_trade.id
        trade_data["user_id"] = test_minor["id"]
        trade_data["portfolio_id"] = minor_portfolio["id"]
        
        trades.append(trade_data)
    
    return trades
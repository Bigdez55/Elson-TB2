"""
Test database initialization and model relationships.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User, UserRole, SubscriptionPlan
from app.models.portfolio import Portfolio, Position
from app.models.account import Account, AccountType, RecurringInvestment, RecurringFrequency

# Create in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)
    
def test_user_creation(db_session):
    """Test that users can be created in the database."""
    # Create a test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.ADULT
    )
    db_session.add(user)
    db_session.commit()
    
    # Query the user
    db_user = db_session.query(User).filter(User.email == "test@example.com").first()
    
    # Verify properties
    assert db_user is not None
    assert db_user.email == "test@example.com"
    assert db_user.first_name == "Test"
    assert db_user.last_name == "User"
    assert db_user.role == UserRole.ADULT
    assert db_user.is_adult is True

def test_portfolio_creation(db_session):
    """Test portfolio creation and relationship with user."""
    # Create a user
    user = User(
        email="portfolio_test@example.com",
        hashed_password="hashed_password",
        role=UserRole.ADULT
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a portfolio
    portfolio = Portfolio(
        user_id=user.id,
        total_value=1000.0,
        cash_balance=500.0,
        invested_amount=500.0,
        risk_profile="moderate"
    )
    db_session.add(portfolio)
    db_session.commit()
    
    # Query the portfolio
    db_portfolio = db_session.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    
    # Verify properties
    assert db_portfolio is not None
    assert db_portfolio.total_value == 1000.0
    assert db_portfolio.cash_balance == 500.0
    assert db_portfolio.invested_amount == 500.0
    assert db_portfolio.risk_profile == "moderate"
    
    # Verify relationship
    assert db_portfolio.user_id == user.id
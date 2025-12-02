from sqlalchemy.orm import Session
import logging
from typing import Dict, Optional

from ..core.config import settings
from ..core.auth import get_password_hash
from ..models.user import User
from ..models.portfolio import Portfolio

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """Initialize the database with required data"""
    try:
        # Create superuser if it doesn't exist
        create_superuser(db)
        
        # Update existing position data with fractional share support
        update_position_model(db)
        
        # Additional initialization can be added here
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
        
def update_position_model(db: Session) -> None:
    """Update position model with fractional share support.
    
    This is a helper for transitioning to the new position model with fractional support.
    """
    try:
        from sqlalchemy import inspect
        from sqlalchemy.sql import text
        from ..models.portfolio import Position
        
        # Check if columns already exist
        inspector = inspect(db.get_bind())
        
        # Get existing columns
        columns = [col['name'] for col in inspector.get_columns('positions')]
        
        # Add columns that don't exist
        if 'is_fractional' not in columns:
            logger.info("Adding is_fractional column to positions table")
            db.execute(text(
                "ALTER TABLE positions ADD COLUMN is_fractional BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        
        if 'cost_basis' not in columns:
            logger.info("Adding cost_basis column to positions table")
            db.execute(text(
                "ALTER TABLE positions ADD COLUMN cost_basis NUMERIC(16,2)"
            ))
            
        if 'market_value' not in columns:
            logger.info("Adding market_value column to positions table")
            db.execute(text(
                "ALTER TABLE positions ADD COLUMN market_value NUMERIC(16,2)"
            ))
            
        if 'minimum_investment' not in columns:
            logger.info("Adding minimum_investment column to positions table")
            db.execute(text(
                "ALTER TABLE positions ADD COLUMN minimum_investment NUMERIC(10,2)"
            ))
            
        if 'last_trade_date' not in columns:
            logger.info("Adding last_trade_date column to positions table")
            db.execute(text(
                "ALTER TABLE positions ADD COLUMN last_trade_date TIMESTAMP WITHOUT TIME ZONE"
            ))
        
        # Check if quantity and price columns need to be converted to Numeric
        column_types = {col['name']: col['type'] for col in inspector.get_columns('positions')}
        
        # Convert columns to Numeric if needed
        type_conversions = {
            'quantity': 'NUMERIC(16,8)',
            'average_price': 'NUMERIC(16,8)',
            'current_price': 'NUMERIC(16,8)',
            'unrealized_pl': 'NUMERIC(16,2)'
        }
        
        for column, new_type in type_conversions.items():
            if column in columns and not str(column_types[column]).startswith('NUMERIC'):
                logger.info(f"Converting {column} to {new_type}")
                db.execute(text(f"ALTER TABLE positions ALTER COLUMN {column} TYPE {new_type} USING {column}::{new_type}"))
        
        # Commit changes
        db.commit()
        logger.info("Successfully updated positions table")
        
    except Exception as e:
        logger.error(f"Error updating position model: {str(e)}")
        db.rollback()

def create_superuser(db: Session) -> Optional[Dict]:
    """Create a superuser if it doesn't exist"""
    try:
        superuser = db.query(User).filter(
            User.email == settings.FIRST_SUPERUSER_EMAIL
        ).first()
        
        if not superuser:
            superuser = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                username=settings.FIRST_SUPERUSER_USERNAME,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="System Administrator",
                is_superuser=True
            )
            db.add(superuser)
            db.commit()
            db.refresh(superuser)
            
            # Create portfolio for superuser
            portfolio = Portfolio(
                user_id=superuser.id,
                total_value=0,
                cash_balance=0,
                invested_amount=0
            )
            db.add(portfolio)
            db.commit()
            
            logger.info(f"Superuser created: {superuser.email}")
            return {
                "email": superuser.email,
                "username": superuser.username
            }
            
        return None
        
    except Exception as e:
        logger.error(f"Error creating superuser: {str(e)}")
        db.rollback()
        raise

def verify_db(db: Session) -> bool:
    """Verify database setup and connectivity"""
    try:
        # Try to execute a simple query using SQLAlchemy text to ensure compatibility
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            logger.info("Database verification successful")
            return True
        else:
            logger.error(f"Database verification failed: unexpected result {result}")
            return False
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False

def initialize_seed_data() -> None:
    """
    Initialize the database with seed data for testing and development.
    
    This function is used when starting with a fresh database to populate it
    with enough sample data to be useful for testing and development.
    """
    from .database import get_db_context
    
    logger.info("Initializing seed data")
    
    try:
        with get_db_context() as db:
            # First, create superuser
            superuser_info = create_superuser(db)
            if superuser_info:
                logger.info(f"Created superuser: {superuser_info['email']}")
            else:
                logger.info("Superuser already exists")
            
            # Create sample users if needed
            create_sample_users(db)
            
            # Create sample portfolios and positions
            create_sample_portfolios(db)
            
            # Create sample trades
            create_sample_trades(db)
            
            # Create sample education data
            create_sample_education_data(db)
            
            logger.info("Seed data initialization complete")
            
    except Exception as e:
        logger.error(f"Error initializing seed data: {str(e)}")
        raise
    
def create_sample_users(db: Session) -> None:
    """Create sample users for testing"""
    from ..models.user import User
    from ..core.auth import get_password_hash
    
    sample_users = [
        {
            "email": "user@example.com",
            "username": "regular_user",
            "password": "samplepass123",
            "full_name": "Regular User",
            "is_superuser": False
        },
        {
            "email": "premium@example.com",
            "username": "premium_user",
            "password": "premiumpass123",
            "full_name": "Premium User",
            "is_superuser": False
        },
        {
            "email": "parent@example.com",
            "username": "parent_user",
            "password": "parentpass123",
            "full_name": "Parent User",
            "is_superuser": False
        }
    ]
    
    for user_data in sample_users:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            new_user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                is_superuser=user_data["is_superuser"]
            )
            db.add(new_user)
            logger.info(f"Created sample user: {new_user.email}")
    
    db.commit()

def create_sample_portfolios(db: Session) -> None:
    """Create sample portfolios and positions"""
    from ..models.user import User
    from ..models.portfolio import Portfolio, Position
    import random
    from datetime import datetime, timedelta
    
    # Define sample stocks and their prices
    sample_stocks = [
        {"symbol": "AAPL", "price": 175.00, "name": "Apple Inc."},
        {"symbol": "MSFT", "price": 380.00, "name": "Microsoft Corporation"},
        {"symbol": "AMZN", "price": 165.00, "name": "Amazon.com, Inc."},
        {"symbol": "GOOGL", "price": 142.00, "name": "Alphabet Inc."},
        {"symbol": "META", "price": 480.00, "name": "Meta Platforms, Inc."},
        {"symbol": "TSLA", "price": 177.00, "name": "Tesla, Inc."},
        {"symbol": "BRK.B", "price": 408.00, "name": "Berkshire Hathaway Inc."},
        {"symbol": "V", "price": 275.00, "name": "Visa Inc."},
        {"symbol": "JPM", "price": 185.00, "name": "JPMorgan Chase & Co."},
        {"symbol": "JNJ", "price": 150.00, "name": "Johnson & Johnson"}
    ]
    
    # Get users
    users = db.query(User).all()
    
    for user in users:
        # Check if user already has a portfolio
        existing_portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        
        if not existing_portfolio:
            # Create a portfolio with random cash balance
            cash_balance = random.randint(5000, 50000)
            portfolio = Portfolio(
                user_id=user.id,
                name=f"{user.username}'s Portfolio",
                description="Sample portfolio for testing",
                cash_balance=cash_balance,
                total_value=cash_balance,  # Will be updated after adding positions
                invested_amount=0  # Will be updated after adding positions
            )
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
            
            # Create 3-7 random positions
            num_positions = random.randint(3, 7)
            invested_amount = 0
            
            for _ in range(num_positions):
                # Select a random stock
                stock = random.choice(sample_stocks)
                
                # Create a position with random quantity
                is_fractional = random.choice([True, False])
                if is_fractional:
                    quantity = round(random.uniform(0.1, 10), 8)
                else:
                    quantity = random.randint(1, 20)
                    
                average_price = round(stock["price"] * (1 + random.uniform(-0.05, 0.05)), 2)
                current_price = round(stock["price"], 2)
                market_value = round(quantity * current_price, 2)
                cost_basis = round(quantity * average_price, 2)
                unrealized_pl = round(market_value - cost_basis, 2)
                
                position = Position(
                    portfolio_id=portfolio.id,
                    symbol=stock["symbol"],
                    company_name=stock["name"],
                    quantity=quantity,
                    average_price=average_price,
                    current_price=current_price,
                    market_value=market_value,
                    cost_basis=cost_basis,
                    unrealized_pl=unrealized_pl,
                    is_fractional=is_fractional,
                    last_trade_date=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                db.add(position)
                invested_amount += cost_basis
            
            # Update portfolio values
            portfolio.invested_amount = invested_amount
            portfolio.total_value = portfolio.cash_balance + invested_amount
            db.commit()
            
            logger.info(f"Created portfolio for user {user.email} with {num_positions} positions")
            
def create_sample_trades(db: Session) -> None:
    """Create sample trade history"""
    # Implement if needed
    pass
    
def create_sample_education_data(db: Session) -> None:
    """Create sample education content"""
    # Implement if needed
    pass
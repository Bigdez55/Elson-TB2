"""
Tests for database models to verify the fixes we've made
"""
from decimal import Decimal
import unittest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

from app.models.base import Base
from app.models.portfolio import Position

# Use direct SQL manipulation to test numeric types without relation issues
class TestDecimalTypes(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create a session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Insert a test portfolio using raw SQL
        self.session.execute(
            text("INSERT INTO portfolios (id, user_id, total_value, cash_balance, invested_amount) "
                 "VALUES (1, 1, 1000.0, 500.0, 500.0)")
        )
        self.session.commit()
        
    def tearDown(self):
        self.session.close()
        
    def test_position_decimal_types(self):
        """Test that the Position model works with Numeric (Decimal) fields"""
        # Create a position with decimal values
        position = Position(
            portfolio_id=1,
            symbol="AAPL",
            quantity=Decimal("1.5"),
            average_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
            is_fractional=True
        )
        self.session.add(position)
        self.session.commit()
        
        # Retrieve the position and verify types
        retrieved_position = self.session.query(Position).filter_by(symbol="AAPL").first()
        assert retrieved_position is not None
        assert isinstance(retrieved_position.quantity, Decimal)
        assert retrieved_position.quantity == Decimal("1.5")
        assert isinstance(retrieved_position.average_price, Decimal)
        assert retrieved_position.average_price == Decimal("150.00")
        assert isinstance(retrieved_position.current_price, Decimal)
        assert retrieved_position.current_price == Decimal("160.00")
        assert retrieved_position.is_fractional is True
        
        # Test decimal math operations
        retrieved_position.update_market_value()
        assert isinstance(retrieved_position.market_value, Decimal)
        assert retrieved_position.market_value == Decimal("240.00")  # 1.5 * 160.00
        
        # Test functions with decimals
        retrieved_position.update_cost_basis()
        assert isinstance(retrieved_position.cost_basis, Decimal)
        assert retrieved_position.cost_basis == Decimal("225.00")  # 1.5 * 150.00
        
        # Test unrealized P&L calculation with decimals
        retrieved_position.update_unrealized_pl()
        assert isinstance(retrieved_position.unrealized_pl, Decimal)
        assert retrieved_position.unrealized_pl == Decimal("15.00")  # 240.00 - 225.00
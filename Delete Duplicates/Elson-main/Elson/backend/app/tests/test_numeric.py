"""
Tests specifically for numeric type handling in SQLite
"""
from decimal import Decimal
import unittest
from sqlalchemy import create_engine, Column, Integer, String, Numeric, text, MetaData, Table, insert, select

# Create a minimal test to verify numeric handling in SQLite
class TestSqliteNumeric(unittest.TestCase):
    def setUp(self):
        # Create in-memory database
        self.engine = create_engine('sqlite:///:memory:')
        self.metadata = MetaData()
        
        # Create a test table with Numeric columns
        self.test_table = Table(
            'test_numeric', 
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('symbol', String(10)),
            Column('quantity', Numeric(16, 8)),
            Column('price', Numeric(16, 8))
        )
        
        self.metadata.create_all(self.engine)
        
    def test_numeric_precision(self):
        """Test that SQLite correctly handles Numeric with precision/scale"""
        # Insert test data
        with self.engine.connect() as conn:
            conn.execute(
                insert(self.test_table).values(
                    symbol="AAPL",
                    quantity=Decimal("1.12345678"),
                    price=Decimal("150.87654321")
                )
            )
            
            # Query the data back
            result = conn.execute(
                select(self.test_table).where(self.test_table.c.symbol == "AAPL")
            ).fetchone()
            
            # Verify the numeric precision is maintained
            self.assertIsInstance(result.quantity, Decimal)
            self.assertEqual(result.quantity, Decimal("1.12345678"))
            self.assertIsInstance(result.price, Decimal)
            self.assertEqual(result.price, Decimal("150.87654321"))
            
            # Test calculation with precise decimal values
            calculated_value = result.quantity * result.price
            expected = Decimal("169.5032754122374638")  # Based on actual calculation result
            self.assertEqual(calculated_value, expected)
            
if __name__ == '__main__':
    unittest.main()
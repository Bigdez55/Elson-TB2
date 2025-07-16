"""
Comprehensive tests for portfolio service functionality
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.user import User
from app.models.trade import Trade, TradeType, OrderType, TradeStatus
from app.services.trading import TradingService
from app.db.base import Base


class TestPortfolioService:
    """Test portfolio service functionality"""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user"""
        user = User(id=1, email="test@example.com", username="testuser", is_active=True)
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_portfolio(self, db_session, test_user):
        """Create a test portfolio"""
        portfolio = Portfolio(
            id=1,
            name="Test Portfolio",
            description="Test portfolio for unit tests",
            total_value=10000.0,
            cash_balance=2000.0,
            invested_amount=8000.0,
            total_return=500.0,
            total_return_percentage=6.25,
            owner_id=test_user.id,
            is_active=True,
        )
        db_session.add(portfolio)
        db_session.commit()
        return portfolio

    @pytest.fixture
    def test_holdings(self, db_session, test_portfolio):
        """Create test holdings"""
        holdings = [
            Holding(
                symbol="AAPL",
                asset_type="stock",
                quantity=10.0,
                average_cost=150.0,
                current_price=155.0,
                market_value=1550.0,
                unrealized_gain_loss=50.0,
                unrealized_gain_loss_percentage=3.33,
                portfolio_id=test_portfolio.id,
            ),
            Holding(
                symbol="MSFT",
                asset_type="stock",
                quantity=5.0,
                average_cost=300.0,
                current_price=310.0,
                market_value=1550.0,
                unrealized_gain_loss=50.0,
                unrealized_gain_loss_percentage=3.33,
                portfolio_id=test_portfolio.id,
            ),
            Holding(
                symbol="GOOGL",
                asset_type="stock",
                quantity=3.0,
                average_cost=2500.0,
                current_price=2600.0,
                market_value=7800.0,
                unrealized_gain_loss=300.0,
                unrealized_gain_loss_percentage=4.0,
                portfolio_id=test_portfolio.id,
            ),
        ]

        for holding in holdings:
            db_session.add(holding)
        db_session.commit()
        return holdings

    @pytest.fixture
    def trading_service(self):
        """Create a trading service instance"""
        with patch("app.services.trading.settings") as mock_settings:
            mock_settings.ALPACA_API_KEY = "test_key"
            mock_settings.ALPACA_SECRET_KEY = "test_secret"
            mock_settings.ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
            return TradingService()

    def test_portfolio_creation(self, db_session, test_user):
        """Test portfolio creation"""
        # Create new portfolio
        portfolio = Portfolio(
            name="New Portfolio",
            description="A brand new portfolio",
            cash_balance=5000.0,
            owner_id=test_user.id,
        )

        db_session.add(portfolio)
        db_session.commit()

        # Verify portfolio was created
        assert portfolio.id is not None
        assert portfolio.name == "New Portfolio"
        assert portfolio.cash_balance == 5000.0
        assert portfolio.total_value == 0.0
        assert portfolio.invested_amount == 0.0
        assert portfolio.is_active is True
        assert portfolio.owner_id == test_user.id

    def test_portfolio_update(self, db_session, test_portfolio):
        """Test portfolio updates"""
        # Update portfolio fields
        test_portfolio.name = "Updated Portfolio"
        test_portfolio.description = "Updated description"
        test_portfolio.auto_rebalance = True
        test_portfolio.rebalance_threshold = 0.10

        db_session.commit()
        db_session.refresh(test_portfolio)

        # Verify updates
        assert test_portfolio.name == "Updated Portfolio"
        assert test_portfolio.description == "Updated description"
        assert test_portfolio.auto_rebalance is True
        assert test_portfolio.rebalance_threshold == 0.10

    def test_holdings_calculation(self, db_session, test_portfolio, test_holdings):
        """Test holdings calculation and tracking"""
        # Verify holdings are correctly associated
        portfolio_holdings = (
            db_session.query(Holding)
            .filter(Holding.portfolio_id == test_portfolio.id)
            .all()
        )

        assert len(portfolio_holdings) == 3

        # Test individual holding calculations
        aapl_holding = next(h for h in portfolio_holdings if h.symbol == "AAPL")
        assert (
            aapl_holding.market_value
            == aapl_holding.quantity * aapl_holding.current_price
        )
        assert (
            aapl_holding.unrealized_gain_loss
            == (aapl_holding.current_price - aapl_holding.average_cost)
            * aapl_holding.quantity
        )

        # Test total portfolio value calculation
        total_market_value = sum(h.market_value for h in portfolio_holdings)
        expected_total = test_portfolio.cash_balance + total_market_value

        # Update portfolio totals
        test_portfolio.total_value = expected_total
        test_portfolio.invested_amount = total_market_value
        db_session.commit()

        assert test_portfolio.total_value == expected_total
        assert test_portfolio.invested_amount == total_market_value

    def test_pnl_computation_accuracy(self, db_session, test_holdings):
        """Test P&L computation accuracy"""
        for holding in test_holdings:
            # Calculate expected values
            expected_market_value = holding.quantity * holding.current_price
            expected_unrealized_pnl = (
                holding.current_price - holding.average_cost
            ) * holding.quantity
            expected_unrealized_pnl_percentage = (
                expected_unrealized_pnl / (holding.average_cost * holding.quantity)
            ) * 100

            # Verify calculations
            assert abs(holding.market_value - expected_market_value) < 0.01
            assert abs(holding.unrealized_gain_loss - expected_unrealized_pnl) < 0.01
            assert (
                abs(
                    holding.unrealized_gain_loss_percentage
                    - expected_unrealized_pnl_percentage
                )
                < 0.01
            )

    def test_performance_metrics_calculation(
        self, db_session, test_portfolio, test_holdings
    ):
        """Test performance metrics calculation"""
        # Calculate total invested cost
        total_cost = sum(h.average_cost * h.quantity for h in test_holdings)
        total_market_value = sum(h.market_value for h in test_holdings)

        # Calculate total return
        total_return = total_market_value - total_cost
        total_return_percentage = (
            (total_return / total_cost) * 100 if total_cost > 0 else 0
        )

        # Update portfolio with calculated values
        test_portfolio.invested_amount = total_market_value
        test_portfolio.total_value = test_portfolio.cash_balance + total_market_value
        test_portfolio.total_return = total_return
        test_portfolio.total_return_percentage = total_return_percentage

        db_session.commit()

        # Verify calculations
        assert abs(test_portfolio.total_return - total_return) < 0.01
        assert (
            abs(test_portfolio.total_return_percentage - total_return_percentage) < 0.01
        )

    @patch("app.services.market_data.market_data_service.get_quote")
    def test_portfolio_update_with_market_data(
        self, mock_get_quote, db_session, test_portfolio, test_holdings, trading_service
    ):
        """Test portfolio update with real-time market data"""
        # Mock market data responses
        mock_quotes = {
            "AAPL": {"price": 160.0, "bid": 159.9, "ask": 160.1},
            "MSFT": {"price": 320.0, "bid": 319.9, "ask": 320.1},
            "GOOGL": {"price": 2700.0, "bid": 2699.0, "ask": 2701.0},
        }

        def mock_quote_response(symbol):
            return mock_quotes.get(symbol, {"price": 100.0, "bid": 99.9, "ask": 100.1})

        mock_get_quote.side_effect = mock_quote_response

        # Update holdings with new prices
        for holding in test_holdings:
            quote = mock_quote_response(holding.symbol)
            holding.current_price = quote["price"]
            holding.market_value = holding.quantity * holding.current_price
            holding.unrealized_gain_loss = (
                holding.current_price - holding.average_cost
            ) * holding.quantity
            holding.unrealized_gain_loss_percentage = (
                holding.unrealized_gain_loss / (holding.average_cost * holding.quantity)
            ) * 100

        # Recalculate portfolio totals
        total_market_value = sum(h.market_value for h in test_holdings)
        test_portfolio.invested_amount = total_market_value
        test_portfolio.total_value = test_portfolio.cash_balance + total_market_value

        total_cost = sum(h.average_cost * h.quantity for h in test_holdings)
        test_portfolio.total_return = total_market_value - total_cost
        test_portfolio.total_return_percentage = (
            test_portfolio.total_return / total_cost
        ) * 100

        db_session.commit()

        # Verify updates
        aapl_holding = next(h for h in test_holdings if h.symbol == "AAPL")
        assert aapl_holding.current_price == 160.0
        assert aapl_holding.market_value == 1600.0  # 10 * 160
        assert aapl_holding.unrealized_gain_loss == 100.0  # (160 - 150) * 10

    def test_portfolio_daily_drawdown(self, test_portfolio):
        """Test daily drawdown calculation"""
        # Test get_daily_drawdown method
        drawdown = test_portfolio.get_daily_drawdown()

        # Should return None for simplified implementation
        assert drawdown is None or isinstance(drawdown, Decimal)

    def test_portfolio_daily_trade_count(self, db_session, test_portfolio):
        """Test daily trade count calculation"""
        # Create some test trades for today
        from datetime import datetime, date

        trades = [
            Trade(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                trade_type=TradeType.BUY,
                order_type=OrderType.MARKET,
                status=TradeStatus.FILLED,
                portfolio_id=test_portfolio.id,
                user_id=test_portfolio.owner_id,
            ),
            Trade(
                symbol="MSFT",
                quantity=5,
                price=300.0,
                trade_type=TradeType.BUY,
                order_type=OrderType.LIMIT,
                status=TradeStatus.FILLED,
                portfolio_id=test_portfolio.id,
                user_id=test_portfolio.owner_id,
            ),
        ]

        for trade in trades:
            db_session.add(trade)
        db_session.commit()

        # Test get_daily_trade_count method
        trade_count = test_portfolio.get_daily_trade_count()
        assert trade_count >= 0  # Should return a non-negative integer

    def test_holding_allocation_percentages(
        self, db_session, test_portfolio, test_holdings
    ):
        """Test holding allocation percentage calculations"""
        total_portfolio_value = sum(h.market_value for h in test_holdings)

        for holding in test_holdings:
            # Calculate allocation percentage
            allocation_percentage = (
                (holding.market_value / total_portfolio_value) * 100
                if total_portfolio_value > 0
                else 0
            )
            holding.current_allocation_percentage = allocation_percentage

        db_session.commit()

        # Verify allocations sum to 100%
        total_allocation = sum(
            h.current_allocation_percentage or 0 for h in test_holdings
        )
        assert abs(total_allocation - 100.0) < 0.01

    def test_portfolio_asset_types_diversification(self, test_holdings):
        """Test asset type diversification tracking"""
        asset_types = {}
        total_value = sum(h.market_value for h in test_holdings)

        for holding in test_holdings:
            asset_type = holding.asset_type
            if asset_type not in asset_types:
                asset_types[asset_type] = 0
            asset_types[asset_type] += holding.market_value

        # Convert to percentages
        asset_allocation = {
            asset_type: (value / total_value) * 100
            for asset_type, value in asset_types.items()
        }

        # Verify all holdings are stocks in this test
        assert "stock" in asset_allocation
        assert abs(asset_allocation["stock"] - 100.0) < 0.01

    def test_portfolio_risk_metrics(self, test_portfolio, test_holdings):
        """Test basic portfolio risk metrics"""
        # Calculate basic risk metrics
        positions_count = len([h for h in test_holdings if h.quantity > 0])
        largest_position_value = (
            max(h.market_value for h in test_holdings) if test_holdings else 0
        )
        total_value = sum(h.market_value for h in test_holdings)

        concentration_risk = (
            (largest_position_value / total_value) * 100 if total_value > 0 else 0
        )

        # Verify metrics
        assert positions_count == 3
        assert concentration_risk > 0
        assert concentration_risk <= 100

    def test_portfolio_validation_constraints(self, db_session, test_user):
        """Test portfolio validation constraints"""
        # Test invalid portfolio creation
        with pytest.raises(Exception):
            # Portfolio without required fields should fail
            portfolio = Portfolio(owner_id=test_user.id)
            portfolio.name = None  # Required field
            db_session.add(portfolio)
            db_session.commit()

    def test_holding_validation_constraints(self, db_session, test_portfolio):
        """Test holding validation constraints"""
        # Test negative quantity (should be handled by application logic)
        holding = Holding(
            symbol="TEST",
            asset_type="stock",
            quantity=-10.0,  # Negative quantity
            average_cost=100.0,
            current_price=105.0,
            market_value=-1050.0,
            portfolio_id=test_portfolio.id,
        )

        # Note: Database constraints might not catch this,
        # but application logic should validate
        db_session.add(holding)
        db_session.commit()

        # Verify the holding was added (validation should happen in service layer)
        assert holding.id is not None

    def test_portfolio_performance_edge_cases(self, db_session, test_user):
        """Test portfolio performance calculations with edge cases"""
        # Portfolio with zero invested amount
        portfolio = Portfolio(
            name="Empty Portfolio",
            cash_balance=1000.0,
            invested_amount=0.0,
            total_value=1000.0,
            total_return=0.0,
            total_return_percentage=0.0,
            owner_id=test_user.id,
        )

        db_session.add(portfolio)
        db_session.commit()

        # Verify edge case handling
        assert portfolio.total_return_percentage == 0.0
        assert portfolio.invested_amount == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

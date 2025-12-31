"""Integration tests for paper trading simulator.

This test suite verifies the integration between the paper trading components,
including the broker abstraction, market simulation, and trade execution.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.trade import InvestmentType, OrderSide, OrderType, Trade, TradeStatus
from app.services.broker.factory import BrokerType, get_broker
from app.services.broker.paper import PaperBroker
from app.services.market_simulation import MarketSimulationService
from app.services.paper_trading import PaperTradingService


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock = MagicMock(spec=Session)

    # Mock portfolio query
    portfolio = MagicMock(spec=Portfolio)
    portfolio.id = 1
    portfolio.cash_balance = Decimal("10000.00")
    portfolio.total_value = Decimal("10000.00")
    portfolio.created_at = datetime.utcnow()

    # Set up the query chain to return the portfolio
    mock.query.return_value.filter.return_value.first.return_value = portfolio

    return mock


@pytest.fixture
def market_simulation():
    """Create a market simulation service."""
    return MarketSimulationService()


@pytest.fixture
def paper_trading(market_simulation):
    """Create a paper trading service."""
    return PaperTradingService(market_simulation)


@pytest.fixture
def paper_broker(mock_db_session):
    """Create a paper broker instance."""
    return PaperBroker(mock_db_session)


@pytest.fixture
def sample_trade():
    """Create a sample trade for testing."""
    return Trade(
        id=1,
        user_id=1,
        portfolio_id=1,
        symbol="AAPL",
        quantity=Decimal("10"),
        price=Decimal("150.00"),
        trade_type="buy",
        order_type=OrderType.MARKET,
        status=TradeStatus.PENDING,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def dollar_based_trade():
    """Create a sample dollar-based trade for testing."""
    return Trade(
        id=2,
        user_id=1,
        portfolio_id=1,
        symbol="AAPL",
        quantity=None,
        price=None,
        investment_amount=Decimal("1000.00"),
        investment_type=InvestmentType.DOLLAR_BASED,
        trade_type="buy",
        order_type=OrderType.MARKET,
        status=TradeStatus.PENDING,
        created_at=datetime.utcnow(),
    )


class TestPaperTrading:
    """Tests for paper trading functionality."""

    def test_market_simulation_price_generation(self, market_simulation):
        """Test that market simulation generates prices correctly."""
        # Get price for a symbol
        price = market_simulation.get_current_price("AAPL")

        # Check that price is a reasonable number
        assert price > 0
        assert price < 1000  # Reasonable upper bound for most stocks

        # Check that bid-ask works
        bid, ask = market_simulation.get_bid_ask("AAPL")
        assert bid < ask
        assert bid > 0

        # Price should be between bid and ask
        assert bid <= price <= ask

        # Test price history
        history = market_simulation.get_price_history("AAPL", days=10)
        assert len(history) == 10
        assert "open" in history[0]
        assert "high" in history[0]
        assert "low" in history[0]
        assert "close" in history[0]
        assert "volume" in history[0]

        # Test market depth
        depth = market_simulation.get_market_depth("AAPL")
        assert "bids" in depth
        assert "asks" in depth
        assert len(depth["bids"]) > 0
        assert len(depth["asks"]) > 0

    def test_paper_trading_execution(self, paper_trading, sample_trade):
        """Test paper trading execution."""
        # Execute the trade
        result = paper_trading.execute_paper_trade(sample_trade)

        # Check result structure
        assert "trade_id" in result
        assert "status" in result
        assert "filled_price" in result
        assert "filled_quantity" in result
        assert "commission" in result
        assert "timestamp" in result
        assert "total_amount" in result

        # Check values
        assert result["status"] == "completed"
        assert result["filled_quantity"] == 10
        assert result["filled_price"] > 0
        assert result["commission"] >= 0

    def test_dollar_based_paper_trading(self, paper_trading, dollar_based_trade):
        """Test dollar-based paper trading."""
        # Execute the trade
        result = paper_trading.execute_paper_trade(dollar_based_trade)

        # Check result structure
        assert "trade_id" in result
        assert "status" in result
        assert "filled_price" in result
        assert "filled_quantity" in result

        # Check values
        assert result["status"] == "completed"
        assert result["filled_price"] > 0

        # For a $1000 investment at ~$150 per share, should be around 6-7 shares
        expected_quantity = 1000 / result["filled_price"]
        assert abs(result["filled_quantity"] - expected_quantity) < 0.0001

        # Total amount should be close to investment amount (may have small difference due to rounding)
        assert abs(result["total_amount"] - 1000) < 10  # Allow for commission

    def test_paper_broker_integration(self, paper_broker, sample_trade):
        """Test paper broker integration."""
        # Execute trade through broker
        result = paper_broker.execute_trade(sample_trade)

        # Get the broker order ID
        broker_order_id = result["trade_id"]

        # Check trade status
        status = paper_broker.get_trade_status(broker_order_id)
        assert status["status"] == "filled"
        assert status["filled_quantity"] == 10

        # Check account info
        account_info = paper_broker.get_account_info("1")
        assert "cash_balance" in account_info
        assert "positions_value" in account_info
        assert "total_value" in account_info

        # Check positions
        positions = paper_broker.get_positions("1")
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 10

        # Execute a sell trade
        sell_trade = Trade(
            id=3,
            user_id=1,
            portfolio_id=1,
            symbol="AAPL",
            quantity=Decimal("5"),
            price=Decimal("150.00"),
            trade_type="sell",
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        paper_broker.execute_trade(sell_trade)

        # Check that position was reduced
        positions = paper_broker.get_positions("1")
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 5

        # Sell the rest
        sell_all_trade = Trade(
            id=4,
            user_id=1,
            portfolio_id=1,
            symbol="AAPL",
            quantity=Decimal("5"),
            price=Decimal("150.00"),
            trade_type="sell",
            order_type=OrderType.MARKET,
            status=TradeStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        paper_broker.execute_trade(sell_all_trade)

        # Check that position was removed
        positions = paper_broker.get_positions("1")
        assert len(positions) == 0

    def test_broker_factory(self, mock_db_session):
        """Test broker factory."""
        # Get broker using factory
        broker = get_broker(BrokerType.PAPER, mock_db_session)

        # Should get a PaperBroker instance
        assert isinstance(broker, PaperBroker)

        # Default should also be paper
        default_broker = get_broker(db=mock_db_session)
        assert isinstance(default_broker, PaperBroker)

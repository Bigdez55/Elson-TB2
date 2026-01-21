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
    from app.models.holding import Holding

    mock = MagicMock(spec=Session)

    # Mock portfolio with holdings (use float to match service expectations)
    portfolio = MagicMock(spec=Portfolio)
    portfolio.id = 1
    portfolio.user_id = 1
    portfolio.cash_balance = 10000.00
    portfolio.total_value = 10000.00
    portfolio.created_at = datetime.utcnow()
    portfolio.holdings = []  # Start with empty holdings
    portfolio.is_paper = True
    portfolio.invested_amount = 0.00

    # Create a smart query mock that returns different values based on model type
    def create_query_mock(model_class):
        filter_mock = MagicMock()

        if model_class == Portfolio:
            filter_mock.first.return_value = portfolio
        elif model_class == Holding:
            # Return None so new holding is created
            filter_mock.first.return_value = None
        else:
            filter_mock.first.return_value = None

        filter_mock.all.return_value = []
        return filter_mock

    # Set up query to handle different models
    def query_side_effect(model_class):
        query_mock = MagicMock()
        query_mock.filter.return_value = create_query_mock(model_class)
        return query_mock

    mock.query.side_effect = query_side_effect

    # Make add/commit/refresh/rollback no-ops
    mock.add = MagicMock()
    mock.commit = MagicMock()
    mock.refresh = MagicMock()
    mock.rollback = MagicMock()

    return mock


@pytest.fixture
def market_simulation():
    """Create a market simulation service."""
    return MarketSimulationService()


@pytest.fixture
def paper_trading(mock_db_session):
    """Create a paper trading service."""
    return PaperTradingService(mock_db_session)


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

    @pytest.mark.asyncio
    async def test_paper_trading_execution(self, paper_trading, sample_trade):
        """Test paper trading execution."""
        # Mock market hours to be open for testing
        with patch.object(paper_trading, '_is_market_open', return_value=True):
            # Execute the trade
            result = await paper_trading.execute_paper_trade(sample_trade)

            # Check result structure
            assert "status" in result
            assert "execution_price" in result
            assert "filled_quantity" in result
            assert "commission" in result

            # Check values - status should be "filled" for a successful market order
            assert result["status"] == "filled"
            assert result["filled_quantity"] == 10
            assert result["execution_price"] > 0
            assert result["commission"] >= 0

    @pytest.mark.asyncio
    async def test_dollar_based_paper_trading(self, paper_trading, dollar_based_trade):
        """Test dollar-based paper trading."""
        # Mock market hours to be open for testing
        with patch.object(paper_trading, '_is_market_open', return_value=True):
            # Execute the trade
            result = await paper_trading.execute_paper_trade(dollar_based_trade)

            # Check result structure
            assert "status" in result
            assert "execution_price" in result
            assert "filled_quantity" in result

            # Check values - status should be "filled" for a successful market order
            assert result["status"] == "filled"
            assert result["execution_price"] > 0

            # Dollar-based trades should fill with fractional shares
            # The quantity should be based on the investment amount and execution price
            assert result["filled_quantity"] > 0

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
        # Get broker using factory with explicit PAPER type
        broker = get_broker(BrokerType.PAPER, mock_db_session)

        # Should get a PaperBroker instance
        assert isinstance(broker, PaperBroker)

        # Verify we can also explicitly get paper broker again
        paper_broker = get_broker(BrokerType.PAPER, db=mock_db_session)
        assert isinstance(paper_broker, PaperBroker)

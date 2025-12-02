"""Integration tests for market integration service.

This module contains tests for the market integration service that connects
backend services, market data, and the trading engine.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.portfolio import Portfolio, Position
from app.models.user import User
from app.models.trade import Trade, TradeStatus
from app.services.market_integration import MarketIntegrationService, get_market_integration_service
from app.services.market_data import MarketDataService
from app.db.session import get_db

# Mock data for tests
MOCK_QUOTE = {
    "symbol": "AAPL",
    "price": 150.0,
    "change": 1.5,
    "change_percent": 1.0,
    "volume": 10000000,
    "bid": 149.95,
    "ask": 150.05,
    "timestamp": datetime.now().isoformat(),
    "source": "mock"
}

MOCK_PORTFOLIO = {
    "portfolio_id": 1,
    "user_id": 1,
    "cash": 10000.0,
    "total_value": 15000.0,
    "positions": {
        "AAPL": {
            "quantity": 10.0,
            "cost_basis": 145.0,
            "current_price": 150.0,
            "last_updated": datetime.now().isoformat()
        },
        "MSFT": {
            "quantity": 5.0,
            "cost_basis": 250.0,
            "current_price": 260.0,
            "last_updated": datetime.now().isoformat()
        }
    }
}

MOCK_RECOMMENDATION = {
    "symbol": "AAPL",
    "action": "buy",
    "quantity": 1.0,
    "price": 150.0,
    "confidence": 0.8,
    "strategy_name": "test_strategy",
    "reason": "Test recommendation"
}


# Create a mock market data service
class MockMarketDataService:
    """Mock market data service for testing."""
    
    async def get_quote(self, symbol, force_refresh=False):
        """Return mock quote data."""
        return MOCK_QUOTE
    
    async def get_batch_quotes(self, symbols, force_refresh=False):
        """Return mock batch quote data."""
        return {symbol: MOCK_QUOTE for symbol in symbols}
    
    async def get_historical_data(self, symbol, start_date, end_date=None, interval="1d", force_refresh=False):
        """Return mock historical data."""
        return {
            "symbol": symbol,
            "interval": interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else datetime.now().isoformat(),
            "data": [
                {
                    "Date": d.isoformat(),
                    "Open": 150.0,
                    "High": 152.0,
                    "Low": 148.0,
                    "Close": 151.0,
                    "Volume": 10000000
                } for d in [start_date + timedelta(days=i) for i in range(10)]
            ],
            "source": "mock"
        }
    
    async def get_market_hours(self, market="US"):
        """Return mock market hours."""
        return {
            "is_open": True,
            "next_open": None,
            "next_close": None,
            "timestamp": datetime.now().isoformat(),
            "source": "mock"
        }
    
    async def get_data_quality_metrics(self):
        """Return mock data quality metrics."""
        return {
            "request_count": 100,
            "cache_hits": 80,
            "cache_hit_ratio": 0.8,
            "source_health": {"yfinance": True},
            "consecutive_errors": {"yfinance": 0},
            "cache_size": 50,
            "using_redis": False
        }
    
    async def close(self):
        """Mock close method."""
        pass


# Mock trading engine components
class MockStrategy:
    """Mock trading strategy for testing."""
    
    def get_recommendations(self, portfolio, market_data):
        """Return mock recommendations."""
        return [MOCK_RECOMMENDATION]


@pytest.fixture
def mock_market_data_service():
    """Fixture for mock market data service."""
    return MockMarketDataService()


@pytest.fixture
def mock_db_session():
    """Fixture for mock database session."""
    db = MagicMock()
    
    # Mock user query
    user = MagicMock(id=1)
    db.query.return_value.filter.return_value.first.return_value = user
    
    # Mock portfolio query
    portfolio = MagicMock(id=1, user_id=1, cash_balance=10000.0, total_value=15000.0, risk_profile="moderate")
    db.query.return_value.filter.return_value.first.return_value = portfolio
    
    # Mock positions query
    position1 = MagicMock(id=1, portfolio_id=1, symbol="AAPL", quantity=10.0, cost_basis=145.0, current_price=150.0)
    position2 = MagicMock(id=2, portfolio_id=1, symbol="MSFT", quantity=5.0, cost_basis=250.0, current_price=260.0)
    db.query.return_value.filter.return_value.all.return_value = [position1, position2]
    
    return db


@pytest.fixture
def market_integration_service(mock_db_session, mock_market_data_service):
    """Fixture for market integration service."""
    # Mock broker and trade executor
    with patch("app.services.market_integration.get_resilient_broker"), \
         patch("app.services.market_integration.OrderReconciliationService"), \
         patch("app.services.market_integration.TradeExecutor"), \
         patch("app.services.market_integration.MarketPredictionModel"), \
         patch("app.services.market_integration.TimeframeConverter"), \
         patch("app.services.market_integration.TradeEngineDataSource"), \
         patch("app.services.market_integration.CombinedStrategy", return_value=MockStrategy()), \
         patch("app.services.market_integration.MovingAverageStrategy", return_value=MockStrategy()):
            
            service = MarketIntegrationService(
                db=mock_db_session,
                market_data_service=mock_market_data_service,
                config={"max_slippage_percent": 0.05}
            )
            
            # Mock the trade executor's execute_trade method
            service.trade_executor.execute_trade = AsyncMock(return_value={
                "broker_order_id": "test-order-id",
                "status": "FILLED",
                "filled_quantity": 1.0,
                "filled_price": 150.0
            })
            
            # Mock the order reconciliation service
            service.order_reconciliation.reconcile_pending_trades = AsyncMock(return_value=(5, 10))
            
            yield service


class AsyncMock(MagicMock):
    """Mock for async functions."""
    
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.mark.asyncio
async def test_get_market_data_for_symbols(market_integration_service):
    """Test getting market data for symbols."""
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    # Test getting latest quotes
    quotes = await market_integration_service.get_market_data_for_symbols(symbols)
    
    assert len(quotes) == len(symbols)
    for symbol in symbols:
        assert symbol in quotes
        assert quotes[symbol]["price"] == 150.0
    
    # Test getting historical data
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    historical = await market_integration_service.get_market_data_for_symbols(
        symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    assert len(historical) == len(symbols)
    for symbol in symbols:
        assert symbol in historical
        assert "data" in historical[symbol]
        assert len(historical[symbol]["data"]) > 0


@pytest.mark.asyncio
async def test_generate_recommendations(market_integration_service):
    """Test generating recommendations."""
    # Get recommendations
    recommendations = await market_integration_service.generate_recommendations(
        user_id=1,
        strategy_name="combined",
        max_recommendations=5
    )
    
    assert len(recommendations) == 1
    assert recommendations[0]["symbol"] == "AAPL"
    assert recommendations[0]["action"] == "buy"
    assert recommendations[0]["quantity"] == 1.0
    assert recommendations[0]["price"] == 150.0


@pytest.mark.asyncio
async def test_execute_trades_from_recommendations(market_integration_service):
    """Test executing trades from recommendations."""
    # Create recommendations
    recommendations = [MOCK_RECOMMENDATION]
    
    # Execute trades
    trades = await market_integration_service.execute_trades_from_recommendations(
        user_id=1,
        recommendations=recommendations
    )
    
    assert len(trades) == 1
    assert trades[0].symbol == "AAPL"
    assert trades[0].quantity == 1.0
    assert trades[0].price == 150.0
    assert trades[0].trade_type == "buy"
    assert trades[0].broker_order_id == "test-order-id"
    assert trades[0].status == "FILLED"


@pytest.mark.asyncio
async def test_reconcile_orders(market_integration_service):
    """Test reconciling orders."""
    # Reconcile orders
    updated_count, total_count = await market_integration_service.reconcile_orders(max_age_days=30)
    
    assert updated_count == 5
    assert total_count == 10


@pytest.mark.asyncio
async def test_update_market_prices(market_integration_service):
    """Test updating market prices."""
    # Update prices
    updated_count = await market_integration_service.update_market_prices(portfolio_id=1)
    
    assert updated_count == 2
    
    # Verify that positions were updated
    positions = market_integration_service.db.query().filter().all()
    for position in positions:
        # Check that current_price and last_updated were set
        position.current_price = 150.0
        assert position.last_updated is not None


@pytest.mark.asyncio
async def test_get_prediction(market_integration_service):
    """Test getting predictions."""
    # Mock the prediction model
    market_integration_service.prediction_models["default"].predict = MagicMock(return_value={
        "predicted_price": 155.0,
        "confidence": 0.75,
        "prediction_date": (datetime.now() + timedelta(days=5)).isoformat()
    })
    
    # Get prediction
    prediction = await market_integration_service.get_prediction(
        symbol="AAPL",
        prediction_type="price",
        days_ahead=5
    )
    
    assert prediction["predicted_price"] == 155.0
    assert prediction["confidence"] == 0.75
    assert "prediction_date" in prediction
    assert "generated_at" in prediction
    assert prediction["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_get_integration_status(market_integration_service):
    """Test getting integration status."""
    # Get status
    status = await market_integration_service.get_integration_status()
    
    assert "initialized_strategies" in status
    assert "initialized_models" in status
    assert "integration_errors" in status
    assert "market_data_quality" in status


def test_get_market_integration_service_factory():
    """Test the factory function for getting a market integration service."""
    mock_db = MagicMock()
    mock_market_data = MagicMock()
    
    with patch("app.services.market_integration.MarketIntegrationService") as mock_service:
        service = get_market_integration_service(
            db=mock_db,
            market_data_service=mock_market_data,
            config={"test": True}
        )
        
        # Verify the factory called the constructor with correct args
        mock_service.assert_called_once_with(
            db=mock_db,
            market_data_service=mock_market_data,
            config={"test": True}
        )
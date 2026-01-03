"""Integration tests for the full trading pipeline.

This test suite verifies the integration between all components
of the trading pipeline, from market data to execution and settlement.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.trading_engine.engine.circuit_breaker import CircuitBreaker
from app.trading_engine.engine.trade_executor import TradeExecutor

from app.db.database import get_db
from app.main import app
from app.models.account import Account, AccountStatus, AccountType
from app.models.portfolio import Portfolio
from app.models.risk import RiskLevel as RiskProfile
from app.models.trade import Trade, OrderSide as TradeSide, TradeStatus, TradeType
from app.models.user import User, UserRole
from app.services.market_data import MarketDataService
from app.services.risk_management import RiskManagementService
from app.services.trading import TradingService


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_market_data():
    """Create a mock market data service."""
    mock = MagicMock(spec=MarketDataService)

    # Setup mock methods
    mock.get_current_price.return_value = 150.00
    mock.get_price_history.return_value = [
        {"timestamp": datetime.now() - timedelta(days=i), "close": 150.00 - i}
        for i in range(10)
    ]

    return mock


@pytest.fixture
def mock_risk_service():
    """Create a mock risk management service."""
    mock = MagicMock(spec=RiskManagementService)

    # Setup mock methods
    mock.validate_trade.return_value = (True, None)
    mock.calculate_portfolio_risk.return_value = {
        "var_95": 0.05,
        "var_99": 0.08,
        "expected_shortfall": 0.10,
        "max_drawdown": 0.12,
    }

    return mock


@pytest.fixture
def mock_trade_executor():
    """Create a mock trade executor."""
    mock = MagicMock(spec=TradeExecutor)

    # Setup mock methods
    mock.execute_trade.return_value = {
        "trade_id": "12345",
        "status": "completed",
        "filled_price": 150.00,
        "filled_quantity": 10,
        "commission": 5.25,
        "timestamp": datetime.now(),
    }

    return mock


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker."""
    mock = MagicMock(spec=CircuitBreaker)

    # Setup mock methods
    mock.check_circuit_breaker.return_value = (True, None)

    return mock


@pytest.fixture
def test_user(mock_db_session):
    """Create a test user."""
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.ADULT,
        is_active=True,
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = user
    return user


@pytest.fixture
def test_account(mock_db_session, test_user):
    """Create a test account."""
    account = Account(
        id=1,
        user_id=test_user.id,
        account_type=AccountType.INDIVIDUAL,
        account_number="TEST123456",
        status=AccountStatus.ACTIVE,
        balance=10000.00,
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = account
    return account


@pytest.fixture
def test_portfolio(mock_db_session, test_user):
    """Create a test portfolio."""
    portfolio = Portfolio(
        id=1,
        user_id=test_user.id,
        name="Test Portfolio",
        description="Test portfolio for integration tests",
        risk_profile=RiskProfile.MODERATE,
        total_value=10000.00,
        cash_balance=5000.00,
    )
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        portfolio
    )
    return portfolio


class TestTradingPipeline:
    """Test the full trading pipeline."""

    @patch("app.services.trading.MarketDataService")
    @patch("app.services.trading.RiskManagementService")
    @patch("app.services.trading.TradeExecutor")
    @patch("app.services.trading.CircuitBreaker")
    def test_market_buy_trade_execution(
        self,
        mock_circuit_breaker_cls,
        mock_executor_cls,
        mock_risk_cls,
        mock_market_cls,
        mock_db_session,
        test_user,
        test_account,
        test_portfolio,
    ):
        """Test a complete market buy trade through the entire pipeline."""
        # Setup mocks
        mock_market_cls.return_value = mock_market_data = MagicMock()
        mock_risk_cls.return_value = mock_risk_service = MagicMock()
        mock_executor_cls.return_value = mock_executor = MagicMock()
        mock_circuit_breaker_cls.return_value = mock_circuit_breaker = MagicMock()

        mock_market_data.get_current_price.return_value = 150.00
        mock_risk_service.validate_trade.return_value = (True, None)
        mock_circuit_breaker.check_circuit_breaker.return_value = (True, None)

        execution_result = {
            "trade_id": "12345",
            "status": "completed",
            "filled_price": 150.00,
            "filled_quantity": 10,
            "commission": 5.25,
            "timestamp": datetime.now(),
        }
        mock_executor.execute_trade.return_value = execution_result

        # Setup trade data
        trade_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": TradeSide.BUY,
            "type": TradeType.MARKET,
            "time_in_force": "day",
            "portfolio_id": test_portfolio.id,
        }

        # Create trading service and inject mocks
        trading_service = TradingService(
            db=mock_db_session,
            market_data_service=mock_market_data,
            risk_service=mock_risk_service,
            trade_executor=mock_executor,
            circuit_breaker=mock_circuit_breaker,
        )

        # Execute the trade
        result = trading_service.create_trade(
            user_id=test_user.id, trade_data=trade_data
        )

        # Assertions to verify the entire pipeline worked correctly

        # 1. Market data was queried
        mock_market_data.get_current_price.assert_called_once_with("AAPL")

        # 2. Risk check was performed
        mock_risk_service.validate_trade.assert_called_once()

        # 3. Circuit breaker was checked
        mock_circuit_breaker.check_circuit_breaker.assert_called_once()

        # 4. Trade was executed
        mock_executor.execute_trade.assert_called_once()

        # 5. Trade was saved to database
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # 6. Result contains expected data
        assert result["status"] == "completed"
        assert result["filled_price"] == 150.00
        assert result["filled_quantity"] == 10

    @patch("app.services.trading.MarketDataService")
    @patch("app.services.trading.RiskManagementService")
    @patch("app.services.trading.TradeExecutor")
    @patch("app.services.trading.CircuitBreaker")
    def test_market_sell_trade_execution(
        self,
        mock_circuit_breaker_cls,
        mock_executor_cls,
        mock_risk_cls,
        mock_market_cls,
        mock_db_session,
        test_user,
        test_account,
        test_portfolio,
    ):
        """Test a complete market sell trade through the entire pipeline."""
        # Setup mocks same as buy test
        mock_market_cls.return_value = mock_market_data = MagicMock()
        mock_risk_cls.return_value = mock_risk_service = MagicMock()
        mock_executor_cls.return_value = mock_executor = MagicMock()
        mock_circuit_breaker_cls.return_value = mock_circuit_breaker = MagicMock()

        mock_market_data.get_current_price.return_value = 150.00
        mock_risk_service.validate_trade.return_value = (True, None)
        mock_circuit_breaker.check_circuit_breaker.return_value = (True, None)

        execution_result = {
            "trade_id": "12345",
            "status": "completed",
            "filled_price": 150.00,
            "filled_quantity": 10,
            "commission": 5.25,
            "timestamp": datetime.now(),
        }
        mock_executor.execute_trade.return_value = execution_result

        # Setup trade data - now it's a SELL
        trade_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": TradeSide.SELL,
            "type": TradeType.MARKET,
            "time_in_force": "day",
            "portfolio_id": test_portfolio.id,
        }

        # Create trading service
        trading_service = TradingService(
            db=mock_db_session,
            market_data_service=mock_market_data,
            risk_service=mock_risk_service,
            trade_executor=mock_executor,
            circuit_breaker=mock_circuit_breaker,
        )

        # Execute the trade
        result = trading_service.create_trade(
            user_id=test_user.id, trade_data=trade_data
        )

        # Assertions to verify the pipeline
        mock_market_data.get_current_price.assert_called_once_with("AAPL")
        mock_risk_service.validate_trade.assert_called_once()
        mock_circuit_breaker.check_circuit_breaker.assert_called_once()
        mock_executor.execute_trade.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        assert result["status"] == "completed"
        assert result["filled_price"] == 150.00
        assert result["filled_quantity"] == 10

    @patch("app.services.trading.MarketDataService")
    @patch("app.services.trading.RiskManagementService")
    @patch("app.services.trading.TradeExecutor")
    @patch("app.services.trading.CircuitBreaker")
    def test_trade_with_circuit_breaker_triggered(
        self,
        mock_circuit_breaker_cls,
        mock_executor_cls,
        mock_risk_cls,
        mock_market_cls,
        mock_db_session,
        test_user,
        test_account,
        test_portfolio,
    ):
        """Test a trade when circuit breaker is triggered."""
        # Setup mocks
        mock_market_cls.return_value = mock_market_data = MagicMock()
        mock_risk_cls.return_value = mock_risk_service = MagicMock()
        mock_executor_cls.return_value = mock_executor = MagicMock()
        mock_circuit_breaker_cls.return_value = mock_circuit_breaker = MagicMock()

        # Configure circuit breaker to trigger
        mock_circuit_breaker.check_circuit_breaker.return_value = (
            False,
            "Daily loss limit reached",
        )

        # Setup trade data
        trade_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "side": TradeSide.BUY,
            "type": TradeType.MARKET,
            "time_in_force": "day",
            "portfolio_id": test_portfolio.id,
        }

        # Create trading service
        trading_service = TradingService(
            db=mock_db_session,
            market_data_service=mock_market_data,
            risk_service=mock_risk_service,
            trade_executor=mock_executor,
            circuit_breaker=mock_circuit_breaker,
        )

        # Execute the trade - should be rejected
        with pytest.raises(ValueError) as excinfo:
            trading_service.create_trade(user_id=test_user.id, trade_data=trade_data)

        # Verify error message mentions circuit breaker
        assert "circuit breaker" in str(excinfo.value).lower()
        assert "daily loss limit" in str(excinfo.value).lower()

        # Verify executor was never called
        mock_executor.execute_trade.assert_not_called()

    @patch("app.services.trading.MarketDataService")
    @patch("app.services.trading.RiskManagementService")
    @patch("app.services.trading.TradeExecutor")
    @patch("app.services.trading.CircuitBreaker")
    def test_trade_with_risk_validation_failure(
        self,
        mock_circuit_breaker_cls,
        mock_executor_cls,
        mock_risk_cls,
        mock_market_cls,
        mock_db_session,
        test_user,
        test_account,
        test_portfolio,
    ):
        """Test a trade that fails risk validation."""
        # Setup mocks
        mock_market_cls.return_value = mock_market_data = MagicMock()
        mock_risk_cls.return_value = mock_risk_service = MagicMock()
        mock_executor_cls.return_value = mock_executor = MagicMock()
        mock_circuit_breaker_cls.return_value = mock_circuit_breaker = MagicMock()

        # Configure risk validation to fail
        mock_risk_service.validate_trade.return_value = (
            False,
            "Trade exceeds portfolio concentration limits",
        )

        # Setup trade data
        trade_data = {
            "symbol": "AAPL",
            "quantity": 1000,  # Large quantity to trigger risk limits
            "side": TradeSide.BUY,
            "type": TradeType.MARKET,
            "time_in_force": "day",
            "portfolio_id": test_portfolio.id,
        }

        # Create trading service
        trading_service = TradingService(
            db=mock_db_session,
            market_data_service=mock_market_data,
            risk_service=mock_risk_service,
            trade_executor=mock_executor,
            circuit_breaker=mock_circuit_breaker,
        )

        # Execute the trade - should be rejected
        with pytest.raises(ValueError) as excinfo:
            trading_service.create_trade(user_id=test_user.id, trade_data=trade_data)

        # Verify error message mentions risk validation
        assert "risk" in str(excinfo.value).lower()
        assert "concentration limits" in str(excinfo.value).lower()

        # Verify circuit breaker and executor were never called
        mock_circuit_breaker.check_circuit_breaker.assert_not_called()
        mock_executor.execute_trade.assert_not_called()

"""
Integration tests for Advanced Trading components

Tests the integration between trading engine, AI models, risk management,
and API endpoints to ensure they work together correctly.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import numpy as np
import pandas as pd
import pytest

from app.ml_models.quantum_models.quantum_classifier import QuantumInspiredClassifier
from app.models.portfolio import Portfolio
from app.services.advanced_trading import AdvancedTradingService
from trading_engine.engine.risk_config import RiskProfile
from trading_engine.strategies.moving_average import MovingAverageStrategy


class TestAdvancedTradingIntegration:
    """Test advanced trading integration"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_market_data_service(self):
        """Mock market data service"""
        service = Mock()
        service.get_quote = AsyncMock(
            return_value={
                "price": 100.0,
                "volume": 1000000,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        service.get_historical_data = AsyncMock(
            return_value=self._create_mock_historical_data()
        )
        return service

    @pytest.fixture
    def mock_portfolio(self):
        """Mock portfolio"""
        portfolio = Mock(spec=Portfolio)
        portfolio.id = 1
        portfolio.total_value = 10000.0
        portfolio.get_daily_drawdown = Mock(return_value=None)
        portfolio.get_daily_trade_count = Mock(return_value=2)
        portfolio.holdings = []
        return portfolio

    def _create_mock_historical_data(self):
        """Create mock historical data"""
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        np.random.seed(42)  # For reproducible tests

        data = []
        price = 100.0
        for date in dates:
            price_change = np.random.normal(0, 0.02)  # 2% daily volatility
            price *= 1 + price_change

            data.append(
                {
                    "timestamp": date.isoformat(),
                    "close": price,
                    "volume": np.random.randint(500000, 2000000),
                }
            )

        return data

    @pytest.mark.asyncio
    async def test_trading_service_initialization(
        self, mock_db, mock_market_data_service
    ):
        """Test advanced trading service initialization"""
        service = AdvancedTradingService(
            db=mock_db,
            market_data_service=mock_market_data_service,
            risk_profile=RiskProfile.MODERATE,
        )

        assert service.risk_profile == RiskProfile.MODERATE
        assert service.strategies == {}
        assert service.ai_models == {}
        assert service.performance_metrics["total_trades"] == 0

    @pytest.mark.asyncio
    async def test_strategy_initialization(self, mock_db, mock_market_data_service):
        """Test strategy initialization"""
        service = AdvancedTradingService(
            db=mock_db, market_data_service=mock_market_data_service
        )

        symbols = ["AAPL", "GOOGL"]
        await service.initialize_strategies(symbols)

        assert len(service.strategies) == 2
        assert "AAPL" in service.strategies
        assert "GOOGL" in service.strategies

        for symbol in symbols:
            # strategies[symbol] is a list of strategy dicts
            assert len(service.strategies[symbol]) > 0
            first_strategy = service.strategies[symbol][0]
            assert "strategy" in first_strategy
            assert "executor" in first_strategy
            assert isinstance(
                first_strategy["strategy"], MovingAverageStrategy
            )

    @pytest.mark.asyncio
    async def test_ai_model_initialization(self, mock_db, mock_market_data_service):
        """Test AI model initialization"""
        service = AdvancedTradingService(
            db=mock_db, market_data_service=mock_market_data_service
        )

        symbols = ["AAPL"]
        await service.initialize_ai_models(symbols)

        assert len(service.ai_models) == 1
        assert "AAPL" in service.ai_models

        model_data = service.ai_models["AAPL"]
        assert "quantum_classifier" in model_data
        assert isinstance(model_data["quantum_classifier"], QuantumInspiredClassifier)
        assert "is_trained" in model_data

    @pytest.mark.asyncio
    async def test_moving_average_strategy_signal_generation(
        self, mock_market_data_service
    ):
        """Test moving average strategy signal generation"""
        strategy = MovingAverageStrategy(
            symbol="AAPL",
            market_data_service=mock_market_data_service,
            short_window=5,
            long_window=10,
        )

        market_data = {"price": 105.0, "volume": 1000000}

        signal = await strategy.generate_signal(market_data)

        assert "action" in signal
        assert "confidence" in signal
        assert "price" in signal
        assert signal["action"] in ["buy", "sell", "hold"]
        assert 0 <= signal["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_quantum_classifier_training_and_prediction(self):
        """Test quantum classifier training and prediction"""
        # Create mock training data
        np.random.seed(42)
        n_samples = 100
        n_features = 10

        X = np.random.randn(n_samples, n_features)
        y = (np.sum(X[:, :3], axis=1) > 0).astype(int)  # Simple pattern

        # Initialize and train model
        model = QuantumInspiredClassifier(
            n_features=n_features, n_qubits=4, max_iterations=50
        )

        model.fit(X, y)

        assert model.is_trained
        assert len(model.training_history["accuracy"]) > 0
        assert model.training_history["quantum_features_used"] > 0

        # Test prediction
        X_test = np.random.randn(10, n_features)
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)

        assert len(predictions) == 10
        assert all(0 <= p <= 1 for p in predictions)
        assert probabilities.shape == (10, 2)

    @pytest.mark.asyncio
    async def test_signal_generation_with_ai(
        self, mock_db, mock_market_data_service, mock_portfolio
    ):
        """Test signal generation with AI enhancement"""
        service = AdvancedTradingService(
            db=mock_db, market_data_service=mock_market_data_service
        )

        # Initialize with limited data for faster testing
        mock_market_data_service.get_historical_data.return_value = (
            self._create_small_historical_data()
        )

        symbols = ["AAPL"]
        await service.initialize_strategies(symbols)
        await service.initialize_ai_models(symbols)

        signals = await service.generate_trading_signals(mock_portfolio)

        # Signals might be empty if no crossover detected, that's normal
        assert isinstance(signals, list)

        for signal_data in signals:
            assert "symbol" in signal_data
            assert "signal" in signal_data
            assert "strategy_name" in signal_data
            assert "timestamp" in signal_data

    def _create_small_historical_data(self):
        """Create small historical data for faster testing"""
        dates = pd.date_range(start="2023-01-01", end="2023-01-31", freq="D")
        np.random.seed(42)

        data = []
        price = 100.0
        for i, date in enumerate(dates):
            # Create a simple trend to trigger crossover
            if i < 15:
                price *= 0.995  # Slight downtrend
            else:
                price *= 1.005  # Slight uptrend

            data.append(
                {"timestamp": date.isoformat(), "close": price, "volume": 1000000}
            )

        return data

    @pytest.mark.asyncio
    async def test_risk_management_integration(
        self, mock_db, mock_market_data_service, mock_portfolio
    ):
        """Test risk management integration"""
        service = AdvancedTradingService(
            db=mock_db,
            market_data_service=mock_market_data_service,
            risk_profile=RiskProfile.CONSERVATIVE,
        )

        # Test risk configuration
        risk_config = service.risk_config
        max_position_size = risk_config.get_param("position_sizing.max_position_size")
        assert max_position_size == 0.05  # Conservative profile

        # Test portfolio monitoring
        monitoring_data = await service.monitor_positions(mock_portfolio)

        assert "total_positions" in monitoring_data
        assert "risk_metrics" in monitoring_data
        assert "alerts" in monitoring_data

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mock_db, mock_market_data_service):
        """Test circuit breaker integration"""
        service = AdvancedTradingService(
            db=mock_db, market_data_service=mock_market_data_service
        )

        circuit_breaker = service.circuit_breaker

        # Test normal operation
        trading_allowed, status = circuit_breaker.check()
        assert trading_allowed

        # Test position sizing
        position_multiplier = circuit_breaker.get_position_sizing()
        assert 0 <= position_multiplier <= 1

    @pytest.mark.asyncio
    async def test_performance_tracking(self, mock_db, mock_market_data_service):
        """Test performance metrics tracking"""
        service = AdvancedTradingService(
            db=mock_db, market_data_service=mock_market_data_service
        )

        # Get initial performance summary
        summary = service.get_performance_summary()

        assert "performance_metrics" in summary
        assert "active_strategies" in summary
        assert "trained_ai_models" in summary
        assert "risk_profile" in summary
        assert "circuit_breaker_status" in summary

        # Check initial values
        assert summary["performance_metrics"]["total_trades"] == 0
        assert summary["active_strategies"] == 0
        assert summary["trained_ai_models"] == 0

    @pytest.mark.asyncio
    async def test_risk_profile_update(self, mock_db, mock_market_data_service):
        """Test risk profile update functionality"""
        service = AdvancedTradingService(
            db=mock_db,
            market_data_service=mock_market_data_service,
            risk_profile=RiskProfile.MODERATE,
        )

        # Test initial profile
        assert service.risk_profile == RiskProfile.MODERATE

        # Update to conservative
        success = await service.update_risk_profile(RiskProfile.CONSERVATIVE)
        assert success
        assert service.risk_profile == RiskProfile.CONSERVATIVE

        # Verify risk configuration changed
        max_position_size = service.risk_config.get_param(
            "position_sizing.max_position_size"
        )
        assert max_position_size == 0.05  # Conservative value


if __name__ == "__main__":
    pytest.main([__file__])

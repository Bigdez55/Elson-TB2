"""Market integration service.

This module provides a bridge between the backend, market data services, and the trading engine.
It ensures proper data flow between components and standardizes the interfaces.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import metrics
from app.models.holding import Position
from app.models.portfolio import Portfolio

# Import backend services and models
from app.models.trade import OrderSide, OrderType, Trade, TradeStatus
from app.models.user import User
from app.services.broker.factory import get_resilient_broker
from app.services.market_data import MarketDataService
from app.services.reconciliation.order_reconciliation import OrderReconciliationService

logger = logging.getLogger(__name__)

# Import real implementations from trading-engine
try:
    from app.trading_engine.engine.trade_executor import TradeExecutor
    from app.trading_engine.ml_models.volatility_regime import VolatilityDetector
    from app.trading_engine.strategies.moving_average import MovingAverageStrategy
    from app.trading_engine.timeframe.market_regime_detector import MarketRegimeDetector

    TRADING_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Trading engine not fully available: {e}")
    TRADING_ENGINE_AVAILABLE = False
    # Fallback stubs only used if trading-engine package is not installed
    MarketRegimeDetector = None
    TradeExecutor = None
    MovingAverageStrategy = None
    VolatilityDetector = None


class MarketIntegrationService:
    """
    Integration service that connects the backend, market data services, and trading engine.

    This service provides:
    1. Standardized data flow between backend and trading engine
    2. Proper initialization and configuration of trading engine components
    3. Conversion between backend models and trading engine models
    4. Coordinated execution of trading strategies
    5. Market data bridging between systems
    """

    def __init__(
        self,
        db: Session,
        market_data_service: Optional[MarketDataService] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the market integration service.

        Args:
            db: Database session
            market_data_service: Market data service instance
            config: Configuration parameters
        """
        self.db = db
        self.config = config or {}

        # Initialize services
        self.market_data = market_data_service or MarketDataService()
        self.broker = get_resilient_broker(db=db)
        self.order_reconciliation = OrderReconciliationService(db=db)

        # Initialize trading engine components
        self.strategies = {}

        if TRADING_ENGINE_AVAILABLE and TradeExecutor is not None:
            # Use real trade executor from trading-engine
            self.trade_executor = (
                TradeExecutor(
                    market_data_service=self.market_data,
                    strategy=None,  # Strategy set per-trade
                )
                if MovingAverageStrategy
                else None
            )
        else:
            self.trade_executor = None
            logger.warning(
                "TradeExecutor not available - trading functionality limited"
            )

        # Initialize AI prediction models from trading-engine
        if TRADING_ENGINE_AVAILABLE and VolatilityDetector is not None:
            self.prediction_models = {"volatility": VolatilityDetector()}
        else:
            self.prediction_models = {}
            logger.warning("Prediction models not available - using basic mode")

        # Initialize market regime detector from trading-engine
        if TRADING_ENGINE_AVAILABLE and MarketRegimeDetector is not None:
            self.market_regime_detector = MarketRegimeDetector()
        else:
            self.market_regime_detector = None
            logger.warning(
                "MarketRegimeDetector not available - regime detection disabled"
            )

        # Metrics and monitoring
        self.last_strategy_run = {}
        self.strategy_performance = {}
        self.integration_errors = 0

        logger.info("Market integration service initialized")
        metrics.increment("market_integration.initialized")

    async def close(self):
        """Close all connections and resources."""
        pass

    async def get_status(self):
        """Get service status."""
        return {
            "status": "operational",
            "volatility_regimes_supported": ["low", "medium", "high", "extreme"],
        }


@lru_cache(maxsize=1)
def get_market_integration_service(
    db: Session,
    market_data_service: Optional[MarketDataService] = None,
    config: Optional[Dict[str, Any]] = None,
) -> MarketIntegrationService:
    """Get a cached instance of the market integration service.

    This function returns a singleton instance of the service to avoid
    redundant initialization.

    Args:
        db: Database session
        market_data_service: Optional market data service
        config: Optional configuration parameters

    Returns:
        MarketIntegrationService instance
    """
    return MarketIntegrationService(
        db=db, market_data_service=market_data_service, config=config
    )


class Recommendation:
    """Recommendation class for the advisor service."""

    def __init__(self, symbol: str, action: str, reason: str, confidence: float = 0.0):
        self.symbol = symbol
        self.action = action
        self.reason = reason
        self.confidence = confidence
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "action": self.action,
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }

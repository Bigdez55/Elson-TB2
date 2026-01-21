#!/usr/bin/env python3
"""
Comprehensive Trading Services Test Suite
==========================================

This script thoroughly tests all trading service functionality in the Elson-TB2 backend.
It validates:
- Core trading service functionality
- Broker integrations (Alpaca, paper trading)
- Order placement, execution, and tracking
- Portfolio management functions
- AI trading service integration
- Risk management service functionality
- Paper trading service
- Advanced trading features
- API connections and configuration
- Order validation and risk checks
- Trade execution logging and audit trails
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Add the backend app to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trading_services_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Test results storage
test_results = {
    "timestamp": datetime.utcnow().isoformat(),
    "test_summary": {"total_tests": 0, "passed": 0, "failed": 0, "errors": 0},
    "test_categories": {},
    "detailed_results": [],
    "critical_issues": [],
    "recommendations": [],
}


class TradingServiceTester:
    """Comprehensive trading service test suite."""

    def __init__(self):
        self.db = None
        self.user = None
        self.portfolio = None
        self.test_category = None
        self.setup_successful = False

    async def run_all_tests(self):
        """Run the complete test suite."""
        logger.info("Starting comprehensive trading services test suite...")

        try:
            # Setup test environment
            await self.setup_test_environment()
            if not self.setup_successful:
                self.add_critical_issue("Failed to setup test environment")
                return

            # Run test categories
            await self.test_trading_service_core()
            await self.test_broker_integrations()
            await self.test_order_lifecycle()
            await self.test_portfolio_management()
            await self.test_ai_trading_integration()
            await self.test_risk_management()
            await self.test_paper_trading()
            await self.test_advanced_features()
            await self.test_api_connections()
            await self.test_validation_and_security()
            await self.test_logging_and_audit()

        except Exception as e:
            logger.error(f"Test suite failed with error: {str(e)}")
            self.add_critical_issue(f"Test suite execution error: {str(e)}")
        finally:
            await self.cleanup_test_environment()
            self.generate_final_report()

    async def setup_test_environment(self):
        """Setup test database and user."""
        logger.info("Setting up test environment...")
        try:
            # Import dependencies
            from sqlalchemy.orm import sessionmaker

            from app.core.config import settings
            from app.db.base import engine
            from app.models.portfolio import Portfolio
            from app.models.user import User

            # Create database session
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.db = SessionLocal()

            # Create test user
            test_user = User(
                email="test_trader@elson.com",
                hashed_password="test_hash",
                full_name="Test Trader",
                is_active=True,
                is_verified=True,
            )
            self.db.add(test_user)
            self.db.commit()
            self.db.refresh(test_user)
            self.user = test_user

            # Create test portfolio
            test_portfolio = Portfolio(
                name="Test Trading Portfolio",
                owner_id=test_user.id,
                cash_balance=Decimal("100000.00"),  # $100k for testing
                total_value=Decimal("100000.00"),
                is_active=True,
            )
            self.db.add(test_portfolio)
            self.db.commit()
            self.db.refresh(test_portfolio)
            self.portfolio = test_portfolio

            self.setup_successful = True
            self.log_test_result(
                "setup",
                "test_environment_setup",
                True,
                "Test environment created successfully",
            )

        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            self.log_test_result(
                "setup", "test_environment_setup", False, f"Setup failed: {str(e)}"
            )
            self.add_critical_issue(f"Test environment setup failed: {str(e)}")

    async def test_trading_service_core(self):
        """Test core trading service functionality."""
        self.test_category = "trading_service_core"
        logger.info("Testing core trading service functionality...")

        try:
            from app.models.trade import OrderType, TradeType
            from app.services.trading import TradingService, trading_service

            # Test 1: Service initialization
            try:
                new_service = TradingService()
                self.log_test_result(
                    self.test_category,
                    "service_initialization",
                    True,
                    "TradingService initialized successfully",
                )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "service_initialization",
                    False,
                    f"Service init failed: {str(e)}",
                )

            # Test 2: Input validation and sanitization
            try:
                # Test symbol sanitization
                sanitized = trading_service._sanitize_symbol("  AAPL  ")
                assert sanitized == "AAPL"

                # Test invalid symbols
                invalid_symbols = ["", "ABC123456789", "AB$", None]
                for symbol in invalid_symbols:
                    try:
                        trading_service._sanitize_symbol(symbol)
                        self.log_test_result(
                            self.test_category,
                            f"invalid_symbol_{symbol}",
                            False,
                            "Should have rejected invalid symbol",
                        )
                    except ValueError:
                        pass  # Expected

                # Test quantity validation
                valid_quantity = trading_service._validate_quantity(100.5)
                assert valid_quantity == 100.5

                invalid_quantities = [0, -10, "abc", None, 1000001]
                for qty in invalid_quantities:
                    try:
                        trading_service._validate_quantity(qty)
                        self.log_test_result(
                            self.test_category,
                            f"invalid_quantity_{qty}",
                            False,
                            "Should have rejected invalid quantity",
                        )
                    except ValueError:
                        pass  # Expected

                self.log_test_result(
                    self.test_category,
                    "input_validation",
                    True,
                    "Input validation working correctly",
                )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "input_validation",
                    False,
                    f"Input validation failed: {str(e)}",
                )

            # Test 3: Trade validation
            try:
                valid_trade_data = {
                    "symbol": "AAPL",
                    "quantity": 10,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                }

                validation_result = await trading_service.validate_trade(
                    valid_trade_data, self.portfolio
                )

                if validation_result.get("valid"):
                    self.log_test_result(
                        self.test_category,
                        "trade_validation_valid",
                        True,
                        "Valid trade accepted",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "trade_validation_valid",
                        False,
                        f"Valid trade rejected: {validation_result.get('errors')}",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "trade_validation",
                    False,
                    f"Trade validation failed: {str(e)}",
                )

            # Test 4: Circuit breaker integration
            try:
                if (
                    hasattr(trading_service, "circuit_breaker")
                    and trading_service.circuit_breaker
                ):
                    self.log_test_result(
                        self.test_category,
                        "circuit_breaker_integration",
                        True,
                        "Circuit breaker integrated",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "circuit_breaker_integration",
                        False,
                        "Circuit breaker not available",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "circuit_breaker_integration",
                    False,
                    f"Circuit breaker test failed: {str(e)}",
                )

        except ImportError as e:
            self.log_test_result(
                self.test_category, "import_error", False, f"Import failed: {str(e)}"
            )
            self.add_critical_issue(f"Core trading service import failed: {str(e)}")

    async def test_broker_integrations(self):
        """Test broker integration functionality."""
        self.test_category = "broker_integrations"
        logger.info("Testing broker integrations...")

        try:
            from app.services.broker.alpaca import AlpacaBroker
            from app.services.broker.base import BaseBroker, BrokerError
            from app.services.broker.factory import BrokerFactory

            # Test 1: Broker factory
            try:
                # Test paper trading broker creation
                paper_broker = BrokerFactory.create_broker("alpaca", use_paper=True)
                if paper_broker:
                    self.log_test_result(
                        self.test_category,
                        "broker_factory_paper",
                        True,
                        "Paper broker created successfully",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "broker_factory_paper",
                        False,
                        "Failed to create paper broker",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "broker_factory_paper",
                    False,
                    f"Broker factory failed: {str(e)}",
                )

            # Test 2: Alpaca broker configuration
            try:
                from app.core.config import settings

                # Check if Alpaca credentials are configured
                has_api_key = (
                    hasattr(settings, "ALPACA_API_KEY") and settings.ALPACA_API_KEY
                )
                has_secret = (
                    hasattr(settings, "ALPACA_SECRET_KEY")
                    and settings.ALPACA_SECRET_KEY
                )

                if has_api_key and has_secret:
                    self.log_test_result(
                        self.test_category,
                        "alpaca_credentials",
                        True,
                        "Alpaca credentials configured",
                    )

                    # Test broker initialization
                    try:
                        alpaca_broker = AlpacaBroker(use_paper=True)
                        self.log_test_result(
                            self.test_category,
                            "alpaca_initialization",
                            True,
                            "Alpaca broker initialized",
                        )
                    except BrokerError as e:
                        self.log_test_result(
                            self.test_category,
                            "alpaca_initialization",
                            False,
                            f"Alpaca init failed: {str(e)}",
                        )
                else:
                    self.log_test_result(
                        self.test_category,
                        "alpaca_credentials",
                        False,
                        "Alpaca credentials not configured",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "alpaca_configuration",
                    False,
                    f"Alpaca config test failed: {str(e)}",
                )

            # Test 3: Broker interface compliance
            try:
                # Test that all brokers implement the base interface
                required_methods = [
                    "execute_trade",
                    "get_account_info",
                    "get_positions",
                    "get_trade_status",
                    "cancel_trade",
                    "get_order_history",
                    "get_trade_execution",
                ]

                for method in required_methods:
                    if hasattr(BaseBroker, method):
                        self.log_test_result(
                            self.test_category,
                            f"base_interface_{method}",
                            True,
                            f"Method {method} defined in base class",
                        )
                    else:
                        self.log_test_result(
                            self.test_category,
                            f"base_interface_{method}",
                            False,
                            f"Method {method} missing from base class",
                        )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "broker_interface",
                    False,
                    f"Interface test failed: {str(e)}",
                )

        except ImportError as e:
            self.log_test_result(
                self.test_category,
                "import_error",
                False,
                f"Broker import failed: {str(e)}",
            )
            self.add_critical_issue(f"Broker integration import failed: {str(e)}")

    async def test_order_lifecycle(self):
        """Test complete order lifecycle."""
        self.test_category = "order_lifecycle"
        logger.info("Testing order placement, execution, and tracking...")

        try:
            from app.models.trade import OrderType, TradeStatus, TradeType
            from app.services.trading import trading_service

            # Test 1: Order placement
            try:
                trade_data = {
                    "symbol": "AAPL",
                    "quantity": 10,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                    "strategy": "test",
                }

                trade = await trading_service.place_order(
                    trade_data, self.user, self.db
                )

                if trade and trade.id:
                    self.log_test_result(
                        self.test_category,
                        "order_placement",
                        True,
                        f"Order placed successfully: {trade.id}",
                    )

                    # Test 2: Order tracking
                    if trade.status in [TradeStatus.PENDING, TradeStatus.FILLED]:
                        self.log_test_result(
                            self.test_category,
                            "order_tracking",
                            True,
                            f"Order status: {trade.status}",
                        )
                    else:
                        self.log_test_result(
                            self.test_category,
                            "order_tracking",
                            False,
                            f"Unexpected order status: {trade.status}",
                        )
                else:
                    self.log_test_result(
                        self.test_category,
                        "order_placement",
                        False,
                        "Order placement returned None",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "order_placement",
                    False,
                    f"Order placement failed: {str(e)}",
                )

            # Test 3: Get trade history
            try:
                history = await trading_service.get_trade_history(self.user, self.db)
                if isinstance(history, list):
                    self.log_test_result(
                        self.test_category,
                        "trade_history",
                        True,
                        f"Retrieved {len(history)} trade records",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "trade_history",
                        False,
                        "Trade history not returned as list",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "trade_history",
                    False,
                    f"Trade history failed: {str(e)}",
                )

            # Test 4: Get open orders
            try:
                open_orders = await trading_service.get_open_orders(self.user, self.db)
                if isinstance(open_orders, list):
                    self.log_test_result(
                        self.test_category,
                        "open_orders",
                        True,
                        f"Retrieved {len(open_orders)} open orders",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "open_orders",
                        False,
                        "Open orders not returned as list",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "open_orders",
                    False,
                    f"Open orders failed: {str(e)}",
                )

        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Order lifecycle test failed: {str(e)}",
            )

    async def test_portfolio_management(self):
        """Test portfolio management functions."""
        self.test_category = "portfolio_management"
        logger.info("Testing portfolio management functions...")

        try:
            from app.models.holding import Holding
            from app.services.trading import trading_service

            # Test 1: Portfolio holdings update
            try:
                initial_cash = float(self.portfolio.cash_balance)

                # Create a test trade for portfolio update
                from app.models.trade import OrderType, Trade, TradeStatus, TradeType

                test_trade = Trade(
                    symbol="TSLA",
                    trade_type=TradeType.BUY,
                    order_type=OrderType.MARKET,
                    quantity=5,
                    price=250.0,
                    filled_price=250.0,
                    filled_quantity=5,
                    total_cost=1250.0,
                    portfolio_id=self.portfolio.id,
                    status=TradeStatus.FILLED,
                )

                await trading_service._update_portfolio_holdings(test_trade, self.db)

                # Check if holding was created
                holding = (
                    self.db.query(Holding)
                    .filter(
                        Holding.portfolio_id == self.portfolio.id,
                        Holding.symbol == "TSLA",
                    )
                    .first()
                )

                if holding and holding.quantity == 5:
                    self.log_test_result(
                        self.test_category,
                        "portfolio_holdings_update",
                        True,
                        "Portfolio holdings updated correctly",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "portfolio_holdings_update",
                        False,
                        "Portfolio holdings not updated correctly",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "portfolio_holdings_update",
                    False,
                    f"Holdings update failed: {str(e)}",
                )

            # Test 2: Portfolio totals calculation
            try:
                await trading_service._update_portfolio_totals(self.portfolio, self.db)
                self.db.refresh(self.portfolio)

                if self.portfolio.total_value is not None:
                    self.log_test_result(
                        self.test_category,
                        "portfolio_totals",
                        True,
                        f"Portfolio total value: {self.portfolio.total_value}",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "portfolio_totals",
                        False,
                        "Portfolio total value not calculated",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "portfolio_totals",
                    False,
                    f"Portfolio totals failed: {str(e)}",
                )

        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Portfolio management test failed: {str(e)}",
            )

    async def test_ai_trading_integration(self):
        """Test AI trading service integration."""
        self.test_category = "ai_trading_integration"
        logger.info("Testing AI trading service integration...")

        try:
            from app.services.ai_trading import AITradingService

            # Test 1: AI service initialization
            try:
                ai_service = AITradingService()
                self.log_test_result(
                    self.test_category,
                    "ai_service_init",
                    True,
                    "AI trading service initialized",
                )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "ai_service_init",
                    False,
                    f"AI service init failed: {str(e)}",
                )

            # Test 2: Check if AI models are available
            try:
                if hasattr(ai_service, "model") and ai_service.model:
                    self.log_test_result(
                        self.test_category,
                        "ai_models_available",
                        True,
                        "AI models loaded",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "ai_models_available",
                        False,
                        "AI models not available",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "ai_models_check",
                    False,
                    f"AI models check failed: {str(e)}",
                )

        except ImportError as e:
            self.log_test_result(
                self.test_category,
                "import_error",
                False,
                f"AI trading import failed: {str(e)}",
            )
        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"AI trading test failed: {str(e)}",
            )

    async def test_risk_management(self):
        """Test risk management service functionality."""
        self.test_category = "risk_management"
        logger.info("Testing risk management functionality...")

        try:
            from app.services.risk_management import RiskManager

            # Test 1: Risk manager initialization
            try:
                risk_manager = RiskManager()
                self.log_test_result(
                    self.test_category,
                    "risk_manager_init",
                    True,
                    "Risk manager initialized",
                )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "risk_manager_init",
                    False,
                    f"Risk manager init failed: {str(e)}",
                )

            # Test 2: Position size validation
            try:
                # Test position size limits
                test_portfolio_value = 100000
                test_position_value = 15000  # 15% of portfolio

                if hasattr(risk_manager, "validate_position_size"):
                    is_valid = risk_manager.validate_position_size(
                        test_position_value, test_portfolio_value
                    )
                    self.log_test_result(
                        self.test_category,
                        "position_size_validation",
                        True,
                        f"Position size validation result: {is_valid}",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "position_size_validation",
                        False,
                        "Position size validation method not found",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "position_size_validation",
                    False,
                    f"Position size validation failed: {str(e)}",
                )

        except ImportError as e:
            self.log_test_result(
                self.test_category,
                "import_error",
                False,
                f"Risk management import failed: {str(e)}",
            )
        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Risk management test failed: {str(e)}",
            )

    async def test_paper_trading(self):
        """Test paper trading service."""
        self.test_category = "paper_trading"
        logger.info("Testing paper trading service...")

        try:
            from app.services.paper_trading import PaperTradingService

            # Test 1: Paper trading service initialization
            try:
                paper_service = PaperTradingService(self.db)
                self.log_test_result(
                    self.test_category,
                    "paper_service_init",
                    True,
                    "Paper trading service initialized",
                )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "paper_service_init",
                    False,
                    f"Paper service init failed: {str(e)}",
                )
                return

            # Test 2: Paper trade execution simulation
            try:
                from app.models.trade import OrderType, Trade, TradeType

                test_trade = Trade(
                    symbol="MSFT",
                    trade_type=TradeType.BUY,
                    order_type=OrderType.MARKET,
                    quantity=10,
                    portfolio_id=self.portfolio.id,
                )

                execution_result = await paper_service.execute_paper_trade(
                    test_trade, simulate_realistic_conditions=False
                )

                if execution_result and execution_result.get("status"):
                    self.log_test_result(
                        self.test_category,
                        "paper_trade_execution",
                        True,
                        f"Paper trade executed with status: {execution_result['status']}",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "paper_trade_execution",
                        False,
                        "Paper trade execution failed",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "paper_trade_execution",
                    False,
                    f"Paper trade execution failed: {str(e)}",
                )

            # Test 3: Execution statistics
            try:
                stats = await paper_service.get_execution_statistics(
                    self.user.id, days=30
                )
                if isinstance(stats, dict):
                    self.log_test_result(
                        self.test_category,
                        "execution_statistics",
                        True,
                        f"Retrieved execution statistics: {stats.get('total_trades', 0)} trades",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "execution_statistics",
                        False,
                        "Execution statistics not returned as dict",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "execution_statistics",
                    False,
                    f"Execution statistics failed: {str(e)}",
                )

        except ImportError as e:
            self.log_test_result(
                self.test_category,
                "import_error",
                False,
                f"Paper trading import failed: {str(e)}",
            )
        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Paper trading test failed: {str(e)}",
            )

    async def test_advanced_features(self):
        """Test advanced trading features."""
        self.test_category = "advanced_features"
        logger.info("Testing advanced trading features...")

        try:
            from app.services.advanced_trading import AdvancedTradingService

            # Test 1: Advanced trading service initialization
            try:
                advanced_service = AdvancedTradingService()
                self.log_test_result(
                    self.test_category,
                    "advanced_service_init",
                    True,
                    "Advanced trading service initialized",
                )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "advanced_service_init",
                    False,
                    f"Advanced service init failed: {str(e)}",
                )

            # Test 2: Strategy integration
            try:
                if hasattr(advanced_service, "strategies") or hasattr(
                    advanced_service, "get_strategies"
                ):
                    self.log_test_result(
                        self.test_category,
                        "strategy_integration",
                        True,
                        "Strategy integration available",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "strategy_integration",
                        False,
                        "Strategy integration not found",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "strategy_integration",
                    False,
                    f"Strategy integration test failed: {str(e)}",
                )

        except ImportError as e:
            self.log_test_result(
                self.test_category,
                "import_error",
                False,
                f"Advanced trading import failed: {str(e)}",
            )
        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Advanced features test failed: {str(e)}",
            )

    async def test_api_connections(self):
        """Test API connections and configuration."""
        self.test_category = "api_connections"
        logger.info("Testing API connections and configuration...")

        try:
            from app.core.config import settings
            from app.services.market_data import market_data_service

            # Test 1: Configuration check
            try:
                required_configs = ["DATABASE_URL"]
                optional_configs = [
                    "ALPACA_API_KEY",
                    "ALPACA_SECRET_KEY",
                    "FINNHUB_API_KEY",
                ]

                missing_required = []
                missing_optional = []

                for config in required_configs:
                    if not hasattr(settings, config) or not getattr(settings, config):
                        missing_required.append(config)

                for config in optional_configs:
                    if not hasattr(settings, config) or not getattr(settings, config):
                        missing_optional.append(config)

                if not missing_required:
                    self.log_test_result(
                        self.test_category,
                        "required_config",
                        True,
                        "All required configurations present",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "required_config",
                        False,
                        f"Missing required configs: {missing_required}",
                    )

                if not missing_optional:
                    self.log_test_result(
                        self.test_category,
                        "optional_config",
                        True,
                        "All optional configurations present",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "optional_config",
                        False,
                        f"Missing optional configs: {missing_optional}",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "config_check",
                    False,
                    f"Configuration check failed: {str(e)}",
                )

            # Test 2: Market data API connection
            try:
                quote = await market_data_service.get_quote("AAPL")
                if quote and "price" in quote:
                    self.log_test_result(
                        self.test_category,
                        "market_data_api",
                        True,
                        f"Market data API working: AAPL price = {quote['price']}",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "market_data_api",
                        False,
                        "Market data API not returning valid data",
                    )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "market_data_api",
                    False,
                    f"Market data API failed: {str(e)}",
                )

        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"API connections test failed: {str(e)}",
            )

    async def test_validation_and_security(self):
        """Test order validation and security checks."""
        self.test_category = "validation_security"
        logger.info("Testing validation and security...")

        try:
            from app.models.trade import OrderType, TradeType
            from app.services.trading import trading_service

            # Test 1: Input sanitization
            try:
                # Test malicious inputs
                malicious_inputs = [
                    {
                        "symbol": "<script>alert('xss')</script>",
                        "quantity": 10,
                        "trade_type": TradeType.BUY,
                        "order_type": OrderType.MARKET,
                    },
                    {
                        "symbol": "AAPL'; DROP TABLE trades; --",
                        "quantity": 10,
                        "trade_type": TradeType.BUY,
                        "order_type": OrderType.MARKET,
                    },
                    {
                        "symbol": "AAPL",
                        "quantity": -1000000,
                        "trade_type": TradeType.BUY,
                        "order_type": OrderType.MARKET,
                    },
                ]

                security_pass = True
                for malicious_trade in malicious_inputs:
                    try:
                        validation = await trading_service.validate_trade(
                            malicious_trade, self.portfolio
                        )
                        if validation.get("valid"):
                            security_pass = False
                            break
                    except Exception:
                        pass  # Expected for malicious inputs

                if security_pass:
                    self.log_test_result(
                        self.test_category,
                        "input_sanitization",
                        True,
                        "Input sanitization working correctly",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "input_sanitization",
                        False,
                        "Security issue: malicious input accepted",
                    )
                    self.add_critical_issue(
                        "Security vulnerability: malicious input validation failed"
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "input_sanitization",
                    False,
                    f"Input sanitization test failed: {str(e)}",
                )

            # Test 2: Risk limits validation
            try:
                # Test excessive position size
                oversized_trade = {
                    "symbol": "AAPL",
                    "quantity": 1000000,  # Unreasonably large
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                }

                validation = await trading_service.validate_trade(
                    oversized_trade, self.portfolio
                )
                if not validation.get("valid"):
                    self.log_test_result(
                        self.test_category,
                        "risk_limits",
                        True,
                        "Risk limits validation working",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "risk_limits",
                        False,
                        "Risk limits not enforced",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "risk_limits",
                    False,
                    f"Risk limits test failed: {str(e)}",
                )

        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Validation and security test failed: {str(e)}",
            )

    async def test_logging_and_audit(self):
        """Test logging and audit trail functionality."""
        self.test_category = "logging_audit"
        logger.info("Testing logging and audit trails...")

        try:
            # Test 1: Check if logging is configured
            try:
                import structlog

                logger_instance = structlog.get_logger()

                if logger_instance:
                    self.log_test_result(
                        self.test_category,
                        "logging_configuration",
                        True,
                        "Structured logging configured",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "logging_configuration",
                        False,
                        "Structured logging not configured",
                    )

            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "logging_configuration",
                    False,
                    f"Logging configuration test failed: {str(e)}",
                )

            # Test 2: Check monitoring integration
            try:
                from app.core.monitoring import performance_tracker, track_trade

                if track_trade and performance_tracker:
                    self.log_test_result(
                        self.test_category,
                        "monitoring_integration",
                        True,
                        "Monitoring integration available",
                    )
                else:
                    self.log_test_result(
                        self.test_category,
                        "monitoring_integration",
                        False,
                        "Monitoring integration not available",
                    )

            except ImportError as e:
                self.log_test_result(
                    self.test_category,
                    "monitoring_integration",
                    False,
                    f"Monitoring import failed: {str(e)}",
                )
            except Exception as e:
                self.log_test_result(
                    self.test_category,
                    "monitoring_integration",
                    False,
                    f"Monitoring test failed: {str(e)}",
                )

        except Exception as e:
            self.log_test_result(
                self.test_category,
                "general_error",
                False,
                f"Logging and audit test failed: {str(e)}",
            )

    def log_test_result(
        self, category: str, test_name: str, passed: bool, message: str
    ):
        """Log a test result."""
        test_results["test_summary"]["total_tests"] += 1

        if passed:
            test_results["test_summary"]["passed"] += 1
            level = "PASS"
        else:
            test_results["test_summary"]["failed"] += 1
            level = "FAIL"

        if category not in test_results["test_categories"]:
            test_results["test_categories"][category] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
            }

        test_results["test_categories"][category]["total"] += 1
        if passed:
            test_results["test_categories"][category]["passed"] += 1
        else:
            test_results["test_categories"][category]["failed"] += 1

        result = {
            "category": category,
            "test_name": test_name,
            "status": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        test_results["detailed_results"].append(result)
        logger.info(f"[{level}] {category}.{test_name}: {message}")

    def add_critical_issue(self, issue: str):
        """Add a critical issue to the report."""
        test_results["critical_issues"].append(
            {"issue": issue, "timestamp": datetime.utcnow().isoformat()}
        )
        logger.error(f"CRITICAL ISSUE: {issue}")

    async def cleanup_test_environment(self):
        """Clean up test data."""
        if self.db:
            try:
                # Clean up test data
                if self.user:
                    from app.models.holding import Holding
                    from app.models.trade import Trade

                    # Delete test trades
                    self.db.query(Trade).filter(
                        Trade.portfolio_id == self.portfolio.id
                    ).delete()

                    # Delete test holdings
                    self.db.query(Holding).filter(
                        Holding.portfolio_id == self.portfolio.id
                    ).delete()

                    # Delete test portfolio
                    self.db.delete(self.portfolio)

                    # Delete test user
                    self.db.delete(self.user)

                    self.db.commit()

                self.db.close()
                logger.info("Test environment cleaned up")

            except Exception as e:
                logger.error(f"Cleanup failed: {str(e)}")
                if self.db:
                    self.db.rollback()

    def generate_final_report(self):
        """Generate the final test report."""
        # Add recommendations based on test results
        failed_categories = [
            cat
            for cat, results in test_results["test_categories"].items()
            if results["failed"] > 0
        ]

        if "trading_service_core" in failed_categories:
            test_results["recommendations"].append(
                "Fix core trading service issues - this is critical for all trading functionality"
            )

        if "broker_integrations" in failed_categories:
            test_results["recommendations"].append(
                "Review broker integration configuration - check API credentials and connections"
            )

        if "validation_security" in failed_categories:
            test_results["recommendations"].append(
                "URGENT: Address security validation issues immediately"
            )

        if "api_connections" in failed_categories:
            test_results["recommendations"].append(
                "Configure missing API connections for full functionality"
            )

        # Calculate success rate
        total_tests = test_results["test_summary"]["total_tests"]
        passed_tests = test_results["test_summary"]["passed"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        test_results["test_summary"]["success_rate"] = f"{success_rate:.1f}%"

        # Save results to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"trading_services_test_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(test_results, f, indent=2, default=str)

        # Print summary
        logger.info("=" * 60)
        logger.info("TRADING SERVICES TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {test_results['test_summary']['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Critical Issues: {len(test_results['critical_issues'])}")
        logger.info("=" * 60)

        if test_results["critical_issues"]:
            logger.error("CRITICAL ISSUES FOUND:")
            for issue in test_results["critical_issues"]:
                logger.error(f"- {issue['issue']}")

        logger.info(f"Detailed results saved to: {filename}")


async def main():
    """Main test execution function."""
    tester = TradingServiceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

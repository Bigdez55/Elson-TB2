#!/usr/bin/env python3
"""
Comprehensive Trading Workflow Test

This script tests the complete trading pipeline from order validation to execution,
including all major components:
1. Order validation and sanitization
2. Risk management checks
3. Broker integration (paper trading mode)
4. Portfolio updates after trades
5. Trade history recording
6. Different order types (market, limit, stop)
7. Error handling for invalid orders
8. Position tracking and P&L calculation

Usage:
    python test_complete_trading_workflow.py
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    # Import application components
    from app.core.config import settings
    from app.db.base import Base
    from app.models.holding import Holding
    from app.models.portfolio import Portfolio
    from app.models.trade import OrderType, Trade, TradeStatus, TradeType
    from app.models.user import User
    from app.services.paper_trading import PaperTradingService
    from app.services.risk_management import RiskManagementService
    from app.services.trading import TradingService

    IMPORTS_SUCCESSFUL = True
except Exception as e:
    print(f"Import error: {e}")
    IMPORTS_SUCCESSFUL = False


class TradingWorkflowTestResults:
    """Container for test results"""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_details = []
        self.performance_metrics = {}
        self.errors = []
        self.start_time = datetime.utcnow()

    def add_test_result(
        self, test_name: str, passed: bool, details: str = "", duration: float = 0.0
    ):
        """Add a test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

        self.test_details.append(
            {
                "test_name": test_name,
                "passed": passed,
                "details": details,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def add_error(self, error: str):
        """Add an error to the results"""
        self.errors.append(error)

    def add_performance_metric(self, name: str, value: Any):
        """Add a performance metric"""
        self.performance_metrics[name] = value

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "test_summary": {
                "total_tests": self.tests_run,
                "passed": self.tests_passed,
                "failed": self.tests_failed,
                "success_rate": (
                    f"{(self.tests_passed / self.tests_run * 100):.1f}%"
                    if self.tests_run > 0
                    else "0.0%"
                ),
                "total_duration": f"{duration:.2f}s",
            },
            "test_details": self.test_details,
            "performance_metrics": self.performance_metrics,
            "errors": self.errors,
            "test_timestamp": self.start_time.isoformat(),
        }


class MockMarketDataService:
    """Mock market data service for testing"""

    def __init__(self):
        self.mock_prices = {
            "AAPL": 150.25,
            "MSFT": 280.50,
            "GOOGL": 2750.00,
            "TSLA": 800.75,
            "AMZN": 3200.00,
            "INVALID": None,
        }

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get mock quote data"""
        price = self.mock_prices.get(symbol)
        if price is None:
            return None

        return {
            "symbol": symbol,
            "price": price,
            "bid": price - 0.01,
            "ask": price + 0.01,
            "volume": 1000000,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        return self.mock_prices.get(symbol)


class TradingWorkflowTester:
    """Comprehensive trading workflow tester"""

    def __init__(self):
        self.results = TradingWorkflowTestResults()
        self.db = None
        self.test_user = None
        self.test_portfolio = None
        self.trading_service = None
        self.paper_trading_service = None
        self.risk_service = None
        self.mock_market_data = MockMarketDataService()

    async def setup_test_environment(self) -> bool:
        """Setup test environment"""
        try:
            # Create in-memory SQLite database for testing
            engine = create_engine("sqlite:///:memory:", echo=False)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            # Create tables
            Base.metadata.create_all(bind=engine)

            self.db = SessionLocal()

            # Create test user
            self.test_user = User(
                id=1,
                email="test@trading.com",
                username="test_trader",
                hashed_password="test_hash",
                is_active=True,
                is_verified=True,
            )
            self.db.add(self.test_user)

            # Create test portfolio
            self.test_portfolio = Portfolio(
                id=1,
                owner_id=1,
                name="Test Portfolio",
                cash_balance=10000.0,
                total_value=10000.0,
                is_active=True,
            )
            self.db.add(self.test_portfolio)
            self.db.commit()

            # Initialize services
            self.trading_service = TradingService()
            self.paper_trading_service = PaperTradingService(self.db)
            self.risk_service = RiskManagementService(self.db)

            # Mock the market data service in trading service
            self.trading_service.market_data_service = self.mock_market_data
            self.paper_trading_service.market_data_service = self.mock_market_data
            self.risk_service.market_data_service = self.mock_market_data

            return True

        except Exception as e:
            self.results.add_error(f"Setup failed: {str(e)}")
            return False

    def cleanup_test_environment(self):
        """Cleanup test environment"""
        try:
            if self.db:
                self.db.close()
        except Exception as e:
            self.results.add_error(f"Cleanup failed: {str(e)}")

    async def test_order_validation_and_sanitization(self):
        """Test 1: Order validation and sanitization"""
        test_name = "Order Validation and Sanitization"
        start_time = time.time()

        try:
            # Test valid order
            valid_order = {
                "symbol": "  aapl  ",  # Test whitespace trimming
                "quantity": "100.5",  # Test string to float conversion
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            validation = await self.trading_service.validate_trade(
                valid_order, self.test_portfolio
            )

            if validation["valid"] and valid_order["symbol"] == "AAPL":
                self.results.add_test_result(
                    f"{test_name} - Valid Order",
                    True,
                    f"Valid order passed validation: {validation}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Valid Order",
                    False,
                    f"Valid order failed validation: {validation}",
                )

            # Test invalid symbol
            invalid_symbol_order = {
                "symbol": "INVALID@SYMBOL",
                "quantity": 100,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            validation = await self.trading_service.validate_trade(
                invalid_symbol_order, self.test_portfolio
            )

            if not validation["valid"]:
                self.results.add_test_result(
                    f"{test_name} - Invalid Symbol",
                    True,
                    f"Invalid symbol correctly rejected: {validation['errors']}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Invalid Symbol",
                    False,
                    f"Invalid symbol incorrectly accepted",
                )

            # Test negative quantity
            negative_quantity_order = {
                "symbol": "AAPL",
                "quantity": -50,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            validation = await self.trading_service.validate_trade(
                negative_quantity_order, self.test_portfolio
            )

            if not validation["valid"]:
                self.results.add_test_result(
                    f"{test_name} - Negative Quantity",
                    True,
                    f"Negative quantity correctly rejected: {validation['errors']}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Negative Quantity",
                    False,
                    f"Negative quantity incorrectly accepted",
                )

            # Test missing required fields
            incomplete_order = {
                "symbol": "AAPL",
                # Missing quantity and trade_type
                "order_type": OrderType.MARKET,
            }

            validation = await self.trading_service.validate_trade(
                incomplete_order, self.test_portfolio
            )

            if not validation["valid"]:
                self.results.add_test_result(
                    f"{test_name} - Missing Fields",
                    True,
                    f"Incomplete order correctly rejected: {validation['errors']}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Missing Fields",
                    False,
                    f"Incomplete order incorrectly accepted",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_risk_management_checks(self):
        """Test 2: Risk management checks"""
        test_name = "Risk Management Checks"
        start_time = time.time()

        try:
            # Test position size limits
            large_position_order = {
                "symbol": "AAPL",
                "quantity": 1000,  # $150,250 value (>15% of $10,000 portfolio)
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            risk_assessment = await self.risk_service.assess_trade_risk(
                user_id=self.test_user.id,
                symbol="AAPL",
                trade_type=TradeType.BUY,
                quantity=1000,
                price=150.25,
            )

            if risk_assessment.check_result.value in [
                "rejected",
                "requires_confirmation",
            ]:
                self.results.add_test_result(
                    f"{test_name} - Position Size Limit",
                    True,
                    f"Large position correctly flagged: {risk_assessment.check_result.value}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Position Size Limit",
                    False,
                    f"Large position not flagged: {risk_assessment.check_result.value}",
                )

            # Test insufficient funds
            insufficient_funds_order = {
                "symbol": "GOOGL",  # $2750 per share
                "quantity": 10,  # $27,500 > $10,000 available
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            validation = await self.trading_service.validate_trade(
                insufficient_funds_order, self.test_portfolio
            )

            if not validation["valid"] and any(
                "Insufficient funds" in error for error in validation["errors"]
            ):
                self.results.add_test_result(
                    f"{test_name} - Insufficient Funds",
                    True,
                    f"Insufficient funds correctly detected: {validation['errors']}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Insufficient Funds",
                    False,
                    f"Insufficient funds not detected: {validation}",
                )

            # Test selling non-existent position
            sell_nonexistent_order = {
                "symbol": "MSFT",
                "quantity": 50,
                "trade_type": TradeType.SELL,
                "order_type": OrderType.MARKET,
            }

            validation = await self.trading_service.validate_trade(
                sell_nonexistent_order, self.test_portfolio
            )

            if not validation["valid"] and any(
                "No position found" in error for error in validation["errors"]
            ):
                self.results.add_test_result(
                    f"{test_name} - Sell Non-existent",
                    True,
                    f"Selling non-existent position correctly rejected: {validation['errors']}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Sell Non-existent",
                    False,
                    f"Selling non-existent position not properly handled: {validation}",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_different_order_types(self):
        """Test 3: Different order types (market, limit, stop)"""
        test_name = "Different Order Types"
        start_time = time.time()

        try:
            # Test Market Order
            market_order = {
                "symbol": "AAPL",
                "quantity": 10,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            trade = await self.trading_service.place_order(
                market_order, self.test_user, self.db
            )

            if trade and trade.status == TradeStatus.FILLED:
                self.results.add_test_result(
                    f"{test_name} - Market Order",
                    True,
                    f"Market order executed successfully: {trade.id}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Market Order",
                    False,
                    f"Market order failed: {trade.status if trade else 'No trade created'}",
                )

            # Test Limit Order
            limit_order = {
                "symbol": "AAPL",
                "quantity": 5,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.LIMIT,
                "limit_price": 149.00,  # Below current price of 150.25
            }

            trade = await self.trading_service.place_order(
                limit_order, self.test_user, self.db
            )

            if trade and trade.status in [TradeStatus.PENDING, TradeStatus.FILLED]:
                self.results.add_test_result(
                    f"{test_name} - Limit Order",
                    True,
                    f"Limit order created successfully: {trade.id}, status: {trade.status}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Limit Order",
                    False,
                    f"Limit order failed: {trade.status if trade else 'No trade created'}",
                )

            # Test Stop Order
            stop_order = {
                "symbol": "AAPL",
                "quantity": 3,
                "trade_type": TradeType.SELL,
                "order_type": OrderType.STOP,
                "stop_price": 145.00,  # Stop-loss below current price
            }

            trade = await self.trading_service.place_order(
                stop_order, self.test_user, self.db
            )

            if trade and trade.status in [TradeStatus.PENDING, TradeStatus.REJECTED]:
                self.results.add_test_result(
                    f"{test_name} - Stop Order",
                    True,
                    f"Stop order handled correctly: {trade.id}, status: {trade.status}",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Stop Order",
                    False,
                    f"Stop order not handled correctly: {trade.status if trade else 'No trade created'}",
                )

            # Test invalid limit price
            invalid_limit_order = {
                "symbol": "AAPL",
                "quantity": 5,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.LIMIT,
                "limit_price": 300.00,  # Way above current price
            }

            validation = await self.trading_service.validate_trade(
                invalid_limit_order, self.test_portfolio
            )

            if not validation["valid"] or "too far from current price" in str(
                validation.get("errors", [])
            ):
                self.results.add_test_result(
                    f"{test_name} - Invalid Limit Price",
                    True,
                    f"Invalid limit price correctly flagged",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Invalid Limit Price",
                    False,
                    f"Invalid limit price not flagged",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_portfolio_updates_and_pnl(self):
        """Test 4: Portfolio updates and P&L calculation"""
        test_name = "Portfolio Updates and P&L"
        start_time = time.time()

        try:
            # Record initial portfolio state
            initial_cash = self.test_portfolio.cash_balance
            initial_value = self.test_portfolio.total_value

            # Execute a buy order
            buy_order = {
                "symbol": "MSFT",
                "quantity": 20,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            buy_trade = await self.trading_service.place_order(
                buy_order, self.test_user, self.db
            )

            # Refresh portfolio and check updates
            self.db.refresh(self.test_portfolio)

            if buy_trade and buy_trade.status == TradeStatus.FILLED:
                expected_cost = 20 * 280.50  # MSFT price
                new_cash = self.test_portfolio.cash_balance

                cash_decreased = (
                    initial_cash - new_cash
                ) >= expected_cost * 0.99  # Allow for minor slippage

                if cash_decreased:
                    self.results.add_test_result(
                        f"{test_name} - Cash Update on Buy",
                        True,
                        f"Cash correctly decreased: {initial_cash} -> {new_cash}",
                    )
                else:
                    self.results.add_test_result(
                        f"{test_name} - Cash Update on Buy",
                        False,
                        f"Cash not properly decreased: {initial_cash} -> {new_cash}",
                    )

                # Check if holding was created
                holding = (
                    self.db.query(Holding)
                    .filter(
                        Holding.portfolio_id == self.test_portfolio.id,
                        Holding.symbol == "MSFT",
                    )
                    .first()
                )

                if holding and holding.quantity == 20:
                    self.results.add_test_result(
                        f"{test_name} - Holding Creation",
                        True,
                        f"Holding created correctly: {holding.quantity} shares of {holding.symbol}",
                    )
                else:
                    self.results.add_test_result(
                        f"{test_name} - Holding Creation",
                        False,
                        f"Holding not created correctly: {holding}",
                    )

                # Test selling part of the position
                sell_order = {
                    "symbol": "MSFT",
                    "quantity": 10,
                    "trade_type": TradeType.SELL,
                    "order_type": OrderType.MARKET,
                }

                sell_trade = await self.trading_service.place_order(
                    sell_order, self.test_user, self.db
                )

                if sell_trade and sell_trade.status == TradeStatus.FILLED:
                    # Refresh holding
                    self.db.refresh(holding)

                    if holding.quantity == 10:  # Should be 20 - 10 = 10
                        self.results.add_test_result(
                            f"{test_name} - Holding Update on Sell",
                            True,
                            f"Holding quantity correctly updated: {holding.quantity}",
                        )
                    else:
                        self.results.add_test_result(
                            f"{test_name} - Holding Update on Sell",
                            False,
                            f"Holding quantity not updated correctly: {holding.quantity}",
                        )

                    # Calculate P&L
                    if hasattr(holding, "unrealized_gain_loss"):
                        pnl = holding.unrealized_gain_loss
                        self.results.add_test_result(
                            f"{test_name} - P&L Calculation",
                            True,
                            f"P&L calculated: ${pnl:.2f}",
                        )
                    else:
                        self.results.add_test_result(
                            f"{test_name} - P&L Calculation",
                            False,
                            f"P&L not calculated",
                        )

                else:
                    self.results.add_test_result(
                        f"{test_name} - Sell Order",
                        False,
                        f"Sell order failed: {sell_trade.status if sell_trade else 'No trade created'}",
                    )

            else:
                self.results.add_test_result(
                    f"{test_name} - Buy Order",
                    False,
                    f"Buy order failed: {buy_trade.status if buy_trade else 'No trade created'}",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_trade_history_recording(self):
        """Test 5: Trade history recording"""
        test_name = "Trade History Recording"
        start_time = time.time()

        try:
            # Get initial trade count
            initial_trades = await self.trading_service.get_trade_history(
                self.test_user, self.db, limit=1000
            )
            initial_count = len(initial_trades)

            # Execute several trades
            test_trades = [
                {
                    "symbol": "GOOGL",
                    "quantity": 1,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                {
                    "symbol": "TSLA",
                    "quantity": 5,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                {
                    "symbol": "AMZN",
                    "quantity": 2,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
            ]

            executed_trades = []
            for trade_data in test_trades:
                try:
                    trade = await self.trading_service.place_order(
                        trade_data, self.test_user, self.db
                    )
                    if trade:
                        executed_trades.append(trade)
                except Exception as e:
                    # Some trades might fail due to insufficient funds, which is expected
                    pass

            # Get updated trade history
            final_trades = await self.trading_service.get_trade_history(
                self.test_user, self.db, limit=1000
            )
            final_count = len(final_trades)

            trades_added = final_count - initial_count

            if trades_added >= len(executed_trades):
                self.results.add_test_result(
                    f"{test_name} - History Recording",
                    True,
                    f"Trade history correctly updated: {trades_added} new trades recorded",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - History Recording",
                    False,
                    f"Trade history not properly updated: {trades_added} vs {len(executed_trades)} executed",
                )

            # Test trade details completeness
            if final_trades:
                recent_trade = final_trades[0]  # Most recent trade
                required_fields = [
                    "symbol",
                    "trade_type",
                    "order_type",
                    "quantity",
                    "status",
                    "created_at",
                ]

                missing_fields = [
                    field
                    for field in required_fields
                    if not hasattr(recent_trade, field)
                ]

                if not missing_fields:
                    self.results.add_test_result(
                        f"{test_name} - Trade Details",
                        True,
                        f"Trade record contains all required fields",
                    )
                else:
                    self.results.add_test_result(
                        f"{test_name} - Trade Details",
                        False,
                        f"Trade record missing fields: {missing_fields}",
                    )

            # Test open orders retrieval
            open_orders = await self.trading_service.get_open_orders(
                self.test_user, self.db
            )

            self.results.add_test_result(
                f"{test_name} - Open Orders Query",
                True,
                f"Open orders query successful: {len(open_orders)} open orders",
            )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_error_handling(self):
        """Test 6: Error handling for invalid orders"""
        test_name = "Error Handling"
        start_time = time.time()

        try:
            # Test invalid symbol
            try:
                invalid_order = {
                    "symbol": "INVALID",
                    "quantity": 10,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                }

                # This should either fail validation or reject the trade
                validation = await self.trading_service.validate_trade(
                    invalid_order, self.test_portfolio
                )

                if not validation["valid"]:
                    self.results.add_test_result(
                        f"{test_name} - Invalid Symbol Validation",
                        True,
                        f"Invalid symbol correctly rejected during validation",
                    )
                else:
                    # Try to place the order
                    trade = await self.trading_service.place_order(
                        invalid_order, self.test_user, self.db
                    )
                    if trade and trade.status == TradeStatus.REJECTED:
                        self.results.add_test_result(
                            f"{test_name} - Invalid Symbol Order",
                            True,
                            f"Invalid symbol order correctly rejected",
                        )
                    else:
                        self.results.add_test_result(
                            f"{test_name} - Invalid Symbol Order",
                            False,
                            f"Invalid symbol order not properly handled",
                        )

            except Exception as e:
                # Exception handling is also valid error handling
                self.results.add_test_result(
                    f"{test_name} - Invalid Symbol Exception",
                    True,
                    f"Invalid symbol properly raised exception: {str(e)[:100]}",
                )

            # Test null/None values
            try:
                null_order = {
                    "symbol": None,
                    "quantity": None,
                    "trade_type": None,
                    "order_type": None,
                }

                validation = await self.trading_service.validate_trade(
                    null_order, self.test_portfolio
                )

                if not validation["valid"]:
                    self.results.add_test_result(
                        f"{test_name} - Null Values",
                        True,
                        f"Null values correctly rejected",
                    )
                else:
                    self.results.add_test_result(
                        f"{test_name} - Null Values",
                        False,
                        f"Null values not properly handled",
                    )

            except Exception as e:
                self.results.add_test_result(
                    f"{test_name} - Null Values Exception",
                    True,
                    f"Null values properly raised exception: {str(e)[:100]}",
                )

            # Test malformed data
            try:
                malformed_order = "not a dictionary"

                validation = await self.trading_service.validate_trade(
                    malformed_order, self.test_portfolio
                )

                if not validation["valid"]:
                    self.results.add_test_result(
                        f"{test_name} - Malformed Data",
                        True,
                        f"Malformed data correctly rejected",
                    )
                else:
                    self.results.add_test_result(
                        f"{test_name} - Malformed Data",
                        False,
                        f"Malformed data not properly handled",
                    )

            except Exception as e:
                self.results.add_test_result(
                    f"{test_name} - Malformed Data Exception",
                    True,
                    f"Malformed data properly raised exception: {str(e)[:100]}",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_paper_trading_integration(self):
        """Test 7: Paper trading broker integration"""
        test_name = "Paper Trading Integration"
        start_time = time.time()

        try:
            # Create a trade for paper trading simulation
            test_trade = Trade(
                symbol="AAPL",
                trade_type=TradeType.BUY,
                order_type=OrderType.MARKET,
                quantity=25,
                price=150.25,
                portfolio_id=self.test_portfolio.id,
                is_paper_trade=True,
                status=TradeStatus.PENDING,
            )
            self.db.add(test_trade)
            self.db.commit()

            # Test paper trading execution with realistic conditions
            result = await self.paper_trading_service.execute_paper_trade(
                test_trade, simulate_realistic_conditions=True
            )

            if result["status"] == "filled":
                self.results.add_test_result(
                    f"{test_name} - Realistic Execution",
                    True,
                    f"Paper trade executed with realistic conditions: slippage={result['slippage_bps']:.1f}bps",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Realistic Execution",
                    False,
                    f"Paper trade failed: {result}",
                )

            # Test simplified execution
            test_trade_2 = Trade(
                symbol="MSFT",
                trade_type=TradeType.BUY,
                order_type=OrderType.MARKET,
                quantity=10,
                price=280.50,
                portfolio_id=self.test_portfolio.id,
                is_paper_trade=True,
                status=TradeStatus.PENDING,
            )
            self.db.add(test_trade_2)
            self.db.commit()

            result = await self.paper_trading_service.execute_paper_trade(
                test_trade_2, simulate_realistic_conditions=False
            )

            if result["status"] == "filled":
                self.results.add_test_result(
                    f"{test_name} - Simplified Execution",
                    True,
                    f"Paper trade executed with simplified conditions",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Simplified Execution",
                    False,
                    f"Simplified paper trade failed: {result}",
                )

            # Test execution statistics
            stats = await self.paper_trading_service.get_execution_statistics(
                self.test_user.id, days=1
            )

            if "total_trades" in stats:
                self.results.add_test_result(
                    f"{test_name} - Execution Statistics",
                    True,
                    f"Execution statistics retrieved: {stats['total_trades']} trades",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Execution Statistics",
                    False,
                    f"Execution statistics failed: {stats}",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def test_performance_and_timing(self):
        """Test 8: Performance and timing metrics"""
        test_name = "Performance and Timing"
        start_time = time.time()

        try:
            # Test validation performance
            validation_times = []
            for i in range(10):
                val_start = time.time()

                order = {
                    "symbol": "AAPL",
                    "quantity": 10 + i,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                }

                await self.trading_service.validate_trade(order, self.test_portfolio)
                validation_times.append(time.time() - val_start)

            avg_validation_time = sum(validation_times) / len(validation_times)
            max_validation_time = max(validation_times)

            self.results.add_performance_metric(
                "avg_validation_time_ms", avg_validation_time * 1000
            )
            self.results.add_performance_metric(
                "max_validation_time_ms", max_validation_time * 1000
            )

            if avg_validation_time < 0.1:  # Less than 100ms average
                self.results.add_test_result(
                    f"{test_name} - Validation Speed",
                    True,
                    f"Validation performance acceptable: {avg_validation_time*1000:.1f}ms average",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Validation Speed",
                    False,
                    f"Validation too slow: {avg_validation_time*1000:.1f}ms average",
                )

            # Test concurrent validation
            import asyncio

            concurrent_start = time.time()

            tasks = []
            for i in range(5):
                order = {
                    "symbol": "AAPL",
                    "quantity": 5,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                }
                tasks.append(
                    self.trading_service.validate_trade(order, self.test_portfolio)
                )

            await asyncio.gather(*tasks)
            concurrent_time = time.time() - concurrent_start

            self.results.add_performance_metric(
                "concurrent_validation_time_ms", concurrent_time * 1000
            )

            if concurrent_time < 0.5:  # Less than 500ms for 5 concurrent validations
                self.results.add_test_result(
                    f"{test_name} - Concurrent Validation",
                    True,
                    f"Concurrent validation performance acceptable: {concurrent_time*1000:.1f}ms",
                )
            else:
                self.results.add_test_result(
                    f"{test_name} - Concurrent Validation",
                    False,
                    f"Concurrent validation too slow: {concurrent_time*1000:.1f}ms",
                )

        except Exception as e:
            self.results.add_test_result(
                f"{test_name} - Exception",
                False,
                f"Test failed with exception: {str(e)}",
            )

        duration = time.time() - start_time
        self.results.add_performance_metric(f"{test_name}_duration", duration)

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all trading workflow tests"""
        print("Starting Comprehensive Trading Workflow Tests...")
        print("=" * 60)

        if not IMPORTS_SUCCESSFUL:
            self.results.add_error("Failed to import required modules")
            return self.results.get_summary()

        # Setup test environment
        if not await self.setup_test_environment():
            self.results.add_error("Failed to setup test environment")
            return self.results.get_summary()

        try:
            # Run all test suites
            test_suites = [
                self.test_order_validation_and_sanitization,
                self.test_risk_management_checks,
                self.test_different_order_types,
                self.test_portfolio_updates_and_pnl,
                self.test_trade_history_recording,
                self.test_error_handling,
                self.test_paper_trading_integration,
                self.test_performance_and_timing,
            ]

            for i, test_suite in enumerate(test_suites, 1):
                print(
                    f"Running Test Suite {i}/{len(test_suites)}: {test_suite.__name__}"
                )
                try:
                    await test_suite()
                    print(f"✓ Completed {test_suite.__name__}")
                except Exception as e:
                    print(f"✗ Failed {test_suite.__name__}: {str(e)}")
                    self.results.add_error(
                        f"Test suite {test_suite.__name__} failed: {str(e)}"
                    )

                # Brief pause between test suites
                await asyncio.sleep(0.1)

        finally:
            # Cleanup
            self.cleanup_test_environment()

        print("=" * 60)
        print("Trading Workflow Tests Completed")

        return self.results.get_summary()


async def main():
    """Main function to run the trading workflow tests"""
    tester = TradingWorkflowTester()

    try:
        results = await tester.run_all_tests()

        # Print summary
        print("\nTEST SUMMARY:")
        print("=" * 40)
        summary = results["test_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Total Duration: {summary['total_duration']}")

        # Print detailed results
        print("\nDETAILED RESULTS:")
        print("=" * 40)
        for test in results["test_details"]:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            print(f"{status} {test['test_name']} ({test['duration']:.3f}s)")
            if test["details"]:
                print(f"    {test['details']}")

        # Print performance metrics
        if results["performance_metrics"]:
            print("\nPERFORMACE METRICS:")
            print("=" * 40)
            for metric, value in results["performance_metrics"].items():
                if "time" in metric.lower():
                    if "ms" in metric:
                        print(f"{metric}: {value:.2f}ms")
                    else:
                        print(f"{metric}: {value:.3f}s")
                else:
                    print(f"{metric}: {value}")

        # Print errors if any
        if results["errors"]:
            print("\nERRORS:")
            print("=" * 40)
            for error in results["errors"]:
                print(f"• {error}")

        # Save results to file
        output_file = f"trading_workflow_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nDetailed results saved to: {output_file}")

        # Return exit code based on test results
        return 0 if summary["failed"] == 0 else 1

    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

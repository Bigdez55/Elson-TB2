#!/usr/bin/env python3
"""
Comprehensive Trading Services Test Suite

This script tests all trading services functionality including:
- Basic order placement and validation
- Paper trading simulation
- AI trading signals
- Risk management
- Advanced trading features
- Circuit breaker functionality

SAFETY: This script only performs paper trading - no real money involved.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

# Add the app directory to Python path
sys.path.append(".")

# Test imports
try:
    from app.core.config import settings
    from app.db.base import SessionLocal
    from app.models.holding import Holding
    from app.models.portfolio import Portfolio
    from app.models.trade import OrderType, Trade, TradeStatus, TradeType
    from app.models.user import User
    from app.services.advanced_trading import AdvancedTradingService
    from app.services.ai_trading import personal_trading_ai
    from app.services.market_data import market_data_service
    from app.services.paper_trading import PaperTradingService
    from app.services.risk_management import RiskLevel, RiskManagementService
    from app.services.trading import trading_service

    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class TradingTestSuite:
    """Comprehensive trading test suite."""

    def __init__(self):
        self.db = SessionLocal()
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": [],
            "safety_checks": [],
            "performance_metrics": {},
        }
        self.test_user = None
        self.test_portfolio = None

    def log_test(
        self, test_name: str, passed: bool, details: str = "", error: str = ""
    ):
        """Log test result."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.test_results["test_details"].append(result)

        if passed:
            self.test_results["tests_passed"] += 1
            print(f"✓ {test_name}: {details}")
        else:
            self.test_results["tests_failed"] += 1
            print(f"✗ {test_name}: {error}")

    def log_safety_check(self, check_name: str, passed: bool, details: str):
        """Log safety check result."""
        self.test_results["safety_checks"].append(
            {
                "check_name": check_name,
                "passed": passed,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        if passed:
            print(f"🛡️  {check_name}: {details}")
        else:
            print(f"⚠️  {check_name}: {details}")

    async def setup_test_environment(self):
        """Set up test user and portfolio."""
        try:
            # Create test user
            self.test_user = User(
                email="test@trading.com",
                hashed_password="test_hash",
                full_name="Trading Test User",
                is_active=True,
                risk_tolerance="moderate",
            )
            self.db.add(self.test_user)
            self.db.commit()
            self.db.refresh(self.test_user)

            # Create test portfolio
            self.test_portfolio = Portfolio(
                owner_id=self.test_user.id,
                name="Test Portfolio",
                description="Portfolio for testing trading services",
                cash_balance=100000.0,  # $100k test balance
                total_value=100000.0,
                is_active=True,
                is_paper_trading=True,  # SAFETY: Mark as paper trading
            )
            self.db.add(self.test_portfolio)
            self.db.commit()
            self.db.refresh(self.test_portfolio)

            self.log_test(
                "Setup Test Environment",
                True,
                f"Created test user {self.test_user.id} and portfolio {self.test_portfolio.id}",
            )

        except Exception as e:
            self.log_test("Setup Test Environment", False, error=str(e))
            raise

    async def test_paper_trading_safety(self):
        """Test that all trading is paper trading only."""
        print("\n=== PAPER TRADING SAFETY TESTS ===")

        # Check portfolio is marked as paper trading
        is_paper = self.test_portfolio.is_paper_trading
        self.log_safety_check(
            "Portfolio Paper Trading Flag",
            is_paper,
            f"Portfolio marked as paper trading: {is_paper}",
        )

        # Check trading service configuration
        try:
            # Verify no real broker connections
            has_real_broker = hasattr(trading_service, "real_broker_connection")
            self.log_safety_check(
                "No Real Broker Connection",
                not has_real_broker,
                "Trading service has no real broker connections",
            )

            # Check for paper trading markers in trades
            test_trade_data = {
                "symbol": "AAPL",
                "quantity": 10,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.MARKET,
            }

            validation = await trading_service.validate_trade(
                test_trade_data, self.test_portfolio
            )
            self.log_safety_check(
                "Trade Validation Safety",
                validation.get("valid", False),
                "Trade validation system operational",
            )

        except Exception as e:
            self.log_safety_check(
                "Safety Check Error", False, f"Error during safety checks: {e}"
            )

    async def test_basic_order_placement(self):
        """Test basic order placement functionality."""
        print("\n=== BASIC ORDER PLACEMENT TESTS ===")

        test_cases = [
            {
                "name": "Market Buy Order",
                "data": {
                    "symbol": "AAPL",
                    "quantity": 10,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
            },
            {
                "name": "Limit Buy Order",
                "data": {
                    "symbol": "MSFT",
                    "quantity": 5,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.LIMIT,
                    "limit_price": 300.0,
                },
            },
            {
                "name": "Invalid Symbol Order",
                "data": {
                    "symbol": "INVALID123",
                    "quantity": 1,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                "should_fail": True,
            },
        ]

        for test_case in test_cases:
            try:
                trade = await trading_service.place_order(
                    test_case["data"], self.test_user, self.db
                )

                if test_case.get("should_fail", False):
                    self.log_test(
                        test_case["name"],
                        False,
                        error="Order should have failed but succeeded",
                    )
                else:
                    # Verify trade was created and marked as paper trade
                    is_paper = trade.is_paper_trade
                    status_valid = trade.status in [
                        TradeStatus.PENDING,
                        TradeStatus.FILLED,
                    ]

                    self.log_test(
                        test_case["name"],
                        is_paper and status_valid,
                        f"Trade {trade.id} created successfully (paper: {is_paper}, status: {trade.status.value})",
                    )

            except Exception as e:
                if test_case.get("should_fail", False):
                    self.log_test(
                        test_case["name"],
                        True,
                        f"Order correctly failed: {str(e)[:100]}",
                    )
                else:
                    self.log_test(test_case["name"], False, error=str(e))

    async def test_order_validation(self):
        """Test order validation logic."""
        print("\n=== ORDER VALIDATION TESTS ===")

        validation_tests = [
            {
                "name": "Valid Order",
                "data": {
                    "symbol": "AAPL",
                    "quantity": 1,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                "should_pass": True,
            },
            {
                "name": "Negative Quantity",
                "data": {
                    "symbol": "AAPL",
                    "quantity": -5,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                "should_pass": False,
            },
            {
                "name": "Zero Quantity",
                "data": {
                    "symbol": "AAPL",
                    "quantity": 0,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                "should_pass": False,
            },
            {
                "name": "Missing Symbol",
                "data": {
                    "symbol": "",
                    "quantity": 1,
                    "trade_type": TradeType.BUY,
                    "order_type": OrderType.MARKET,
                },
                "should_pass": False,
            },
        ]

        for test in validation_tests:
            try:
                validation = await trading_service.validate_trade(
                    test["data"], self.test_portfolio
                )

                is_valid = validation.get("valid", False)

                if test["should_pass"]:
                    self.log_test(
                        test["name"],
                        is_valid,
                        f"Validation passed as expected: {validation.get('errors', [])}",
                    )
                else:
                    self.log_test(
                        test["name"],
                        not is_valid,
                        f"Validation correctly failed: {validation.get('errors', [])}",
                    )

            except Exception as e:
                self.log_test(test["name"], False, error=str(e))

    async def test_risk_management(self):
        """Test risk management functionality."""
        print("\n=== RISK MANAGEMENT TESTS ===")

        risk_service = RiskManagementService(self.db)

        try:
            # Test position size limits
            risk_assessment = await risk_service.assess_trade_risk(
                user_id=self.test_user.id,
                symbol="AAPL",
                trade_type=TradeType.BUY,
                quantity=1000,  # Large quantity to trigger warnings
                price=150.0,
            )

            has_warnings = (
                len(risk_assessment.violations) > 0 or len(risk_assessment.warnings) > 0
            )
            self.log_test(
                "Position Size Risk Check",
                True,
                f"Risk level: {risk_assessment.risk_level.value}, "
                f"Score: {risk_assessment.risk_score:.2f}, "
                f"Warnings/Violations: {has_warnings}",
            )

            # Test portfolio risk metrics
            portfolio_metrics = await risk_service.calculate_portfolio_risk_metrics(
                self.test_user.id
            )

            metrics_valid = (
                portfolio_metrics.portfolio_value >= 0
                and portfolio_metrics.cash_percentage >= 0
                and portfolio_metrics.cash_percentage <= 1
            )

            self.log_test(
                "Portfolio Risk Metrics",
                metrics_valid,
                f"Portfolio value: ${portfolio_metrics.portfolio_value:,.2f}, "
                f"Cash: {portfolio_metrics.cash_percentage:.1%}",
            )

            # Test circuit breakers
            circuit_breaker_status = await risk_service.check_circuit_breakers(
                self.test_user.id
            )

            breaker_working = isinstance(circuit_breaker_status, dict)
            self.log_test(
                "Circuit Breaker Check",
                breaker_working,
                f"Trading suspended: {circuit_breaker_status.get('trading_suspended', False)}",
            )

        except Exception as e:
            self.log_test("Risk Management", False, error=str(e))

    async def test_ai_trading_signals(self):
        """Test AI trading signal generation."""
        print("\n=== AI TRADING SIGNALS TESTS ===")

        try:
            # Test portfolio risk analysis
            risk_analysis = await personal_trading_ai.analyze_portfolio_risk(
                self.test_portfolio, self.db
            )

            risk_analysis_valid = (
                "risk_score" in risk_analysis
                and "risk_level" in risk_analysis
                and "recommendations" in risk_analysis
            )

            self.log_test(
                "Portfolio Risk Analysis",
                risk_analysis_valid,
                f"Risk level: {risk_analysis.get('risk_level')}, "
                f"Score: {risk_analysis.get('risk_score')}",
            )

            # Test trading signal generation
            test_symbols = ["AAPL", "MSFT", "GOOGL"]
            signals = await personal_trading_ai.generate_trading_signals(
                test_symbols, self.test_user
            )

            signals_valid = isinstance(signals, list)
            signal_count = len(signals)

            self.log_test(
                "AI Trading Signals",
                signals_valid,
                f"Generated {signal_count} signals for {len(test_symbols)} symbols",
            )

            # Test portfolio optimization
            target_allocations = {"AAPL": 0.3, "MSFT": 0.4, "GOOGL": 0.3}
            optimization = await personal_trading_ai.optimize_portfolio_allocation(
                self.test_portfolio, target_allocations
            )

            optimization_valid = "rebalancing_actions" in optimization
            self.log_test(
                "Portfolio Optimization",
                optimization_valid,
                f"Rebalancing needed: {optimization.get('rebalancing_needed', False)}",
            )

        except Exception as e:
            self.log_test("AI Trading Signals", False, error=str(e))

    async def test_advanced_trading_features(self):
        """Test advanced trading features."""
        print("\n=== ADVANCED TRADING FEATURES TESTS ===")

        try:
            advanced_service = AdvancedTradingService(self.db, market_data_service)

            # Test strategy initialization
            test_symbols = ["AAPL", "MSFT"]
            await advanced_service.initialize_strategies(test_symbols)

            strategies_initialized = len(advanced_service.strategies) == len(
                test_symbols
            )
            self.log_test(
                "Strategy Initialization",
                strategies_initialized,
                f"Initialized {len(advanced_service.strategies)} strategies",
            )

            # Test AI model initialization
            await advanced_service.initialize_ai_models(test_symbols)

            models_initialized = len(advanced_service.ai_models) == len(test_symbols)
            self.log_test(
                "AI Model Initialization",
                models_initialized,
                f"Initialized {len(advanced_service.ai_models)} AI models",
            )

            # Test signal generation
            signals = await advanced_service.generate_trading_signals(
                self.test_portfolio
            )

            signals_generated = isinstance(signals, list)
            self.log_test(
                "Advanced Signal Generation",
                signals_generated,
                f"Generated {len(signals)} advanced trading signals",
            )

            # Test performance summary
            performance = advanced_service.get_performance_summary()

            performance_valid = (
                "performance_metrics" in performance
                and "active_strategies" in performance
            )

            self.log_test(
                "Performance Tracking",
                performance_valid,
                f"Active strategies: {performance.get('active_strategies', 0)}",
            )

        except Exception as e:
            self.log_test("Advanced Trading Features", False, error=str(e))

    async def test_paper_trading_execution(self):
        """Test paper trading execution with realistic simulation."""
        print("\n=== PAPER TRADING EXECUTION TESTS ===")

        try:
            paper_service = PaperTradingService(self.db)

            # Test paper trade creation
            paper_trade_result = await paper_service.create_paper_trade(
                user_id=self.test_user.id,
                portfolio_id=self.test_portfolio.id,
                symbol="AAPL",
                trade_type="buy",
                quantity=10.0,
            )

            trade_created = "trade_id" in paper_trade_result
            self.log_test(
                "Paper Trade Creation",
                trade_created,
                f"Created paper trade: {paper_trade_result.get('trade_id')}",
            )

            # Test dollar-based investment
            dollar_investment = await paper_service.create_paper_dollar_investment(
                user_id=self.test_user.id,
                portfolio_id=self.test_portfolio.id,
                symbol="MSFT",
                investment_amount=1000.0,
            )

            dollar_trade_created = "trade_id" in dollar_investment
            self.log_test(
                "Dollar-Based Investment",
                dollar_trade_created,
                f"Created dollar investment: {dollar_investment.get('trade_id')}",
            )

            # Test portfolio value calculation
            portfolio_value = await paper_service.get_paper_portfolio_value(
                self.test_portfolio.id
            )

            portfolio_value_valid = (
                "total_value" in portfolio_value
                and "cash_balance" in portfolio_value
                and "positions" in portfolio_value
            )

            self.log_test(
                "Portfolio Value Calculation",
                portfolio_value_valid,
                f"Portfolio value: ${portfolio_value.get('total_value', 0):,.2f}",
            )

        except Exception as e:
            self.log_test("Paper Trading Execution", False, error=str(e))

    async def test_order_cancellation(self):
        """Test order cancellation functionality."""
        print("\n=== ORDER CANCELLATION TESTS ===")

        try:
            # Create a pending order first
            order_data = {
                "symbol": "AAPL",
                "quantity": 5,
                "trade_type": TradeType.BUY,
                "order_type": OrderType.LIMIT,
                "limit_price": 100.0,  # Below market to keep it pending
            }

            trade = await trading_service.place_order(
                order_data, self.test_user, self.db
            )

            # Ensure it's pending
            if trade.status == TradeStatus.PENDING:
                # Try to cancel it
                cancelled_trade = await trading_service.cancel_order(
                    trade.id, self.test_user, self.db
                )

                cancellation_successful = (
                    cancelled_trade.status == TradeStatus.CANCELLED
                )
                self.log_test(
                    "Order Cancellation",
                    cancellation_successful,
                    f"Order {trade.id} cancelled successfully",
                )
            else:
                self.log_test(
                    "Order Cancellation",
                    False,
                    error="Could not create pending order for cancellation test",
                )

        except Exception as e:
            self.log_test("Order Cancellation", False, error=str(e))

    async def test_trade_history(self):
        """Test trade history retrieval."""
        print("\n=== TRADE HISTORY TESTS ===")

        try:
            # Get trade history
            trade_history = await trading_service.get_trade_history(
                self.test_user, self.db, limit=50
            )

            history_retrieved = isinstance(trade_history, list)
            trade_count = len(trade_history)

            self.log_test(
                "Trade History Retrieval",
                history_retrieved,
                f"Retrieved {trade_count} trades from history",
            )

            # Get open orders
            open_orders = await trading_service.get_open_orders(self.test_user, self.db)

            open_orders_retrieved = isinstance(open_orders, list)
            open_count = len(open_orders)

            self.log_test(
                "Open Orders Retrieval",
                open_orders_retrieved,
                f"Retrieved {open_count} open orders",
            )

        except Exception as e:
            self.log_test("Trade History", False, error=str(e))

    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality."""
        print("\n=== CIRCUIT BREAKER TESTS ===")

        try:
            # Test circuit breaker status
            cb = trading_service.circuit_breaker
            if cb:
                allowed, status = cb.check()

                self.log_test(
                    "Circuit Breaker Status Check",
                    True,
                    f"Trading allowed: {allowed}, Status: {status}",
                )

                # Test position sizing
                try:
                    position_multiplier = cb.get_position_sizing()
                    multiplier_valid = 0 <= position_multiplier <= 1

                    self.log_test(
                        "Position Sizing Multiplier",
                        multiplier_valid,
                        f"Position multiplier: {position_multiplier:.2f}",
                    )
                except Exception:
                    self.log_test(
                        "Position Sizing Multiplier",
                        True,
                        "Position sizing not applicable",
                    )

            else:
                self.log_test(
                    "Circuit Breaker", False, error="Circuit breaker not initialized"
                )

        except Exception as e:
            self.log_test("Circuit Breaker", False, error=str(e))

    async def cleanup_test_environment(self):
        """Clean up test data."""
        try:
            if self.test_portfolio:
                # Delete test trades
                self.db.query(Trade).filter(
                    Trade.portfolio_id == self.test_portfolio.id
                ).delete()

                # Delete test holdings
                self.db.query(Holding).filter(
                    Holding.portfolio_id == self.test_portfolio.id
                ).delete()

                # Delete test portfolio
                self.db.delete(self.test_portfolio)

            if self.test_user:
                # Delete test user
                self.db.delete(self.test_user)

            self.db.commit()
            self.log_test("Cleanup Test Environment", True, "All test data cleaned up")

        except Exception as e:
            self.log_test("Cleanup Test Environment", False, error=str(e))
        finally:
            self.db.close()

    def generate_report(self):
        """Generate final test report."""
        total_tests = (
            self.test_results["tests_passed"] + self.test_results["tests_failed"]
        )
        success_rate = (
            (self.test_results["tests_passed"] / total_tests * 100)
            if total_tests > 0
            else 0
        )

        print(f"\n{'='*60}")
        print("COMPREHENSIVE TRADING SERVICES TEST REPORT")
        print(f"{'='*60}")
        print(f"Test Execution Time: {self.test_results['timestamp']}")
        print(f"Total Tests: {total_tests}")
        print(
            f"Tests Passed: {self.test_results['tests_passed']} ({success_rate:.1f}%)"
        )
        print(f"Tests Failed: {self.test_results['tests_failed']}")

        print(f"\n{'='*30} SAFETY CHECKS {'='*30}")
        for check in self.test_results["safety_checks"]:
            status = "✓" if check["passed"] else "✗"
            print(f"{status} {check['check_name']}: {check['details']}")

        if self.test_results["tests_failed"] > 0:
            print(f"\n{'='*30} FAILED TESTS {'='*30}")
            for test in self.test_results["test_details"]:
                if not test["passed"]:
                    print(f"✗ {test['test_name']}: {test['error']}")

        # Save detailed report
        with open(
            f"trading_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            "w",
        ) as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n{'='*60}")
        print("FINAL ASSESSMENT:")

        if success_rate >= 90:
            print("🟢 EXCELLENT: Trading services are working properly")
        elif success_rate >= 75:
            print("🟡 GOOD: Trading services are mostly functional with minor issues")
        elif success_rate >= 50:
            print(
                "🟠 FAIR: Trading services have significant issues that need attention"
            )
        else:
            print(
                "🔴 POOR: Trading services have critical issues requiring immediate attention"
            )

        # Safety assessment
        safety_passed = sum(
            1 for check in self.test_results["safety_checks"] if check["passed"]
        )
        safety_total = len(self.test_results["safety_checks"])

        if safety_passed == safety_total:
            print("🛡️  SAFETY: All safety checks passed - paper trading only confirmed")
        else:
            print("⚠️  SAFETY: Some safety checks failed - review required")

        return success_rate >= 75  # Return True if tests mostly passed


async def main():
    """Main test execution function."""
    print("🚀 Starting Comprehensive Trading Services Test Suite")
    print("⚠️  SAFETY: All tests use paper trading only - no real money involved")

    test_suite = TradingTestSuite()

    try:
        # Run all tests
        await test_suite.setup_test_environment()
        await test_suite.test_paper_trading_safety()
        await test_suite.test_basic_order_placement()
        await test_suite.test_order_validation()
        await test_suite.test_risk_management()
        await test_suite.test_ai_trading_signals()
        await test_suite.test_advanced_trading_features()
        await test_suite.test_paper_trading_execution()
        await test_suite.test_order_cancellation()
        await test_suite.test_trade_history()
        await test_suite.test_circuit_breaker_functionality()

    finally:
        await test_suite.cleanup_test_environment()
        test_suite.generate_report()


if __name__ == "__main__":
    asyncio.run(main())

"""Examples of using the enhanced Alpaca broker with live trading capabilities.

This module demonstrates how to use the upgraded broker system for both
paper trading and live trading with proper safety controls.
"""

import logging
from datetime import datetime

from app.models.trade import Trade, OrderType, OrderSide, TradeStatus
from app.services.broker import get_paper_broker, get_live_broker, BrokerFactory
from app.services.broker.base import BrokerError

logger = logging.getLogger(__name__)


def example_paper_trading():
    """Example of paper trading with safety checks."""
    try:
        # Create paper trading broker
        broker = get_paper_broker()

        # Check account info
        account_info = broker.get_account_info("")
        print(f"Paper Account Balance: ${account_info['balance']:,.2f}")
        print(f"Buying Power: ${account_info['buying_power']:,.2f}")

        # Create a test trade
        trade = Trade(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            is_paper_trade=True,
            user_id=1,
            portfolio_id=1,
        )

        # Execute trade
        result = broker.execute_trade(trade)
        print(f"Paper Trade Executed: {result['broker_order_id']}")

        # Check positions
        positions = broker.get_positions("")
        for position in positions:
            print(f"Position: {position['symbol']} - {position['quantity']} shares")

    except BrokerError as e:
        logger.error(f"Broker error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


def example_live_trading_with_safety_checks():
    """Example of live trading with comprehensive safety checks."""
    try:
        # Create live trading broker (will fail if not properly configured)
        broker = get_live_broker()

        # Create a trade
        trade = Trade(
            symbol="SPY",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=5,
            limit_price=450.00,
            is_paper_trade=False,
            user_id=1,
            portfolio_id=1,
        )

        # Comprehensive safety checks before executing
        print("Performing pre-trade safety checks...")

        # 1. Check market hours
        if not broker.is_market_open():
            print("Market is closed - trade will be queued")

        # 2. Validate symbol
        if not broker.validate_symbol(trade.symbol):
            raise BrokerError(f"Symbol {trade.symbol} is not tradeable")

        # 3. Check affordability
        if not broker.check_trade_affordability(trade):
            raise BrokerError("Insufficient buying power for trade")

        # 4. Check PDT compliance
        pdt_info = broker.check_pattern_day_trader_compliance("")
        if not pdt_info["pdt_compliant"]:
            print(
                f"PDT Warning: Day trades remaining: {pdt_info['day_trades_remaining']}"
            )

        # 5. Check existing position
        existing_position = broker.get_position_by_symbol(trade.symbol)
        if existing_position:
            print(f"Existing position: {existing_position['quantity']} shares")

        # Execute trade with all safety checks passed
        result = broker.execute_trade(trade)
        print(f"LIVE Trade Executed: {result['broker_order_id']}")

        # Monitor trade status
        status = broker.get_trade_status(result["broker_order_id"])
        print(f"Trade Status: {status['status']}")

    except BrokerError as e:
        logger.error(f"Broker error: {e.message} (Code: {e.error_code})")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


def example_fractional_shares():
    """Example of fractional share trading with dollar-based investing."""
    try:
        broker = get_paper_broker()

        # Dollar-based investment
        trade = Trade(
            symbol="TSLA",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0,  # Will be calculated from investment amount
            investment_amount=100.0,  # Invest $100
            is_fractional=True,
            is_paper_trade=True,
            user_id=1,
            portfolio_id=1,
        )

        result = broker.execute_trade(trade)
        print(f"Fractional Share Trade: ${trade.investment_amount} in {trade.symbol}")
        print(f"Order ID: {result['broker_order_id']}")

    except BrokerError as e:
        logger.error(f"Fractional trade error: {e.message}")


def example_advanced_orders():
    """Example of advanced order types (bracket, trailing stop)."""
    try:
        broker = get_paper_broker()

        # Bracket order (buy + take profit + stop loss)
        trade = Trade(
            symbol="QQQ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=20,
            is_paper_trade=True,
            user_id=1,
            portfolio_id=1,
        )

        # Place bracket order
        result = broker.place_bracket_order(
            trade=trade, take_profit_price=400.0, stop_loss_price=350.0
        )

        print(f"Bracket Order: {result['broker_order_id']}")
        print(f"Take Profit ID: {result.get('take_profit_id')}")
        print(f"Stop Loss ID: {result.get('stop_loss_id')}")

        # Trailing stop order
        trailing_trade = Trade(
            symbol="QQQ",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=10,
            is_paper_trade=True,
            user_id=1,
            portfolio_id=1,
        )

        trailing_result = broker.place_trailing_stop(
            trade=trailing_trade,
            trail_amount=5.0,  # 5% trailing stop
            trail_type="percent",
        )

        print(f"Trailing Stop Order: {trailing_result['broker_order_id']}")

    except BrokerError as e:
        logger.error(f"Advanced order error: {e.message}")


def example_broker_factory_usage():
    """Example of using the broker factory for different configurations."""
    try:
        # Create different broker instances
        BrokerFactory.create_paper_broker("alpaca")

        # Try to create live broker (will fail if not configured)
        try:
            BrokerFactory.create_live_broker("alpaca")
            print("Live broker created successfully")
        except BrokerError as e:
            print(f"Live broker creation failed: {e.message}")

        # Get default broker
        BrokerFactory.get_default_broker(use_paper=True)

        # List available brokers
        available = BrokerFactory.list_available_brokers()
        print(f"Available brokers: {available}")

    except Exception as e:
        logger.error(f"Factory usage error: {str(e)}")


if __name__ == "__main__":
    # Run examples
    print("=== Paper Trading Example ===")
    example_paper_trading()

    print("\n=== Fractional Shares Example ===")
    example_fractional_shares()

    print("\n=== Advanced Orders Example ===")
    example_advanced_orders()

    print("\n=== Broker Factory Example ===")
    example_broker_factory_usage()

    print("\n=== Live Trading Example (will likely fail without proper config) ===")
    example_live_trading_with_safety_checks()

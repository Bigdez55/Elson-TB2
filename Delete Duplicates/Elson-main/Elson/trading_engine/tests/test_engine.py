import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
from datetime import datetime

from engine.trade_executor import TradeExecutor
from engine.risk_manager import RiskManager
from engine.strategy_optimizer import StrategyOptimizer
from engine.performance_monitor import PerformanceMonitor
from strategies.moving_average import MovingAverageStrategy


class TestTradeExecutor(unittest.TestCase):
    def setUp(self):
        self.risk_manager = MagicMock()
        self.trade_executor = TradeExecutor(self.risk_manager)
        
        # Mock the API client
        self.trade_executor.api_client = MagicMock()
    
    def test_execute_trade_buy(self):
        # Test data
        symbol = "AAPL"
        quantity = 10
        portfolio_id = "portfolio-123"
        
        # Execute the trade
        self.trade_executor.execute_trade(symbol, "buy", quantity, portfolio_id)
        
        # Verify the API client was called with the correct parameters
        self.trade_executor.api_client.place_market_order.assert_called_once_with(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side="buy",
            quantity=quantity
        )
    
    def test_execute_trade_sell(self):
        # Test data
        symbol = "MSFT"
        quantity = 5
        portfolio_id = "portfolio-456"
        
        # Execute the trade
        self.trade_executor.execute_trade(symbol, "sell", quantity, portfolio_id)
        
        # Verify the API client was called with the correct parameters
        self.trade_executor.api_client.place_market_order.assert_called_once_with(
            portfolio_id=portfolio_id,
            symbol=symbol,
            side="sell",
            quantity=quantity
        )
    
    def test_execute_trade_with_risk_check(self):
        # Test data
        symbol = "TSLA"
        quantity = 20
        portfolio_id = "portfolio-789"
        
        # Mock the risk manager to deny the trade
        self.risk_manager.check_trade_risk.return_value = False
        
        # Execute the trade
        result = self.trade_executor.execute_trade(symbol, "buy", quantity, portfolio_id, check_risk=True)
        
        # Verify the risk was checked and the trade was denied
        self.risk_manager.check_trade_risk.assert_called_once()
        self.trade_executor.api_client.place_market_order.assert_not_called()
        self.assertFalse(result)
    
    @patch('engine.trade_executor.time.sleep', return_value=None)
    def test_execute_batch_trades(self, mock_sleep):
        # Test data
        trades = [
            {"symbol": "AAPL", "side": "buy", "quantity": 10, "portfolio_id": "portfolio-123"},
            {"symbol": "MSFT", "side": "sell", "quantity": 5, "portfolio_id": "portfolio-456"},
            {"symbol": "GOOGL", "side": "buy", "quantity": 2, "portfolio_id": "portfolio-789"}
        ]
        
        # Mock the risk manager to allow all trades
        self.risk_manager.check_trade_risk.return_value = True
        
        # Execute the batch trades
        self.trade_executor.execute_batch_trades(trades)
        
        # Verify all trades were executed
        self.assertEqual(self.trade_executor.api_client.place_market_order.call_count, 3)


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.risk_manager = RiskManager()
        
        # Mock the API client
        self.risk_manager.api_client = MagicMock()
    
    def test_check_trade_risk_within_limits(self):
        # Test data
        symbol = "AAPL"
        side = "buy"
        quantity = 10
        portfolio_id = "portfolio-123"
        
        # Mock portfolio data
        portfolio_value = 100000.0
        cash_balance = 50000.0
        self.risk_manager.get_portfolio_details = MagicMock(
            return_value={"total_value": portfolio_value, "cash_balance": cash_balance}
        )
        
        # Mock market data - current price
        current_price = 150.0
        self.risk_manager.get_current_price = MagicMock(return_value=current_price)
        
        # Check the risk
        result = self.risk_manager.check_trade_risk(symbol, side, quantity, portfolio_id)
        
        # Verify the trade is within risk limits
        self.assertTrue(result)
    
    def test_check_trade_risk_exceeds_cash(self):
        # Test data
        symbol = "AAPL"
        side = "buy"
        quantity = 1000
        portfolio_id = "portfolio-123"
        
        # Mock portfolio data with low cash balance
        portfolio_value = 100000.0
        cash_balance = 5000.0
        self.risk_manager.get_portfolio_details = MagicMock(
            return_value={"total_value": portfolio_value, "cash_balance": cash_balance}
        )
        
        # Mock market data - current price
        current_price = 150.0
        self.risk_manager.get_current_price = MagicMock(return_value=current_price)
        
        # Check the risk
        result = self.risk_manager.check_trade_risk(symbol, side, quantity, portfolio_id)
        
        # Verify the trade exceeds risk limits
        self.assertFalse(result)
    
    def test_check_trade_risk_exceeds_position_size(self):
        # Test data
        symbol = "TSLA"
        side = "buy"
        quantity = 100
        portfolio_id = "portfolio-123"
        
        # Mock portfolio data
        portfolio_value = 100000.0
        cash_balance = 100000.0
        self.risk_manager.get_portfolio_details = MagicMock(
            return_value={"total_value": portfolio_value, "cash_balance": cash_balance}
        )
        
        # Mock market data - current price for an expensive stock
        current_price = 900.0
        self.risk_manager.get_current_price = MagicMock(return_value=current_price)
        
        # Check the risk
        result = self.risk_manager.check_trade_risk(symbol, side, quantity, portfolio_id, max_position_pct=0.5)
        
        # Verify the trade exceeds position size limits
        self.assertFalse(result)


class TestStrategyOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = StrategyOptimizer()
        
        # Create a test strategy
        self.strategy = MovingAverageStrategy(short_window=10, long_window=50)
        
        # Sample data
        dates = pd.date_range(start='2020-01-01', periods=200)
        self.data = pd.DataFrame({
            'date': dates,
            'close': np.random.normal(100, 10, 200),
            'volume': np.random.randint(1000000, 10000000, 200)
        })
        self.data.set_index('date', inplace=True)
    
    def test_optimize_moving_average_strategy(self):
        # Define the parameter grid
        param_grid = {
            'short_window': [5, 10, 15],
            'long_window': [30, 50, 70]
        }
        
        # Optimize the strategy
        best_params, best_score = self.optimizer.optimize_strategy(
            strategy_class=MovingAverageStrategy,
            param_grid=param_grid,
            data=self.data,
            target_metric='sharpe_ratio'
        )
        
        # Verify the return values
        self.assertIsInstance(best_params, dict)
        self.assertIn('short_window', best_params)
        self.assertIn('long_window', best_params)
        self.assertIsInstance(best_score, float)
        
        # Ensure short window is less than long window
        self.assertLess(best_params['short_window'], best_params['long_window'])


class TestPerformanceMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = PerformanceMonitor()
        
        # Sample trade data
        self.trades = [
            {
                'id': 'trade-1',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 10,
                'price': 150.0,
                'timestamp': datetime(2021, 1, 1)
            },
            {
                'id': 'trade-2',
                'symbol': 'AAPL',
                'side': 'sell',
                'quantity': 10,
                'price': 170.0,
                'timestamp': datetime(2021, 2, 1)
            },
            {
                'id': 'trade-3',
                'symbol': 'MSFT',
                'side': 'buy',
                'quantity': 5,
                'price': 200.0,
                'timestamp': datetime(2021, 1, 15)
            }
        ]
    
    def test_calculate_profit_loss(self):
        # Calculate P&L
        pnl = self.monitor.calculate_profit_loss(self.trades)
        
        # Expected P&L: (170 - 150) * 10 = $200 for the AAPL round trip
        expected_pnl = 200.0
        
        # Verify the P&L calculation
        self.assertEqual(pnl, expected_pnl)
    
    def test_calculate_win_rate(self):
        # Add more trades to test win rate
        additional_trades = [
            {
                'id': 'trade-4',
                'symbol': 'MSFT',
                'side': 'sell',
                'quantity': 5,
                'price': 180.0,  # Loss on MSFT
                'timestamp': datetime(2021, 2, 15)
            },
            {
                'id': 'trade-5',
                'symbol': 'GOOGL',
                'side': 'buy',
                'quantity': 2,
                'price': 1000.0,
                'timestamp': datetime(2021, 3, 1)
            },
            {
                'id': 'trade-6',
                'symbol': 'GOOGL',
                'side': 'sell',
                'quantity': 2,
                'price': 1100.0,  # Win on GOOGL
                'timestamp': datetime(2021, 4, 1)
            }
        ]
        all_trades = self.trades + additional_trades
        
        # Calculate win rate
        win_rate = self.monitor.calculate_win_rate(all_trades)
        
        # Expected win rate: 2 wins (AAPL, GOOGL) out of 3 round trips = 66.67%
        expected_win_rate = 2 / 3
        
        # Verify the win rate calculation with some tolerance for floating point math
        self.assertAlmostEqual(win_rate, expected_win_rate, places=2)
    
    def test_calculate_sharpe_ratio(self):
        # Sample returns data (daily returns as a percentage)
        returns = pd.Series([
            0.01, -0.005, 0.02, 0.01, -0.01, 0.015, 0.005, -0.007, 0.012, 0.008,
            -0.003, 0.009, 0.011, -0.002, 0.007, 0.004, -0.006, 0.01, 0.008, 0.005
        ])
        
        # Calculate Sharpe ratio
        sharpe = self.monitor.calculate_sharpe_ratio(returns)
        
        # Verify the Sharpe ratio is a sensible value (usually between -3 and 4)
        self.assertGreater(sharpe, -3)
        self.assertLess(sharpe, 4)


if __name__ == '__main__':
    unittest.main()
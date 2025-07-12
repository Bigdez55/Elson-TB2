"""
Backtesting module for evaluating trading strategies and models across different market conditions.

This module provides tools for backtesting the adaptive parameters and enhanced
circuit breaker implementations across different volatility regimes.
"""

# Use absolute imports instead of relative imports
from Elson.trading_engine.backtesting.hybrid_model_evaluation import (
    HybridModelBacktester,
    BacktestResult,
    RegimePerformance,
    run_hybrid_model_backtest
)

__all__ = [
    'HybridModelBacktester',
    'BacktestResult',
    'RegimePerformance',
    'run_hybrid_model_backtest'
]
"""
Trading Strategies Module

Contains base strategy framework and comprehensive trading strategy implementations
covering technical analysis, breakout, momentum, mean reversion, arbitrage,
grid trading, and execution algorithms.
"""

# Statistical Arbitrage Strategies
from .arbitrage import PairsTradingStrategy

# Base classes and registry
from .base import TradingStrategy

# Breakout Strategies
from .breakout import DonchianBreakout, OpeningRangeBreakout, SupportResistanceBreakout

# Execution Algorithms
from .execution import (
    IcebergExecutionStrategy,
    TWAPExecutionStrategy,
    VWAPExecutionStrategy,
)

# Grid and DCA Strategies
from .grid import DCAStrategy, GridTradingStrategy

# Mean Reversion Strategies
from .mean_reversion import RSIMeanReversion, StatisticalMeanReversion

# Momentum Strategies
from .momentum import MomentumFactorStrategy, TrendFollowingStrategy
from .registry import StrategyCategory, StrategyRegistry

# Technical Analysis Strategies
from .technical import (
    ADXTrendStrategy,
    BollingerBandsStrategy,
    CandlestickPatternStrategy,
    IchimokuCloudStrategy,
    MACDStrategy,
    RSIStrategy,
    StochasticStrategy,
)

__all__ = [
    # Base
    "TradingStrategy",
    "StrategyRegistry",
    "StrategyCategory",
    # Technical
    "RSIStrategy",
    "BollingerBandsStrategy",
    "MACDStrategy",
    "IchimokuCloudStrategy",
    "ADXTrendStrategy",
    "StochasticStrategy",
    "CandlestickPatternStrategy",
    # Breakout
    "SupportResistanceBreakout",
    "OpeningRangeBreakout",
    "DonchianBreakout",
    # Mean Reversion
    "StatisticalMeanReversion",
    "RSIMeanReversion",
    # Momentum
    "MomentumFactorStrategy",
    "TrendFollowingStrategy",
    # Arbitrage
    "PairsTradingStrategy",
    # Grid/DCA
    "GridTradingStrategy",
    "DCAStrategy",
    # Execution
    "VWAPExecutionStrategy",
    "TWAPExecutionStrategy",
    "IcebergExecutionStrategy",
]

# Strategy count for documentation
STRATEGY_COUNT = len(__all__) - 3  # Exclude base classes


def get_all_strategies():
    """Get a dictionary of all available strategies by category"""
    return {
        "technical": [
            "RSIStrategy",
            "BollingerBandsStrategy",
            "MACDStrategy",
            "IchimokuCloudStrategy",
            "ADXTrendStrategy",
            "StochasticStrategy",
            "CandlestickPatternStrategy",
        ],
        "breakout": [
            "SupportResistanceBreakout",
            "OpeningRangeBreakout",
            "DonchianBreakout",
        ],
        "mean_reversion": [
            "StatisticalMeanReversion",
            "RSIMeanReversion",
        ],
        "momentum": [
            "MomentumFactorStrategy",
            "TrendFollowingStrategy",
        ],
        "arbitrage": [
            "PairsTradingStrategy",
        ],
        "grid": [
            "GridTradingStrategy",
            "DCAStrategy",
        ],
        "execution": [
            "VWAPExecutionStrategy",
            "TWAPExecutionStrategy",
            "IcebergExecutionStrategy",
        ],
    }


def create_strategy(name: str, symbol: str, **kwargs):
    """
    Factory function to create a strategy by name.

    Args:
        name: Strategy name (registered in StrategyRegistry)
        symbol: Trading symbol
        **kwargs: Strategy-specific parameters

    Returns:
        Configured strategy instance
    """
    return StrategyRegistry.create(name, symbol=symbol, **kwargs)

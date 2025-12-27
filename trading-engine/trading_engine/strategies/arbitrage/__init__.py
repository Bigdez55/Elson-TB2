"""
Statistical Arbitrage & Pairs Trading Strategies

Contains market-neutral strategies based on statistical relationships
between securities.
"""

from .pairs_trading import PairsTradingStrategy

__all__ = [
    "PairsTradingStrategy",
]

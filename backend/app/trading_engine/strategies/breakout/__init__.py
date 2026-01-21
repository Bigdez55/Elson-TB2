"""
Breakout Trading Strategies

Contains strategies based on support/resistance breakouts,
opening range breakouts, and chart pattern breakouts.
"""

from .donchian_breakout import DonchianBreakout
from .opening_range import OpeningRangeBreakout
from .support_resistance import SupportResistanceBreakout

__all__ = [
    "SupportResistanceBreakout",
    "OpeningRangeBreakout",
    "DonchianBreakout",
]

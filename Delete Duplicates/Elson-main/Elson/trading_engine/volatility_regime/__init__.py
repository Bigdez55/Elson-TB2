"""
Volatility regime detection module for Elson Wealth Trading Platform.

This module implements Phase 2 of the Hybrid Model Improvement Plan,
focusing on volatility robustness through regime detection and
specialized model variants for different market conditions.
"""

from .volatility_detector import VolatilityDetector, VolatilityRegime

__all__ = ['VolatilityDetector', 'VolatilityRegime']
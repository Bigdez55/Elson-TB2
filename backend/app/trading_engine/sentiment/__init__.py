"""Sentiment analysis module for Elson Trading Engine.

This module provides sentiment analysis capabilities using NLP models.
Heavy ML dependencies (tensorflow, transformers, torch) are optional.
When not available, stub implementations are provided.
"""

import logging

logger = logging.getLogger(__name__)

# Track which components are available
SENTIMENT_ML_AVAILABLE = False
SENTIMENT_SOURCES_AVAILABLE = False

# Try to import ML-based sentiment analysis (requires tensorflow, transformers, torch)
try:
    from .nlp_models import (
        TextPreprocessor,
        TransformerSentimentAnalyzer,
        find_market_moving_news,
    )
    from .sentiment_aggregator import SentimentAggregator, aggregate_sentiment

    SENTIMENT_ML_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Sentiment ML models not available (missing dependencies): {e}")

    # Provide stub implementations
    class TextPreprocessor:
        """Stub for text preprocessing when ML dependencies unavailable."""

        def __init__(self, **kwargs):
            pass

        def preprocess(self, text: str) -> str:
            return text

    class TransformerSentimentAnalyzer:
        """Stub for transformer sentiment when ML dependencies unavailable."""

        def __init__(self, **kwargs):
            pass

        def analyze(self, text: str) -> dict:
            return {"sentiment": "neutral", "confidence": 0.5}

    class SentimentAggregator:
        """Stub for sentiment aggregation when ML dependencies unavailable."""

        def __init__(self, **kwargs):
            pass

        def get_aggregated_sentiment(self, symbol: str) -> dict:
            return {"symbol": symbol, "sentiment": 0.0, "confidence": 0.5}

    def find_market_moving_news(*args, **kwargs):
        """Stub for market moving news detection."""
        return []

    def aggregate_sentiment(*args, **kwargs):
        """Stub for sentiment aggregation."""
        return {"sentiment": 0.0, "confidence": 0.5}


# Try to import sentiment sources
try:
    from .sentiment_sources import *

    SENTIMENT_SOURCES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Sentiment sources not available: {e}")

# External API integration (already has graceful fallbacks)
try:
    from .external_api import BACKEND_AVAILABLE
except ImportError:
    BACKEND_AVAILABLE = False

__all__ = [
    "TextPreprocessor",
    "TransformerSentimentAnalyzer",
    "SentimentAggregator",
    "find_market_moving_news",
    "aggregate_sentiment",
    "SENTIMENT_ML_AVAILABLE",
    "SENTIMENT_SOURCES_AVAILABLE",
    "BACKEND_AVAILABLE",
]

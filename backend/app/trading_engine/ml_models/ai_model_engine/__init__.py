"""
AI Model Engine for the trading bot.
Implements various machine learning models for price prediction and analysis.
"""

from .quantum_models import (
    QuantumFeatureEncoder,
    QuantumKernelClassifier,
    QuantumVariationalClassifier,
    quantum_range_prediction
)

from .deep_learning_models import (
    TimeSeriesGenerator,
    LSTMPricePredictor,
    CNNPricePredictor,
    deep_learning_range_prediction
)

from .nlp_models import (
    TextPreprocessor,
    TransformerSentimentAnalyzer,
    FinancialNewsClassifier,
    sentiment_analysis_batch,
    find_market_moving_news,
    # Phase 1: FinGPT sentiment analysis
    FinGPTSentimentAnalyzer,
    fingpt_sentiment_analysis,
    analyze_market_sentiment
)

__all__ = [
    'QuantumFeatureEncoder',
    'QuantumKernelClassifier',
    'QuantumVariationalClassifier',
    'quantum_range_prediction',
    'TimeSeriesGenerator',
    'LSTMPricePredictor',
    'CNNPricePredictor',
    'deep_learning_range_prediction',
    'TextPreprocessor',
    'TransformerSentimentAnalyzer',
    'FinancialNewsClassifier',
    'sentiment_analysis_batch',
    'find_market_moving_news',
    # Phase 1: FinGPT
    'FinGPTSentimentAnalyzer',
    'fingpt_sentiment_analysis',
    'analyze_market_sentiment'
]
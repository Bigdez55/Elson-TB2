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

# Phase 2: Sentiment Benchmark (FinGPT vs DistilBERT comparison)
from .sentiment_benchmark import (
    SentimentBenchmark,
    BenchmarkResult,
    BenchmarkDataset,
    FinancialSentimentDatasets,
    run_quick_benchmark
)

# Phase 2: Advanced PEFT Adapters (DoRA, QDoRA, DVoRA)
from .advanced_adapters import (
    AdapterType,
    AdapterConfig,
    AdvancedFinancialAnalyzer,
    create_adapter_config,
    create_quantization_config,
    create_qdora_analyzer,
    create_dvora_analyzer,
    get_adapter_comparison,
    check_dora_support
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
    'analyze_market_sentiment',
    # Phase 2: Benchmark
    'SentimentBenchmark',
    'BenchmarkResult',
    'BenchmarkDataset',
    'FinancialSentimentDatasets',
    'run_quick_benchmark',
    # Phase 2: Advanced Adapters (DoRA, QDoRA, DVoRA)
    'AdapterType',
    'AdapterConfig',
    'AdvancedFinancialAnalyzer',
    'create_adapter_config',
    'create_quantization_config',
    'create_qdora_analyzer',
    'create_dvora_analyzer',
    'get_adapter_comparison',
    'check_dora_support'
]
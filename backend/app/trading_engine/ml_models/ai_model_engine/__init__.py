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

# Phase 3: Wealth Management Integration (5-Layer Architecture)
from .wealth_model_loader import (
    WealthModelLoader,
    ModelConfig,
    ModelSource,
    create_wealth_model_loader,
    load_wealth_model,
    get_wealth_model_info
)

from .wealth_llm_service import (
    # Enums
    ServiceTier,
    AdvisoryMode,
    DecisionAuthority,
    ComplianceCategory,
    # Data classes
    UserProfile,
    ComplianceResult,
    QueryContext,
    AdvisoryResponse,
    # 5-Layer Components
    QueryRouter,
    RAGLayer,
    ComplianceEngine,
    ValidationLayer,
    # Main Service
    WealthLLMService,
    create_wealth_service,
    quick_wealth_query
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
    'check_dora_support',
    # Phase 3: Wealth Management (5-Layer Architecture)
    'WealthModelLoader',
    'ModelConfig',
    'ModelSource',
    'create_wealth_model_loader',
    'load_wealth_model',
    'get_wealth_model_info',
    'ServiceTier',
    'AdvisoryMode',
    'DecisionAuthority',
    'ComplianceCategory',
    'UserProfile',
    'ComplianceResult',
    'QueryContext',
    'AdvisoryResponse',
    'QueryRouter',
    'RAGLayer',
    'ComplianceEngine',
    'ValidationLayer',
    'WealthLLMService',
    'create_wealth_service',
    'quick_wealth_query'
]
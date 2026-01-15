"""
AI Model Engine for the trading bot.
Implements various machine learning models for price prediction and analysis,
including the comprehensive wealth management QDoRA model integration.
"""

import logging

logger = logging.getLogger(__name__)

# Optional quantum models (requires qiskit)
try:
    from .quantum_models import (  # noqa: E402
        QuantumFeatureEncoder,
        QuantumKernelClassifier,
        QuantumVariationalClassifier,
        quantum_range_prediction
    )
    _QUANTUM_AVAILABLE = True
except ImportError:
    QuantumFeatureEncoder = None
    QuantumKernelClassifier = None
    QuantumVariationalClassifier = None
    quantum_range_prediction = None
    _QUANTUM_AVAILABLE = False
    logger.debug("Quantum models not available (qiskit not installed)")

# Optional deep learning models (requires tensorflow/torch)
try:
    from .deep_learning_models import (  # noqa: E402
        TimeSeriesGenerator,
        LSTMPricePredictor,
        CNNPricePredictor,
        deep_learning_range_prediction
    )
    _DEEP_LEARNING_AVAILABLE = True
except ImportError:
    TimeSeriesGenerator = None
    LSTMPricePredictor = None
    CNNPricePredictor = None
    deep_learning_range_prediction = None
    _DEEP_LEARNING_AVAILABLE = False
    logger.debug("Deep learning models not available")

# NLP models
try:
    from .nlp_models import (  # noqa: E402
        TextPreprocessor,
        TransformerSentimentAnalyzer,
        FinancialNewsClassifier,
        sentiment_analysis_batch,
        find_market_moving_news
    )
    _NLP_AVAILABLE = True
except ImportError:
    TextPreprocessor = None
    TransformerSentimentAnalyzer = None
    FinancialNewsClassifier = None
    sentiment_analysis_batch = None
    find_market_moving_news = None
    _NLP_AVAILABLE = False
    logger.debug("NLP models not available")

# Wealth Management Integration (5-Layer Hybrid Architecture)
from .wealth_model_loader import (  # noqa: E402
    WealthModelLoader,
    ModelConfig,
    ModelSource,
    create_wealth_model_loader,
    load_wealth_model,
    get_wealth_model_info
)

from .wealth_llm_service import (  # noqa: E402
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
    # Quantum models (optional - requires qiskit)
    'QuantumFeatureEncoder',
    'QuantumKernelClassifier',
    'QuantumVariationalClassifier',
    'quantum_range_prediction',
    # Deep learning models (optional - requires tensorflow/torch)
    'TimeSeriesGenerator',
    'LSTMPricePredictor',
    'CNNPricePredictor',
    'deep_learning_range_prediction',
    # NLP models
    'TextPreprocessor',
    'TransformerSentimentAnalyzer',
    'FinancialNewsClassifier',
    'sentiment_analysis_batch',
    'find_market_moving_news',
    # Wealth Management Model Loader
    'WealthModelLoader',
    'ModelConfig',
    'ModelSource',
    'create_wealth_model_loader',
    'load_wealth_model',
    'get_wealth_model_info',
    # Wealth Management LLM Service (5-Layer Architecture)
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
    'quick_wealth_query',
]

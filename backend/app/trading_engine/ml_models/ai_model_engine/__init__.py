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
        quantum_range_prediction,
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
        CNNPricePredictor,
        LSTMPricePredictor,
        TimeSeriesGenerator,
        deep_learning_range_prediction,
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
        FinancialNewsClassifier,
        TextPreprocessor,
        TransformerSentimentAnalyzer,
        find_market_moving_news,
        sentiment_analysis_batch,
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

from .wealth_llm_service import (  # noqa: E402; Enums; Data classes; 5-Layer Components; Main Service
    AdvisoryMode,
    AdvisoryResponse,
    ComplianceCategory,
    ComplianceEngine,
    ComplianceResult,
    DecisionAuthority,
    QueryContext,
    QueryRouter,
    RAGLayer,
    ServiceTier,
    UserProfile,
    ValidationLayer,
    WealthLLMService,
    create_wealth_service,
    quick_wealth_query,
)

# Wealth Management Integration (5-Layer Hybrid Architecture)
from .wealth_model_loader import (  # noqa: E402
    ModelConfig,
    ModelSource,
    WealthModelLoader,
    create_wealth_model_loader,
    get_wealth_model_info,
    load_wealth_model,
)

__all__ = [
    # Quantum models (optional - requires qiskit)
    "QuantumFeatureEncoder",
    "QuantumKernelClassifier",
    "QuantumVariationalClassifier",
    "quantum_range_prediction",
    # Deep learning models (optional - requires tensorflow/torch)
    "TimeSeriesGenerator",
    "LSTMPricePredictor",
    "CNNPricePredictor",
    "deep_learning_range_prediction",
    # NLP models
    "TextPreprocessor",
    "TransformerSentimentAnalyzer",
    "FinancialNewsClassifier",
    "sentiment_analysis_batch",
    "find_market_moving_news",
    # Wealth Management Model Loader
    "WealthModelLoader",
    "ModelConfig",
    "ModelSource",
    "create_wealth_model_loader",
    "load_wealth_model",
    "get_wealth_model_info",
    # Wealth Management LLM Service (5-Layer Architecture)
    "ServiceTier",
    "AdvisoryMode",
    "DecisionAuthority",
    "ComplianceCategory",
    "UserProfile",
    "ComplianceResult",
    "QueryContext",
    "AdvisoryResponse",
    "QueryRouter",
    "RAGLayer",
    "ComplianceEngine",
    "ValidationLayer",
    "WealthLLMService",
    "create_wealth_service",
    "quick_wealth_query",
]

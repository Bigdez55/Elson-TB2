"""
Machine Learning Module for Elson Trading Platform

This module provides a unified interface for all ML models including:
- Deep Learning (TensorFlow/PyTorch) - LSTM, CNN, Transformers
- NLP/Sentiment Analysis
- Quantum Machine Learning
- Reinforcement Learning
- Classical ML (scikit-learn, XGBoost)

The module automatically detects the deployment environment and uses
appropriate models (lightweight for Vercel, full-stack for GCP).

Usage:
    from app.ml import get_ml_config, MLModelFactory
    from app.ml import get_enhanced_ml_service
    from app.ml import get_sentiment_analyzer
    from app.ml import get_quantum_classifier
    from app.ml import get_rl_service

Example:
    # Get ML configuration
    config = get_ml_config()
    print(f"Environment: {config.environment}")
    print(f"Deep learning available: {config.can_use_deep_learning()}")

    # Create models
    factory = MLModelFactory(config)
    predictor = factory.create_price_predictor(model_type="auto")

    # Use enhanced service
    service = get_enhanced_ml_service()
    result = await service.train_price_prediction_model(symbol, data)
"""

from app.ml.config import (
    MLConfig,
    MLAvailability,
    MLBackend,
    DeploymentEnvironment,
    get_ml_config,
    reset_ml_config,
)

from app.ml.model_factory import (
    MLModelFactory,
    BasePredictor,
    SklearnPredictor,
    EnsemblePredictor,
    SimpleSentimentAnalyzer,
)

from app.ml.enhanced_service import (
    EnhancedNeuralNetworkService,
    get_enhanced_ml_service,
)

from app.ml.sentiment import (
    get_sentiment_analyzer,
    SentimentAnalyzerFactory,
    SentimentResult,
    SentimentLabel,
)

from app.ml.quantum import (
    QuantumClassifier,
    QuantumInspiredClassifier,
    get_quantum_classifier,
    QISKIT_AVAILABLE,
)

from app.ml.reinforcement import (
    RLTradingService,
    DQNAgent,
    SimpleTradingEnvironment,
    get_rl_service,
)

from app.ml.signals import (
    TradingSignal,
    SignalAction,
    SignalSource,
    RedisSignalPublisher,
    StrategySignalGenerator,
    get_signal_publisher,
    get_signal_generator,
)

from app.ml.strategy_engine import StrategyEngine

__all__ = [
    # Configuration
    "MLConfig",
    "MLAvailability",
    "MLBackend",
    "DeploymentEnvironment",
    "get_ml_config",
    "reset_ml_config",
    # Model Factory
    "MLModelFactory",
    "BasePredictor",
    "SklearnPredictor",
    "EnsemblePredictor",
    # Enhanced Service
    "EnhancedNeuralNetworkService",
    "get_enhanced_ml_service",
    # Sentiment Analysis
    "get_sentiment_analyzer",
    "SentimentAnalyzerFactory",
    "SentimentResult",
    "SentimentLabel",
    "SimpleSentimentAnalyzer",
    # Quantum ML
    "QuantumClassifier",
    "QuantumInspiredClassifier",
    "get_quantum_classifier",
    "QISKIT_AVAILABLE",
    # Reinforcement Learning
    "RLTradingService",
    "DQNAgent",
    "SimpleTradingEnvironment",
    "get_rl_service",
    # Trading Signals (Brain & Body Architecture)
    "TradingSignal",
    "SignalAction",
    "SignalSource",
    "RedisSignalPublisher",
    "StrategySignalGenerator",
    "get_signal_publisher",
    "get_signal_generator",
    "StrategyEngine",
]

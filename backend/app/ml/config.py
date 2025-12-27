"""
ML Configuration Module

Handles environment detection and ML library availability checking.
Provides a unified configuration for ML models across different deployment environments.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Deployment environment types"""
    VERCEL = "vercel"  # Serverless, limited resources
    GCP = "gcp"  # Full ML stack available
    LOCAL = "local"  # Development environment
    DOCKER = "docker"  # Container deployment


class MLBackend(Enum):
    """Available ML backends"""
    SKLEARN = "sklearn"  # Always available
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    TRANSFORMERS = "transformers"
    QISKIT = "qiskit"


@dataclass
class MLAvailability:
    """Tracks which ML libraries are available"""
    sklearn: bool = True  # Always available
    tensorflow: bool = False
    pytorch: bool = False
    transformers: bool = False
    qiskit: bool = False
    gymnasium: bool = False
    xgboost: bool = True  # Always in requirements

    # Version info
    tensorflow_version: Optional[str] = None
    pytorch_version: Optional[str] = None
    transformers_version: Optional[str] = None
    qiskit_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sklearn": self.sklearn,
            "tensorflow": self.tensorflow,
            "pytorch": self.pytorch,
            "transformers": self.transformers,
            "qiskit": self.qiskit,
            "gymnasium": self.gymnasium,
            "xgboost": self.xgboost,
            "versions": {
                "tensorflow": self.tensorflow_version,
                "pytorch": self.pytorch_version,
                "transformers": self.transformers_version,
                "qiskit": self.qiskit_version,
            }
        }


@dataclass
class MLConfig:
    """Configuration for ML models"""
    environment: DeploymentEnvironment
    availability: MLAvailability

    # Model settings
    use_gpu: bool = False
    max_model_size_mb: int = 500  # Max model size to load
    cache_models: bool = True
    model_cache_dir: str = "/tmp/ml_models"

    # Deep learning settings
    lstm_enabled: bool = False
    cnn_enabled: bool = False
    transformer_enabled: bool = False

    # NLP settings
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    max_text_length: int = 512

    # Quantum ML settings
    quantum_enabled: bool = False
    quantum_backend: str = "aer_simulator"
    num_qubits: int = 4

    # Reinforcement learning settings
    rl_enabled: bool = False
    rl_training_episodes: int = 100

    # Fallback settings
    use_mock_predictions: bool = False
    fallback_to_sklearn: bool = True

    def can_use_deep_learning(self) -> bool:
        """Check if deep learning is available"""
        return self.availability.tensorflow or self.availability.pytorch

    def can_use_transformers(self) -> bool:
        """Check if transformer models are available"""
        return self.availability.transformers and self.availability.pytorch

    def can_use_quantum(self) -> bool:
        """Check if quantum ML is available"""
        return self.availability.qiskit

    def can_use_rl(self) -> bool:
        """Check if reinforcement learning is available"""
        return self.availability.gymnasium and self.availability.tensorflow

    def get_preferred_backend(self) -> MLBackend:
        """Get the preferred ML backend based on availability"""
        if self.availability.tensorflow:
            return MLBackend.TENSORFLOW
        elif self.availability.pytorch:
            return MLBackend.PYTORCH
        else:
            return MLBackend.SKLEARN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment.value,
            "availability": self.availability.to_dict(),
            "use_gpu": self.use_gpu,
            "deep_learning": {
                "lstm_enabled": self.lstm_enabled,
                "cnn_enabled": self.cnn_enabled,
                "transformer_enabled": self.transformer_enabled,
            },
            "quantum": {
                "enabled": self.quantum_enabled,
                "backend": self.quantum_backend,
                "num_qubits": self.num_qubits,
            },
            "rl": {
                "enabled": self.rl_enabled,
                "training_episodes": self.rl_training_episodes,
            },
            "preferred_backend": self.get_preferred_backend().value,
        }


def _detect_environment() -> DeploymentEnvironment:
    """Detect the current deployment environment"""
    # Check for Vercel
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return DeploymentEnvironment.VERCEL

    # Check for GCP
    if os.environ.get("K_SERVICE") or os.environ.get("GOOGLE_CLOUD_PROJECT"):
        return DeploymentEnvironment.GCP

    # Check for Docker
    if os.path.exists("/.dockerenv"):
        return DeploymentEnvironment.DOCKER

    # Default to local
    return DeploymentEnvironment.LOCAL


def _check_library_availability() -> MLAvailability:
    """Check which ML libraries are available"""
    availability = MLAvailability()

    # Check TensorFlow
    try:
        import tensorflow as tf
        availability.tensorflow = True
        availability.tensorflow_version = tf.__version__
        logger.info(f"TensorFlow {tf.__version__} available")
    except ImportError:
        logger.info("TensorFlow not available")

    # Check PyTorch
    try:
        import torch
        availability.pytorch = True
        availability.pytorch_version = torch.__version__
        logger.info(f"PyTorch {torch.__version__} available")
    except ImportError:
        logger.info("PyTorch not available")

    # Check Transformers
    try:
        import transformers
        availability.transformers = True
        availability.transformers_version = transformers.__version__
        logger.info(f"Transformers {transformers.__version__} available")
    except ImportError:
        logger.info("Transformers not available")

    # Check Qiskit
    try:
        import qiskit
        availability.qiskit = True
        availability.qiskit_version = qiskit.__version__
        logger.info(f"Qiskit {qiskit.__version__} available")
    except ImportError:
        logger.info("Qiskit not available")

    # Check Gymnasium
    try:
        import gymnasium
        availability.gymnasium = True
        logger.info("Gymnasium available")
    except ImportError:
        logger.info("Gymnasium not available")

    return availability


def _create_config(
    environment: DeploymentEnvironment,
    availability: MLAvailability
) -> MLConfig:
    """Create ML configuration based on environment and availability"""

    # Base configuration
    config = MLConfig(
        environment=environment,
        availability=availability,
    )

    # Environment-specific settings
    if environment == DeploymentEnvironment.VERCEL:
        # Vercel has size limits, use lightweight models only
        config.max_model_size_mb = 100
        config.use_mock_predictions = not availability.sklearn
        config.fallback_to_sklearn = True
        config.lstm_enabled = False
        config.cnn_enabled = False
        config.transformer_enabled = False
        config.quantum_enabled = False
        config.rl_enabled = False

    elif environment == DeploymentEnvironment.GCP:
        # GCP has full resources available
        config.max_model_size_mb = 2000
        config.use_gpu = _check_gpu_availability()
        config.lstm_enabled = availability.tensorflow
        config.cnn_enabled = availability.tensorflow
        config.transformer_enabled = availability.transformers and availability.pytorch
        config.quantum_enabled = availability.qiskit
        config.rl_enabled = availability.gymnasium and availability.tensorflow

    else:  # LOCAL or DOCKER
        # Development/container environment
        config.max_model_size_mb = 1000
        config.use_gpu = _check_gpu_availability()
        config.lstm_enabled = availability.tensorflow
        config.cnn_enabled = availability.tensorflow
        config.transformer_enabled = availability.transformers and availability.pytorch
        config.quantum_enabled = availability.qiskit
        config.rl_enabled = availability.gymnasium and availability.tensorflow

    return config


def _check_gpu_availability() -> bool:
    """Check if GPU is available"""
    try:
        import tensorflow as tf
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            logger.info(f"Found {len(gpus)} GPU(s)")
            return True
    except Exception:
        pass

    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            return True
    except Exception:
        pass

    return False


@lru_cache(maxsize=1)
def get_ml_config() -> MLConfig:
    """
    Get the ML configuration singleton.

    This function detects the environment and available libraries,
    then creates an appropriate configuration.

    Returns:
        MLConfig: The ML configuration for this environment
    """
    environment = _detect_environment()
    availability = _check_library_availability()
    config = _create_config(environment, availability)

    logger.info(f"ML Configuration initialized: {environment.value}")
    logger.info(f"Available backends: sklearn={availability.sklearn}, "
                f"tensorflow={availability.tensorflow}, "
                f"pytorch={availability.pytorch}, "
                f"transformers={availability.transformers}")

    return config


def reset_ml_config():
    """Reset the cached ML configuration (useful for testing)"""
    get_ml_config.cache_clear()

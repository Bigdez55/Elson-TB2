"""ML Models module for Elson Trading Engine."""

# Core ML models (always available)
from .neural_network import *

# Volatility regime detection
from .volatility_regime import VolatilityDetector, VolatilityRegime

# Optional imports that require backend app to be installed
try:
    from .ai import *
except ImportError:
    pass  # ai module requires backend app dependencies

try:
    from .ai_portfolio_manager import *
except ImportError:
    pass  # ai_portfolio_manager requires backend app dependencies

try:
    from .anomaly_detector import *
except ImportError:
    pass  # anomaly_detector requires backend app dependencies

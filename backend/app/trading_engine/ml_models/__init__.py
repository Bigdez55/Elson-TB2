"""ML Models module for Elson Trading Engine."""

# Volatility regime detection
from .volatility_regime import VolatilityDetector, VolatilityRegime

# Optional imports that require backend app to be installed
try:
    from .ai import *
except ImportError:
    pass  # ai module requires backend app dependencies

# Neural network service - use from app.services.neural_network
try:
    from app.services.neural_network import NeuralNetworkService
except ImportError:
    pass  # neural_network requires backend app dependencies

# AI Portfolio Manager - use from app.services.ai_portfolio_manager
try:
    from app.services.ai_portfolio_manager import AIPortfolioManager
except ImportError:
    pass  # ai_portfolio_manager requires backend app dependencies

# Anomaly Detector - use from app.services.anomaly_detector
try:
    from app.services.anomaly_detector import AnomalyDetector
except ImportError:
    pass  # anomaly_detector requires backend app dependencies

# Phase 1: Financial Ratios Engine (FinanceToolkit)
try:
    from .ratios_engine import ElsonFinancialRatios, quick_ratio_analysis
except ImportError:
    pass  # ratios_engine requires financetoolkit

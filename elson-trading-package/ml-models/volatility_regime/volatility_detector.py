# Volatility Regime Detector for Elson Wealth Trading Platform

import numpy as np
import pandas as pd
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class VolatilityRegime(Enum):
    """Enum representing different volatility regimes."""
    LOW = 1       # 0-15% annualized volatility
    NORMAL = 2    # 15-25% annualized volatility
    HIGH = 3      # 25-40% annualized volatility
    EXTREME = 4   # >40% annualized volatility

class VolatilityDetector:
    """Detect and classify market volatility regimes.
    
    This class implements the first component of Phase 2 in the
    Hybrid Model Improvement Plan. It detects and classifies
    different volatility regimes to enable regime-specific models.
    """
    
    def __init__(self, lookback_periods=20, vix_weight=0.3):
        """Initialize the volatility detector.
        
        Args:
            lookback_periods: Number of periods to use for volatility calculation
            vix_weight: Weight to give to VIX index if available (0-1)
        """
        self.lookback_periods = lookback_periods
        self.vix_weight = vix_weight
        
    def calculate_realized_volatility(self, returns):
        """Calculate realized volatility from returns series.
        
        Args:
            returns: Series of asset returns
            
        Returns:
            Annualized volatility as a percentage
        """
        if len(returns) < self.lookback_periods:
            logger.warning(f"Insufficient data for volatility calculation. Using available {len(returns)} periods.")
            periods = max(5, len(returns))
        else:
            periods = self.lookback_periods
            
        # Calculate standard deviation of returns
        return_volatility = returns.rolling(window=periods).std().iloc[-1]
        
        # Annualize volatility (assuming daily data - multiply by sqrt(252))
        annualized_volatility = return_volatility * np.sqrt(252) * 100
        
        return annualized_volatility
    
    def detect_regime(self, data, vix_data=None):
        """Detect the current volatility regime.
        
        Args:
            data: DataFrame with 'close' prices for the asset
            vix_data: Optional DataFrame with VIX index data
            
        Returns:
            VolatilityRegime enum value and annualized volatility
        """
        # Validate inputs
        if 'close' not in data.columns:
            raise ValueError("Input data must contain 'close' column")
            
        # Calculate returns
        returns = data['close'].pct_change().dropna()
        
        # Calculate realized volatility
        realized_volatility = self.calculate_realized_volatility(returns)
        
        # Incorporate VIX data if available
        if vix_data is not None and 'close' in vix_data.columns:
            try:
                # Get latest VIX value
                vix_value = vix_data['close'].iloc[-1]
                
                # Combine realized volatility and VIX
                blended_volatility = ((1 - self.vix_weight) * realized_volatility + 
                                     self.vix_weight * vix_value)
            except Exception as e:
                logger.warning(f"Error incorporating VIX data: {str(e)}. Using realized volatility only.")
                blended_volatility = realized_volatility
        else:
            blended_volatility = realized_volatility
            
        # Classify volatility regime
        if blended_volatility < 15:
            regime = VolatilityRegime.LOW
        elif blended_volatility < 25:
            regime = VolatilityRegime.NORMAL
        elif blended_volatility < 40:
            regime = VolatilityRegime.HIGH
        else:
            regime = VolatilityRegime.EXTREME
            
        return regime, blended_volatility
    
    def get_regime_description(self, regime):
        """Get a human-readable description of a volatility regime.
        
        Args:
            regime: VolatilityRegime enum value
            
        Returns:
            Description string
        """
        descriptions = {
            VolatilityRegime.LOW: "Low volatility (0-15%)",
            VolatilityRegime.NORMAL: "Normal volatility (15-25%)",
            VolatilityRegime.HIGH: "High volatility (25-40%)",
            VolatilityRegime.EXTREME: "Extreme volatility (40%+)"
        }
        
        return descriptions.get(regime, "Unknown volatility regime")
    
    def should_activate_circuit_breaker(self, regime, volatility):
        """Determine if circuit breaker should be activated.
        
        Args:
            regime: VolatilityRegime enum value
            volatility: Calculated volatility value
            
        Returns:
            Boolean indicating if circuit breaker should activate
        """
        # Activate for extreme volatility
        if regime == VolatilityRegime.EXTREME:
            return True
            
        # Also activate if in high regime but volatility is near extreme threshold
        if regime == VolatilityRegime.HIGH and volatility > 38:
            return True
            
        return False
    
    def get_recommended_parameters(self, regime):
        """Get recommended model parameters for the detected regime.
        
        Args:
            regime: VolatilityRegime enum value
            
        Returns:
            Dictionary of recommended parameters
        """
        # Parameter recommendations for different regimes
        recommendations = {
            VolatilityRegime.LOW: {
                "confidence_threshold": 0.55,
                "prediction_horizon": 5,
                "model_weights": {
                    "random_forest": 1.0,
                    "gradient_boosting": 1.0,
                    "neural_network": 1.0,
                    "quantum_kernel": 1.2,
                    "quantum_variational": 1.2
                }
            },
            VolatilityRegime.NORMAL: {
                "confidence_threshold": 0.60,
                "prediction_horizon": 3,
                "model_weights": {
                    "random_forest": 1.1,
                    "gradient_boosting": 1.1,
                    "neural_network": 0.9,
                    "quantum_kernel": 1.0,
                    "quantum_variational": 0.9
                }
            },
            VolatilityRegime.HIGH: {
                "confidence_threshold": 0.65,
                "prediction_horizon": 2,
                "model_weights": {
                    "random_forest": 1.2,
                    "gradient_boosting": 1.3,
                    "neural_network": 0.7,
                    "quantum_kernel": 0.8,
                    "quantum_variational": 0.7
                }
            },
            VolatilityRegime.EXTREME: {
                "confidence_threshold": 0.75,
                "prediction_horizon": 1,
                "model_weights": {
                    "random_forest": 1.5,
                    "gradient_boosting": 1.5,
                    "neural_network": 0.5,
                    "quantum_kernel": 0.5,
                    "quantum_variational": 0.5
                },
                "circuit_breaker": True
            }
        }
        
        return recommendations.get(regime, recommendations[VolatilityRegime.NORMAL])

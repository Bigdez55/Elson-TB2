"""Volatility-aware feature engineering for the Elson Wealth Trading Platform.

This module implements the volatility-aware feature engineering component of Phase 2
in the Hybrid Model Improvement Plan. It provides features that are normalized for
different volatility regimes and adds relative volatility metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
from scipy import stats
import warnings

# Suppress warnings for operations that might generate them
warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


class VolatilityFeatureEngineer:
    """
    Feature engineering class specialized for volatility-aware features.
    
    This class generates features that are normalized for different volatility
    regimes and provides relative volatility metrics to help models adapt to
    changing market conditions.
    """
    
    def __init__(
        self,
        base_lookback: int = 20,
        long_lookback: int = 252,  # ~1 year of trading days
        volatility_regimes: Dict[str, Tuple[float, float]] = None,
        use_log_returns: bool = True
    ):
        """
        Initialize the volatility feature engineer.
        
        Args:
            base_lookback: Base lookback period for short-term metrics
            long_lookback: Longer lookback period for historical comparisons
            volatility_regimes: Dictionary defining volatility regime boundaries
            use_log_returns: Whether to use log returns instead of simple returns
        """
        self.base_lookback = base_lookback
        self.long_lookback = long_lookback
        self.use_log_returns = use_log_returns
        
        # Define volatility regimes if not provided (with updated thresholds)
        self.volatility_regimes = volatility_regimes or {
            'low': (0.0, 0.15),      # 0-15% annualized
            'normal': (0.15, 0.20),   # 15-20% annualized (updated from 15-25%)
            'high': (0.20, 0.35),     # 20-35% annualized (updated from 25-40%)
            'extreme': (0.35, float('inf'))  # >35% annualized (updated from >40%)
        }
        
        # Storage for computed metrics
        self.rolling_metrics = {}
        self.relative_metrics = {}
        self.market_regime_features = {}
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """
        Calculate returns series based on price data.
        
        Args:
            prices: Series of price data
            
        Returns:
            Series of returns
        """
        if self.use_log_returns:
            # Log returns: log(P_t / P_{t-1})
            returns = np.log(prices / prices.shift(1))
        else:
            # Simple returns: (P_t - P_{t-1}) / P_{t-1}
            returns = prices.pct_change()
        
        # Replace infinite values with NaN, then fill NaNs
        returns.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        return returns
    
    def calculate_volatility(
        self, 
        returns: pd.Series, 
        window: int, 
        method: str = 'standard',
        annualize: bool = True
    ) -> pd.Series:
        """
        Calculate rolling volatility from returns using various methods.
        
        Args:
            returns: Series of returns
            window: Lookback window for rolling volatility
            method: Volatility calculation method ('standard', 'parkinson', 'gk', 'rs', 'ewma')
            annualize: Whether to annualize the volatility
            
        Returns:
            Series of rolling volatility
        """
        if method == 'standard':
            # Standard deviation of returns
            vol = returns.rolling(window=window).std()
        
        elif method == 'ewma':
            # Exponentially Weighted Moving Average volatility (gives more weight to recent observations)
            # Standard EWMA with lambda = 0.94 (industry standard for daily data)
            lambda_param = 0.94
            vol = np.sqrt(returns.ewm(alpha=1-lambda_param).var())
        
        elif method == 'parkinson':
            # Parkinson's volatility estimator (uses high-low range)
            # Requires high and low price data, so we'll calculate a proxy if not available
            if hasattr(returns, 'index') and isinstance(returns.index, pd.DateTimeIndex):
                # Try to get high and low prices from the original data frame
                if 'high' in returns.index.name and 'low' in returns.index.name:
                    high = returns['high']
                    low = returns['low']
                    
                    # Parkinson estimator
                    log_hl = np.log(high / low)
                    vol = np.sqrt(1 / (4 * np.log(2)) * log_hl**2)
                    vol = vol.rolling(window=window).mean()
                else:
                    # Fall back to standard if high/low not available
                    vol = returns.rolling(window=window).std()
            else:
                # Fall back to standard if needed
                vol = returns.rolling(window=window).std()
        
        elif method == 'rs':
            # Rogers-Satchell volatility estimator (considers both high-low range and close-to-close)
            # This is a proxy implementation that works with return data only
            # Real RS requires OHLC data
            abs_returns = np.abs(returns)
            vol = np.sqrt(abs_returns.rolling(window=window).mean() ** 2)
        
        else:
            # Default to standard volatility
            logger.warning(f"Unknown volatility method '{method}', using standard deviation")
            vol = returns.rolling(window=window).std()
            
        # Annualize if requested (assuming daily data, multiply by sqrt(252))
        if annualize:
            vol = vol * np.sqrt(252)
            
        return vol
    
    def calculate_garch_volatility_proxy(self, returns: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate a GARCH-like volatility proxy that responds quickly to volatility clustering.
        
        This is a simplified implementation that captures the essence of GARCH without
        requiring the statsmodels dependency, making it faster and more robust.
        
        Args:
            returns: Series of returns
            window: Lookback window
            
        Returns:
            Series of GARCH-like volatility estimates
        """
        # Start with a simple volatility estimate
        vol = np.abs(returns)
        
        # Initialize the GARCH-like volatility with the standard deviation
        initial_vol = returns.rolling(window=min(window, len(returns) // 2)).std().fillna(returns.std())
        
        # Parameters similar to GARCH(1,1)
        omega = 0.05   # Weight of long-run average variance
        alpha = 0.1    # Weight of previous return shock
        beta = 0.85    # Weight of previous volatility
        
        # Initialize result array
        garch_vol = np.zeros_like(returns)
        garch_vol[:] = np.nan
        
        # Use the initial volatility for the first observation
        if len(returns) > 0 and not np.isnan(initial_vol.iloc[0]):
            garch_vol[0] = initial_vol.iloc[0]
            
            # Iterate through the returns to update the volatility estimate
            for t in range(1, len(returns)):
                if np.isnan(returns.iloc[t]) or np.isnan(garch_vol[t-1]):
                    # Handle missing data
                    garch_vol[t] = garch_vol[t-1] if t > 0 else initial_vol.iloc[0]
                else:
                    # GARCH update equation: long-run component + alpha*recent_shock + beta*previous_vol
                    long_run_var = initial_vol.iloc[t] if t < len(initial_vol) else initial_vol.iloc[-1]
                    prev_shock = returns.iloc[t-1]**2
                    prev_vol = garch_vol[t-1]**2
                    
                    # Calculate new variance and convert to volatility
                    new_var = omega * long_run_var**2 + alpha * prev_shock + beta * prev_vol
                    garch_vol[t] = np.sqrt(new_var)
        
        # Convert to Series with the same index as returns
        garch_vol_series = pd.Series(garch_vol, index=returns.index)
        
        # Annualize (assuming daily data)
        garch_vol_series = garch_vol_series * np.sqrt(252)
        
        return garch_vol_series
        
    def calculate_jump_robust_volatility(self, returns: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate a jump-robust volatility measure that reduces the impact of outliers.
        
        This implementation uses a modified median absolute deviation (MAD) approach.
        
        Args:
            returns: Series of returns
            window: Lookback window
            
        Returns:
            Series of jump-robust volatility estimates
        """
        # Use a rolling median absolute deviation approach
        # MAD is more robust to outliers/jumps than standard deviation
        def mad_volatility(x):
            if len(x) == 0 or np.isnan(x).all():
                return np.nan
                
            median_x = np.nanmedian(x)
            mad = np.nanmedian(np.abs(x - median_x))
            
            # Convert MAD to standard deviation equivalent (1.4826 is the scaling factor)
            return mad * 1.4826
            
        # Calculate rolling MAD-based volatility
        mad_vol = returns.rolling(window=window).apply(mad_volatility, raw=True)
        
        # Annualize (assuming daily data)
        mad_vol = mad_vol * np.sqrt(252)
        
        return mad_vol
    
    def engineer_volatility_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer volatility-aware features from market data.
        
        Args:
            data: DataFrame with market data (must include 'close' column)
            
        Returns:
            DataFrame with additional volatility-aware features
        """
        # Input validation
        if 'close' not in data.columns:
            raise ValueError("Input data must contain 'close' column")
        
        # Copy the input data to avoid modifying it
        df = data.copy()
        
        # Calculate returns
        df['returns'] = self.calculate_returns(df['close'])
        
        # ------ Advanced Volatility Features ------
        
        # Short-term volatility using multiple methods
        df['volatility_short'] = self.calculate_volatility(df['returns'], window=self.base_lookback, method='standard')
        df['volatility_short_ewma'] = self.calculate_volatility(df['returns'], window=self.base_lookback, method='ewma')
        df['volatility_short_jump_robust'] = self.calculate_jump_robust_volatility(df['returns'], window=self.base_lookback)
        df['volatility_short_garch'] = self.calculate_garch_volatility_proxy(df['returns'], window=self.base_lookback)
        
        # Create a blended volatility indicator (combined model approach)
        df['volatility_short_blended'] = (
            df['volatility_short'] * 0.3 + 
            df['volatility_short_ewma'] * 0.3 + 
            df['volatility_short_jump_robust'] * 0.2 + 
            df['volatility_short_garch'] * 0.2
        )
        
        # Medium-term volatility
        medium_window = min(self.base_lookback * 2, len(df) // 2)
        df['volatility_medium'] = self.calculate_volatility(df['returns'], window=medium_window)
        df['volatility_medium_garch'] = self.calculate_garch_volatility_proxy(df['returns'], window=medium_window)
        
        # Long-term volatility
        long_window = min(self.long_lookback, len(df) // 2)
        df['volatility_long'] = self.calculate_volatility(df['returns'], window=long_window)
        
        # Use our blended volatility as the primary volatility metric for regime classification
        # This provides a more stable and accurate measure than standard volatility alone
        primary_volatility = df['volatility_short_blended']
        
        # ------ Volatility Regime Classification ------
        
        # Classify current volatility regime using blended volatility
        vol_conditions = [
            (primary_volatility >= low) & (primary_volatility < high)
            for regime, (low, high) in self.volatility_regimes.items()
        ]
        vol_choices = list(self.volatility_regimes.keys())
        
        # Create categorical regime variable
        df['volatility_regime'] = np.select(vol_conditions, vol_choices, default='unknown')
        
        # Create binary indicator variables for each regime
        for regime in self.volatility_regimes.keys():
            df[f'regime_{regime}'] = (df['volatility_regime'] == regime).astype(int)
        
        # ------ Relative Volatility Metrics ------
        
        # Relative volatility (short-term vs long-term)
        df['volatility_ratio_short_long'] = df['volatility_short'] / df['volatility_long'].replace(0, np.nan)
        
        # Z-score of current volatility relative to historical distribution
        # (how many standard deviations from the historical mean)
        if len(df) >= self.long_lookback:
            vol_mean = df['volatility_short'].rolling(window=self.long_lookback).mean()
            vol_std = df['volatility_short'].rolling(window=self.long_lookback).std()
            df['volatility_zscore'] = (df['volatility_short'] - vol_mean) / vol_std.replace(0, np.nan)
        else:
            # If we don't have enough data, use expanding window
            vol_mean = df['volatility_short'].expanding().mean()
            vol_std = df['volatility_short'].expanding().std()
            df['volatility_zscore'] = (df['volatility_short'] - vol_mean) / vol_std.replace(0, np.nan)
        
        # Percentile of current volatility in historical distribution
        df['volatility_percentile'] = df['volatility_short'].rolling(window=self.long_lookback).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else np.nan
        )
        
        # ------ Volatility-Adjusted Indicators ------
        
        # Volatility-adjusted returns (return divided by volatility)
        df['returns_vol_adjusted'] = df['returns'] / df['volatility_short'].replace(0, np.nan)
        
        # Volatility-adjusted price changes
        df['price_change_vol_adjusted'] = (df['close'].pct_change() / df['volatility_short']).replace([np.inf, -np.inf], np.nan)
        
        # ------ Volatility Trend Features ------
        
        # Volatility trend (is volatility increasing or decreasing)
        df['volatility_trend_5d'] = df['volatility_short'].pct_change(5)
        df['volatility_trend_10d'] = df['volatility_short'].pct_change(10)
        df['volatility_trend_20d'] = df['volatility_short'].pct_change(20)
        
        # Volatility acceleration/deceleration
        df['volatility_acceleration'] = df['volatility_trend_5d'].diff()
        
        # ------ Volatility-Based Moving Averages ------
        
        # Standard moving averages
        df['sma_short'] = df['close'].rolling(window=self.base_lookback).mean()
        
        # Volatility-adjusted moving average (weights recent prices more in high vol regimes)
        # Start with a copy of close prices
        close_vals = df['close'].values
        vol_vals = df['volatility_short'].values
        vol_adjusted_ma = np.full_like(close_vals, np.nan, dtype=float)
        
        # Calculate a vol-weighted MA where higher volatility reduces the effective lookback
        for i in range(self.base_lookback, len(close_vals)):
            # Convert volatility to a weight factor (higher vol = shorter lookback)
            # Normalize to range [0.2, 1.0] where 1.0 means use full lookback
            # and 0.2 means use only 20% of the lookback period
            curr_vol = vol_vals[i]
            
            # Skip if volatility is NaN
            if np.isnan(curr_vol):
                continue
                
            # Determine effective lookback based on volatility
            vol_factor = max(0.2, min(1.0, 0.15 / max(curr_vol, 0.01)))  # Normalize vol
            effective_lookback = max(5, int(self.base_lookback * vol_factor))
            
            # Calculate the MA with the effective lookback
            # if all values are valid
            if i >= effective_lookback and not np.isnan(close_vals[i-effective_lookback:i]).any():
                vol_adjusted_ma[i] = np.mean(close_vals[i-effective_lookback:i])
        
        df['vol_adjusted_ma'] = vol_adjusted_ma
        
        # ------ Market Regime Features ------
        
        # Simple trend detection (bull, bear, sideways)
        # Using SMA relationships as a proxy
        df['sma_medium'] = df['close'].rolling(window=medium_window).mean()
        df['sma_long'] = df['close'].rolling(window=long_window).mean()
        
        # Bull market: price > medium SMA > long SMA
        df['bull_market'] = ((df['close'] > df['sma_medium']) & 
                             (df['sma_medium'] > df['sma_long'])).astype(int)
        
        # Bear market: price < medium SMA < long SMA
        df['bear_market'] = ((df['close'] < df['sma_medium']) & 
                             (df['sma_medium'] < df['sma_long'])).astype(int)
        
        # Sideways market: neither bull nor bear
        df['sideways_market'] = ((df['bull_market'] == 0) & (df['bear_market'] == 0)).astype(int)
        
        # ------ Interaction Features ------
        
        # Interaction between volatility regime and market regime
        # These features help the model understand how volatility affects different market regimes
        df['bull_market_low_vol'] = (df['bull_market'] & df['regime_low']).astype(int)
        df['bull_market_high_vol'] = (df['bull_market'] & df['regime_high']).astype(int)
        df['bear_market_low_vol'] = (df['bear_market'] & df['regime_low']).astype(int)
        df['bear_market_high_vol'] = (df['bear_market'] & df['regime_high']).astype(int)
        
        # ------ Clean Up ------
        
        # Replace any remaining NaN values
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        # Store computed features for later reference
        self.rolling_metrics = {
            'volatility_short': df['volatility_short'].iloc[-1],
            'volatility_medium': df['volatility_medium'].iloc[-1],
            'volatility_long': df['volatility_long'].iloc[-1]
        }
        
        self.relative_metrics = {
            'volatility_ratio': df['volatility_ratio_short_long'].iloc[-1],
            'volatility_zscore': df['volatility_zscore'].iloc[-1],
            'volatility_percentile': df['volatility_percentile'].iloc[-1]
        }
        
        self.market_regime_features = {
            'current_regime': df['volatility_regime'].iloc[-1],
            'is_bull_market': bool(df['bull_market'].iloc[-1]),
            'is_bear_market': bool(df['bear_market'].iloc[-1]),
            'is_sideways': bool(df['sideways_market'].iloc[-1])
        }
        
        return df
    
    def get_current_volatility_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current volatility metrics.
        
        Returns:
            Dictionary with volatility summary metrics
        """
        summary = {
            'metrics': self.rolling_metrics,
            'relative_metrics': self.relative_metrics,
            'market_regime': self.market_regime_features,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add regime-specific recommendations
        current_regime = self.market_regime_features.get('current_regime')
        summary['recommendations'] = self.get_regime_recommendations(current_regime)
        
        return summary
    
    def get_regime_recommendations(self, regime: str) -> Dict[str, Any]:
        """
        Get model parameter recommendations based on volatility regime.
        
        Args:
            regime: Current volatility regime
            
        Returns:
            Dictionary with parameter recommendations
        """
        # Default recommendations
        default_rec = {
            'confidence_threshold': 0.6,
            'prediction_horizon': 3,
            'lookback_periods': self.base_lookback,
            'circuit_breaker': False,
            'position_sizing': 1.0
        }
        
        # Regime-specific recommendations with updated thresholds
        recommendations = {
            'low': {
                'confidence_threshold': 0.55,
                'prediction_horizon': 5,
                'lookback_periods': self.base_lookback,
                'circuit_breaker': False,
                'position_sizing': 1.0,
                'model_weights': {
                    'random_forest': 1.0,
                    'gradient_boosting': 1.0,
                    'neural_network': 1.0,
                    'quantum_kernel': 1.2,
                    'quantum_variational': 1.2
                }
            },
            'normal': {
                'confidence_threshold': 0.60,
                'prediction_horizon': 3,
                'lookback_periods': self.base_lookback,
                'circuit_breaker': False,
                'position_sizing': 1.0,
                'model_weights': {
                    'random_forest': 1.1,
                    'gradient_boosting': 1.1,
                    'neural_network': 0.9,
                    'quantum_kernel': 1.0,
                    'quantum_variational': 0.9
                }
            },
            'high': {
                'confidence_threshold': 0.82,  # Updated from 0.65
                'prediction_horizon': 1,       # Updated from 2
                'lookback_periods': 8,         # Updated from base_lookback/2
                'circuit_breaker': True,       # Updated from False
                'position_sizing': 0.25,       # Updated from 0.75
                'model_weights': {
                    'random_forest': 2.0,
                    'gradient_boosting': 1.7,
                    'neural_network': 0.2,
                    'quantum_kernel': 0.4,
                    'quantum_variational': 0.3
                }
            },
            'extreme': {
                'confidence_threshold': 0.90,  # Updated from 0.75
                'prediction_horizon': 1,
                'lookback_periods': 5,         # Updated from base_lookback/4
                'circuit_breaker': True,
                'position_sizing': 0.10,       # Updated from 0.5
                'model_weights': {
                    'random_forest': 2.5,
                    'gradient_boosting': 2.0,
                    'neural_network': 0.1,
                    'quantum_kernel': 0.1,
                    'quantum_variational': 0.1
                }
            }
        }
        
        # Return regime-specific recommendations or default if regime not found
        return recommendations.get(regime, default_rec)


def create_volatility_adjusted_features(data: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to create volatility-adjusted features.
    
    Args:
        data: DataFrame with market data
        
    Returns:
        DataFrame with additional volatility-aware features
    """
    engineer = VolatilityFeatureEngineer()
    return engineer.engineer_volatility_features(data)


def get_current_volatility_regime(data: pd.DataFrame) -> str:
    """
    Get the current volatility regime from market data.
    
    Args:
        data: DataFrame with market data
        
    Returns:
        String indicating the current volatility regime
    """
    engineer = VolatilityFeatureEngineer()
    engineer.engineer_volatility_features(data)
    return engineer.market_regime_features.get('current_regime', 'unknown')


def get_volatility_recommendations(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Get volatility-based recommendations for model parameters.
    
    Args:
        data: DataFrame with market data
        
    Returns:
        Dictionary with parameter recommendations
    """
    engineer = VolatilityFeatureEngineer()
    engineer.engineer_volatility_features(data)
    regime = engineer.market_regime_features.get('current_regime', 'normal')
    return engineer.get_regime_recommendations(regime)
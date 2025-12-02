"""Market data processing service.

This module provides functionality for processing market data, including
handling corporate actions, validating data quality, caching, and managing
multiple data sources.
"""

import logging
from typing import Dict, List, Optional, Union, Tuple, Any
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import hashlib
import time
from functools import lru_cache
from fastapi import HTTPException

from app.services.market_data import MarketDataService
from app.core.config import settings
from app.core.metrics import record_metric

logger = logging.getLogger(__name__)


class DataQualityIssue(Exception):
    """Exception raised for data quality issues."""
    pass


class CorporateAction:
    """Represents a corporate action (split, dividend, etc.)."""
    def __init__(
        self,
        symbol: str,
        action_type: str,
        ex_date: datetime,
        ratio: Optional[float] = None,
        amount: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.symbol = symbol
        self.action_type = action_type  # split, dividend, merger, etc.
        self.ex_date = ex_date
        self.ratio = ratio  # For splits
        self.amount = amount  # For dividends
        self.details = details or {}
        
    def __repr__(self):
        return f"<CorporateAction {self.action_type} for {self.symbol} on {self.ex_date.date()}>"


class MarketDataProcessor:
    """Service for processing market data with advanced features."""
    
    def __init__(
        self,
        market_data_service: Optional[MarketDataService] = None,
        max_cache_size: int = 1000,
        cache_ttl: int = 300  # 5 minutes in seconds
    ):
        """Initialize with market data service."""
        self.market_data = market_data_service
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
        
        # Cache for market data
        self._price_cache = {}
        self._historical_cache = {}
        self._corporate_actions_cache = {}
        
        # Data quality thresholds
        self.max_price_change_pct = float(getattr(settings, 'MAX_PRICE_CHANGE_PCT', 10.0))  # 10% default
        self.min_valid_price = float(getattr(settings, 'MIN_VALID_PRICE', 0.01))
        self.max_valid_price = float(getattr(settings, 'MAX_VALID_PRICE', 1000000))
        
        # Fallback data sources priority
        self.data_sources = [
            "primary",    # Main data source
            "secondary",  # Secondary source
            "tertiary",   # Tertiary source
            "historical", # Historical/cached data
        ]
        
        # Known corporate actions database
        # In production, this would be stored in a database
        self.corporate_actions = []
        
        # Market regime detection parameters
        self.regime_volatility_window = 30  # Days for volatility calculation
        self.regime_ma_fast = 20  # Fast moving average period
        self.regime_ma_slow = 50  # Slow moving average period
    
    async def get_price_with_validation(self, symbol: str) -> Dict[str, Any]:
        """Get current price with data quality validation.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary containing validated price data
            
        Raises:
            DataQualityIssue: If data quality checks fail
        """
        # First check cache
        cache_key = f"price_{symbol}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Try each data source in order
        for source in self.data_sources:
            try:
                # Skip historical for real-time quotes
                if source == "historical":
                    continue
                
                if source == "primary":
                    # Get from primary source
                    quote = await self.market_data.get_quote(symbol)
                elif source == "secondary":
                    # In a real system, would call secondary source here
                    continue
                elif source == "tertiary":
                    # In a real system, would call tertiary source here
                    continue
                else:
                    continue
                
                # Validate the data
                validated_data = self._validate_price_data(symbol, quote)
                
                # Store in cache
                self._add_to_cache(cache_key, validated_data)
                
                # Record successful retrieval
                record_metric("market_data_retrieval_success", 1, 
                             {"symbol": symbol, "source": source})
                
                return validated_data
                
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol} from {source}: {e}")
                record_metric("market_data_retrieval_failure", 1, 
                            {"symbol": symbol, "source": source, "error": str(e)})
        
        # If all live sources fail, check if we have historical data
        try:
            # Get most recent historical data point
            historical = await self.get_historical_data(symbol, 
                                                       start_date=datetime.now() - timedelta(days=5),
                                                       end_date=datetime.now(),
                                                       interval="1d")
            
            if not historical.empty:
                # Get last row
                last_price = historical.iloc[-1]
                
                result = {
                    "symbol": symbol,
                    "price": float(last_price["Close"]),
                    "change": 0.0,  # Can't determine change
                    "change_percent": 0.0,
                    "volume": int(last_price["Volume"]),
                    "timestamp": last_price.name.isoformat(),
                    "source": "historical_fallback",
                    "is_fallback": True
                }
                
                logger.warning(f"Using historical fallback price for {symbol}")
                record_metric("market_data_historical_fallback", 1, {"symbol": symbol})
                
                return result
        except Exception as e:
            logger.error(f"Historical fallback failed for {symbol}: {e}")
        
        # All sources failed
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve price data for {symbol} from any source"
        )
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
        adjust_for_corporate_actions: bool = True
    ) -> pd.DataFrame:
        """Get historical data with data quality validation and corporate action adjustments.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data (defaults to now)
            interval: Data interval (1d, 1h, etc.)
            adjust_for_corporate_actions: Whether to adjust for corporate actions
            
        Returns:
            DataFrame containing validated historical price data
        """
        end_date = end_date or datetime.now()
        
        # Check cache
        cache_key = f"hist_{symbol}_{start_date.date()}_{end_date.date()}_{interval}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Try each data source
        for source in self.data_sources:
            if source in ["primary", "historical"]:
                try:
                    # Get historical data from primary source
                    df = await self.market_data.get_historical_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval
                    )
                    
                    # Validate data
                    df = self._validate_historical_data(symbol, df)
                    
                    # Process corporate actions if needed
                    if adjust_for_corporate_actions:
                        df = self._adjust_for_corporate_actions(symbol, df)
                    
                    # Cache result
                    self._add_to_cache(cache_key, df)
                    
                    return df
                except Exception as e:
                    logger.warning(f"Failed to get historical data for {symbol} from {source}: {e}")
                    record_metric("historical_data_retrieval_failure", 1, 
                                 {"symbol": symbol, "source": source, "error": str(e)})
        
        # All sources failed
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve historical data for {symbol} from any source"
        )
    
    async def get_corporate_actions(
        self,
        symbol: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> List[CorporateAction]:
        """Get corporate actions for a symbol in a date range.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for corporate actions
            end_date: End date for corporate actions (defaults to now)
            
        Returns:
            List of corporate actions
        """
        end_date = end_date or datetime.now()
        
        # Check cache
        cache_key = f"corp_{symbol}_{start_date.date()}_{end_date.date()}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # In a real implementation, this would query an API or database
        # For this implementation, we'll just use the in-memory list
        actions = [
            action for action in self.corporate_actions
            if action.symbol == symbol and start_date <= action.ex_date <= end_date
        ]
        
        # Cache the result
        self._add_to_cache(cache_key, actions)
        
        return actions
    
    async def add_corporate_action(self, corporate_action: CorporateAction) -> bool:
        """Add a corporate action to the database.
        
        Args:
            corporate_action: The corporate action to add
            
        Returns:
            True if added successfully
        """
        # In a real implementation, this would save to a database
        self.corporate_actions.append(corporate_action)
        
        # Invalidate relevant cache entries
        self._invalidate_corporate_action_cache(corporate_action.symbol)
        
        logger.info(f"Added corporate action: {corporate_action}")
        return True
    
    async def calculate_adjusted_price(
        self,
        symbol: str,
        price: float,
        from_date: datetime,
        to_date: datetime
    ) -> float:
        """Calculate price adjusted for corporate actions between dates.
        
        Args:
            symbol: Stock ticker symbol
            price: Original price
            from_date: Original date for the price
            to_date: Date to adjust the price to
            
        Returns:
            Adjusted price
        """
        # Get corporate actions between the dates
        actions = await self.get_corporate_actions(symbol, from_date, to_date)
        
        adjusted_price = price
        
        # Apply adjustments
        for action in actions:
            if action.action_type == "split" and action.ratio:
                adjusted_price *= action.ratio
            elif action.action_type == "dividend" and action.amount:
                # Simple dividend adjustment
                adjusted_price -= action.amount
        
        return adjusted_price
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Clear the market data cache.
        
        Args:
            symbol: If provided, only clear cache for this symbol
        """
        if symbol:
            # Clear only for specific symbol
            keys_to_remove = []
            
            for key in self._price_cache:
                if key.startswith(f"price_{symbol}"):
                    keys_to_remove.append(key)
                    
            for key in self._historical_cache:
                if key.startswith(f"hist_{symbol}"):
                    keys_to_remove.append(key)
                    
            for key in self._corporate_actions_cache:
                if key.startswith(f"corp_{symbol}"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                if key in self._price_cache:
                    del self._price_cache[key]
                if key in self._historical_cache:
                    del self._historical_cache[key]
                if key in self._corporate_actions_cache:
                    del self._corporate_actions_cache[key]
                    
            logger.info(f"Cleared cache for symbol {symbol}")
        else:
            # Clear entire cache
            self._price_cache = {}
            self._historical_cache = {}
            self._corporate_actions_cache = {}
            logger.info("Cleared entire market data cache")
    
    def _validate_price_data(self, symbol: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate price data quality.
        
        Args:
            symbol: Stock ticker symbol
            price_data: Price data to validate
            
        Returns:
            Validated price data
            
        Raises:
            DataQualityIssue: If validation fails
        """
        # Get the price
        price = price_data.get("price")
        if price is None:
            raise DataQualityIssue("Missing price in data")
        
        # Basic range check
        if not (self.min_valid_price <= price <= self.max_valid_price):
            raise DataQualityIssue(
                f"Price {price} is outside valid range: {self.min_valid_price} - {self.max_valid_price}"
            )
        
        # Check for extreme price change
        if "change_percent" in price_data:
            change_pct = abs(price_data["change_percent"])
            if change_pct > self.max_price_change_pct:
                # Log but don't reject - this might be legitimate (e.g., earnings surprise)
                logger.warning(
                    f"Unusual price change for {symbol}: {change_pct}% (exceeds {self.max_price_change_pct}%)"
                )
                record_metric("unusual_price_change", float(change_pct), {"symbol": symbol})
        
        # Check timestamp is recent
        if "timestamp" in price_data:
            timestamp = pd.to_datetime(price_data["timestamp"])
            time_diff = datetime.now() - timestamp
            
            if time_diff > timedelta(minutes=15) and "source" not in price_data:
                # If not from a fallback source and data is stale
                logger.warning(
                    f"Stale price data for {symbol}, timestamp: {timestamp}, "
                    f"age: {time_diff.total_seconds() / 60:.1f} minutes"
                )
        
        return price_data
    
    def _validate_historical_data(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """Validate historical data quality.
        
        Args:
            symbol: Stock ticker symbol
            df: DataFrame with historical data
            
        Returns:
            DataFrame with validated data (gaps/issues fixed where possible)
        """
        if df.empty:
            raise DataQualityIssue(f"Empty historical data for {symbol}")
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Check required columns
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataQualityIssue(f"Missing required columns: {missing_columns}")
        
        # Check for valid ranges
        for col in ["Open", "High", "Low", "Close"]:
            # Replace invalid values with NaN
            df.loc[df[col] < self.min_valid_price, col] = np.nan
            df.loc[df[col] > self.max_valid_price, col] = np.nan
        
        # Check consistency
        df.loc[df["Low"] > df["High"], ["Low", "High"]] = np.nan
        df.loc[df["Open"] > df["High"], "Open"] = df["High"]
        df.loc[df["Open"] < df["Low"], "Open"] = df["Low"]
        df.loc[df["Close"] > df["High"], "Close"] = df["High"]
        df.loc[df["Close"] < df["Low"], "Close"] = df["Low"]
        
        # Check for missing dates
        if df.index.name != "Date" and "Date" in df.columns:
            df = df.set_index("Date")
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Fill gaps with forward-fill (assumes last known price)
        # First, check if there are gaps
        expected_index = pd.date_range(
            start=df.index.min(),
            end=df.index.max(),
            freq="B"  # Business days
        )
        
        missing_dates = expected_index.difference(df.index)
        if len(missing_dates) > 0:
            logger.warning(f"Found {len(missing_dates)} missing dates in {symbol} data")
            
            # Create a complete dataframe with the expected index
            complete_df = pd.DataFrame(index=expected_index)
            
            # Merge with original data
            complete_df = complete_df.join(df)
            
            # Forward fill missing values
            complete_df = complete_df.fillna(method="ffill")
            
            # If there are still NaNs at the beginning, backward fill
            complete_df = complete_df.fillna(method="bfill")
            
            df = complete_df
        
        # Fill any remaining NaNs with interpolation
        if df.isna().any().any():
            df = df.interpolate(method="time")
            
            # Count remaining NaNs after interpolation
            remaining_nans = df.isna().sum().sum()
            if remaining_nans > 0:
                logger.warning(f"{remaining_nans} NaN values remain in {symbol} data after interpolation")
        
        return df
    
    def _adjust_for_corporate_actions(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """Adjust historical data for corporate actions.
        
        Args:
            symbol: Stock ticker symbol
            df: DataFrame with historical data
            
        Returns:
            Adjusted DataFrame
        """
        # In a real implementation, this would properly adjust for corporate actions
        # This is a simplified placeholder
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Get corporate actions for this period
        start_date = df.index.min()
        end_date = df.index.max()
        
        # Use synchronous approach since we're in a sync method
        actions = []
        for action in self.corporate_actions:
            if (action.symbol == symbol and 
                start_date <= action.ex_date <= end_date):
                actions.append(action)
        
        # Apply adjustments
        for action in actions:
            if action.action_type == "split" and action.ratio:
                # Apply split adjustment to all data before the ex-date
                mask = df.index < action.ex_date
                df.loc[mask, ["Open", "High", "Low", "Close"]] *= action.ratio
                df.loc[mask, "Volume"] /= action.ratio
                
                logger.info(
                    f"Applied {action.ratio}:1 split adjustment for {symbol} "
                    f"on {action.ex_date.date()}"
                )
            
            elif action.action_type == "dividend" and action.amount:
                # Simple dividend adjustment
                mask = df.index < action.ex_date
                df.loc[mask, ["Open", "High", "Low", "Close"]] -= action.amount
                
                logger.info(
                    f"Applied ${action.amount} dividend adjustment for {symbol} "
                    f"on {action.ex_date.date()}"
                )
        
        return df
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if available and not expired."""
        # Check price cache
        if key.startswith("price_") and key in self._price_cache:
            entry = self._price_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._price_cache[key]  # Remove expired entry
        
        # Check historical cache
        elif key.startswith("hist_") and key in self._historical_cache:
            entry = self._historical_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._historical_cache[key]  # Remove expired entry
        
        # Check corporate actions cache
        elif key.startswith("corp_") and key in self._corporate_actions_cache:
            entry = self._corporate_actions_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._corporate_actions_cache[key]  # Remove expired entry
        
        return None
    
    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add data to cache with timestamp."""
        entry = {
            "data": data,
            "timestamp": time.time()
        }
        
        # Add to appropriate cache based on key prefix
        if key.startswith("price_"):
            cache = self._price_cache
        elif key.startswith("hist_"):
            cache = self._historical_cache
        elif key.startswith("corp_"):
            cache = self._corporate_actions_cache
        else:
            logger.warning(f"Unknown cache key prefix: {key}")
            return
        
        # Add to cache
        cache[key] = entry
        
        # Check if cache is too large
        if len(cache) > self.max_cache_size:
            # Remove oldest entries
            sorted_keys = sorted(cache.keys(), key=lambda k: cache[k]["timestamp"])
            keys_to_remove = sorted_keys[:len(cache) - self.max_cache_size]
            for k in keys_to_remove:
                del cache[k]
    
    def _invalidate_corporate_action_cache(self, symbol: str) -> None:
        """Invalidate cache entries for a symbol when corporate actions change."""
        # Clear corp_ cache entries
        keys_to_remove = [
            key for key in self._corporate_actions_cache
            if key.startswith(f"corp_{symbol}")
        ]
        for key in keys_to_remove:
            del self._corporate_actions_cache[key]
        
        # Clear hist_ cache entries that might be affected
        keys_to_remove = [
            key for key in self._historical_cache
            if key.startswith(f"hist_{symbol}")
        ]
        for key in keys_to_remove:
            del self._historical_cache[key]
    
    #
    # Technical Analysis and Market Regime Methods
    #
    
    def detect_market_regime(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str
    ) -> str:
        """
        Detect the current market regime (bull, bear, choppy)
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            
        Returns:
            String indication of market regime: "bull", "bear", or "choppy"
        """
        # Convert historical data to dataframe format
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty or len(df) < 50:  # Need enough data for reliable detection
            return "unknown"
            
        # Calculate indicators for regime detection
        # 1. Trend direction using moving averages
        df['ma_fast'] = df['close'].rolling(window=self.regime_ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=self.regime_ma_slow).mean()
        
        # 2. Volatility
        volatility = self.calculate_volatility(historical_data, symbol, self.regime_volatility_window)
        
        # 3. Directional strength (ADX-like measure)
        df['price_change'] = df['close'].diff()
        df['up_move'] = np.where(df['price_change'] > 0, df['price_change'], 0)
        df['down_move'] = np.where(df['price_change'] < 0, -df['price_change'], 0)
        
        df['up_avg'] = df['up_move'].rolling(window=14).mean()
        df['down_avg'] = df['down_move'].rolling(window=14).mean()
        
        # Positive and negative directional indicators
        df['pdi'] = 100 * df['up_avg'] / (df['up_avg'] + df['down_avg'])
        df['ndi'] = 100 * df['down_avg'] / (df['up_avg'] + df['down_avg'])
        
        # Directional movement index
        df['dx'] = 100 * abs(df['pdi'] - df['ndi']) / (df['pdi'] + df['ndi'])
        
        # Smooth for ADX
        df['adx'] = df['dx'].rolling(window=14).mean()
        
        # Get latest values
        try:
            latest = df.iloc[-1]
            
            # Check trend direction
            trend_up = latest['ma_fast'] > latest['ma_slow']
            
            # High directional strength = trending market
            strong_trend = latest['adx'] > 25 if not pd.isna(latest['adx']) else False
            
            # High volatility can indicate choppy markets or major transitions
            high_volatility = volatility > 0.025 if volatility is not None else False
            
            # Determine regime
            if strong_trend and trend_up and not high_volatility:
                return "bull"
            elif strong_trend and not trend_up and not high_volatility:
                return "bear"
            elif high_volatility or not strong_trend:
                return "choppy"
            else:
                return "unknown"
        except (IndexError, KeyError) as e:
            logger.error(f"Error in market regime detection: {str(e)}")
            return "unknown"
    
    def calculate_volatility(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str, 
        window: int = 20
    ) -> Optional[float]:
        """
        Calculate historical volatility
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            window: Rolling window for volatility calculation
            
        Returns:
            Annualized volatility as a decimal (e.g., 0.15 = 15% volatility)
        """
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty or len(df) < window:
            return None
            
        # Calculate daily returns
        df['returns'] = df['close'].pct_change()
        
        # Calculate rolling standard deviation
        df['volatility'] = df['returns'].rolling(window=window).std()
        
        # Annualize (approximately 252 trading days in a year)
        df['annualized_volatility'] = df['volatility'] * np.sqrt(252)
        
        # Return most recent value
        latest_volatility = df['annualized_volatility'].iloc[-1]
        return float(latest_volatility) if not pd.isna(latest_volatility) else None
    
    def calculate_momentum(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str, 
        window: int = 14
    ) -> Optional[float]:
        """
        Calculate price momentum
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            window: Lookback period for momentum calculation
            
        Returns:
            Momentum value (percentage change over the period)
        """
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty or len(df) < window:
            return None
            
        # Simple momentum calculation (percentage change over period)
        current_price = df['close'].iloc[-1]
        past_price = df['close'].iloc[-window]
        
        momentum = (current_price / past_price) - 1.0
        return float(momentum)
    
    def calculate_rsi(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str, 
        window: int = 14
    ) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            window: RSI calculation period
            
        Returns:
            RSI value (0-100)
        """
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty or len(df) < window + 1:
            return None
            
        # Calculate price changes
        df['change'] = df['close'].diff()
        
        # Separate gains and losses
        df['gain'] = np.where(df['change'] > 0, df['change'], 0)
        df['loss'] = np.where(df['change'] < 0, -df['change'], 0)
        
        # Calculate average gain and loss
        df['avg_gain'] = df['gain'].rolling(window=window).mean()
        df['avg_loss'] = df['loss'].rolling(window=window).mean()
        
        # Calculate RS and RSI
        df['rs'] = df['avg_gain'] / df['avg_loss']
        df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # Return most recent value
        latest_rsi = df['rsi'].iloc[-1]
        return float(latest_rsi) if not pd.isna(latest_rsi) else None
    
    def calculate_macd(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Dict[str, float]]:
        """
        Calculate Moving Average Convergence Divergence (MACD)
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            Dictionary with MACD values
        """
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty or len(df) < slow_period + signal_period:
            return None
            
        # Calculate EMAs
        df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line and signal line
        df['macd_line'] = df['ema_fast'] - df['ema_slow']
        df['signal_line'] = df['macd_line'].ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram (difference between MACD and signal)
        df['histogram'] = df['macd_line'] - df['signal_line']
        
        # Get latest values
        latest = df.iloc[-1]
        
        # Return MACD values
        return {
            'macd': float(latest['macd_line']),
            'signal': float(latest['signal_line']),
            'histogram': float(latest['histogram']),
            'direction': 1 if latest['macd_line'] > latest['signal_line'] else -1
        }
    
    def calculate_bollinger_bands(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str,
        window: int = 20,
        num_std: float = 2.0
    ) -> Optional[Dict[str, float]]:
        """
        Calculate Bollinger Bands
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            window: Moving average period
            num_std: Number of standard deviations
            
        Returns:
            Dictionary with Bollinger Band values
        """
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty or len(df) < window:
            return None
            
        # Calculate the SMA and standard deviation
        df['sma'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        
        # Calculate upper and lower bands
        df['upper_band'] = df['sma'] + (df['std'] * num_std)
        df['lower_band'] = df['sma'] - (df['std'] * num_std)
        
        # Calculate %B (position within the bands)
        df['percent_b'] = (df['close'] - df['lower_band']) / (df['upper_band'] - df['lower_band'])
        
        # Get latest values
        latest = df.iloc[-1]
        
        # Return Bollinger Band values
        return {
            'middle': float(latest['sma']),
            'upper': float(latest['upper_band']),
            'lower': float(latest['lower_band']),
            'percent_b': float(latest['percent_b']),
            'price': float(latest['close']),
            'width': float(latest['upper_band'] - latest['lower_band']) / latest['sma']
        }
    
    def extract_features(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str
    ) -> Dict[str, List[float]]:
        """
        Extract technical analysis features for ML models
        
        Args:
            historical_data: Historical price data
            symbol: Symbol to analyze
            
        Returns:
            Dictionary of features
        """
        df = self._convert_to_dataframe(historical_data, symbol)
        if df.empty:
            return {}
            
        # Create feature dictionary
        features = {}
        
        # Basic price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            if len(df) >= period:
                df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
                # Moving average crossover features
                df[f'ma_ratio_{period}'] = df['close'] / df[f'ma_{period}']
        
        # Volatility features
        for period in [5, 10, 20]:
            if len(df) >= period:
                df[f'volatility_{period}'] = df['returns'].rolling(window=period).std() * np.sqrt(252)
        
        # Volume features
        if 'volume' in df:
            df['volume_ma_10'] = df['volume'].rolling(window=10).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma_10']
        
        # Calculate RSI
        if len(df) >= 14:
            # RSI calculation code reused
            df['change'] = df['close'].diff()
            df['gain'] = np.where(df['change'] > 0, df['change'], 0)
            df['loss'] = np.where(df['change'] < 0, -df['change'], 0)
            df['avg_gain'] = df['gain'].rolling(window=14).mean()
            df['avg_loss'] = df['loss'].rolling(window=14).mean()
            df['rs'] = df['avg_gain'] / df['avg_loss']
            df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # MACD
        if len(df) >= 26 + 9:
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd_line'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd_line'] - df['macd_signal']
        
        # Bollinger Bands
        if len(df) >= 20:
            df['bb_ma'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_ma'] + (2 * df['bb_std'])
            df['bb_lower'] = df['bb_ma'] - (2 * df['bb_std'])
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_ma']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Consolidate features
        feature_keys = [col for col in df.columns if col not in ['date', 'open', 'high', 'low', 'close', 'volume']]
        
        for key in feature_keys:
            if not df[key].isna().all():  # Skip columns that are all NaN
                # Get last 30 values (or fewer if less data) for each feature
                values = df[key].dropna().iloc[-min(30, len(df)):]
                if len(values) > 0:
                    features[key] = values.tolist()
        
        # Add some metadata
        features['symbol'] = symbol
        features['timestamp'] = datetime.now().isoformat()
        features['last_price'] = float(df['close'].iloc[-1])
        features['features_version'] = "1.0"
        
        return features
    
    def _convert_to_dataframe(
        self, 
        historical_data: Dict[str, List[Dict]], 
        symbol: str
    ) -> pd.DataFrame:
        """Convert historical data dictionary to pandas DataFrame"""
        if symbol not in historical_data or not historical_data[symbol]:
            return pd.DataFrame()
            
        # Extract data for symbol
        data = historical_data[symbol]
        
        # Convert to DataFrame
        df_data = []
        for day in data:
            df_data.append({
                'date': day.get('date', None),
                'open': day.get('open', None),
                'high': day.get('high', None),
                'low': day.get('low', None),
                'close': day.get('close', None),
                'volume': day.get('volume', None),
            })
        
        df = pd.DataFrame(df_data)
        
        # Set date as index if available
        if 'date' in df.columns and not df['date'].isna().all():
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
        
        # Forward fill NaN values
        df = df.ffill()
        
        return df
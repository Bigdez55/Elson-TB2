"""Market Data Processor Service

Handles processing and analysis of market data for AI/ML models with advanced features:
- Data quality validation
- Corporate actions handling
- Multi-source data retrieval with fallback
- Technical analysis indicators
- Market regime detection
- Caching with TTL
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.market_data import MarketData
from app.services.market_data import MarketDataService

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
        details: Optional[Dict[str, Any]] = None,
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
    """Advanced market data processing for AI/ML applications."""

    def __init__(
        self,
        db: Optional[Session] = None,
        market_data_service: Optional[MarketDataService] = None,
        max_cache_size: int = 1000,
        cache_ttl: int = 300,  # 5 minutes in seconds
    ):
        """Initialize with market data service and caching."""
        self.db = db
        self.market_data_service = market_data_service or MarketDataService()
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl

        # Cache for market data
        self._price_cache = {}
        self._historical_cache = {}
        self._corporate_actions_cache = {}

        # Data quality thresholds
        self.max_price_change_pct = float(
            getattr(settings, "MAX_PRICE_CHANGE_PCT", 10.0)
        )
        self.min_valid_price = float(getattr(settings, "MIN_VALID_PRICE", 0.01))
        self.max_valid_price = float(getattr(settings, "MAX_VALID_PRICE", 1000000))

        # Fallback data sources priority
        self.data_sources = [
            "primary",  # Main data source
            "secondary",  # Secondary source
            "tertiary",  # Tertiary source
            "historical",  # Historical/cached data
        ]

        # Known corporate actions database
        # In production, this would be stored in a database
        self.corporate_actions = []

        # Market regime detection parameters
        self.regime_volatility_window = 30  # Days for volatility calculation
        self.regime_ma_fast = 20  # Fast moving average period
        self.regime_ma_slow = 50  # Slow moving average period

    # ============================================================================
    # Data Retrieval with Quality Validation
    # ============================================================================

    async def get_price_with_validation(self, symbol: str) -> Dict[str, Any]:
        """Get current price with data quality validation."""
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
                    quote = await self.market_data_service.get_quote(symbol)
                else:
                    # In a real system, would call other sources
                    continue

                # Validate the data
                validated_data = self._validate_price_data(symbol, quote)

                # Store in cache
                self._add_to_cache(cache_key, validated_data)

                return validated_data

            except Exception as e:
                logger.warning(f"Failed to get price for {symbol} from {source}: {e}")

        # If all sources fail, try historical fallback
        try:
            historical = await self.market_data_service.get_historical_data(
                symbol,
                start_date=datetime.utcnow() - timedelta(days=5),
                end_date=datetime.utcnow(),
            )

            if historical:
                last_price = historical[-1]
                result = {
                    "symbol": symbol,
                    "price": last_price.get("close"),
                    "volume": last_price.get("volume"),
                    "timestamp": last_price.get("timestamp"),
                    "source": "historical_fallback",
                    "is_fallback": True,
                }
                return result
        except Exception as e:
            logger.error(f"Historical fallback failed for {symbol}: {e}")

        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve price data for {symbol} from any source",
        )

    async def get_processed_historical_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        features: Optional[List[str]] = None,
        normalize: bool = True,
        adjust_for_corporate_actions: bool = True,
    ) -> pd.DataFrame:
        """Get processed historical data with technical indicators and features."""
        try:
            # Get raw historical data
            all_data = []
            for symbol in symbols:
                data = await self.market_data_service.get_historical_data(
                    symbol, start_date, end_date
                )
                if data:
                    df = pd.DataFrame(data)
                    df["symbol"] = symbol
                    all_data.append(df)

            if not all_data:
                logger.warning(f"No historical data found for symbols: {symbols}")
                return pd.DataFrame()

            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])
            combined_df = combined_df.sort_values(["symbol", "timestamp"])

            # Calculate technical indicators
            processed_df = self._calculate_technical_indicators(combined_df)

            # Adjust for corporate actions if needed
            if adjust_for_corporate_actions:
                for symbol in symbols:
                    symbol_df = processed_df[processed_df["symbol"] == symbol].copy()
                    adjusted_df = self._adjust_for_corporate_actions_df(
                        symbol, symbol_df
                    )
                    processed_df.loc[processed_df["symbol"] == symbol] = adjusted_df

            # Add features if specified
            if features:
                available_features = processed_df.columns.tolist()
                selected_features = ["symbol", "timestamp"] + [
                    f for f in features if f in available_features
                ]
                processed_df = processed_df[selected_features]

            # Normalize if requested
            if normalize:
                processed_df = self._normalize_data(processed_df)

            return processed_df

        except Exception as e:
            logger.error(f"Error processing historical data: {str(e)}")
            return pd.DataFrame()

    # ============================================================================
    # Technical Indicators
    # ============================================================================

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the dataset."""
        result_dfs = []

        for symbol in df["symbol"].unique():
            symbol_df = df[df["symbol"] == symbol].copy()
            symbol_df = symbol_df.sort_values("timestamp")

            # Price-based indicators
            symbol_df["sma_20"] = symbol_df["close"].rolling(window=20).mean()
            symbol_df["sma_50"] = symbol_df["close"].rolling(window=50).mean()
            symbol_df["ema_12"] = symbol_df["close"].ewm(span=12).mean()
            symbol_df["ema_26"] = symbol_df["close"].ewm(span=26).mean()

            # MACD
            symbol_df["macd"] = symbol_df["ema_12"] - symbol_df["ema_26"]
            symbol_df["macd_signal"] = symbol_df["macd"].ewm(span=9).mean()
            symbol_df["macd_histogram"] = symbol_df["macd"] - symbol_df["macd_signal"]

            # RSI
            symbol_df["rsi"] = self._calculate_rsi(symbol_df["close"])

            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            symbol_df["bb_middle"] = symbol_df["close"].rolling(window=bb_period).mean()
            bb_std_dev = symbol_df["close"].rolling(window=bb_period).std()
            symbol_df["bb_upper"] = symbol_df["bb_middle"] + (bb_std_dev * bb_std)
            symbol_df["bb_lower"] = symbol_df["bb_middle"] - (bb_std_dev * bb_std)
            symbol_df["bb_width"] = symbol_df["bb_upper"] - symbol_df["bb_lower"]
            symbol_df["bb_position"] = (
                symbol_df["close"] - symbol_df["bb_lower"]
            ) / symbol_df["bb_width"]

            # Volume indicators
            symbol_df["volume_sma"] = symbol_df["volume"].rolling(window=20).mean()
            symbol_df["volume_ratio"] = symbol_df["volume"] / symbol_df["volume_sma"]

            # Price change indicators
            symbol_df["price_change"] = symbol_df["close"].pct_change()
            symbol_df["price_change_5d"] = symbol_df["close"].pct_change(periods=5)
            symbol_df["price_volatility"] = (
                symbol_df["price_change"].rolling(window=20).std()
            )

            # Support and resistance levels
            symbol_df["high_20d"] = symbol_df["high"].rolling(window=20).max()
            symbol_df["low_20d"] = symbol_df["low"].rolling(window=20).min()

            result_dfs.append(symbol_df)

        return pd.concat(result_dfs, ignore_index=True)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical columns."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        exclude_columns = ["symbol", "timestamp"]

        for col in numeric_columns:
            if col not in exclude_columns:
                # Use min-max normalization
                col_min = df[col].min()
                col_max = df[col].max()
                if col_max != col_min:
                    df[col] = (df[col] - col_min) / (col_max - col_min)

        return df

    # ============================================================================
    # Data Quality Validation
    # ============================================================================

    def _validate_price_data(
        self, symbol: str, price_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate price data quality."""
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
                logger.warning(
                    f"Unusual price change for {symbol}: {change_pct}% (exceeds {self.max_price_change_pct}%)"
                )

        return price_data

    # ============================================================================
    # Corporate Actions
    # ============================================================================

    async def get_corporate_actions(
        self, symbol: str, start_date: datetime, end_date: Optional[datetime] = None
    ) -> List[CorporateAction]:
        """Get corporate actions for a symbol in a date range."""
        end_date = end_date or datetime.utcnow()

        # Check cache
        cache_key = f"corp_{symbol}_{start_date.date()}_{end_date.date()}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Filter corporate actions
        actions = [
            action
            for action in self.corporate_actions
            if action.symbol == symbol and start_date <= action.ex_date <= end_date
        ]

        # Cache the result
        self._add_to_cache(cache_key, actions)

        return actions

    async def add_corporate_action(self, corporate_action: CorporateAction) -> bool:
        """Add a corporate action to the database."""
        self.corporate_actions.append(corporate_action)
        self._invalidate_corporate_action_cache(corporate_action.symbol)
        logger.info(f"Added corporate action: {corporate_action}")
        return True

    def _adjust_for_corporate_actions_df(
        self, symbol: str, df: pd.DataFrame
    ) -> pd.DataFrame:
        """Adjust historical data for corporate actions."""
        df = df.copy()

        # Get corporate actions for this period
        start_date = (
            df.index.min()
            if isinstance(df.index, pd.DatetimeIndex)
            else df["timestamp"].min()
        )
        end_date = (
            df.index.max()
            if isinstance(df.index, pd.DatetimeIndex)
            else df["timestamp"].max()
        )

        actions = []
        for action in self.corporate_actions:
            if action.symbol == symbol and start_date <= action.ex_date <= end_date:
                actions.append(action)

        # Apply adjustments
        for action in actions:
            if action.action_type == "split" and action.ratio:
                # Apply split adjustment
                mask = (
                    df.index < action.ex_date
                    if isinstance(df.index, pd.DatetimeIndex)
                    else df["timestamp"] < action.ex_date
                )
                df.loc[mask, ["open", "high", "low", "close"]] *= action.ratio
                df.loc[mask, "volume"] /= action.ratio

        return df

    # ============================================================================
    # Market Analysis Methods
    # ============================================================================

    async def calculate_correlation_matrix(
        self, symbols: List[str], lookback_days: int = 252
    ) -> pd.DataFrame:
        """Calculate correlation matrix for a list of symbols."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        # Get price data for all symbols
        price_data = {}
        for symbol in symbols:
            data = await self.market_data_service.get_historical_data(
                symbol, start_date, end_date
            )
            if data:
                df = pd.DataFrame(data)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp")["close"]
                price_data[symbol] = df

        if not price_data:
            return pd.DataFrame()

        # Create price DataFrame
        price_df = pd.DataFrame(price_data)

        # Calculate returns
        returns_df = price_df.pct_change().dropna()

        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()

        return correlation_matrix

    async def calculate_volatility_metrics(
        self, symbol: str, lookback_days: int = 30
    ) -> Dict[str, float]:
        """Calculate various volatility metrics for a symbol."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        data = await self.market_data_service.get_historical_data(
            symbol, start_date, end_date
        )

        if not data:
            return {}

        df = pd.DataFrame(data)
        df["returns"] = df["close"].pct_change()

        # Calculate various volatility measures
        daily_vol = df["returns"].std()
        annualized_vol = daily_vol * np.sqrt(252)

        # Calculate high-low volatility
        df["hl_vol"] = np.log(df["high"] / df["low"])
        hl_volatility = df["hl_vol"].mean() * np.sqrt(252)

        # Calculate maximum drawdown
        df["cumulative"] = (1 + df["returns"]).cumprod()
        df["rolling_max"] = df["cumulative"].expanding().max()
        df["drawdown"] = df["cumulative"] / df["rolling_max"] - 1
        max_drawdown = df["drawdown"].min()

        return {
            "daily_volatility": daily_vol,
            "annualized_volatility": annualized_vol,
            "high_low_volatility": hl_volatility,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": df["returns"].mean() / daily_vol if daily_vol > 0 else 0,
        }

    async def detect_market_regime(
        self, symbols: List[str], lookback_days: int = 60
    ) -> Dict[str, Any]:
        """Detect current market regime based on multiple indicators."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        regime_scores = []

        for symbol in symbols:
            data = await self.market_data_service.get_historical_data(
                symbol, start_date, end_date
            )

            if not data:
                continue

            df = pd.DataFrame(data)
            df["returns"] = df["close"].pct_change()

            # Calculate regime indicators
            volatility = df["returns"].std()
            trend = df["close"].iloc[-1] / df["close"].iloc[0] - 1

            # Volatility regime (high volatility = stress)
            vol_percentile = df["returns"].rolling(20).std().rank(pct=True).iloc[-1]

            regime_scores.append(
                {
                    "symbol": symbol,
                    "volatility_percentile": vol_percentile,
                    "trend": trend,
                    "volatility": volatility,
                }
            )

        if not regime_scores:
            return {"regime": "unknown", "confidence": 0.0}

        # Aggregate scores
        avg_vol_percentile = np.mean(
            [s["volatility_percentile"] for s in regime_scores]
        )
        avg_trend = np.mean([s["trend"] for s in regime_scores])

        # Determine regime
        if avg_vol_percentile > 0.8:
            regime = "high_volatility"
        elif avg_vol_percentile < 0.2 and avg_trend > 0.02:
            regime = "bull_market"
        elif avg_vol_percentile < 0.2 and avg_trend < -0.02:
            regime = "bear_market"
        else:
            regime = "normal"

        confidence = min(abs(avg_vol_percentile - 0.5) * 2, 1.0)

        return {
            "regime": regime,
            "confidence": confidence,
            "volatility_percentile": avg_vol_percentile,
            "trend": avg_trend,
            "details": regime_scores,
        }

    # ============================================================================
    # Cache Management
    # ============================================================================

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if available and not expired."""
        # Check price cache
        if key.startswith("price_") and key in self._price_cache:
            entry = self._price_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._price_cache[key]

        # Check historical cache
        elif key.startswith("hist_") and key in self._historical_cache:
            entry = self._historical_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._historical_cache[key]

        # Check corporate actions cache
        elif key.startswith("corp_") and key in self._corporate_actions_cache:
            entry = self._corporate_actions_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["data"]
            else:
                del self._corporate_actions_cache[key]

        return None

    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add data to cache with timestamp."""
        entry = {"data": data, "timestamp": time.time()}

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
            keys_to_remove = sorted_keys[: len(cache) - self.max_cache_size]
            for k in keys_to_remove:
                del cache[k]

    def _invalidate_corporate_action_cache(self, symbol: str) -> None:
        """Invalidate cache entries for a symbol when corporate actions change."""
        keys_to_remove = [
            key
            for key in self._corporate_actions_cache
            if key.startswith(f"corp_{symbol}")
        ]
        for key in keys_to_remove:
            del self._corporate_actions_cache[key]

        # Clear hist_ cache entries that might be affected
        keys_to_remove = [
            key for key in self._historical_cache if key.startswith(f"hist_{symbol}")
        ]
        for key in keys_to_remove:
            del self._historical_cache[key]

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Clear the market data cache."""
        if symbol:
            # Clear only for specific symbol
            keys_to_remove = []

            for cache in [
                self._price_cache,
                self._historical_cache,
                self._corporate_actions_cache,
            ]:
                keys_to_remove.extend([key for key in cache if symbol in key])

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

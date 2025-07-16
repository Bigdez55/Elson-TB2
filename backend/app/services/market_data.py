import asyncio
import time
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from functools import wraps
import json

import aiohttp
import structlog
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.models.market_data import MarketData

logger = structlog.get_logger()
std_logger = logging.getLogger(__name__)


class MarketDataSource(str, Enum):
    """Available market data sources."""

    YAHOO_FINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    POLYGON = "polygon"
    FMP = "fmp"


class MarketDataError(Exception):
    """Exception raised for market data errors."""

    def __init__(self, message: str, source: str = None, status_code: int = None):
        self.message = message
        self.source = source
        self.status_code = status_code
        super().__init__(self.message)


class CacheResult:
    """Wrapper for cached results."""

    def __init__(self, data: Any, timestamp: float, source: str):
        self.data = data
        self.timestamp = timestamp
        self.source = source

    def is_fresh(self, ttl_seconds: float) -> bool:
        """Check if the cached data is still fresh."""
        return (time.time() - self.timestamp) < ttl_seconds

    def age_seconds(self) -> float:
        """Get the age of the cached data in seconds."""
        return time.time() - self.timestamp


def handle_errors(func):
    """Decorator to handle errors in market data methods."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MarketDataError as e:
            std_logger.error(f"Market data error from {e.source}: {str(e)}")
            raise HTTPException(
                status_code=e.status_code or 500, detail=f"Market data error: {str(e)}"
            )
        except Exception as e:
            std_logger.error(
                f"Unexpected error in market data service: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"Unexpected market data error: {str(e)}"
            )
    
    return wrapper


class MarketDataProvider:
    """Base class for market data providers"""

    def __init__(self):
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Default 1 second between requests

    async def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol"""
        raise NotImplementedError

    async def get_historical_data(
        self, symbol: str, timeframe: str = "1day", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical market data"""
        raise NotImplementedError


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage market data provider"""

    def __init__(self):
        super().__init__()
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.0  # Alpha Vantage free tier: 5 calls per minute

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Alpha Vantage"""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured")
            return None

        await self._rate_limit()

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Check for API limit
                        if "Note" in data:
                            logger.warning(
                                f"Alpha Vantage rate limit hit: {data['Note']}"
                            )
                            return None

                        quote_data = data.get("Global Quote", {})
                        if quote_data:
                            return {
                                "symbol": quote_data.get("01. symbol"),
                                "open": float(quote_data.get("02. open", 0)),
                                "high": float(quote_data.get("03. high", 0)),
                                "low": float(quote_data.get("04. low", 0)),
                                "price": float(quote_data.get("05. price", 0)),
                                "volume": int(quote_data.get("06. volume", 0)),
                                "latest_trading_day": quote_data.get(
                                    "07. latest trading day"
                                ),
                                "previous_close": float(
                                    quote_data.get("08. previous close", 0)
                                ),
                                "change": float(quote_data.get("09. change", 0)),
                                "change_percent": quote_data.get(
                                    "10. change percent", "0%"
                                ).rstrip("%"),
                                "source": "alpha_vantage",
                            }
                    else:
                        logger.error(f"Alpha Vantage API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching quote from Alpha Vantage: {str(e)}")

        return None

    async def get_historical_data(
        self, symbol: str, timeframe: str = "1day", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical data from Alpha Vantage"""
        if not self.api_key:
            return []

        await self._rate_limit()

        # Map timeframe to Alpha Vantage function
        function_map = {
            "1min": "TIME_SERIES_INTRADAY",
            "5min": "TIME_SERIES_INTRADAY",
            "15min": "TIME_SERIES_INTRADAY",
            "30min": "TIME_SERIES_INTRADAY",
            "60min": "TIME_SERIES_INTRADAY",
            "1day": "TIME_SERIES_DAILY",
        }

        function = function_map.get(timeframe, "TIME_SERIES_DAILY")
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "compact",
        }

        if "INTRADAY" in function:
            params["interval"] = timeframe

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Find the time series data
                        time_series_key = None
                        for key in data.keys():
                            if "Time Series" in key:
                                time_series_key = key
                                break

                        if time_series_key and time_series_key in data:
                            time_series = data[time_series_key]
                            historical_data = []

                            for timestamp, values in list(time_series.items())[:limit]:
                                historical_data.append(
                                    {
                                        "timestamp": timestamp,
                                        "open": float(values.get("1. open", 0)),
                                        "high": float(values.get("2. high", 0)),
                                        "low": float(values.get("3. low", 0)),
                                        "close": float(values.get("4. close", 0)),
                                        "volume": int(values.get("5. volume", 0)),
                                        "source": "alpha_vantage",
                                    }
                                )

                            return historical_data

        except Exception as e:
            logger.error(f"Error fetching historical data from Alpha Vantage: {str(e)}")

        return []


class PolygonProvider(MarketDataProvider):
    """Polygon.io market data provider (fallback)"""

    def __init__(self):
        super().__init__()
        self.api_key = settings.POLYGON_API_KEY
        self.base_url = "https://api.polygon.io"
        self.rate_limit_delay = 12.0  # Free tier limit

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Polygon"""
        if not self.api_key:
            logger.warning("Polygon API key not configured")
            return None

        await self._rate_limit()

        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
        params = {"apikey": self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])

                        if results:
                            result = results[0]
                            return {
                                "symbol": symbol,
                                "open": result.get("o", 0),
                                "high": result.get("h", 0),
                                "low": result.get("l", 0),
                                "price": result.get("c", 0),
                                "volume": result.get("v", 0),
                                "timestamp": result.get("t"),
                                "source": "polygon",
                            }
                    else:
                        logger.error(f"Polygon API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching quote from Polygon: {str(e)}")

        return None


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance provider using yfinance library"""

    def __init__(self):
        super().__init__()
        self.rate_limit_delay = 0.5  # Yahoo Finance is more lenient

    @handle_errors
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Yahoo Finance"""
        try:
            await self._rate_limit()

            # Run yfinance in executor to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)

            if info and "regularMarketPrice" in info:
                return {
                    "symbol": symbol,
                    "open": info.get("regularMarketOpen", 0),
                    "high": info.get("dayHigh", 0),
                    "low": info.get("dayLow", 0),
                    "price": info.get("regularMarketPrice", 0),
                    "volume": info.get("regularMarketVolume", 0),
                    "previous_close": info.get("previousClose", 0),
                    "change": info.get("regularMarketChange", 0),
                    "change_percent": info.get("regularMarketChangePercent", 0),
                    "source": "yahoo_finance",
                }

        except Exception as e:
            logger.error(f"Error fetching quote from Yahoo Finance: {str(e)}")
            raise MarketDataError(f"Yahoo Finance error: {str(e)}", "yahoo_finance")

        return None

    async def get_historical_data(
        self, symbol: str, timeframe: str = "1day", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical data from Yahoo Finance"""
        try:
            await self._rate_limit()

            # Map timeframe to period
            period_map = {
                "1min": "1d",
                "5min": "5d",
                "15min": "5d",
                "30min": "5d",
                "60min": "5d",
                "1day": "1y",
            }

            period = period_map.get(timeframe, "1y")
            interval = "1d" if timeframe == "1day" else timeframe

            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            hist = await loop.run_in_executor(
                None, lambda: ticker.history(period=period, interval=interval)
            )

            if not hist.empty:
                historical_data = []
                for timestamp, row in hist.iterrows():
                    historical_data.append(
                        {
                            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "open": float(row["Open"]),
                            "high": float(row["High"]),
                            "low": float(row["Low"]),
                            "close": float(row["Close"]),
                            "volume": int(row["Volume"]),
                            "source": "yahoo_finance",
                        }
                    )

                return historical_data[:limit]

        except Exception as e:
            logger.error(f"Error fetching historical data from Yahoo Finance: {str(e)}")

        return []


class FinnhubProvider(MarketDataProvider):
    """Finnhub market data provider"""

    def __init__(self):
        super().__init__()
        self.api_key = getattr(settings, "FINNHUB_API_KEY", None)
        self.base_url = "https://finnhub.io/api/v1"
        self.rate_limit_delay = 1.0  # Free tier: 60 calls per minute

    @handle_errors
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Finnhub"""
        if not self.api_key:
            logger.warning("Finnhub API key not configured")
            return None

        await self._rate_limit()

        url = f"{self.base_url}/quote"
        params = {"symbol": symbol, "token": self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data and data.get("c"):  # 'c' is current price
                            return {
                                "symbol": symbol,
                                "open": data.get("o", 0),  # open
                                "high": data.get("h", 0),  # high
                                "low": data.get("l", 0),  # low
                                "price": data.get("c", 0),  # current
                                "previous_close": data.get("pc", 0),  # previous close
                                "change": data.get("d", 0),  # change
                                "change_percent": data.get("dp", 0),  # change percent
                                "timestamp": int(data.get("t", time.time())),
                                "source": "finnhub",
                            }
                    else:
                        logger.error(f"Finnhub API error: {response.status}")
                        raise MarketDataError(
                            f"API error: {response.status}", "finnhub", response.status
                        )

        except Exception as e:
            logger.error(f"Error fetching quote from Finnhub: {str(e)}")
            raise MarketDataError(f"Finnhub error: {str(e)}", "finnhub")

        return None

    async def get_historical_data(
        self, symbol: str, timeframe: str = "1day", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical data from Finnhub"""
        if not self.api_key:
            return []

        await self._rate_limit()

        # Finnhub uses UNIX timestamps
        end_time = int(time.time())
        start_time = end_time - (limit * 24 * 60 * 60)  # limit days back

        url = f"{self.base_url}/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": "D",  # Daily resolution
            "from": start_time,
            "to": end_time,
            "token": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data and data.get("s") == "ok":  # status ok
                            historical_data = []
                            timestamps = data.get("t", [])
                            opens = data.get("o", [])
                            highs = data.get("h", [])
                            lows = data.get("l", [])
                            closes = data.get("c", [])
                            volumes = data.get("v", [])

                            for i in range(len(timestamps)):
                                historical_data.append(
                                    {
                                        "timestamp": datetime.fromtimestamp(
                                            timestamps[i]
                                        ).strftime("%Y-%m-%d %H:%M:%S"),
                                        "open": float(opens[i]),
                                        "high": float(highs[i]),
                                        "low": float(lows[i]),
                                        "close": float(closes[i]),
                                        "volume": int(volumes[i]),
                                        "source": "finnhub",
                                    }
                                )

                            return historical_data

        except Exception as e:
            logger.error(f"Error fetching historical data from Finnhub: {str(e)}")

        return []


class MarketDataService:
    """Enhanced market data service with multi-provider failover and robust error handling"""

    def __init__(self, cache_ttl: int = None):
        # Initialize all available providers with priority order
        self.providers = [
            YahooFinanceProvider(),  # Most reliable, free
            AlphaVantageProvider(),  # Good for real-time data
            FinnhubProvider(),  # Alternative source
            PolygonProvider(),  # Fallback option
        ]

        # Enhanced caching with cache result objects
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = cache_ttl or getattr(
            settings, "MARKET_DATA_CACHE_TTL", 60
        )  # Default 1 minute cache

        # Health tracking for providers with dynamic thresholds
        self.source_health = {
            provider.__class__.__name__: True for provider in self.providers
        }
        self.consecutive_errors = {
            provider.__class__.__name__: 0 for provider in self.providers
        }
        self.max_consecutive_errors = getattr(
            settings, "MARKET_DATA_ERROR_THRESHOLD", 3
        )
        self.provider_last_success = {
            provider.__class__.__name__: time.time() for provider in self.providers
        }

        # Enhanced metrics and monitoring
        self.request_count = 0
        self.cache_hits = 0
        self.provider_success_count = {
            provider.__class__.__name__: 0 for provider in self.providers
        }
        self.provider_error_count = {
            provider.__class__.__name__: 0 for provider in self.providers
        }
        self.total_errors = 0

        # Data validation settings
        self.validate_quotes = True
        self.stale_data_threshold = 300  # 5 minutes for stale data warnings

    def _get_cached_data(
        self, cache_key: str, allow_stale: bool = False
    ) -> Optional[CacheResult]:
        """Get data from cache with enhanced stale data handling"""
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if isinstance(cached_result, CacheResult):
                if cached_result.is_fresh(self.cache_ttl):
                    self.cache_hits += 1
                    return cached_result
                elif (
                    allow_stale
                    and cached_result.age_seconds() < self.stale_data_threshold
                ):
                    # Return stale data with warning flag
                    cached_result.data["is_stale"] = True
                    cached_result.data[
                        "stale_age_seconds"
                    ] = cached_result.age_seconds()
                    self.cache_hits += 1
                    return cached_result
                else:
                    # Clean up expired cache entry
                    del self.cache[cache_key]
            elif isinstance(cached_result, tuple):  # Legacy cache format
                cached_data, timestamp = cached_result
                age = time.time() - timestamp
                if age < self.cache_ttl:
                    self.cache_hits += 1
                    return CacheResult(cached_data, timestamp, "legacy")
                elif allow_stale and age < self.stale_data_threshold:
                    cached_data["is_stale"] = True
                    cached_data["stale_age_seconds"] = age
                    self.cache_hits += 1
                    return CacheResult(cached_data, timestamp, "legacy")
                else:
                    del self.cache[cache_key]
        return None

    def _cache_data(self, cache_key: str, data: Dict[str, Any], source: str) -> None:
        """Cache data with metadata and size management"""
        # Clean up stale entries if cache is getting large
        if len(self.cache) > 1000:  # Reasonable limit for personal use
            current_time = time.time()
            stale_keys = [
                key
                for key, cached_result in self.cache.items()
                if isinstance(cached_result, CacheResult)
                and (current_time - cached_result.timestamp) > self.cache_ttl * 2
            ]
            for key in stale_keys[:100]:  # Remove up to 100 stale entries
                del self.cache[key]

        cache_result = CacheResult(data, time.time(), source)
        self.cache[cache_key] = cache_result

    def _update_provider_health(self, provider_name: str, success: bool) -> None:
        """Update provider health tracking with enhanced logic"""
        current_time = time.time()

        if success:
            self.consecutive_errors[provider_name] = 0
            self.provider_last_success[provider_name] = current_time
            self.provider_success_count[provider_name] += 1

            # Restore health if provider was marked unhealthy
            if not self.source_health[provider_name]:
                self.source_health[provider_name] = True
                std_logger.info(f"Provider {provider_name} restored to healthy status")
        else:
            self.consecutive_errors[provider_name] += 1
            self.provider_error_count[provider_name] += 1
            self.total_errors += 1

            # Mark as unhealthy after consecutive errors
            if self.consecutive_errors[provider_name] >= self.max_consecutive_errors:
                if self.source_health[provider_name]:  # Only log when status changes
                    self.source_health[provider_name] = False
                    std_logger.warning(
                        f"Provider {provider_name} marked as unhealthy after "
                        f"{self.max_consecutive_errors} consecutive errors. "
                        f"Last success: {current_time - self.provider_last_success[provider_name]:.1f}s ago"
                    )

    def _validate_quote_data(self, quote: Dict[str, Any], symbol: str) -> bool:
        """Validate quote data quality"""
        if not self.validate_quotes:
            return True

        required_fields = ["symbol", "price"]
        for field in required_fields:
            if field not in quote or quote[field] is None:
                std_logger.warning(f"Invalid quote for {symbol}: missing {field}")
                return False

        # Validate price is reasonable (positive number)
        try:
            price = float(quote["price"])
            if price <= 0:
                std_logger.warning(f"Invalid quote for {symbol}: price {price} <= 0")
                return False
        except (ValueError, TypeError):
            std_logger.warning(f"Invalid quote for {symbol}: price is not a number")
            return False

        return True

    @handle_errors
    async def get_quote(
        self, symbol: str, force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get quote with enhanced failover, validation, and stale data handling"""
        symbol = symbol.upper()
        self.request_count += 1
        cache_key = f"quote_{symbol}"

        # Check cache first unless forcing refresh
        if not force_refresh:
            cached_quote = self._get_cached_data(cache_key)
            if cached_quote:
                return cached_quote.data

        # Try providers in order, prioritizing healthy ones
        healthy_providers = [
            p
            for p in self.providers
            if self.source_health.get(p.__class__.__name__, True)
        ]
        unhealthy_providers = [
            p
            for p in self.providers
            if not self.source_health.get(p.__class__.__name__, True)
        ]

        # Try healthy providers first, then unhealthy ones as fallback
        all_providers = healthy_providers + unhealthy_providers
        errors = []

        for provider in all_providers:
            provider_name = provider.__class__.__name__
            try:
                quote = await provider.get_quote(symbol)
                if quote and self._validate_quote_data(quote, symbol):
                    # Cache the result and update health
                    self._cache_data(
                        cache_key, quote, quote.get("source", provider_name.lower())
                    )
                    self._update_provider_health(provider_name, True)

                    std_logger.info(
                        f"Successfully retrieved quote for {symbol} from {provider_name} "
                        f"(price: {quote.get('price', 'N/A')})"
                    )
                    return quote
                else:
                    # Provider returned invalid data
                    error_msg = (
                        f"Provider {provider_name} returned invalid data for {symbol}"
                    )
                    std_logger.warning(error_msg)
                    errors.append(error_msg)

            except MarketDataError as e:
                self._update_provider_health(provider_name, False)
                error_msg = f"Provider {provider_name} failed for {symbol}: {str(e)}"
                std_logger.error(error_msg)
                errors.append(error_msg)
                continue
            except Exception as e:
                self._update_provider_health(provider_name, False)
                error_msg = f"Unexpected error from provider {provider_name} for {symbol}: {str(e)}"
                std_logger.error(error_msg)
                errors.append(error_msg)
                continue

        # All providers failed - try to return stale data
        stale_data = self._get_cached_data(cache_key, allow_stale=True)
        if stale_data:
            std_logger.warning(
                f"All providers failed for {symbol}, returning stale data "
                f"(age: {stale_data.age_seconds():.1f}s)"
            )
            return stale_data.data

        # No data available at all
        error_summary = f"All providers failed for symbol {symbol}: {'; '.join(errors)}"
        std_logger.error(error_summary)
        raise MarketDataError(error_summary)

    async def get_multiple_quotes(
        self, symbols: List[str], force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple symbols with enhanced error handling"""
        if not symbols:
            return {}

        symbols = [s.upper() for s in symbols]
        quotes = {}

        # Create tasks for all symbols
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.get_quote(symbol, force_refresh))
            tasks.append((symbol, task))

        # Wait for all tasks to complete
        for symbol, task in tasks:
            try:
                quote = await task
                if quote:
                    quotes[symbol] = quote
                else:
                    quotes[symbol] = {
                        "symbol": symbol,
                        "error": "No data available",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
            except Exception as e:
                std_logger.error(f"Error getting quote for {symbol}: {str(e)}")
                quotes[symbol] = {
                    "symbol": symbol,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }

        return quotes

    async def save_market_data(
        self, symbol: str, quote_data: Dict[str, Any], db: Session
    ):
        """Save market data to database"""
        try:
            market_data = MarketData(
                symbol=symbol,
                open_price=quote_data.get("open", 0),
                high_price=quote_data.get("high", 0),
                low_price=quote_data.get("low", 0),
                close_price=quote_data.get("price", 0),
                volume=quote_data.get("volume", 0),
                previous_close=quote_data.get("previous_close", 0),
                change=quote_data.get("change", 0),
                change_percentage=float(
                    str(quote_data.get("change_percent", 0)).rstrip("%")
                ),
                data_source=quote_data.get("source", "unknown"),
                timestamp=datetime.utcnow(),
                timeframe="realtime",
            )

            db.add(market_data)
            db.commit()
            logger.info(f"Saved market data for {symbol}")

        except Exception as e:
            logger.error(f"Error saving market data for {symbol}: {str(e)}")
            db.rollback()

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status and service metrics"""
        total_requests = max(self.request_count, 1)  # Avoid division by zero
        cache_hit_rate = (self.cache_hits / total_requests) * 100
        current_time = time.time()

        provider_stats = {}
        healthy_count = 0

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            success_count = self.provider_success_count.get(provider_name, 0)
            error_count = self.provider_error_count.get(provider_name, 0)
            consecutive_errors = self.consecutive_errors.get(provider_name, 0)
            is_healthy = self.source_health.get(provider_name, True)
            last_success = self.provider_last_success.get(provider_name, current_time)

            if is_healthy:
                healthy_count += 1

            total_provider_requests = success_count + error_count
            success_rate = (success_count / max(1, total_provider_requests)) * 100

            provider_stats[provider_name] = {
                "healthy": is_healthy,
                "consecutive_errors": consecutive_errors,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate_percent": success_rate,
                "last_success_seconds_ago": current_time - last_success,
                "total_requests": total_provider_requests,
            }

        # Cache statistics
        cache_stats = {
            "total_entries": len(self.cache),
            "fresh_entries": sum(
                1
                for cached_result in self.cache.values()
                if isinstance(cached_result, CacheResult)
                and cached_result.is_fresh(self.cache_ttl)
            ),
            "stale_entries": sum(
                1
                for cached_result in self.cache.values()
                if isinstance(cached_result, CacheResult)
                and not cached_result.is_fresh(self.cache_ttl)
            ),
        }

        return {
            "service_metrics": {
                "total_requests": self.request_count,
                "cache_hits": self.cache_hits,
                "cache_hit_rate_percent": cache_hit_rate,
                "total_errors": self.total_errors,
                "error_rate_percent": (self.total_errors / total_requests) * 100,
                "uptime_seconds": current_time
                - min(self.provider_last_success.values()),
            },
            "cache_stats": cache_stats,
            "providers": provider_stats,
            "summary": {
                "healthy_providers": healthy_count,
                "total_providers": len(self.providers),
                "all_providers_healthy": healthy_count == len(self.providers),
                "service_operational": healthy_count > 0,
            },
        }

    def reset_health_tracking(self) -> None:
        """Reset health tracking for all providers (useful for testing)"""
        current_time = time.time()
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            self.source_health[provider_name] = True
            self.consecutive_errors[provider_name] = 0
            self.provider_last_success[provider_name] = current_time

        std_logger.info("Reset health tracking for all market data providers")

    def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries, optionally matching a pattern"""
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
            return len(keys_to_remove)
        else:
            count = len(self.cache)
            self.cache.clear()
            return count

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        fresh_count = 0
        stale_count = 0

        for cached_result in self.cache.values():
            if isinstance(cached_result, CacheResult):
                if cached_result.is_fresh(self.cache_ttl):
                    fresh_count += 1
                else:
                    stale_count += 1

        return {
            "total_entries": len(self.cache),
            "fresh_entries": fresh_count,
            "stale_entries": stale_count,
            "cache_ttl_seconds": self.cache_ttl,
            "hit_rate_percent": (self.cache_hits / max(1, self.request_count)) * 100,
        }

    async def get_historical_data_enhanced(
        self,
        symbol: str,
        timeframe: str = "1day",
        limit: int = 100,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get historical data with enhanced caching and validation"""
        symbol = symbol.upper()
        cache_key = f"hist_{symbol}_{timeframe}_{limit}"

        # Check cache first unless forcing refresh
        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data.data

        # Try providers in order of preference
        healthy_providers = [
            p
            for p in self.providers
            if self.source_health.get(p.__class__.__name__, True)
        ]
        all_providers = healthy_providers + [
            p
            for p in self.providers
            if not self.source_health.get(p.__class__.__name__, True)
        ]

        for provider in all_providers:
            provider_name = provider.__class__.__name__
            try:
                historical_data = await provider.get_historical_data(
                    symbol, timeframe, limit
                )
                if historical_data and len(historical_data) > 0:
                    # Validate data quality
                    valid_data = [
                        item
                        for item in historical_data
                        if item.get("close") is not None
                        and item.get("timestamp") is not None
                    ]

                    if len(valid_data) > 0:
                        self._cache_data(cache_key, valid_data, provider_name.lower())
                        self._update_provider_health(provider_name, True)
                        std_logger.info(
                            f"Retrieved {len(valid_data)} historical data points for {symbol} from {provider_name}"
                        )
                        return valid_data

            except Exception as e:
                self._update_provider_health(provider_name, False)
                std_logger.error(
                    f"Error getting historical data from {provider_name} for {symbol}: {str(e)}"
                )
                continue

        # Try stale data as fallback
        stale_data = self._get_cached_data(cache_key, allow_stale=True)
        if stale_data:
            std_logger.warning(
                f"Returning stale historical data for {symbol} (age: {stale_data.age_seconds():.1f}s)"
            )
            return stale_data.data

        std_logger.error(f"All providers failed for historical data: {symbol}")
        return []

    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status with intelligent fallback"""
        cache_key = "market_status"

        # Check cache first (5 minute TTL for market status)
        cached_status = self._get_cached_data(cache_key)
        if cached_status and cached_status.is_fresh(300):  # 5 minutes
            return cached_status.data

        # Calculate market status based on time (fallback method)
        now = datetime.now()
        is_weekday = now.weekday() < 5  # Monday = 0, Sunday = 6

        # US market hours: 9:30 AM - 4:00 PM ET
        market_open_hour = 9
        market_open_minute = 30
        market_close_hour = 16
        market_close_minute = 0

        current_hour = now.hour
        current_minute = now.minute
        current_time_minutes = current_hour * 60 + current_minute
        market_open_minutes = market_open_hour * 60 + market_open_minute
        market_close_minutes = market_close_hour * 60 + market_close_minute

        is_market_hours = (
            market_open_minutes <= current_time_minutes < market_close_minutes
        )
        is_open = is_weekday and is_market_hours

        # Calculate next open/close times
        if is_open:
            # Market is open, next event is close
            next_close = now.replace(
                hour=market_close_hour,
                minute=market_close_minute,
                second=0,
                microsecond=0,
            )
            if next_close <= now:
                next_close += timedelta(days=1)
            next_event = "close"
            next_time = next_close
        else:
            # Market is closed, next event is open
            next_open = now.replace(
                hour=market_open_hour,
                minute=market_open_minute,
                second=0,
                microsecond=0,
            )

            # If it's after market hours today, next open is tomorrow
            if current_time_minutes >= market_close_minutes:
                next_open += timedelta(days=1)

            # If it's weekend, next open is Monday
            while next_open.weekday() >= 5:  # Saturday or Sunday
                next_open += timedelta(days=1)

            next_event = "open"
            next_time = next_open

        status = {
            "is_open": is_open,
            "is_weekday": is_weekday,
            "is_market_hours": is_market_hours,
            "next_event": next_event,
            "next_time": next_time.isoformat(),
            "current_time": now.isoformat(),
            "timezone": "ET",  # Assuming ET for US markets
            "source": "calculated",
            "timestamp": now.isoformat(),
        }

        # Cache the result
        self._cache_data(cache_key, status, "calculated")

        return status

    def get_provider_performance(self) -> Dict[str, Any]:
        """Get detailed performance metrics for each provider"""
        performance = {}
        current_time = time.time()

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            success_count = self.provider_success_count.get(provider_name, 0)
            error_count = self.provider_error_count.get(provider_name, 0)
            total_requests = success_count + error_count
            last_success = self.provider_last_success.get(provider_name, current_time)

            performance[provider_name] = {
                "success_count": success_count,
                "error_count": error_count,
                "total_requests": total_requests,
                "success_rate": (success_count / max(1, total_requests)) * 100,
                "is_healthy": self.source_health.get(provider_name, True),
                "consecutive_errors": self.consecutive_errors.get(provider_name, 0),
                "last_success_ago": current_time - last_success,
                "rate_limit_delay": getattr(provider, "rate_limit_delay", 0),
            }

        return performance


# Global instance
market_data_service = MarketDataService()

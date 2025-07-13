import asyncio
import time
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from functools import wraps

import aiohttp
import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.market_data import MarketData

logger = structlog.get_logger()
std_logger = logging.getLogger(__name__)

class MarketDataSource(str, Enum):
    """Available market data sources."""
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    YAHOO_FINANCE = "yfinance"
    FINNHUB = "finnhub"
    
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
            raise
        except Exception as e:
            std_logger.error(f"Unexpected error in market data service: {str(e)}", exc_info=True)
            raise MarketDataError(f"Unexpected market data error: {str(e)}")
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

    async def get_historical_data(self, symbol: str, timeframe: str = "1day", limit: int = 100) -> List[Dict[str, Any]]:
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
                            logger.warning(f"Alpha Vantage rate limit hit: {data['Note']}")
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
                                "latest_trading_day": quote_data.get("07. latest trading day"),
                                "previous_close": float(quote_data.get("08. previous close", 0)),
                                "change": float(quote_data.get("09. change", 0)),
                                "change_percent": quote_data.get("10. change percent", "0%").rstrip("%"),
                                "source": "alpha_vantage",
                            }
                    else:
                        logger.error(f"Alpha Vantage API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching quote from Alpha Vantage: {str(e)}")

        return None

    async def get_historical_data(self, symbol: str, timeframe: str = "1day", limit: int = 100) -> List[Dict[str, Any]]:
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
            
            if info and 'regularMarketPrice' in info:
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

    async def get_historical_data(self, symbol: str, timeframe: str = "1day", limit: int = 100) -> List[Dict[str, Any]]:
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
            hist = await loop.run_in_executor(None, lambda: ticker.history(period=period, interval=interval))
            
            if not hist.empty:
                historical_data = []
                for timestamp, row in hist.iterrows():
                    historical_data.append({
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume']),
                        "source": "yahoo_finance",
                    })
                
                return historical_data[:limit]
                
        except Exception as e:
            logger.error(f"Error fetching historical data from Yahoo Finance: {str(e)}")
            
        return []


class FinnhubProvider(MarketDataProvider):
    """Finnhub market data provider"""

    def __init__(self):
        super().__init__()
        self.api_key = getattr(settings, 'FINNHUB_API_KEY', None)
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
                        
                        if data and data.get('c'):  # 'c' is current price
                            return {
                                "symbol": symbol,
                                "open": data.get("o", 0),  # open
                                "high": data.get("h", 0),  # high
                                "low": data.get("l", 0),   # low
                                "price": data.get("c", 0), # current
                                "previous_close": data.get("pc", 0), # previous close
                                "change": data.get("d", 0),  # change
                                "change_percent": data.get("dp", 0), # change percent
                                "timestamp": int(data.get("t", time.time())),
                                "source": "finnhub",
                            }
                    else:
                        logger.error(f"Finnhub API error: {response.status}")
                        raise MarketDataError(f"API error: {response.status}", "finnhub", response.status)

        except Exception as e:
            logger.error(f"Error fetching quote from Finnhub: {str(e)}")
            raise MarketDataError(f"Finnhub error: {str(e)}", "finnhub")

        return None

    async def get_historical_data(self, symbol: str, timeframe: str = "1day", limit: int = 100) -> List[Dict[str, Any]]:
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
            "token": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and data.get('s') == 'ok':  # status ok
                            historical_data = []
                            timestamps = data.get('t', [])
                            opens = data.get('o', [])
                            highs = data.get('h', [])
                            lows = data.get('l', [])
                            closes = data.get('c', [])
                            volumes = data.get('v', [])
                            
                            for i in range(len(timestamps)):
                                historical_data.append({
                                    "timestamp": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d %H:%M:%S"),
                                    "open": float(opens[i]),
                                    "high": float(highs[i]),
                                    "low": float(lows[i]),
                                    "close": float(closes[i]),
                                    "volume": int(volumes[i]),
                                    "source": "finnhub",
                                })
                            
                            return historical_data

        except Exception as e:
            logger.error(f"Error fetching historical data from Finnhub: {str(e)}")

        return []


class MarketDataService:
    """Market data service with failover support"""

    def __init__(self):
        # Initialize all available providers with priority order
        self.providers = [
            YahooFinanceProvider(),      # Most reliable, free
            AlphaVantageProvider(),      # Good for real-time data
            FinnhubProvider(),           # Alternative source
            PolygonProvider(),           # Fallback option
        ]
        
        # Enhanced caching with cache result objects
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 60  # 1 minute cache
        
        # Health tracking for providers
        self.source_health = {provider.__class__.__name__: True for provider in self.providers}
        self.consecutive_errors = {provider.__class__.__name__: 0 for provider in self.providers}
        self.max_consecutive_errors = 3  # Mark provider as unhealthy after 3 consecutive errors
        
        # Metrics
        self.request_count = 0
        self.cache_hits = 0
        self.provider_success_count = {provider.__class__.__name__: 0 for provider in self.providers}

    def _get_cached_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from cache if fresh"""
        cache_key = f"quote_{symbol}"
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if isinstance(cached_result, CacheResult) and cached_result.is_fresh(self.cache_ttl):
                self.cache_hits += 1
                return cached_result.data
            elif isinstance(cached_result, tuple):  # Legacy cache format
                cached_data, timestamp = cached_result
                if time.time() - timestamp < self.cache_ttl:
                    self.cache_hits += 1
                    return cached_data
                else:
                    # Clean up stale cache entry
                    del self.cache[cache_key]
        return None

    def _cache_quote(self, symbol: str, quote_data: Dict[str, Any], source: str) -> None:
        """Cache quote data with metadata"""
        cache_key = f"quote_{symbol}"
        cache_result = CacheResult(quote_data, time.time(), source)
        self.cache[cache_key] = cache_result

    def _update_provider_health(self, provider_name: str, success: bool) -> None:
        """Update provider health tracking"""
        if success:
            self.consecutive_errors[provider_name] = 0
            self.source_health[provider_name] = True
            self.provider_success_count[provider_name] += 1
        else:
            self.consecutive_errors[provider_name] += 1
            if self.consecutive_errors[provider_name] >= self.max_consecutive_errors:
                self.source_health[provider_name] = False
                logger.warning(f"Provider {provider_name} marked as unhealthy after {self.max_consecutive_errors} consecutive errors")

    @handle_errors
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote with provider failover and health tracking"""
        self.request_count += 1
        
        # Check cache first
        cached_quote = self._get_cached_quote(symbol)
        if cached_quote:
            return cached_quote

        # Try providers in order, but skip unhealthy ones initially
        healthy_providers = [p for p in self.providers if self.source_health.get(p.__class__.__name__, True)]
        all_providers = self.providers if not healthy_providers else healthy_providers
        
        for provider in all_providers:
            provider_name = provider.__class__.__name__
            try:
                quote = await provider.get_quote(symbol)
                if quote:
                    # Cache the result and update health
                    self._cache_quote(symbol, quote, quote.get('source', provider_name.lower()))
                    self._update_provider_health(provider_name, True)
                    
                    std_logger.info(f"Successfully retrieved quote for {symbol} from {provider_name}")
                    return quote
                else:
                    # Provider returned None, but no exception - might be temporary
                    std_logger.warning(f"Provider {provider_name} returned no data for {symbol}")
                    
            except MarketDataError as e:
                self._update_provider_health(provider_name, False)
                std_logger.error(f"Provider {provider_name} failed for {symbol}: {str(e)}")
                continue
            except Exception as e:
                self._update_provider_health(provider_name, False)
                std_logger.error(f"Unexpected error from provider {provider_name} for {symbol}: {str(e)}")
                continue

        logger.error(f"All providers failed for symbol {symbol}")
        return None

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple symbols"""
        quotes = {}
        tasks = []

        for symbol in symbols:
            task = asyncio.create_task(self.get_quote(symbol))
            tasks.append((symbol, task))

        for symbol, task in tasks:
            try:
                quote = await task
                if quote:
                    quotes[symbol] = quote
            except Exception as e:
                logger.error(f"Error getting quote for {symbol}: {str(e)}")

        return quotes

    async def save_market_data(self, symbol: str, quote_data: Dict[str, Any], db: Session):
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
                change_percentage=float(str(quote_data.get("change_percent", 0)).rstrip("%")),
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
        """Get health status of all providers and service metrics"""
        total_requests = max(self.request_count, 1)  # Avoid division by zero
        cache_hit_rate = (self.cache_hits / total_requests) * 100
        
        provider_stats = {}
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            success_count = self.provider_success_count.get(provider_name, 0)
            error_count = self.consecutive_errors.get(provider_name, 0)
            is_healthy = self.source_health.get(provider_name, True)
            
            provider_stats[provider_name] = {
                "healthy": is_healthy,
                "consecutive_errors": error_count,
                "success_count": success_count,
                "success_rate": (success_count / total_requests) * 100 if total_requests > 0 else 0
            }
        
        return {
            "service_metrics": {
                "total_requests": self.request_count,
                "cache_hits": self.cache_hits,
                "cache_hit_rate_percent": cache_hit_rate,
                "active_cache_entries": len(self.cache)
            },
            "providers": provider_stats,
            "healthy_providers": sum(1 for health in self.source_health.values() if health),
            "total_providers": len(self.providers)
        }

    def reset_health_tracking(self) -> None:
        """Reset health tracking for all providers (useful for testing)"""
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            self.source_health[provider_name] = True
            self.consecutive_errors[provider_name] = 0
        
        std_logger.info("Reset health tracking for all market data providers")


# Global instance
market_data_service = MarketDataService()

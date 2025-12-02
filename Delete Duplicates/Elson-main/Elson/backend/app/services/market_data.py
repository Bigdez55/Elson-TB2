from typing import Dict, List, Optional, Any, Tuple, Union
import aiohttp
import asyncio
import yfinance as yf
import pandas as pd
from app.services.external_api.integration import get_stock_quote as external_api_get_quote, get_historical_data as external_api_get_historical
from datetime import datetime, timedelta
import logging
import time
import json
from fastapi import HTTPException
from functools import wraps
from enum import Enum
import aioredis

from app.core.config import settings
from app.core.metrics import metrics
# We'll import alert_manager when needed to avoid circular dependency

logger = logging.getLogger(__name__)

class MarketDataSource(str, Enum):
    """Available market data sources."""
    SCHWAB = "schwab"
    ALPACA = "alpaca"
    YAHOO_FINANCE = "yfinance"
    POLYGON = "polygon"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    FMP = "fmp"
    EXTERNAL_API = "external_api"  # New source for the external API infrastructure

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

class MarketDataError(Exception):
    """Exception raised for market data errors."""
    
    def __init__(self, message: str, source: str = None, status_code: int = None):
        self.message = message
        self.source = source
        self.status_code = status_code
        super().__init__(self.message)

def handle_errors(func):
    """Decorator to handle errors in market data methods."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MarketDataError as e:
            # Already handled error, just log and re-raise
            logger.error(f"Market data error from {e.source}: {str(e)}")
            metrics.increment(f"market_data.error.{e.source}")
            raise HTTPException(
                status_code=e.status_code or 500,
                detail=f"Market data error: {str(e)}"
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in market data service: {str(e)}", exc_info=True)
            metrics.increment("market_data.unexpected_error")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected market data error: {str(e)}"
            )
    return wrapper

class MarketDataService:
    """Enhanced market data service with caching and multiple data sources."""
    
    def __init__(
        self,
        redis_url: str = None,
        api_keys: Dict[str, str] = None,
        cache_ttl: int = None
    ):
        """Initialize with configuration."""
        self.api_keys = api_keys or {}
        self.schwab_api_key = self.api_keys.get("schwab", settings.SCHWAB_API_KEY)
        self.alpaca_api_key = self.api_keys.get("alpaca", settings.ALPACA_API_KEY)
        self.polygon_api_key = self.api_keys.get("polygon", settings.POLYGON_API_KEY)
        
        # Initialize sessions
        self.sessions = {}
        self.base_urls = {
            MarketDataSource.SCHWAB: "https://api.schwab.com/v1/markets",
            MarketDataSource.ALPACA: "https://data.alpaca.markets/v2",
            MarketDataSource.POLYGON: "https://api.polygon.io/v2"
        }
        
        # Configure cache
        self.cache_ttl = cache_ttl or settings.MARKET_DATA_CACHE_TTL
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis = None
        self.in_memory_cache = {}
        
        # Data source priority
        default_priority = [
            MarketDataSource.EXTERNAL_API,  # Try new external API infrastructure first
            MarketDataSource.ALPHA_VANTAGE,
            MarketDataSource.SCHWAB,
            MarketDataSource.ALPACA,
            MarketDataSource.YAHOO_FINANCE,
            MarketDataSource.POLYGON
        ]
        self.source_priority = getattr(settings, "MARKET_DATA_SOURCE_PRIORITY", default_priority)
        
        # Health tracking
        self.source_health = {src: True for src in MarketDataSource}
        self.consecutive_errors = {src: 0 for src in MarketDataSource}
        
        # Metrics
        self.request_count = 0
        self.cache_hits = 0
        
    async def setup(self):
        """Setup connections and sessions."""
        # Setup aiohttp sessions for each source
        for source in [MarketDataSource.SCHWAB, MarketDataSource.ALPACA, MarketDataSource.POLYGON]:
            headers = self._get_headers_for_source(source)
            if headers:
                self.sessions[source] = aiohttp.ClientSession(headers=headers)
        
        # Setup Redis if available
        if self.redis_url:
            try:
                self.redis = await aioredis.from_url(self.redis_url)
                logger.info("Connected to Redis for market data caching")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory cache: {str(e)}")
                self.redis = None
    
    def _get_headers_for_source(self, source: MarketDataSource) -> Dict[str, str]:
        """Get appropriate headers for the given data source."""
        if source == MarketDataSource.SCHWAB:
            if not self.schwab_api_key:
                return None
            return {
                "Authorization": f"Bearer {self.schwab_api_key}",
                "Content-Type": "application/json"
            }
        elif source == MarketDataSource.ALPACA:
            if not self.alpaca_api_key:
                return None
            return {
                "APCA-API-KEY-ID": self.api_keys.get("alpaca_key_id", ""),
                "APCA-API-SECRET-KEY": self.api_keys.get("alpaca_secret_key", ""),
                "Content-Type": "application/json"
            }
        elif source == MarketDataSource.POLYGON:
            if not self.polygon_api_key:
                return None
            return {
                "Authorization": f"Bearer {self.polygon_api_key}",
                "Content-Type": "application/json"
            }
        return {}
    
    async def _get_from_cache(self, key: str) -> Optional[CacheResult]:
        """Get data from cache (Redis or in-memory)."""
        if self.redis:
            cached_data = await self.redis.get(key)
            if cached_data:
                try:
                    cache_obj = json.loads(cached_data)
                    return CacheResult(
                        data=cache_obj["data"],
                        timestamp=cache_obj["timestamp"],
                        source=cache_obj["source"]
                    )
                except Exception as e:
                    logger.warning(f"Error deserializing cached data: {str(e)}")
        
        # Fallback to in-memory cache
        if key in self.in_memory_cache:
            cache_result = self.in_memory_cache[key]
            if cache_result.is_fresh(self.cache_ttl):
                return cache_result
            else:
                # Clean up stale cache entries
                del self.in_memory_cache[key]
        
        return None
    
    async def _save_to_cache(self, key: str, data: Any, source: str) -> None:
        """Save data to cache (Redis or in-memory)."""
        cache_obj = {
            "data": data,
            "timestamp": time.time(),
            "source": source
        }
        
        # Always update in-memory cache for fast access
        self.in_memory_cache[key] = CacheResult(**cache_obj)
        
        # Update Redis if available
        if self.redis:
            try:
                await self.redis.setex(
                    key,
                    self.cache_ttl,
                    json.dumps(cache_obj)
                )
            except Exception as e:
                logger.warning(f"Error saving to Redis cache: {str(e)}")
    
    def _update_source_health(self, source: str, success: bool) -> None:
        """Update health status for a data source."""
        if success:
            self.consecutive_errors[source] = 0
            if not self.source_health[source]:
                logger.info(f"Market data source {source} is now healthy")
                metrics.gauge(f"market_data.source.{source}.healthy", 1)
            self.source_health[source] = True
        else:
            self.consecutive_errors[source] += 1
            if self.consecutive_errors[source] >= settings.MARKET_DATA_ERROR_THRESHOLD:
                if self.source_health[source]:
                    logger.warning(f"Market data source {source} marked unhealthy after {self.consecutive_errors[source]} errors")
                    metrics.gauge(f"market_data.source.{source}.healthy", 0)
                    # Send alert if all sources are unhealthy
                    if all(not self.source_health[src] for src in self.source_priority):
                        # Import here to avoid circular dependency
                        from app.core.alerts_manager import alert_manager
                        alert_manager.send_alert(
                            "All market data sources are unhealthy",
                            f"All configured market data sources have failed: {', '.join(self.source_priority)}",
                            level="critical"
                        )
                self.source_health[source] = False
    
    async def _get_quote_from_source(self, symbol: str, source: MarketDataSource) -> Dict:
        """Get quote from a specific source."""
        try:
            if source == MarketDataSource.EXTERNAL_API:
                # Use the new external API infrastructure
                try:
                    result = await external_api_get_quote(symbol)
                    # Add source information
                    result["source"] = f"external_api_{result.get('provider', 'unknown')}"
                    return result
                except Exception as e:
                    raise MarketDataError(f"Error from External API: {str(e)}", source=source.value)
                
            elif source == MarketDataSource.YAHOO_FINANCE:
                # Yahoo Finance doesn't need a session
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Check for valid data
                if not info or "regularMarketPrice" not in info:
                    raise MarketDataError("Invalid data from Yahoo Finance", source=source.value)
                
                return {
                    "symbol": symbol,
                    "price": info.get("regularMarketPrice"),
                    "change": info.get("regularMarketChange", 0),
                    "change_percent": info.get("regularMarketChangePercent", 0),
                    "volume": info.get("regularMarketVolume", 0),
                    "bid": info.get("bid", info.get("regularMarketPrice")),
                    "ask": info.get("ask", info.get("regularMarketPrice")),
                    "high": info.get("dayHigh", info.get("regularMarketDayHigh")),
                    "low": info.get("dayLow", info.get("regularMarketDayLow")),
                    "open": info.get("open", info.get("regularMarketOpen")),
                    "prev_close": info.get("previousClose", info.get("regularMarketPreviousClose")),
                    "timestamp": datetime.now().isoformat(),
                    "source": source.value
                }
            
            # Get from API sources
            session = self.sessions.get(source)
            if not session:
                raise MarketDataError(f"No session available for {source}", source=source.value)
            
            if source == MarketDataSource.SCHWAB:
                async with session.get(f"{self.base_urls[source]}/quotes/{symbol}") as response:
                    if response.status != 200:
                        raise MarketDataError(
                            f"Error from Schwab API: {response.status}",
                            source=source.value,
                            status_code=response.status
                        )
                    data = await response.json()
                    return self._normalize_quote(data, symbol, source)
            
            elif source == MarketDataSource.ALPACA:
                async with session.get(f"{self.base_urls[source]}/stocks/{symbol}/quotes/latest") as response:
                    if response.status != 200:
                        raise MarketDataError(
                            f"Error from Alpaca API: {response.status}",
                            source=source.value,
                            status_code=response.status
                        )
                    data = await response.json()
                    return self._normalize_quote(data, symbol, source)
            
            elif source == MarketDataSource.POLYGON:
                async with session.get(f"{self.base_urls[source]}/aggs/ticker/{symbol}/prev") as response:
                    if response.status != 200:
                        raise MarketDataError(
                            f"Error from Polygon API: {response.status}",
                            source=source.value,
                            status_code=response.status
                        )
                    data = await response.json()
                    return self._normalize_quote(data, symbol, source)
            
            raise MarketDataError(f"Unknown data source: {source}", source=source.value)
            
        except MarketDataError:
            raise
        except Exception as e:
            raise MarketDataError(f"Error fetching from {source}: {str(e)}", source=source.value)
    
    def _normalize_quote(self, data: Dict, symbol: str, source: MarketDataSource) -> Dict:
        """Normalize quote data from different sources to a common format."""
        try:
            if source == MarketDataSource.SCHWAB:
                return {
                    "symbol": symbol,
                    "price": data.get("lastPrice"),
                    "change": data.get("netChange"),
                    "change_percent": data.get("percentChange"),
                    "volume": data.get("volume"),
                    "bid": data.get("bidPrice"),
                    "ask": data.get("askPrice"),
                    "high": data.get("highPrice"),
                    "low": data.get("lowPrice"),
                    "open": data.get("openPrice"),
                    "prev_close": data.get("previousClose"),
                    "timestamp": data.get("quoteTimestamp", datetime.now().isoformat()),
                    "source": source.value
                }
            
            elif source == MarketDataSource.ALPACA:
                quote = data.get("quote", {})
                return {
                    "symbol": symbol,
                    "price": (quote.get("ap") + quote.get("bp")) / 2 if quote.get("ap") and quote.get("bp") else None,
                    "bid": quote.get("bp"),
                    "ask": quote.get("ap"),
                    "bid_size": quote.get("bs"),
                    "ask_size": quote.get("as"),
                    "timestamp": quote.get("t", datetime.now().timestamp()) / 1000,
                    "source": source.value
                }
            
            elif source == MarketDataSource.POLYGON:
                result = data.get("results", [{}])[0] if data.get("results") else {}
                return {
                    "symbol": symbol,
                    "price": result.get("c"),  # close price
                    "open": result.get("o"),
                    "high": result.get("h"),
                    "low": result.get("l"),
                    "volume": result.get("v"),
                    "prev_close": None,  # Not available in this endpoint
                    "timestamp": datetime.fromtimestamp(result.get("t", time.time()) / 1000).isoformat() if result.get("t") else datetime.now().isoformat(),
                    "source": source.value
                }
            
            return {
                "symbol": symbol,
                "price": None,
                "timestamp": datetime.now().isoformat(),
                "source": source.value,
                "error": "Unknown format"
            }
            
        except Exception as e:
            logger.error(f"Error normalizing quote data from {source}: {str(e)}")
            return {
                "symbol": symbol,
                "price": None,
                "timestamp": datetime.now().isoformat(),
                "source": source.value,
                "error": str(e)
            }
    
    @handle_errors
    async def get_quote(self, symbol: str, force_refresh: bool = False) -> Dict:
        """Get real-time quote for a symbol with caching and failover."""
        symbol = symbol.upper()
        start_time = time.time()
        self.request_count += 1
        metrics.increment("market_data.quote.requests")
        
        # Try cache first if not forcing refresh
        cache_key = f"quote:{symbol}"
        if not force_refresh:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                metrics.increment("market_data.quote.cache_hits")
                metrics.timing("market_data.quote.cache_age", cached_result.age_seconds() * 1000)
                return cached_result.data
        
        # Get quote from prioritized sources with failover
        errors = []
        for source in self.source_priority:
            # Skip unhealthy sources
            if not self.source_health.get(source, True):
                continue
                
            try:
                source_enum = MarketDataSource(source)
                quote = await self._get_quote_from_source(symbol, source_enum)
                
                # Update health status on success
                self._update_source_health(source, True)
                
                # Add source information
                quote["source"] = source
                
                # Quality check - validate required fields
                if quote.get("price") is None:
                    logger.warning(f"Invalid quote received from {source} for {symbol}: missing price")
                    continue
                    
                # Record metrics
                metrics.timing("market_data.quote.response_time", (time.time() - start_time) * 1000)
                metrics.increment(f"market_data.source.{source}.success")
                
                # Cache the successful result
                await self._save_to_cache(cache_key, quote, source)
                
                return quote
                
            except Exception as e:
                # Update health status on failure
                self._update_source_health(source, False)
                
                # Record error metrics
                metrics.increment(f"market_data.source.{source}.error")
                
                # Log error and continue to next source
                logger.warning(f"Error getting quote from {source} for {symbol}: {str(e)}")
                errors.append(f"{source}: {str(e)}")
                continue
        
        # If we reach here, all sources failed
        error_message = f"All data sources failed for {symbol}: {'; '.join(errors)}"
        metrics.increment("market_data.all_sources_failed")
        logger.error(error_message)
        
        # Check if we have stale data in cache that we can return
        stale_cache = await self._get_from_cache(cache_key)
        if stale_cache:
            # Mark as stale but return it anyway
            stale_cache.data["is_stale"] = True
            stale_cache.data["stale_age_seconds"] = stale_cache.age_seconds()
            logger.warning(f"Returning stale data for {symbol}, age: {stale_cache.age_seconds():.1f}s")
            metrics.increment("market_data.stale_data_returned")
            return stale_cache.data
            
        # No data available at all
        raise MarketDataError(error_message)
    
    @handle_errors
    async def get_batch_quotes(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, Dict]:
        """Get quotes for multiple symbols with parallel requests."""
        start_time = time.time()
        normalized_symbols = [s.upper() for s in symbols]
        results = {}
        
        # Get cached results first if not forcing refresh
        if not force_refresh:
            cache_tasks = [self._get_from_cache(f"quote:{symbol}") for symbol in normalized_symbols]
            cached_results = await asyncio.gather(*cache_tasks)
            
            # Identify which symbols we need to fetch
            symbols_to_fetch = []
            for symbol, cached_result in zip(normalized_symbols, cached_results):
                if cached_result:
                    results[symbol] = cached_result.data
                    self.cache_hits += 1
                else:
                    symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch = normalized_symbols
        
        # Fetch any symbols not in cache
        if symbols_to_fetch:
            fetch_tasks = [self.get_quote(symbol, force_refresh) for symbol in symbols_to_fetch]
            fetched_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            
            for symbol, result in zip(symbols_to_fetch, fetched_results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching quote for {symbol}: {str(result)}")
                    results[symbol] = {"symbol": symbol, "error": str(result), "timestamp": datetime.now().isoformat()}
                else:
                    results[symbol] = result
        
        # Record metrics
        metrics.timing("market_data.batch_quotes.response_time", (time.time() - start_time) * 1000)
        metrics.gauge("market_data.batch_quotes.symbol_count", len(symbols))
        
        return results
    
    @handle_errors
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
        force_refresh: bool = False
    ) -> Dict:
        """Get historical price data with caching."""
        symbol = symbol.upper()
        start_time = time.time()
        end_date = end_date or datetime.now()
        
        # Create cache key
        cache_key = f"hist:{symbol}:{start_date.isoformat()}:{end_date.isoformat()}:{interval}"
        
        # Try cache first if not forcing refresh
        if not force_refresh:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.cache_hits += 1
                metrics.increment("market_data.historical.cache_hits")
                return cached_result.data
        
        # Try to get data from multiple sources
        for source in self.source_priority:
            # Skip unhealthy sources
            if not self.source_health.get(source, True):
                continue
                
            try:
                # Use yfinance as the default historical data source for now
                # We could implement other APIs for historical data in the future
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval
                )
                
                # Convert to serializable format
                result = {
                    "symbol": symbol,
                    "interval": interval,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "data": df.reset_index().to_dict(orient="records"),
                    "source": "yfinance",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Update health status
                self._update_source_health(source, True)
                
                # Cache the result
                await self._save_to_cache(cache_key, result, source)
                
                # Record metrics
                metrics.timing("market_data.historical.response_time", (time.time() - start_time) * 1000)
                metrics.increment(f"market_data.source.{source}.success")
                
                return result
            
            except Exception as e:
                # Update health status
                self._update_source_health(source, False)
                
                # Record metrics
                metrics.increment(f"market_data.source.{source}.error")
                
                logger.warning(f"Error getting historical data from {source} for {symbol}: {str(e)}")
                continue
        
        # If we get here, all sources failed
        error_message = f"All sources failed for historical data for {symbol}"
        metrics.increment("market_data.all_sources_failed")
        logger.error(error_message)
        
        # Check for stale cache
        stale_cache = await self._get_from_cache(cache_key)
        if stale_cache:
            stale_cache.data["is_stale"] = True
            stale_cache.data["stale_age_seconds"] = stale_cache.age_seconds()
            logger.warning(f"Returning stale historical data for {symbol}, age: {stale_cache.age_seconds():.1f}s")
            metrics.increment("market_data.stale_data_returned")
            return stale_cache.data
            
        raise MarketDataError(error_message)
    
    @handle_errors
    async def get_market_hours(self, market: str = "US") -> Dict:
        """Get market hours and trading status with caching."""
        start_time = time.time()
        cache_key = f"market_hours:{market}"
        
        # Check cache first
        cached_result = await self._get_from_cache(cache_key)
        if cached_result and cached_result.is_fresh(300):  # 5 minute TTL for market hours
            self.cache_hits += 1
            metrics.increment("market_data.market_hours.cache_hits")
            return cached_result.data
        
        # Try each source
        for source in self.source_priority:
            # Skip unhealthy sources
            if not self.source_health.get(source, True):
                continue
                
            try:
                source_enum = MarketDataSource(source)
                session = self.sessions.get(source_enum)
                
                if source_enum == MarketDataSource.SCHWAB and session:
                    async with session.get(f"{self.base_urls[source_enum]}/hours") as response:
                        if response.status == 200:
                            data = await response.json()
                            result = {
                                "is_open": data.get("isOpen", False),
                                "next_open": data.get("nextOpenTime"),
                                "next_close": data.get("nextCloseTime"),
                                "timestamp": datetime.now().isoformat(),
                                "source": source
                            }
                            
                            # Cache the result
                            await self._save_to_cache(cache_key, result, source)
                            
                            # Update health and metrics
                            self._update_source_health(source, True)
                            metrics.timing("market_data.market_hours.response_time", (time.time() - start_time) * 1000)
                            metrics.increment(f"market_data.source.{source}.success")
                            
                            return result
                
                elif source_enum == MarketDataSource.ALPACA and session:
                    async with session.get(f"{self.base_urls[source_enum]}/calendar") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Find today's calendar entry
                            today = datetime.now().strftime("%Y-%m-%d")
                            today_data = next((d for d in data if d.get("date") == today), None)
                            
                            now = datetime.now()
                            is_open = False
                            
                            if today_data:
                                open_time = datetime.strptime(f"{today} {today_data.get('open')}", "%Y-%m-%d %H:%M")
                                close_time = datetime.strptime(f"{today} {today_data.get('close')}", "%Y-%m-%d %H:%M")
                                is_open = open_time <= now <= close_time
                            
                            result = {
                                "is_open": is_open,
                                "next_open": today_data.get("open") if today_data else None,
                                "next_close": today_data.get("close") if today_data else None,
                                "timestamp": datetime.now().isoformat(),
                                "source": source
                            }
                            
                            # Cache the result
                            await self._save_to_cache(cache_key, result, source)
                            
                            # Update health and metrics
                            self._update_source_health(source, True)
                            metrics.timing("market_data.market_hours.response_time", (time.time() - start_time) * 1000)
                            metrics.increment(f"market_data.source.{source}.success")
                            
                            return result
            
            except Exception as e:
                self._update_source_health(source, False)
                metrics.increment(f"market_data.source.{source}.error")
                logger.warning(f"Error getting market hours from {source}: {str(e)}")
                continue
        
        # Fallback to calculated hours
        now = datetime.now()
        is_weekday = now.weekday() < 5
        is_market_hours = 9 <= now.hour < 16
        
        result = {
            "is_open": is_weekday and is_market_hours,
            "next_open": None,
            "next_close": None,
            "timestamp": now.isoformat(),
            "source": "calculated",
            "is_fallback": True
        }
        
        # Cache the fallback result too
        await self._save_to_cache(cache_key, result, "calculated")
        
        return result
    
    async def get_data_quality_metrics(self) -> Dict:
        """Get metrics about data quality and service health."""
        return {
            "request_count": self.request_count,
            "cache_hits": self.cache_hits,
            "cache_hit_ratio": self.cache_hits / max(1, self.request_count),
            "source_health": self.source_health,
            "consecutive_errors": self.consecutive_errors,
            "cache_size": len(self.in_memory_cache),
            "using_redis": self.redis is not None
        }
    
    async def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries, optionally matching a pattern."""
        if pattern:
            # Clear matching in-memory cache
            keys_to_remove = [k for k in self.in_memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.in_memory_cache[key]
            
            # Clear matching Redis cache
            count = 0
            if self.redis:
                keys = await self.redis.keys(f"*{pattern}*")
                if keys:
                    count = await self.redis.delete(*keys)
            
            return len(keys_to_remove) + (count or 0)
        else:
            # Clear all cache
            count = len(self.in_memory_cache)
            self.in_memory_cache.clear()
            
            if self.redis:
                await self.redis.flushdb()
            
            return count
    
    async def close(self):
        """Close all connections and sessions."""
        for session in self.sessions.values():
            if session:
                await session.close()
        
        if self.redis:
            await self.redis.close()
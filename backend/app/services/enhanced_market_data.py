"""
Enhanced Market Data Service with Improved Caching and Multiple Providers

This service provides high-performance market data with intelligent caching,
failover between providers, and optimized for personal trading use.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class MarketDataCache:
    """
    In-memory cache for market data with TTL support.
    For personal use, this is more efficient than Redis.
    """

    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl_map = {
            "quote": 60,  # 1 minute for quotes
            "historical": 3600,  # 1 hour for historical data
            "news": 1800,  # 30 minutes for news
            "fundamentals": 86400,  # 24 hours for fundamentals
        }

    def get(self, key: str, data_type: str = "quote") -> Optional[Any]:
        """Get data from cache if not expired."""
        if key not in self._cache:
            return None

        data, timestamp = self._cache[key]
        ttl = self._ttl_map.get(data_type, 300)

        if time.time() - timestamp > ttl:
            del self._cache[key]
            return None

        return data

    def set(self, key: str, data: Any, data_type: str = "quote") -> None:
        """Store data in cache with timestamp."""
        self._cache[key] = (data, time.time())

    def clear_expired(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = []

        for key, (data, timestamp) in self._cache.items():
            # Use default TTL if type cannot be determined
            if current_time - timestamp > 3600:  # 1 hour default
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]


class EnhancedMarketDataProvider:
    """Base class for enhanced market data providers."""

    def __init__(self, name: str):
        self.name = name
        self.last_request_time = 0
        self.rate_limit_delay = 1.0
        self.error_count = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes

    async def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.error_count >= self.circuit_breaker_threshold:
            if time.time() - self.last_request_time < self.circuit_breaker_timeout:
                return True
            else:
                # Reset circuit breaker after timeout
                self.error_count = 0
        return False

    def record_success(self):
        """Record successful request."""
        self.error_count = max(0, self.error_count - 1)

    def record_error(self):
        """Record failed request."""
        self.error_count += 1

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote."""
        raise NotImplementedError

    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[List[Dict[str, Any]]]:
        """Get historical data."""
        raise NotImplementedError


class YFinanceProvider(EnhancedMarketDataProvider):
    """Yahoo Finance provider (free, reliable)."""

    def __init__(self):
        super().__init__("YFinance")
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.rate_limit_delay = 0.5  # More generous rate limit

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Yahoo Finance."""
        if self.is_circuit_open():
            return None

        try:
            await self._rate_limit()

            url = f"{self.base_url}/{symbol}"
            params = {
                "interval": "1m",
                "range": "1d",
                "includePrePost": "true",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("chart", {}).get("result", [])

                        if result:
                            meta = result[0].get("meta", {})
                            quote_data = {
                                "symbol": symbol,
                                "price": meta.get("regularMarketPrice", 0),
                                "change": meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0),
                                "change_percent": (
                                    (meta.get("regularMarketPrice", 0) - meta.get("previousClose", 1))
                                    / meta.get("previousClose", 1)
                                    * 100
                                ),
                                "volume": meta.get("regularMarketVolume", 0),
                                "market_cap": meta.get("marketCap"),
                                "pe_ratio": meta.get("trailingPE"),
                                "timestamp": datetime.utcnow().isoformat(),
                                "provider": self.name,
                            }
                            self.record_success()
                            return quote_data

            self.record_error()
            return None

        except Exception as e:
            logger.error(f"YFinance quote error for {symbol}", error=str(e))
            self.record_error()
            return None

    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[List[Dict[str, Any]]]:
        """Get historical data from Yahoo Finance."""
        if self.is_circuit_open():
            return None

        try:
            await self._rate_limit()

            # Convert period to range parameter
            range_map = {
                "1d": "1d",
                "5d": "5d",
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
                "1y": "1y",
                "2y": "2y",
                "5y": "5y",
            }

            url = f"{self.base_url}/{symbol}"
            params = {"interval": "1d", "range": range_map.get(period, "1mo")}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("chart", {}).get("result", [])

                        if result:
                            timestamps = result[0].get("timestamp", [])
                            indicators = result[0].get("indicators", {})
                            quotes = indicators.get("quote", [{}])[0]

                            historical_data = []
                            for i, timestamp in enumerate(timestamps):
                                historical_data.append(
                                    {
                                        "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                                        "open": quotes.get("open", [None])[i],
                                        "high": quotes.get("high", [None])[i],
                                        "low": quotes.get("low", [None])[i],
                                        "close": quotes.get("close", [None])[i],
                                        "volume": quotes.get("volume", [None])[i],
                                    }
                                )

                            self.record_success()
                            return historical_data

            self.record_error()
            return None

        except Exception as e:
            logger.error(f"YFinance historical data error for {symbol}", error=str(e))
            self.record_error()
            return None


class AlphaVantageProviderEnhanced(EnhancedMarketDataProvider):
    """Enhanced Alpha Vantage provider with better error handling."""

    def __init__(self):
        super().__init__("AlphaVantage")
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.0  # 5 calls per minute

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from Alpha Vantage."""
        if not self.api_key or self.is_circuit_open():
            return None

        try:
            await self._rate_limit()

            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get("Global Quote", {})

                        if quote:
                            quote_data = {
                                "symbol": symbol,
                                "price": float(quote.get("05. price", 0)),
                                "change": float(quote.get("09. change", 0)),
                                "change_percent": float(quote.get("10. change percent", "0%").rstrip("%")),
                                "volume": int(quote.get("06. volume", 0)),
                                "timestamp": datetime.utcnow().isoformat(),
                                "provider": self.name,
                            }
                            self.record_success()
                            return quote_data

            self.record_error()
            return None

        except Exception as e:
            logger.error(f"AlphaVantage quote error for {symbol}", error=str(e))
            self.record_error()
            return None


class EnhancedMarketDataService:
    """
    Enhanced market data service with caching, failover, and multiple providers.
    Optimized for personal trading use.
    """

    def __init__(self):
        self.cache = MarketDataCache()
        self.providers = [
            YFinanceProvider(),
            AlphaVantageProviderEnhanced(),
        ]
        self.primary_provider = 0

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote with caching and failover.

        Args:
            symbol: Stock symbol to get quote for

        Returns:
            Quote data or None if unavailable
        """
        symbol = symbol.upper().strip()
        cache_key = f"quote:{symbol}"

        # Check cache first
        cached_data = self.cache.get(cache_key, "quote")
        if cached_data:
            logger.debug(f"Quote cache hit for {symbol}")
            return cached_data

        # Try providers in order
        for i, provider in enumerate(self.providers):
            try:
                quote = await provider.get_quote(symbol)
                if quote:
                    # Cache successful result
                    self.cache.set(cache_key, quote, "quote")

                    # Update primary provider if this one worked
                    if i != self.primary_provider:
                        logger.info(
                            f"Switching primary provider to {provider.name}",
                            old_provider=self.providers[self.primary_provider].name,
                            new_provider=provider.name,
                        )
                        self.primary_provider = i

                    return quote

            except Exception as e:
                logger.warning(
                    f"Provider {provider.name} failed for quote {symbol}",
                    error=str(e),
                )
                continue

        logger.error(f"All providers failed for quote {symbol}")
        return None

    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[List[Dict[str, Any]]]:
        """
        Get historical data with caching and failover.

        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)

        Returns:
            Historical data or None if unavailable
        """
        symbol = symbol.upper().strip()
        cache_key = f"historical:{symbol}:{period}"

        # Check cache first
        cached_data = self.cache.get(cache_key, "historical")
        if cached_data:
            logger.debug(f"Historical data cache hit for {symbol}")
            return cached_data

        # Try providers in order
        for provider in self.providers:
            try:
                data = await provider.get_historical_data(symbol, period)
                if data:
                    # Cache successful result
                    self.cache.set(cache_key, data, "historical")
                    return data

            except Exception as e:
                logger.warning(
                    f"Provider {provider.name} failed for historical {symbol}",
                    error=str(e),
                )
                continue

        logger.error(f"All providers failed for historical data {symbol}")
        return None

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get quotes for multiple symbols efficiently.

        Args:
            symbols: List of symbols to get quotes for

        Returns:
            Dictionary mapping symbols to quote data
        """
        results = {}

        # Process in batches to avoid overwhelming providers
        batch_size = 5
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]

            # Get quotes concurrently for this batch
            tasks = [self.get_quote(symbol) for symbol in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error getting quote for {symbol}", error=str(result))
                    results[symbol] = None
                else:
                    results[symbol] = result

            # Small delay between batches
            await asyncio.sleep(0.1)

        return results

    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols based on company name or symbol.

        Args:
            query: Search query

        Returns:
            List of matching symbols with metadata
        """
        # For now, return a simple placeholder
        # In a full implementation, this would integrate with
        # symbol search APIs from various providers

        query = query.upper().strip()

        # Basic hardcoded examples for demonstration
        common_symbols = {
            "APPLE": {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock"},
            "MICROSOFT": {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "type": "stock",
            },
            "AMAZON": {
                "symbol": "AMZN",
                "name": "Amazon.com Inc.",
                "type": "stock",
            },
            "GOOGLE": {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "type": "stock",
            },
            "TESLA": {"symbol": "TSLA", "name": "Tesla Inc.", "type": "stock"},
            "BITCOIN": {
                "symbol": "BTC-USD",
                "name": "Bitcoin USD",
                "type": "crypto",
            },
            "ETHEREUM": {
                "symbol": "ETH-USD",
                "name": "Ethereum USD",
                "type": "crypto",
            },
        }

        results = []
        for name, data in common_symbols.items():
            if query in name or query in data["symbol"]:
                results.append(data)

        # If exact symbol match, add it
        if query not in [r["symbol"] for r in results]:
            results.append(
                {
                    "symbol": query,
                    "name": f"{query} (Symbol)",
                    "type": "unknown",
                }
            )

        return results[:10]  # Limit to 10 results

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "cache_size": len(self.cache._cache),
            "primary_provider": self.providers[self.primary_provider].name,
            "provider_status": [
                {
                    "name": p.name,
                    "error_count": p.error_count,
                    "circuit_open": p.is_circuit_open(),
                }
                for p in self.providers
            ],
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for all providers."""
        health_status = {
            "overall_status": "healthy",
            "providers": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        for provider in self.providers:
            try:
                # Try to get a simple quote to test provider
                test_quote = await provider.get_quote("AAPL")
                status = "healthy" if test_quote else "degraded"
            except Exception:
                status = "unhealthy"

            health_status["providers"].append(
                {
                    "name": provider.name,
                    "status": status,
                    "error_count": provider.error_count,
                    "circuit_open": provider.is_circuit_open(),
                }
            )

        # Overall status based on provider health
        healthy_providers = sum(1 for p in health_status["providers"] if p["status"] in ["healthy", "degraded"])

        if healthy_providers == 0:
            health_status["overall_status"] = "critical"
        elif healthy_providers < len(self.providers):
            health_status["overall_status"] = "degraded"

        return health_status


# Singleton instance for the application
enhanced_market_data_service = EnhancedMarketDataService()

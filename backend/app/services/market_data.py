import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.market_data import MarketData

logger = structlog.get_logger()


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


class MarketDataService:
    """Market data service with failover support"""

    def __init__(self):
        self.providers = [AlphaVantageProvider(), PolygonProvider()]
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 60  # 1 minute cache

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote with provider failover"""
        # Check cache first
        cache_key = f"quote_{symbol}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data

        # Try providers in order
        for provider in self.providers:
            try:
                quote = await provider.get_quote(symbol)
                if quote:
                    # Cache the result
                    self.cache[cache_key] = (quote, time.time())
                    return quote
            except Exception as e:
                logger.error(f"Provider {provider.__class__.__name__} failed: {str(e)}")
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


# Global instance
market_data_service = MarketDataService()

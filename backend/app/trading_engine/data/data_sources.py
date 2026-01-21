"""
Data Sources module for the trading engine.
Implements connections to various data sources like market data, news, economic data, etc.

Phase 1 Enhancement: OpenBB Platform integration for 100+ data sources
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import numpy as np
import pandas as pd
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv
from newsapi import NewsApiClient

# OpenBB Platform import (Phase 1)
try:
    from openbb import obb

    OPENBB_AVAILABLE = True
except ImportError:
    OPENBB_AVAILABLE = False

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DataSource:
    """Base class for all data sources"""

    def __init__(self):
        self.name = "base_data_source"

    async def fetch_data(self, *args, **kwargs):
        """Base method to fetch data from the source"""
        raise NotImplementedError("Subclasses must implement fetch_data method")


class MarketDataSource(DataSource):
    """Market data source for fetching price and volume data"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "market_data"
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.alpha_vantage = TimeSeries(key=self.api_key, output_format="pandas")

    async def fetch_data(
        self,
        symbols: List[str],
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source: str = "yfinance",
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch market data for the given symbols

        Args:
            symbols: List of stock symbols
            interval: Data interval (1m, 5m, 1h, 1d, etc.)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            source: Data source ('yfinance' or 'alpha_vantage')

        Returns:
            Dictionary of DataFrames with market data for each symbol
        """
        if source == "yfinance":
            return await self._fetch_from_yfinance(
                symbols, interval, start_date, end_date
            )
        elif source == "alpha_vantage":
            return await self._fetch_from_alpha_vantage(symbols, interval)
        else:
            raise ValueError(f"Unsupported data source: {source}")

    async def _fetch_from_yfinance(
        self,
        symbols: List[str],
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data from Yahoo Finance"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        result = {}
        for symbol in symbols:
            try:
                data = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    progress=False,
                )
                if not data.empty:
                    # Standardize column names
                    data.columns = [col.lower() for col in data.columns]
                    result[symbol] = data
                else:
                    logger.warning(f"No data returned for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")

        return result

    async def _fetch_from_alpha_vantage(
        self, symbols: List[str], interval: str = "daily"
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data from Alpha Vantage"""
        result = {}

        alpha_intervals = {
            "1m": "TIME_SERIES_INTRADAY",
            "5m": "TIME_SERIES_INTRADAY",
            "15m": "TIME_SERIES_INTRADAY",
            "30m": "TIME_SERIES_INTRADAY",
            "1h": "TIME_SERIES_INTRADAY",
            "daily": "TIME_SERIES_DAILY_ADJUSTED",
            "weekly": "TIME_SERIES_WEEKLY",
            "monthly": "TIME_SERIES_MONTHLY",
        }

        # Map interval to Alpha Vantage format
        av_interval = interval
        if interval in ["1m", "5m", "15m", "30m", "1h"]:
            interval_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "60min",
            }
            av_interval = interval_map.get(interval, "5min")

        for symbol in symbols:
            try:
                if "min" in av_interval:
                    data, meta_data = self.alpha_vantage.get_intraday(
                        symbol=symbol, interval=av_interval, outputsize="full"
                    )
                elif interval == "daily":
                    data, meta_data = self.alpha_vantage.get_daily_adjusted(
                        symbol=symbol, outputsize="full"
                    )
                elif interval == "weekly":
                    data, meta_data = self.alpha_vantage.get_weekly_adjusted(
                        symbol=symbol
                    )
                elif interval == "monthly":
                    data, meta_data = self.alpha_vantage.get_monthly_adjusted(
                        symbol=symbol
                    )

                # Standardize column names
                data.columns = [col.lower() for col in data.columns]
                result[symbol] = data

                # Alpha Vantage has rate limits, so we need to wait
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(
                    f"Error fetching Alpha Vantage data for {symbol}: {str(e)}"
                )

        return result


class NewsDataSource(DataSource):
    """News data source for fetching financial news and sentiment"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "news_data"
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.news_api = NewsApiClient(api_key=self.api_key)

    async def fetch_data(
        self, symbols: List[str] = None, keywords: List[str] = None, days_back: int = 7
    ) -> pd.DataFrame:
        """
        Fetch news data related to the given symbols or keywords

        Args:
            symbols: List of stock symbols to fetch news for
            keywords: List of keywords to search for
            days_back: Number of days to look back

        Returns:
            DataFrame with news articles
        """
        if not symbols and not keywords:
            raise ValueError("Either symbols or keywords must be provided")

        # Create query string
        query_parts = []
        if symbols:
            query_parts.extend(symbols)
        if keywords:
            query_parts.extend(keywords)

        query = " OR ".join(query_parts)

        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        try:
            news = self.news_api.get_everything(
                q=query,
                from_param=from_date,
                to=to_date,
                language="en",
                sort_by="relevancy",
                page_size=100,
            )

            if "articles" in news and news["articles"]:
                df = pd.DataFrame(news["articles"])
                # Convert publishedAt to datetime
                df["publishedAt"] = pd.to_datetime(df["publishedAt"])
                return df
            else:
                logger.warning(f"No news articles found for query: {query}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching news data: {str(e)}")
            return pd.DataFrame()


class EconomicDataSource(DataSource):
    """Economic data source for fetching macro-economic indicators"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "economic_data"
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"

    async def fetch_data(
        self,
        indicators: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch economic indicators from FRED

        Args:
            indicators: List of FRED indicator codes (e.g., 'GDP', 'UNRATE', 'CPI')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary of DataFrames with economic data for each indicator
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        result = {}

        async with aiohttp.ClientSession() as session:
            for indicator in indicators:
                try:
                    params = {
                        "series_id": indicator,
                        "api_key": self.api_key,
                        "file_type": "json",
                        "observation_start": start_date,
                        "observation_end": end_date,
                    }

                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "observations" in data:
                                df = pd.DataFrame(data["observations"])
                                df["date"] = pd.to_datetime(df["date"])
                                df["value"] = pd.to_numeric(
                                    df["value"], errors="coerce"
                                )
                                df = df.set_index("date")
                                result[indicator] = df
                            else:
                                logger.warning(
                                    f"No data returned for indicator {indicator}"
                                )
                        else:
                            logger.error(
                                f"Error fetching data for {indicator}: {response.status}"
                            )

                except Exception as e:
                    logger.error(
                        f"Error fetching economic data for {indicator}: {str(e)}"
                    )

        return result


class OrderBookDataSource(DataSource):
    """Order book data source for fetching Level 2 market data"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "order_book_data"
        self.api_key = api_key or os.getenv("BROKER_API_KEY")

    async def fetch_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch order book data for the given symbol

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with bid and ask data
        """
        # This would typically connect to a broker API that provides order book data
        # For now, we'll simulate the data

        # Simulate bid and ask data
        bid_prices = np.linspace(99.5, 100.0, 10)
        bid_sizes = np.random.randint(100, 1000, 10)

        ask_prices = np.linspace(100.1, 100.6, 10)
        ask_sizes = np.random.randint(100, 1000, 10)

        bids = [
            {"price": float(p), "size": int(s)} for p, s in zip(bid_prices, bid_sizes)
        ]
        asks = [
            {"price": float(p), "size": int(s)} for p, s in zip(ask_prices, ask_sizes)
        ]

        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "bids": bids,
            "asks": asks,
        }


class OpenBBDataProvider(DataSource):
    """
    OpenBB Platform data provider - Access 100+ financial data sources

    Phase 1 Enhancement: Unified access to multiple data providers including:
    - Alpha Vantage, Polygon.io, Intrinio, FRED, Quandl, IEX Cloud, and more

    Usage:
        provider = OpenBBDataProvider()
        stock_data = await provider.get_stock_data('AAPL')
        options_data = await provider.get_options_chain('AAPL')
        macro_data = await provider.get_macro_indicators()
    """

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize OpenBB data provider

        Args:
            credentials: Dictionary of API credentials for various providers
                        e.g., {'fmp_api_key': 'xxx', 'polygon_api_key': 'xxx'}
        """
        super().__init__()
        self.name = "openbb_data"
        self.available = OPENBB_AVAILABLE

        if not self.available:
            logger.warning("OpenBB not installed. Install with: pip install openbb")
            return

        # Configure credentials if provided
        if credentials:
            self._configure_credentials(credentials)

    def _configure_credentials(self, credentials: Dict[str, str]) -> None:
        """Configure OpenBB with API credentials"""
        if not self.available:
            return

        try:
            for key, value in credentials.items():
                setattr(obb.user.credentials, key, value)
            logger.info("OpenBB credentials configured successfully")
        except Exception as e:
            logger.error(f"Error configuring OpenBB credentials: {str(e)}")

    async def fetch_data(self, *args, **kwargs) -> Any:
        """Generic fetch method - delegates to specific methods"""
        raise NotImplementedError(
            "Use specific methods like get_stock_data, get_options_chain, etc."
        )

    async def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        provider: str = "yfinance",
    ) -> pd.DataFrame:
        """
        Get historical stock price data

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            provider: Data provider (yfinance, fmp, polygon, intrinio, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        if not self.available:
            logger.warning("OpenBB not available, falling back to yfinance")
            return await self._fallback_stock_data(symbol, start_date, end_date)

        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            result = obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
            )

            # Convert to DataFrame
            df = result.to_df()
            df.columns = [col.lower() for col in df.columns]
            return df

        except Exception as e:
            logger.error(f"OpenBB error fetching {symbol}: {str(e)}")
            return await self._fallback_stock_data(symbol, start_date, end_date)

    async def _fallback_stock_data(
        self, symbol: str, start_date: Optional[str], end_date: Optional[str]
    ) -> pd.DataFrame:
        """Fallback to yfinance if OpenBB fails"""
        try:
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            data.columns = [col.lower() for col in data.columns]
            return data
        except Exception as e:
            logger.error(f"Fallback yfinance error: {str(e)}")
            return pd.DataFrame()

    async def get_options_chain(
        self, symbol: str, provider: str = "intrinio"
    ) -> Dict[str, pd.DataFrame]:
        """
        Get options chain data

        Args:
            symbol: Stock ticker symbol
            provider: Data provider (intrinio, tradier, cboe, etc.)

        Returns:
            Dictionary with 'calls' and 'puts' DataFrames
        """
        if not self.available:
            logger.warning("OpenBB not available for options data")
            return {"calls": pd.DataFrame(), "puts": pd.DataFrame()}

        try:
            result = obb.derivatives.options.chains(symbol=symbol, provider=provider)
            df = result.to_df()

            # Split into calls and puts
            calls = (
                df[df["option_type"].str.lower() == "call"]
                if "option_type" in df.columns
                else df
            )
            puts = (
                df[df["option_type"].str.lower() == "put"]
                if "option_type" in df.columns
                else pd.DataFrame()
            )

            return {"calls": calls, "puts": puts}

        except Exception as e:
            logger.error(f"Error fetching options chain for {symbol}: {str(e)}")
            return {"calls": pd.DataFrame(), "puts": pd.DataFrame()}

    async def get_macro_indicators(
        self, indicators: List[str] = None, provider: str = "fred"
    ) -> Dict[str, pd.DataFrame]:
        """
        Get macroeconomic indicators

        Args:
            indicators: List of indicator codes (e.g., ['GDP', 'UNRATE', 'CPIAUCSL'])
            provider: Data provider (fred, oecd, etc.)

        Returns:
            Dictionary of indicator DataFrames
        """
        if not self.available:
            logger.warning("OpenBB not available for macro data")
            return {}

        if indicators is None:
            indicators = ["GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS", "DGS10"]

        results = {}
        for indicator in indicators:
            try:
                result = obb.economy.fred_series(symbol=indicator, provider=provider)
                results[indicator] = result.to_df()
            except Exception as e:
                logger.error(f"Error fetching {indicator}: {str(e)}")

        return results

    async def get_crypto_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        provider: str = "yfinance",
    ) -> pd.DataFrame:
        """
        Get cryptocurrency price data

        Args:
            symbol: Crypto symbol (e.g., 'BTC-USD', 'ETH-USD')
            start_date: Start date
            end_date: End date
            provider: Data provider

        Returns:
            DataFrame with OHLCV data
        """
        if not self.available:
            return await self._fallback_stock_data(symbol, start_date, end_date)

        try:
            result = obb.crypto.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
            )
            return result.to_df()
        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {str(e)}")
            return pd.DataFrame()

    async def get_forex_data(
        self,
        pair: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        provider: str = "yfinance",
    ) -> pd.DataFrame:
        """
        Get forex pair data

        Args:
            pair: Currency pair (e.g., 'EURUSD', 'GBPUSD')
            start_date: Start date
            end_date: End date
            provider: Data provider

        Returns:
            DataFrame with OHLCV data
        """
        if not self.available:
            # Convert to yfinance format (e.g., EURUSD -> EURUSD=X)
            yf_symbol = f"{pair}=X"
            return await self._fallback_stock_data(yf_symbol, start_date, end_date)

        try:
            result = obb.currency.price.historical(
                symbol=pair, start_date=start_date, end_date=end_date, provider=provider
            )
            return result.to_df()
        except Exception as e:
            logger.error(f"Error fetching forex data for {pair}: {str(e)}")
            return pd.DataFrame()

    async def get_company_fundamentals(
        self, symbol: str, provider: str = "fmp"
    ) -> Dict[str, Any]:
        """
        Get company fundamental data

        Args:
            symbol: Stock ticker symbol
            provider: Data provider (fmp, polygon, intrinio, etc.)

        Returns:
            Dictionary with fundamental data
        """
        if not self.available:
            logger.warning("OpenBB not available for fundamental data")
            return {}

        try:
            fundamentals = {}

            # Get various fundamental data
            try:
                income = obb.equity.fundamental.income(symbol=symbol, provider=provider)
                fundamentals["income_statement"] = income.to_df()
            except Exception:
                pass

            try:
                balance = obb.equity.fundamental.balance(
                    symbol=symbol, provider=provider
                )
                fundamentals["balance_sheet"] = balance.to_df()
            except Exception:
                pass

            try:
                cash = obb.equity.fundamental.cash(symbol=symbol, provider=provider)
                fundamentals["cash_flow"] = cash.to_df()
            except Exception:
                pass

            return fundamentals

        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {str(e)}")
            return {}

    async def get_earnings_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        provider: str = "fmp",
    ) -> pd.DataFrame:
        """
        Get earnings calendar

        Args:
            start_date: Start date
            end_date: End date
            provider: Data provider

        Returns:
            DataFrame with earnings calendar data
        """
        if not self.available:
            return pd.DataFrame()

        try:
            if not start_date:
                start_date = datetime.now().strftime("%Y-%m-%d")
            if not end_date:
                end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

            result = obb.equity.calendar.earnings(
                start_date=start_date, end_date=end_date, provider=provider
            )
            return result.to_df()
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {str(e)}")
            return pd.DataFrame()


# Factory to create the appropriate data source
def create_data_source(source_type: str, api_key: Optional[str] = None) -> DataSource:
    """
    Factory function to create a data source based on the type

    Args:
        source_type: Type of data source ('market', 'news', 'economic', 'order_book')
        api_key: API key for the data source

    Returns:
        DataSource instance
    """
    if source_type == "market":
        return MarketDataSource(api_key)
    elif source_type == "news":
        return NewsDataSource(api_key)
    elif source_type == "economic":
        return EconomicDataSource(api_key)
    elif source_type == "order_book":
        return OrderBookDataSource(api_key)
    elif source_type == "openbb":
        return OpenBBDataProvider()
    else:
        raise ValueError(f"Unsupported data source type: {source_type}")

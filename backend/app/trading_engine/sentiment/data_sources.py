"""
Data Sources module for the trading engine.
Implements connections to various data sources like market data, news, economic data, etc.
"""
import os
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from alpha_vantage.timeseries import TimeSeries
from newsapi import NewsApiClient
import aiohttp
import asyncio
import json
from dotenv import load_dotenv

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
        self.alpha_vantage = TimeSeries(key=self.api_key, output_format='pandas')
        
    async def fetch_data(
        self, 
        symbols: List[str], 
        interval: str = '1d', 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        source: str = 'yfinance'
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
        if source == 'yfinance':
            return await self._fetch_from_yfinance(symbols, interval, start_date, end_date)
        elif source == 'alpha_vantage':
            return await self._fetch_from_alpha_vantage(symbols, interval)
        else:
            raise ValueError(f"Unsupported data source: {source}")
    
    async def _fetch_from_yfinance(
        self, 
        symbols: List[str], 
        interval: str = '1d', 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data from Yahoo Finance"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        result = {}
        for symbol in symbols:
            try:
                data = yf.download(
                    symbol, 
                    start=start_date, 
                    end=end_date, 
                    interval=interval,
                    progress=False
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
        self, 
        symbols: List[str], 
        interval: str = 'daily'
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data from Alpha Vantage"""
        result = {}
        
        alpha_intervals = {
            '1m': 'TIME_SERIES_INTRADAY', 
            '5m': 'TIME_SERIES_INTRADAY',
            '15m': 'TIME_SERIES_INTRADAY',
            '30m': 'TIME_SERIES_INTRADAY',
            '1h': 'TIME_SERIES_INTRADAY',
            'daily': 'TIME_SERIES_DAILY_ADJUSTED',
            'weekly': 'TIME_SERIES_WEEKLY',
            'monthly': 'TIME_SERIES_MONTHLY'
        }
        
        # Map interval to Alpha Vantage format
        av_interval = interval
        if interval in ['1m', '5m', '15m', '30m', '1h']:
            interval_map = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '1h': '60min'}
            av_interval = interval_map.get(interval, '5min')
        
        for symbol in symbols:
            try:
                if 'min' in av_interval:
                    data, meta_data = self.alpha_vantage.get_intraday(
                        symbol=symbol, 
                        interval=av_interval, 
                        outputsize='full'
                    )
                elif interval == 'daily':
                    data, meta_data = self.alpha_vantage.get_daily_adjusted(
                        symbol=symbol, 
                        outputsize='full'
                    )
                elif interval == 'weekly':
                    data, meta_data = self.alpha_vantage.get_weekly_adjusted(symbol=symbol)
                elif interval == 'monthly':
                    data, meta_data = self.alpha_vantage.get_monthly_adjusted(symbol=symbol)
                
                # Standardize column names
                data.columns = [col.lower() for col in data.columns]
                result[symbol] = data
                
                # Alpha Vantage has rate limits, so we need to wait
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
        
        return result


class NewsDataSource(DataSource):
    """News data source for fetching financial news and sentiment"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "news_data"
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.news_api = NewsApiClient(api_key=self.api_key)
        
    async def fetch_data(
        self, 
        symbols: List[str] = None, 
        keywords: List[str] = None,
        days_back: int = 7
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
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            news = self.news_api.get_everything(
                q=query,
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='relevancy',
                page_size=100
            )
            
            if 'articles' in news and news['articles']:
                df = pd.DataFrame(news['articles'])
                # Convert publishedAt to datetime
                df['publishedAt'] = pd.to_datetime(df['publishedAt'])
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
        end_date: Optional[str] = None
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
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        result = {}
        
        async with aiohttp.ClientSession() as session:
            for indicator in indicators:
                try:
                    params = {
                        'series_id': indicator,
                        'api_key': self.api_key,
                        'file_type': 'json',
                        'observation_start': start_date,
                        'observation_end': end_date
                    }
                    
                    async with session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'observations' in data:
                                df = pd.DataFrame(data['observations'])
                                df['date'] = pd.to_datetime(df['date'])
                                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                                df = df.set_index('date')
                                result[indicator] = df
                            else:
                                logger.warning(f"No data returned for indicator {indicator}")
                        else:
                            logger.error(f"Error fetching data for {indicator}: {response.status}")
                            
                except Exception as e:
                    logger.error(f"Error fetching economic data for {indicator}: {str(e)}")
        
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
        
        bids = [{"price": float(p), "size": int(s)} for p, s in zip(bid_prices, bid_sizes)]
        asks = [{"price": float(p), "size": int(s)} for p, s in zip(ask_prices, ask_sizes)]
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "bids": bids,
            "asks": asks
        }


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
    if source_type == 'market':
        return MarketDataSource(api_key)
    elif source_type == 'news':
        return NewsDataSource(api_key)
    elif source_type == 'economic':
        return EconomicDataSource(api_key)
    elif source_type == 'order_book':
        return OrderBookDataSource(api_key)
    else:
        raise ValueError(f"Unsupported data source type: {source_type}")
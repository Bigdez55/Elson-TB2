"""
Alpha Vantage API client.

This module provides the Alpha Vantage API client implementation for
retrieving stock data, technical indicators, and other financial information.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from app.services.external_api.base import BaseApiClient, ApiError

logger = logging.getLogger(__name__)


class AlphaVantageClient(BaseApiClient):
    """Alpha Vantage API client implementation."""
    
    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return "https://www.alphavantage.co/query"
    
    @property
    def provider_name(self) -> str:
        """Get the name of the API provider."""
        return "alpha_vantage"
    
    def _add_auth(self, request_kwargs: Dict[str, Any]) -> None:
        """Add API key to request as a query parameter."""
        params = request_kwargs.get("params", {}) or {}
        params["apikey"] = self.api_key
        request_kwargs["params"] = params
    
    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Stock quote data
            
        Raises:
            ApiError: If the request fails
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        
        response = await self.get("", params=params)
        
        # Check for error responses
        if "Error Message" in response:
            raise ApiError(response["Error Message"])
        
        if "Global Quote" not in response or not response["Global Quote"]:
            raise ApiError(f"No quote data found for symbol: {symbol}")
        
        # Normalize data
        quote_data = response["Global Quote"]
        
        return {
            "symbol": quote_data.get("01. symbol", symbol),
            "price": float(quote_data.get("05. price", 0)),
            "open": float(quote_data.get("02. open", 0)),
            "high": float(quote_data.get("03. high", 0)),
            "low": float(quote_data.get("04. low", 0)),
            "volume": int(float(quote_data.get("06. volume", 0))),
            "latest_trading_day": quote_data.get("07. latest trading day"),
            "previous_close": float(quote_data.get("08. previous close", 0)),
            "change": float(quote_data.get("09. change", 0)),
            "change_percent": quote_data.get("10. change percent", "0%").rstrip("%"),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        interval: str = "daily"
    ) -> Dict[str, Any]:
        """Get historical price data.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (daily, weekly, monthly)
            
        Returns:
            Historical price data
            
        Raises:
            ApiError: If the request fails
        """
        # Map interval to Alpha Vantage function
        function_map = {
            "daily": "TIME_SERIES_DAILY",
            "weekly": "TIME_SERIES_WEEKLY",
            "monthly": "TIME_SERIES_MONTHLY",
            "intraday": "TIME_SERIES_INTRADAY"
        }
        
        function = function_map.get(interval.lower(), "TIME_SERIES_DAILY")
        
        # Add outputsize parameter for daily data
        params = {
            "function": function,
            "symbol": symbol
        }
        
        if function == "TIME_SERIES_DAILY":
            params["outputsize"] = "full"
            
        if function == "TIME_SERIES_INTRADAY":
            params["interval"] = "5min"
        
        response = await self.get("", params=params)
        
        # Check for error responses
        if "Error Message" in response:
            raise ApiError(response["Error Message"])
            
        # Determine the time series key
        time_series_key = None
        for key in response:
            if "Time Series" in key:
                time_series_key = key
                break
                
        if not time_series_key or time_series_key not in response:
            raise ApiError(f"No historical data found for symbol: {symbol}")
            
        # Get the time series data
        time_series = response[time_series_key]
        
        # Filter by date range if provided
        if start_date or end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.min
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
            
            filtered_data = {}
            for date_str, values in time_series.items():
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if start <= date <= end:
                    filtered_data[date_str] = values
            
            time_series = filtered_data
        
        # Normalize data
        normalized_data = []
        for date_str, values in time_series.items():
            data_point = {
                "date": date_str,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": int(float(values.get("5. volume", 0)))
            }
            normalized_data.append(data_point)
        
        # Sort by date
        normalized_data.sort(key=lambda x: x["date"])
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data": normalized_data
        }
    
    async def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close"
    ) -> Dict[str, Any]:
        """Get technical indicator data.
        
        Args:
            symbol: Stock ticker symbol
            indicator: Indicator function (e.g., SMA, EMA, RSI)
            interval: Data interval (daily, weekly, monthly)
            time_period: Number of data points for calculation
            series_type: Price series to use (close, open, high, low)
            
        Returns:
            Technical indicator data
            
        Raises:
            ApiError: If the request fails
        """
        params = {
            "function": indicator,
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type
        }
        
        response = await self.get("", params=params)
        
        # Check for error responses
        if "Error Message" in response:
            raise ApiError(response["Error Message"])
            
        # Determine the indicator data key
        technical_key = None
        for key in response:
            if "Technical Analysis" in key:
                technical_key = key
                break
                
        if not technical_key or technical_key not in response:
            raise ApiError(f"No indicator data found for symbol: {symbol}")
            
        # Get the indicator data
        indicator_data = response[technical_key]
        
        # Normalize data
        normalized_data = []
        for date_str, values in indicator_data.items():
            data_point = {
                "date": date_str,
            }
            
            # Add all indicator values
            for key, value in values.items():
                # Extract the indicator name from the key
                indicator_name = key.split(":")[0] if ":" in key else key
                data_point[indicator_name.lower()] = float(value)
                
            normalized_data.append(data_point)
        
        # Sort by date
        normalized_data.sort(key=lambda x: x["date"])
        
        return {
            "symbol": symbol,
            "indicator": indicator,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type,
            "data": normalized_data
        }
    
    async def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """Get company overview information.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company overview data
            
        Raises:
            ApiError: If the request fails
        """
        params = {
            "function": "OVERVIEW",
            "symbol": symbol
        }
        
        response = await self.get("", params=params)
        
        # Check for error responses
        if "Error Message" in response:
            raise ApiError(response["Error Message"])
            
        if not response or "Symbol" not in response:
            raise ApiError(f"No company data found for symbol: {symbol}")
            
        # Return the data as is (already in a good format)
        return response
        
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile information.
        
        This method is an alias for get_company_overview to maintain
        compatibility with the expected interface in integration.py.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company profile data formatted in a standardized structure
            
        Raises:
            ApiError: If the request fails
        """
        # Get overview data
        overview = await self.get_company_overview(symbol)
        
        # Format the data into a standardized profile structure
        # This ensures consistent format regardless of the data provider
        profile = {
            "symbol": overview.get("Symbol"),
            "name": overview.get("Name"),
            "description": overview.get("Description"),
            "exchange": overview.get("Exchange"),
            "sector": overview.get("Sector"),
            "industry": overview.get("Industry"),
            "market_cap": float(overview.get("MarketCapitalization", 0)),
            "pe_ratio": float(overview.get("PERatio", 0)) if overview.get("PERatio") else None,
            "dividend_yield": float(overview.get("DividendYield", 0)) if overview.get("DividendYield") else None,
            "dividend_per_share": float(overview.get("DividendPerShare", 0)) if overview.get("DividendPerShare") else None,
            "beta": float(overview.get("Beta", 0)) if overview.get("Beta") else None,
            "52_week_high": float(overview.get("52WeekHigh", 0)) if overview.get("52WeekHigh") else None,
            "52_week_low": float(overview.get("52WeekLow", 0)) if overview.get("52WeekLow") else None,
            "50_day_moving_avg": float(overview.get("50DayMovingAverage", 0)) if overview.get("50DayMovingAverage") else None,
            "200_day_moving_avg": float(overview.get("200DayMovingAverage", 0)) if overview.get("200DayMovingAverage") else None,
            "country": overview.get("Country"),
            "employees": int(overview.get("FullTimeEmployees", 0)) if overview.get("FullTimeEmployees") else None,
            "ceo": overview.get("CEO"),
            "website": overview.get("Website"),
            "fiscal_year_end": overview.get("FiscalYearEnd"),
            "latest_quarter": overview.get("LatestQuarter"),
            # Add provider info for metrics tracking
            "provider": self.provider_name
        }
        
        return profile
    
    async def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """Search for symbols matching keywords.
        
        Args:
            keywords: Search keywords
            
        Returns:
            Symbol search results
            
        Raises:
            ApiError: If the request fails
        """
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords
        }
        
        response = await self.get("", params=params)
        
        # Check for error responses
        if "Error Message" in response:
            raise ApiError(response["Error Message"])
            
        if "bestMatches" not in response:
            raise ApiError(f"No search results found for: {keywords}")
            
        # Get the search results
        matches = response["bestMatches"]
        
        # Normalize data
        normalized_matches = []
        for match in matches:
            normalized_match = {
                "symbol": match.get("1. symbol"),
                "name": match.get("2. name"),
                "type": match.get("3. type"),
                "region": match.get("4. region"),
                "market_open": match.get("5. marketOpen"),
                "market_close": match.get("6. marketClose"),
                "timezone": match.get("7. timezone"),
                "currency": match.get("8. currency"),
                "match_score": float(match.get("9. matchScore", 0))
            }
            normalized_matches.append(normalized_match)
        
        return {
            "keywords": keywords,
            "matches": normalized_matches
        }
    
    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data.
        
        Returns:
            Sector performance data
            
        Raises:
            ApiError: If the request fails
        """
        params = {
            "function": "SECTOR"
        }
        
        response = await self.get("", params=params)
        
        # Check for error responses
        if "Error Message" in response:
            raise ApiError(response["Error Message"])
            
        if not response or len(response) == 0:
            raise ApiError("No sector performance data available")
            
        # Extract metadata and performance information
        metadata = response.get("Meta Data", {})
        
        # Get the sector data for different time ranges
        ranges = [
            "Rank A: Real-Time Performance",
            "Rank B: 1 Day Performance",
            "Rank C: 5 Day Performance",
            "Rank D: 1 Month Performance",
            "Rank E: 3 Month Performance",
            "Rank F: Year-to-Date (YTD) Performance",
            "Rank G: 1 Year Performance",
            "Rank H: 3 Year Performance",
            "Rank I: 5 Year Performance",
            "Rank J: 10 Year Performance"
        ]
        
        # Normalize data
        normalized_data = {
            "last_updated": metadata.get("Last Refreshed", ""),
            "ranges": {}
        }
        
        for time_range in ranges:
            if time_range in response:
                range_key = time_range.split(":")[1].strip().lower().replace(" ", "_")
                range_data = {}
                
                for sector, performance in response[time_range].items():
                    # Remove percentage sign and convert to float
                    performance_value = float(performance.rstrip("%"))
                    range_data[sector] = performance_value
                
                normalized_data["ranges"][range_key] = range_data
        
        return normalized_data
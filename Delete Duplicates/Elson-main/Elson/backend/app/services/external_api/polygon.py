"""
Polygon.io API client.

This module provides the Polygon.io API client implementation for
retrieving stock data, reference data, and other market information.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from app.services.external_api.base import BaseApiClient, ApiError

logger = logging.getLogger(__name__)


class PolygonClient(BaseApiClient):
    """Polygon.io API client implementation."""
    
    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return "https://api.polygon.io"
    
    @property
    def provider_name(self) -> str:
        """Get the name of the API provider."""
        return "polygon"
    
    def _add_auth(self, request_kwargs: Dict[str, Any]) -> None:
        """Add API key to request as a query parameter."""
        params = request_kwargs.get("params", {}) or {}
        params["apiKey"] = self.api_key
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
        response = await self.get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
        
        # Check for error responses
        if not response or "status" in response and response["status"] != "OK":
            error_msg = response.get("error", f"No quote data found for symbol: {symbol}")
            raise ApiError(error_msg)
        
        # Extract ticker data
        ticker = response.get("ticker", {})
        day = ticker.get("day", {})
        prev_day = ticker.get("prevDay", {})
        quote = ticker.get("lastQuote", {})
        trade = ticker.get("lastTrade", {})
        
        # Normalize data
        return {
            "symbol": symbol,
            "price": trade.get("p", 0),  # Last trade price
            "open": day.get("o", 0),     # Open price
            "high": day.get("h", 0),     # High price
            "low": day.get("l", 0),      # Low price
            "volume": day.get("v", 0),   # Volume
            "previous_close": prev_day.get("c", 0),  # Previous close
            "change": trade.get("p", 0) - prev_day.get("c", 0) if trade.get("p") and prev_day.get("c") else 0,
            "change_percent": ((trade.get("p", 0) - prev_day.get("c", 0)) / prev_day.get("c", 1)) * 100 if trade.get("p") and prev_day.get("c") and prev_day.get("c") != 0 else 0,
            "bid": quote.get("b", 0),   # Bid price
            "ask": quote.get("a", 0),   # Ask price
            "bid_size": quote.get("bs", 0),  # Bid size
            "ask_size": quote.get("as", 0),  # Ask size
            "timestamp": datetime.fromtimestamp(quote.get("t", 0) / 1000).isoformat() if quote.get("t") else datetime.now().isoformat()
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
        # Convert dates to required format
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Map interval to Polygon timespan
        if interval.lower() == "daily":
            timespan = "day"
        elif interval.lower() == "weekly":
            timespan = "week"
        elif interval.lower() == "monthly":
            timespan = "month"
        else:
            timespan = "day"
        
        # Make the API request
        response = await self.get(f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{start_date}/{end_date}")
        
        # Check for error responses
        if not response or "status" in response and response["status"] != "OK":
            error_msg = response.get("error", f"No historical data found for symbol: {symbol}")
            raise ApiError(error_msg)
            
        # Extract results array
        results = response.get("results", [])
        
        if not results:
            raise ApiError(f"No historical data found for symbol: {symbol}")
        
        # Normalize data
        normalized_data = []
        for result in results:
            timestamp = result.get("t")  # Timestamp in milliseconds
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d") if timestamp else None
            
            if not date_str:
                continue
                
            data_point = {
                "date": date_str,
                "open": result.get("o", 0),
                "high": result.get("h", 0),
                "low": result.get("l", 0),
                "close": result.get("c", 0),
                "volume": result.get("v", 0),
                "vwap": result.get("vw", 0)  # Volume-weighted average price
            }
            normalized_data.append(data_point)
        
        # Sort by date
        normalized_data.sort(key=lambda x: x["date"])
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data": normalized_data
        }
    
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile information.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Company profile data
            
        Raises:
            ApiError: If the request fails
        """
        # Polygon.io has separate endpoints for different pieces of company information
        # We'll need to make multiple requests to build a complete profile
        
        # First, get ticker details
        ticker_details = await self.get(f"/v3/reference/tickers/{symbol}")
        
        if not ticker_details or "status" in ticker_details and ticker_details["status"] != "OK":
            error_msg = ticker_details.get("error", f"No company data found for symbol: {symbol}")
            raise ApiError(error_msg)
            
        # Extract the results from the response
        ticker_data = ticker_details.get("results", {})
        
        if not ticker_data:
            raise ApiError(f"No company data found for symbol: {symbol}")
            
        # Now get financials
        try:
            financials = await self.get(f"/v2/reference/financials/{symbol}")
            financial_data = financials.get("results", [{}])[0] if financials.get("results") else {}
        except Exception as e:
            logger.warning(f"Error fetching financials for {symbol}: {e}")
            financial_data = {}
        
        # Format the data into a standardized profile structure
        profile = {
            "symbol": ticker_data.get("ticker"),
            "name": ticker_data.get("name"),
            "description": ticker_data.get("description"),
            "exchange": ticker_data.get("primary_exchange"),
            "sector": ticker_data.get("sic_description"),
            "industry": ticker_data.get("sic_description"),
            "market_cap": ticker_data.get("market_cap"),
            "employee_count": ticker_data.get("total_employees"),
            "website": ticker_data.get("homepage_url"),
            "logo": ticker_data.get("branding", {}).get("logo_url"),
            "country": ticker_data.get("locale"),
            "headquarters": ", ".join(filter(None, [
                ticker_data.get("address", {}).get("city"),
                ticker_data.get("address", {}).get("state")
            ])) or None,
            "ceo": None,  # Not provided by Polygon
            "listed_exchange": ticker_data.get("primary_exchange"),
            "type": ticker_data.get("type"),
            "currency": ticker_data.get("currency_name"),
            "outstanding_shares": ticker_data.get("share_class_shares_outstanding"),
            "pe_ratio": financial_data.get("ratios", {}).get("pe") if financial_data.get("ratios") else None,
            "dividend_yield": None,  # Would need another request to a dividends endpoint
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
        response = await self.get(f"/v3/reference/tickers", params={
            "search": keywords,
            "active": True,
            "sort": "ticker",
            "order": "asc",
            "limit": 10
        })
        
        # Check for error responses
        if not response or "status" in response and response["status"] != "OK":
            error_msg = response.get("error", f"No search results found for: {keywords}")
            raise ApiError(error_msg)
            
        # Extract results
        results = response.get("results", [])
        
        if not results:
            raise ApiError(f"No search results found for: {keywords}")
        
        # Normalize data
        normalized_matches = []
        for result in results:
            normalized_match = {
                "symbol": result.get("ticker"),
                "name": result.get("name"),
                "type": result.get("type"),
                "market": result.get("market"),
                "exchange": result.get("primary_exchange"),
                "currency": result.get("currency_name"),
                "locale": result.get("locale")
            }
            normalized_matches.append(normalized_match)
        
        return {
            "keywords": keywords,
            "matches": normalized_matches
        }
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status.
        
        Returns:
            Market status information
            
        Raises:
            ApiError: If the request fails
        """
        response = await self.get("/v1/marketstatus/now")
        
        # Check for error responses
        if not response or "status" in response and response["status"] != "OK":
            error_msg = response.get("error", "Unable to get market status")
            raise ApiError(error_msg)
            
        # Format the response
        return {
            "market": response.get("market", "unknown"),
            "early_hours": response.get("earlyHours", False),
            "after_hours": response.get("afterHours", False),
            "trading_day": response.get("tradingDay", False),
            "exchanges": response.get("exchanges", {}),
            "provider": self.provider_name
        }
"""
Coinbase API client.

This module provides the Coinbase API client implementation for
retrieving cryptocurrency prices and related information.
"""

import logging
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from app.services.external_api.base import BaseApiClient, ApiError

logger = logging.getLogger(__name__)


class CoinbaseClient(BaseApiClient):
    """Coinbase API client implementation."""
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, **kwargs):
        """Initialize with API key and secret.
        
        Args:
            api_key: The API key for authentication
            api_secret: The API secret for authentication
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.api_secret = api_secret
    
    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return "https://api.coinbase.com/v2"
    
    @property
    def provider_name(self) -> str:
        """Get the name of the API provider."""
        return "coinbase"
    
    def _add_auth(self, request_kwargs: Dict[str, Any]) -> None:
        """Add authentication headers to the request.
        
        For authenticated requests, this adds the required headers.
        For public endpoints, it does nothing.
        """
        # Check if we're using an authenticated endpoint
        url = request_kwargs.get("url", "")
        method = request_kwargs.get("method", "GET")
        
        if not self.api_secret or "/public/" in url:
            # Public endpoint or no secret available
            return
            
        # Authenticated request - add required headers
        timestamp = str(int(time.time()))
        body = request_kwargs.get("data", "") or ""
        
        # Create the message to sign
        message = f"{timestamp}{method}{url}{body}"
        
        # Create the signature
        signature = hmac.new(
            key=self.api_secret.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Set headers
        headers = request_kwargs.get("headers", {}) or {}
        headers.update({
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-VERSION": "2021-04-29"  # API version
        })
        
        request_kwargs["headers"] = headers
    
    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time crypto quote.
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            
        Returns:
            Crypto quote data
            
        Raises:
            ApiError: If the request fails
        """
        # Coinbase uses currency pairs, commonly with USD
        # Convert simple symbols to currency pairs
        if "-" not in symbol:
            symbol = f"{symbol}-USD"
            
        response = await self.get(f"/prices/{symbol}/spot")
        
        # Check for error responses
        if "errors" in response:
            errors = response.get("errors", [])
            error_msg = errors[0].get("message") if errors else f"No quote data found for symbol: {symbol}"
            raise ApiError(error_msg)
            
        # Extract data from response
        data = response.get("data", {})
        
        if not data:
            raise ApiError(f"No quote data found for symbol: {symbol}")
            
        # Normalize data to common format
        # Note: Coinbase spot endpoint provides limited data
        base_symbol = symbol.split("-")[0] if "-" in symbol else symbol
        
        return {
            "symbol": base_symbol,
            "price": float(data.get("amount", 0)),
            "currency": data.get("currency", "USD"),
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
        
        Note: Coinbase API doesn't provide historical candles directly.
        This method uses the Pro API which has more features.
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (daily, hourly)
            
        Returns:
            Historical price data
            
        Raises:
            ApiError: If the request fails
        """
        # For historical data, we need to use the Coinbase Pro API
        pro_base_url = "https://api.exchange.coinbase.com"
        
        # Convert simple symbols to currency pairs
        if "-" not in symbol:
            symbol = f"{symbol}-USD"
            
        # Convert interval to granularity (in seconds)
        granularity_map = {
            "daily": 86400,     # 1 day
            "hourly": 3600,     # 1 hour
            "minute": 60        # 1 minute
        }
        
        granularity = granularity_map.get(interval.lower(), 86400)
        
        # Convert dates to ISO format for API
        if not start_date:
            start = datetime.now() - timedelta(days=30)
        else:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            
        if not end_date:
            end = datetime.now()
        else:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
        # Format dates as ISO strings
        start_iso = start.isoformat()
        end_iso = end.isoformat()
        
        # Build request URL with parameters
        url = f"{pro_base_url}/products/{symbol}/candles"
        params = {
            "start": start_iso,
            "end": end_iso,
            "granularity": granularity
        }
        
        # Make the request directly (not using self.get since it's a different base URL)
        response = await self.get(
            url=url,
            params=params,
            _bypass_base_url=True  # Flag to bypass base URL
        )
        
        # Check for error responses
        if isinstance(response, dict) and "message" in response:
            raise ApiError(response.get("message", f"No historical data found for symbol: {symbol}"))
            
        # The response is an array of arrays:
        # [timestamp, low, high, open, close, volume]
        if not response or not isinstance(response, list):
            raise ApiError(f"No historical data found for symbol: {symbol}")
            
        # Normalize data
        normalized_data = []
        for candle in response:
            if len(candle) < 6:
                continue
                
            timestamp, low, high, open_price, close, volume = candle
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            
            data_point = {
                "date": date_str,
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume)
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
        """Get crypto asset profile information.
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            
        Returns:
            Crypto asset profile data
            
        Raises:
            ApiError: If the request fails
        """
        # Extract the base asset if it's a pair
        base_symbol = symbol.split("-")[0] if "-" in symbol else symbol
        
        # Get asset data
        response = await self.get(f"/assets/{base_symbol}")
        
        # Check for error responses
        if "errors" in response:
            errors = response.get("errors", [])
            error_msg = errors[0].get("message") if errors else f"No asset data found for symbol: {base_symbol}"
            raise ApiError(error_msg)
            
        # Extract data from response
        data = response.get("data", {})
        
        if not data:
            raise ApiError(f"No asset data found for symbol: {base_symbol}")
            
        # Format the data into a standardized profile structure
        profile = {
            "symbol": data.get("symbol"),
            "name": data.get("name"),
            "description": data.get("description", ""),
            "asset_type": "cryptocurrency",
            "website": data.get("website"),
            "white_paper": data.get("white_paper"),
            "links": data.get("links", {}),
            # Format price data from spot price
            "price": None,  # We'll add this next
            "change": None,
            "change_percent": None,
            # Additional cryptocurrency-specific fields
            "market_cap": None,
            "circulating_supply": None,
            "max_supply": None,
            # Add provider info for metrics tracking
            "provider": self.provider_name
        }
        
        # Get current price to add to profile
        try:
            quote = await self.get_stock_quote(symbol)
            profile["price"] = quote.get("price")
        except Exception as e:
            logger.warning(f"Error fetching price for {symbol}: {e}")
        
        return profile
    
    async def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """Search for crypto assets matching keywords.
        
        Args:
            keywords: Search keywords
            
        Returns:
            Symbol search results
            
        Raises:
            ApiError: If the request fails
        """
        # Coinbase doesn't have a direct search endpoint, so we'll get all assets
        # and filter them based on the keywords
        response = await self.get("/currencies")
        
        # Check for error responses
        if "errors" in response:
            errors = response.get("errors", [])
            error_msg = errors[0].get("message") if errors else "Failed to search currencies"
            raise ApiError(error_msg)
            
        # Extract data from response
        data = response.get("data", [])
        
        if not data:
            raise ApiError("No currencies available")
            
        # Filter based on keywords
        keywords_lower = keywords.lower()
        filtered_results = []
        
        for currency in data:
            name = currency.get("name", "").lower()
            symbol = currency.get("code", "").lower()
            
            if keywords_lower in name or keywords_lower in symbol:
                filtered_results.append(currency)
                
        if not filtered_results:
            raise ApiError(f"No search results found for: {keywords}")
            
        # Normalize data
        normalized_matches = []
        for result in filtered_results:
            normalized_match = {
                "symbol": result.get("code"),
                "name": result.get("name"),
                "type": "cryptocurrency",
                "currency": "USD"  # Default trading pair currency
            }
            normalized_matches.append(normalized_match)
            
        return {
            "keywords": keywords,
            "matches": normalized_matches
        }
    
    async def get_exchange_rates(self, base_currency: str = "USD") -> Dict[str, Any]:
        """Get current exchange rates.
        
        Args:
            base_currency: Base currency for rates
            
        Returns:
            Exchange rate data
            
        Raises:
            ApiError: If the request fails
        """
        response = await self.get(f"/exchange-rates?currency={base_currency}")
        
        # Check for error responses
        if "errors" in response:
            errors = response.get("errors", [])
            error_msg = errors[0].get("message") if errors else f"Failed to get exchange rates for {base_currency}"
            raise ApiError(error_msg)
            
        # Extract data from response
        data = response.get("data", {})
        
        if not data or "rates" not in data:
            raise ApiError(f"No exchange rate data available for {base_currency}")
            
        return {
            "base": data.get("currency"),
            "rates": data.get("rates", {}),
            "provider": self.provider_name
        }
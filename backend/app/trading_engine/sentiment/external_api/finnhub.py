"""
Finnhub API client.

This module provides the Finnhub API client implementation for
retrieving stock data, company information, and other financial data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.services.external_api.base import ApiError, BaseApiClient

logger = logging.getLogger(__name__)


class FinnhubClient(BaseApiClient):
    """Finnhub API client implementation."""

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return "https://finnhub.io/api/v1"

    @property
    def provider_name(self) -> str:
        """Get the name of the API provider."""
        return "finnhub"

    def _add_auth(self, request_kwargs: Dict[str, Any]) -> None:
        """Add API key to request as a query parameter."""
        params = request_kwargs.get("params", {}) or {}
        params["token"] = self.api_key
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
        response = await self.get(f"/quote", params={"symbol": symbol})

        # Check for error responses
        if "error" in response:
            raise ApiError(response.get("error", "Unknown Finnhub API error"))

        # Normalize data to common format
        return {
            "symbol": symbol,
            "price": response.get("c", 0),  # Current price
            "open": response.get("o", 0),  # Open price
            "high": response.get("h", 0),  # High price
            "low": response.get("l", 0),  # Low price
            "previous_close": response.get("pc", 0),  # Previous close
            "change": response.get("c", 0) - response.get("pc", 0),  # Change
            "change_percent": (
                (response.get("c", 0) - response.get("pc", 0)) / response.get("pc", 1)
            )
            * 100
            if response.get("pc", 0)
            else 0,
            "timestamp": datetime.fromtimestamp(response.get("t", 0)).isoformat()
            if response.get("t", 0)
            else datetime.now().isoformat(),
        }

    async def get_historical_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        interval: str = "daily",
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
        # Convert dates to timestamps
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

        # Map interval to Finnhub resolution
        resolution_map = {
            "daily": "D",
            "weekly": "W",
            "monthly": "M",
            "intraday": "60",  # 60 minutes
        }

        resolution = resolution_map.get(interval.lower(), "D")

        # Make the API request
        response = await self.get(
            "/stock/candle",
            params={
                "symbol": symbol,
                "resolution": resolution,
                "from": start_ts,
                "to": end_ts,
            },
        )

        # Check for error response
        if response.get("s") == "no_data":
            raise ApiError(f"No historical data found for symbol: {symbol}")

        if "error" in response:
            raise ApiError(response.get("error", "Unknown Finnhub API error"))

        # Extract data arrays
        timestamps = response.get("t", [])
        opens = response.get("o", [])
        highs = response.get("h", [])
        lows = response.get("l", [])
        closes = response.get("c", [])
        volumes = response.get("v", [])

        # Normalize data
        normalized_data = []
        for i in range(len(timestamps)):
            if (
                i < len(opens)
                and i < len(highs)
                and i < len(lows)
                and i < len(closes)
                and i < len(volumes)
            ):
                date_str = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                data_point = {
                    "date": date_str,
                    "open": opens[i],
                    "high": highs[i],
                    "low": lows[i],
                    "close": closes[i],
                    "volume": volumes[i],
                }
                normalized_data.append(data_point)

        # Sort by date
        normalized_data.sort(key=lambda x: x["date"])

        return {"symbol": symbol, "interval": interval, "data": normalized_data}

    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile information.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Company profile data

        Raises:
            ApiError: If the request fails
        """
        response = await self.get("/stock/profile2", params={"symbol": symbol})

        # Check for error responses
        if not response or "error" in response:
            raise ApiError(
                response.get("error", f"No company data found for symbol: {symbol}")
            )

        # Format the data into a standardized profile structure
        profile = {
            "symbol": response.get("ticker"),
            "name": response.get("name"),
            "description": response.get("finnhubIndustry"),
            "exchange": response.get("exchange"),
            "industry": response.get("finnhubIndustry"),
            "market_cap": float(response.get("marketCapitalization", 0)) * 1000000
            if response.get("marketCapitalization")
            else 0,
            "outstanding_shares": response.get("shareOutstanding", 0),
            "phone": response.get("phone"),
            "country": response.get("country"),
            "employees": None,  # Not provided by Finnhub in this endpoint
            "ceo": None,  # Not provided by Finnhub in this endpoint
            "website": response.get("weburl"),
            "ipo_date": response.get("ipo"),
            "logo": response.get("logo"),
            # Add provider info for metrics tracking
            "provider": self.provider_name,
        }

        return profile

    async def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "daily",
        time_period: int = 14,
    ) -> Dict[str, Any]:
        """Get technical indicator data.

        Args:
            symbol: Stock ticker symbol
            indicator: Indicator function (e.g., RSI, MACD)
            interval: Data interval (daily, weekly, monthly)
            time_period: Number of data points for calculation

        Returns:
            Technical indicator data

        Raises:
            ApiError: If the request fails
        """
        # Convert interval to Finnhub resolution
        resolution_map = {
            "daily": "D",
            "weekly": "W",
            "monthly": "M",
            "intraday": "60",  # 60 minutes
        }

        resolution = resolution_map.get(interval.lower(), "D")

        # Calculate timestamps (30 days by default)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        # Make the API request
        response = await self.get(
            "/indicator",
            params={
                "symbol": symbol,
                "resolution": resolution,
                "from": start_ts,
                "to": end_ts,
                "indicator": indicator,
                "timeperiod": time_period,
            },
        )

        # Check for error response
        if response.get("s") == "no_data":
            raise ApiError(f"No indicator data found for symbol: {symbol}")

        if "error" in response:
            raise ApiError(response.get("error", "Unknown Finnhub API error"))

        # Extract data
        timestamps = response.get("t", [])
        values = response.get("result", [])

        # Normalize data
        normalized_data = []
        for i in range(len(timestamps)):
            if i < len(values):
                date_str = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                data_point = {"date": date_str, indicator.lower(): values[i]}
                normalized_data.append(data_point)

        # Sort by date
        normalized_data.sort(key=lambda x: x["date"])

        return {
            "symbol": symbol,
            "indicator": indicator,
            "interval": interval,
            "time_period": time_period,
            "data": normalized_data,
        }

    async def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """Search for symbols matching keywords.

        Args:
            keywords: Search keywords

        Returns:
            Symbol search results

        Raises:
            ApiError: If the request fails
        """
        response = await self.get("/search", params={"q": keywords})

        # Check for error responses
        if "error" in response:
            raise ApiError(response.get("error", "Unknown Finnhub API error"))

        if "result" not in response or not response["result"]:
            raise ApiError(f"No search results found for: {keywords}")

        # Get the search results
        matches = response["result"]

        # Normalize data
        normalized_matches = []
        for match in matches:
            normalized_match = {
                "symbol": match.get("symbol"),
                "name": match.get("description"),
                "type": match.get("type"),
                "currency": None,  # Not provided in this endpoint
                "match_score": None,  # Not provided in this endpoint
            }
            normalized_matches.append(normalized_match)

        return {"keywords": keywords, "matches": normalized_matches}

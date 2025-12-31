"""
Financial Modeling Prep (FMP) API client.

This module provides the Financial Modeling Prep API client implementation for
retrieving stock data, financial statements, and other company information.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.services.external_api.base import ApiError, BaseApiClient

logger = logging.getLogger(__name__)


class FMPClient(BaseApiClient):
    """Financial Modeling Prep API client implementation."""

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return "https://financialmodelingprep.com/api/v3"

    @property
    def provider_name(self) -> str:
        """Get the name of the API provider."""
        return "fmp"

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
        response = await self.get(f"/quote/{symbol}")

        # Check for error responses or empty results
        if not response or len(response) == 0:
            raise ApiError(f"No quote data found for symbol: {symbol}")

        quote_data = response[0]  # Get the first (and should be only) quote

        # Normalize data
        return {
            "symbol": quote_data.get("symbol", symbol),
            "price": float(quote_data.get("price", 0)),
            "open": float(quote_data.get("open", 0)),
            "high": float(quote_data.get("dayHigh", 0)),
            "low": float(quote_data.get("dayLow", 0)),
            "volume": int(float(quote_data.get("volume", 0))),
            "previous_close": float(quote_data.get("previousClose", 0)),
            "change": float(quote_data.get("change", 0)),
            "change_percent": float(quote_data.get("changesPercentage", 0)),
            "timestamp": datetime.now().isoformat(),
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
        # Map interval to FMP time series
        if interval.lower() == "daily":
            endpoint = f"/historical-price-full/{symbol}"
        elif interval.lower() == "weekly":
            endpoint = f"/historical-price-full/{symbol}?timeseries=7"
        elif interval.lower() == "monthly":
            endpoint = f"/historical-price-full/{symbol}?timeseries=30"
        else:
            endpoint = f"/historical-price-full/{symbol}"

        response = await self.get(endpoint)

        # Check for error responses or empty results
        if not response or "historical" not in response:
            raise ApiError(f"No historical data found for symbol: {symbol}")

        # Extract historical data
        historical_data = response.get("historical", [])

        # Filter by date range if provided
        if start_date or end_date:
            start = (
                datetime.strptime(start_date, "%Y-%m-%d")
                if start_date
                else datetime.min
            )
            end = (
                datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
            )

            filtered_data = []
            for data_point in historical_data:
                date_str = data_point.get("date", "")
                if not date_str:
                    continue

                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start <= date <= end:
                        filtered_data.append(data_point)
                except ValueError:
                    logger.warning(
                        f"Invalid date format in historical data: {date_str}"
                    )

            historical_data = filtered_data

        # Normalize data
        normalized_data = []
        for data_point in historical_data:
            normalized_point = {
                "date": data_point.get("date"),
                "open": float(data_point.get("open", 0)),
                "high": float(data_point.get("high", 0)),
                "low": float(data_point.get("low", 0)),
                "close": float(data_point.get("close", 0)),
                "volume": int(float(data_point.get("volume", 0))),
                "adjusted_close": float(data_point.get("adjClose", 0))
                if "adjClose" in data_point
                else None,
            }
            normalized_data.append(normalized_point)

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
        response = await self.get(f"/profile/{symbol}")

        # Check for error responses or empty results
        if not response or len(response) == 0:
            raise ApiError(f"No company data found for symbol: {symbol}")

        profile_data = response[0]  # Get the first (and should be only) profile

        # Format the data into a standardized profile structure
        profile = {
            "symbol": profile_data.get("symbol"),
            "name": profile_data.get("companyName"),
            "description": profile_data.get("description"),
            "exchange": profile_data.get("exchange"),
            "sector": profile_data.get("sector"),
            "industry": profile_data.get("industry"),
            "market_cap": float(profile_data.get("mktCap", 0)),
            "pe_ratio": float(profile_data.get("pe", 0))
            if profile_data.get("pe")
            else None,
            "dividend_yield": float(profile_data.get("lastDiv", 0))
            if profile_data.get("lastDiv")
            else None,
            "beta": float(profile_data.get("beta", 0))
            if profile_data.get("beta")
            else None,
            "52_week_high": float(profile_data.get("range", "0-0").split("-")[1])
            if "-" in profile_data.get("range", "")
            else None,
            "52_week_low": float(profile_data.get("range", "0-0").split("-")[0])
            if "-" in profile_data.get("range", "")
            else None,
            "country": profile_data.get("country"),
            "employees": int(profile_data.get("fullTimeEmployees", 0))
            if profile_data.get("fullTimeEmployees")
            else None,
            "ceo": profile_data.get("ceo"),
            "website": profile_data.get("website"),
            "image": profile_data.get("image"),
            "price": float(profile_data.get("price", 0)),
            "change_percent": float(profile_data.get("changes", 0)),
            "change": float(
                profile_data.get("changes", 0) * profile_data.get("price", 0) / 100
            )
            if profile_data.get("price")
            else 0,
            "isin": profile_data.get("isin"),
            "cusip": profile_data.get("cusip"),
            # Add provider info for metrics tracking
            "provider": self.provider_name,
        }

        return profile

    async def get_financial_ratios(self, symbol: str) -> Dict[str, Any]:
        """Get financial ratios for a company.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Financial ratios data

        Raises:
            ApiError: If the request fails
        """
        response = await self.get(f"/ratios/{symbol}")

        # Check for error responses or empty results
        if not response or len(response) == 0:
            raise ApiError(f"No financial ratios found for symbol: {symbol}")

        # The response is an array of ratios for different periods
        # Return the most recent period
        return {"symbol": symbol, "ratios": response[0], "provider": self.provider_name}

    async def get_financial_statements(
        self, symbol: str, statement_type: str = "income", period: str = "annual"
    ) -> Dict[str, Any]:
        """Get financial statements for a company.

        Args:
            symbol: Stock ticker symbol
            statement_type: Type of statement (income, balance, cash)
            period: Period of statement (annual, quarter)

        Returns:
            Financial statement data

        Raises:
            ApiError: If the request fails
        """
        # Map statement type to endpoint
        if statement_type.lower() == "income":
            endpoint = "/income-statement"
        elif statement_type.lower() in ["balance", "balance-sheet"]:
            endpoint = "/balance-sheet-statement"
        elif statement_type.lower() in ["cash", "cash-flow"]:
            endpoint = "/cash-flow-statement"
        else:
            raise ApiError(f"Invalid statement type: {statement_type}")

        # Set period parameter
        period_param = "period=quarter" if period.lower() == "quarter" else ""

        # Make request
        url = f"{endpoint}/{symbol}?{period_param}"
        response = await self.get(url)

        # Check for error responses or empty results
        if not response or len(response) == 0:
            raise ApiError(f"No {statement_type} statement found for symbol: {symbol}")

        return {
            "symbol": symbol,
            "statement_type": statement_type,
            "period": period,
            "statements": response,
            "provider": self.provider_name,
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
        response = await self.get(f"/search?query={keywords}&limit=10")

        # Check for error responses or empty results
        if not response:
            raise ApiError(f"No search results found for: {keywords}")

        # Normalize data
        normalized_matches = []
        for match in response:
            normalized_match = {
                "symbol": match.get("symbol"),
                "name": match.get("name"),
                "exchange": match.get("exchangeShortName"),
                "type": match.get("exchangeShortName"),  # Type not directly provided
                "currency": match.get("currency"),
                "stock_exchange": match.get("stockExchange"),
            }
            normalized_matches.append(normalized_match)

        return {"keywords": keywords, "matches": normalized_matches}

"""
Integration of external API clients with the market data service.

This module provides utilities to integrate external API clients with
the existing market data service, allowing for a seamless transition
and fallback between different data providers.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.core.metrics import metrics
from app.services.external_api.base import ApiError
from app.services.external_api.factory import (
    ApiProvider,
    api_factory,
    get_resilient_client,
)

logger = logging.getLogger(__name__)


async def get_stock_quote(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Get stock quote using the resilient API client.

    Args:
        symbol: Stock symbol to get quote for
        force_refresh: Whether to force a refresh or allow cached data

    Returns:
        Stock quote data

    Raises:
        ApiError: If the request fails with all providers
    """
    start_time = datetime.now()
    client = get_resilient_client("market_data")

    try:
        quote = await client.get_stock_quote(symbol)

        # Record success metrics
        metrics.timing(
            "market_data.quote.external_api",
            (datetime.now() - start_time).total_seconds() * 1000,
            tags={"symbol": symbol, "provider": quote.get("provider", "unknown")},
        )

        return quote
    except ApiError as e:
        # Record failure metrics
        metrics.increment(
            "market_data.quote.external_api.error", tags={"symbol": symbol}
        )

        logger.error(f"Failed to get quote for {symbol} from all providers: {str(e)}")
        raise


async def get_historical_data(
    symbol: str,
    start_date: Union[str, datetime],
    end_date: Optional[Union[str, datetime]] = None,
    interval: str = "daily",
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Get historical price data using the resilient API client.

    Args:
        symbol: Stock symbol to get data for
        start_date: Start date (YYYY-MM-DD string or datetime)
        end_date: End date (YYYY-MM-DD string or datetime)
        interval: Data interval (daily, weekly, monthly)
        force_refresh: Whether to force a refresh or allow cached data

    Returns:
        Historical price data

    Raises:
        ApiError: If the request fails with all providers
    """
    start_time = datetime.now()
    client = get_resilient_client("market_data")

    # Convert dates to string format if they are datetime objects
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d")

    if end_date and isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%d")
    elif not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        historical_data = await client.get_historical_data(
            symbol, start_date, end_date, interval
        )

        # Record success metrics
        metrics.timing(
            "market_data.historical.external_api",
            (datetime.now() - start_time).total_seconds() * 1000,
            tags={
                "symbol": symbol,
                "provider": historical_data.get("provider", "unknown"),
            },
        )

        return historical_data
    except ApiError as e:
        # Record failure metrics
        metrics.increment(
            "market_data.historical.external_api.error", tags={"symbol": symbol}
        )

        logger.error(
            f"Failed to get historical data for {symbol} from all providers: {str(e)}"
        )
        raise


async def get_company_profile(symbol: str) -> Dict[str, Any]:
    """Get company profile data using the resilient API client.

    Args:
        symbol: Stock symbol to get data for

    Returns:
        Company profile data

    Raises:
        ApiError: If the request fails with all providers
    """
    start_time = datetime.now()
    client = get_resilient_client("company_data")

    try:
        profile = await client.get_company_profile(symbol)

        # Record success metrics
        metrics.timing(
            "company_data.profile.external_api",
            (datetime.now() - start_time).total_seconds() * 1000,
            tags={"symbol": symbol, "provider": profile.get("provider", "unknown")},
        )

        return profile
    except ApiError as e:
        # Record failure metrics
        metrics.increment(
            "company_data.profile.external_api.error", tags={"symbol": symbol}
        )

        logger.error(
            f"Failed to get company profile for {symbol} from all providers: {str(e)}"
        )
        raise


async def get_provider_health() -> Dict[str, Any]:
    """Get health status of all API providers.

    Returns:
        Dictionary with health status of all providers
    """
    health_tracker = api_factory.get_health_tracker()
    return health_tracker.get_health_report()


async def get_available_providers() -> List[str]:
    """Get list of available API providers.

    Returns:
        List of available provider names
    """
    return [provider.value for provider in api_factory.get_available_providers()]

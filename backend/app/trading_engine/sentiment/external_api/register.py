"""
Register external API clients with the factory.

This module is responsible for importing and registering all API client
implementations with the API client factory.
"""

import logging

from app.services.external_api.alpha_vantage import AlphaVantageClient
from app.services.external_api.coinbase import CoinbaseClient
from app.services.external_api.factory import ApiProvider, api_factory
from app.services.external_api.finnhub import FinnhubClient
from app.services.external_api.fmp import FMPClient
from app.services.external_api.polygon import PolygonClient

logger = logging.getLogger(__name__)

# Register Alpha Vantage client
try:
    api_factory.register(ApiProvider.ALPHA_VANTAGE, AlphaVantageClient)
    logger.info("Registered Alpha Vantage API client")
except Exception as e:
    logger.error(f"Failed to register Alpha Vantage API client: {str(e)}")

# Register Finnhub client
try:
    api_factory.register(ApiProvider.FINNHUB, FinnhubClient)
    logger.info("Registered Finnhub API client")
except Exception as e:
    logger.error(f"Failed to register Finnhub API client: {str(e)}")

# Register Financial Modeling Prep client
try:
    api_factory.register(ApiProvider.FMP, FMPClient)
    logger.info("Registered Financial Modeling Prep API client")
except Exception as e:
    logger.error(f"Failed to register Financial Modeling Prep API client: {str(e)}")

# Register Polygon.io client
try:
    api_factory.register(ApiProvider.POLYGON, PolygonClient)
    logger.info("Registered Polygon.io API client")
except Exception as e:
    logger.error(f"Failed to register Polygon.io API client: {str(e)}")

# Register Coinbase client
try:
    api_factory.register(ApiProvider.COINBASE, CoinbaseClient)
    logger.info("Registered Coinbase API client")
except Exception as e:
    logger.error(f"Failed to register Coinbase API client: {str(e)}")

"""
External API integration module.

This module provides a framework for integrating with external financial data APIs,
including a base client class, factory pattern, and specific implementations for
various data providers.

Note: This module optionally integrates with the backend app services. When running
standalone (without the backend), fallback implementations are used.
"""

# Optional backend imports - gracefully handle when backend is not available
try:
    # Import and register all clients from backend
    import app.services.external_api.register
    from app.services.external_api.base import ApiError, BaseApiClient
    from app.services.external_api.factory import (
        ApiProvider,
        api_factory,
        get_api_client,
        get_resilient_client,
    )

    BACKEND_AVAILABLE = True
except ImportError:
    # Backend not available - define minimal fallbacks
    BACKEND_AVAILABLE = False

    class ApiError(Exception):
        """API error exception for standalone mode."""

        pass

    class BaseApiClient:
        """Base API client stub for standalone mode."""

        pass

    class ApiProvider:
        """API provider stub for standalone mode."""

        YAHOO_FINANCE = "yahoo_finance"
        ALPHA_VANTAGE = "alpha_vantage"

    api_factory = None
    get_api_client = None
    get_resilient_client = None

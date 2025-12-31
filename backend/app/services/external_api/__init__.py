"""
External API integration module.

This module provides a framework for integrating with external financial data APIs,
including a base client class, factory pattern, and specific implementations for
various data providers.
"""

# Import and register all clients
import app.services.external_api.register
from app.services.external_api.base import ApiError, BaseApiClient
from app.services.external_api.factory import (
    ApiProvider,
    api_factory,
    get_api_client,
    get_resilient_client,
)

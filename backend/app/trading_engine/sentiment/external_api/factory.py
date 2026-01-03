"""
API client factory.

This module provides a factory for creating API client instances based on configuration,
allowing the application to seamlessly switch between different data providers.
It also provides a resilient client with failover capabilities.
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from app.core.alerts_manager import alert_manager
from app.core.config import settings
from app.core.metrics import metrics
from app.services.external_api.base import ApiError, BaseApiClient

logger = logging.getLogger(__name__)


class ApiProvider(str, Enum):
    """Types of supported API providers."""

    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    FMP = "fmp"
    POLYGON = "polygon"
    COINBASE = "coinbase"
    # Add more providers as needed


class ApiClientHealth:
    """Track health and availability of API providers."""

    def __init__(self):
        """Initialize API health tracking."""
        self._health_status = {}
        self._consecutive_failures = {}
        self._last_checked = {}

        # Initialize all providers with unknown health
        for provider in ApiProvider:
            self._health_status[
                provider
            ] = True  # Assume healthy until proven otherwise
            self._consecutive_failures[provider] = 0
            self._last_checked[provider] = time.time()

    def record_success(self, provider: ApiProvider) -> None:
        """Record a successful API operation."""
        self._health_status[provider] = True
        self._consecutive_failures[provider] = 0
        self._last_checked[provider] = time.time()
        # Update metrics
        metrics.gauge(f"api.health.{provider}", 1)
        metrics.gauge(f"api.consecutive_failures.{provider}", 0)

    def record_failure(self, provider: ApiProvider) -> None:
        """Record a failed API operation."""
        self._consecutive_failures[provider] += 1
        self._last_checked[provider] = time.time()

        # Mark as unhealthy after configured number of failures
        if self._consecutive_failures[provider] >= settings.API_FAILURE_THRESHOLD:
            if self._health_status[provider]:  # Only log and alert on status change
                logger.warning(
                    f"API provider {provider} marked as unhealthy after "
                    f"{self._consecutive_failures[provider]} consecutive failures"
                )
                alert_manager.send_alert(
                    f"API provider {provider} unavailable",
                    f"Provider {provider} has failed {self._consecutive_failures[provider]} consecutive operations",
                    level="error",
                )
            self._health_status[provider] = False

        # Update metrics
        if not self._health_status[provider]:
            metrics.gauge(f"api.health.{provider}", 0)
        metrics.gauge(
            f"api.consecutive_failures.{provider}", self._consecutive_failures[provider]
        )

    def is_healthy(self, provider: ApiProvider) -> bool:
        """Check if a provider is currently healthy."""
        # If it's been too long since we last checked, revert to healthy to force a retry
        time_since_check = time.time() - self._last_checked.get(provider, 0)
        if (
            not self._health_status[provider]
            and time_since_check > settings.API_RETRY_INTERVAL
        ):
            logger.info(
                f"API provider {provider} retry period elapsed, marking for retry"
            )
            self._health_status[provider] = True

        return self._health_status[provider]

    def get_health_report(self) -> Dict[str, Any]:
        """Get a report of all API provider health statuses."""
        report = {}
        for provider in ApiProvider:
            report[provider] = {
                "healthy": self._health_status.get(provider, False),
                "consecutive_failures": self._consecutive_failures.get(provider, 0),
                "last_checked": self._last_checked.get(provider, 0),
            }
        return report


class ApiClientFactory:
    """Factory for creating API client instances."""

    def __init__(self):
        """Initialize with registry of API client implementations."""
        self._registry = {}
        self._health_tracker = ApiClientHealth()

        # Lazy load API client implementations to avoid circular imports
        self._loaded = False

    def _ensure_loaded(self):
        """Ensure API client implementations are loaded."""
        if self._loaded:
            return

        # Load API client implementations
        try:
            # Import and register all API client implementations
            from app.services.external_api.register import api_factory as loaded_factory

            # If needed, copy any registrations that might have happened in register.py
            for provider, client_class in loaded_factory._registry.items():
                if provider not in self._registry:
                    self._registry[provider] = client_class

        except ImportError as e:
            logger.warning(f"Error loading API clients: {str(e)}")

        self._loaded = True

    def register(
        self, provider: ApiProvider, client_class: Type[BaseApiClient]
    ) -> None:
        """Register an API client implementation."""
        self._registry[provider] = client_class
        logger.info(f"Registered API client implementation: {provider}")

    def create(
        self,
        provider: ApiProvider,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseApiClient:
        """Create an API client instance of the specified provider.

        Args:
            provider: The API provider to use
            api_key: Optional API key (falls back to settings if not provided)
            config: Additional configuration options

        Returns:
            An initialized API client

        Raises:
            ValueError: If the provider is not supported
        """
        self._ensure_loaded()

        # Get client class from registry
        client_class = self._registry.get(provider)

        if not client_class:
            logger.error(f"No API client implementation found for: {provider}")
            raise ValueError(f"No API client implementation available for {provider}")

        # Get API key from settings if not provided
        if api_key is None:
            setting_name = f"{provider.upper()}_API_KEY"
            api_key = getattr(settings, setting_name, None)

            if not api_key:
                raise ValueError(f"No API key found for {provider}")

        # Create configuration
        if config is None:
            config = {}

        # Create and initialize client instance
        client = client_class(api_key=api_key, **config)
        return client

    def get_health_tracker(self) -> ApiClientHealth:
        """Get the API health tracker instance."""
        return self._health_tracker

    def get_available_providers(self) -> List[ApiProvider]:
        """Get a list of all available API providers."""
        self._ensure_loaded()
        return list(self._registry.keys())

    def get_preferred_provider_order(self, feature: str) -> List[ApiProvider]:
        """Get the list of providers in preferred order for a given feature.

        Args:
            feature: The feature or data type being requested

        Returns:
            List of providers in preferred order
        """
        # Get provider priority from settings
        setting_name = f"{feature.upper()}_PROVIDER_PRIORITY"
        preferred_order = getattr(settings, setting_name, None)

        if not preferred_order:
            # Use default priority order
            preferred_order = settings.DEFAULT_API_PROVIDER_PRIORITY

        # Only include registered providers
        return [provider for provider in preferred_order if provider in self._registry]


# Global factory instance
api_factory = ApiClientFactory()


class ResilientApiClient:
    """A wrapper that provides resilient API operations with failover."""

    def __init__(self, feature: str, config: Optional[Dict[str, Any]] = None):
        """Initialize for a specific feature with optional configuration.

        Args:
            feature: The feature or data type being requested (e.g., "market_data")
            config: Optional additional configuration
        """
        self.feature = feature
        self.config = config or {}
        self.health_tracker = api_factory.get_health_tracker()

    async def _execute_with_failover(
        self, method_name: str, *args, **kwargs
    ) -> Tuple[Any, ApiProvider]:
        """Execute an API method with failover capabilities.

        Args:
            method_name: Method to call on the API client
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method

        Returns:
            Tuple of (result, provider_used)

        Raises:
            ApiError: If all providers fail
        """
        start_time = time.time()
        preferred_providers = api_factory.get_preferred_provider_order(self.feature)

        # Try each provider in order of preference
        for provider in preferred_providers:
            # Skip unhealthy providers
            if not self.health_tracker.is_healthy(provider):
                logger.debug(f"Skipping unhealthy provider: {provider}")
                continue

            try:
                # Create client instance
                client = api_factory.create(provider)

                # Find and call the requested method
                method = getattr(client, method_name, None)
                if not method:
                    logger.warning(
                        f"Method {method_name} not supported by provider {provider}"
                    )
                    continue

                # Execute operation with timing
                method_start = time.time()
                result = await method(*args, **kwargs)
                method_duration = time.time() - method_start

                # Record metrics
                metrics.timing(f"api.{provider}.{method_name}", method_duration * 1000)
                metrics.increment(f"api.{provider}.{method_name}.success")

                # Record successful operation
                self.health_tracker.record_success(provider)

                logger.debug(
                    f"Successfully executed {method_name} using provider {provider}"
                )

                # Close client session
                await client.close()

                return result, provider

            except ApiError as e:
                logger.warning(
                    f"Provider {provider} operation {method_name} failed: {e}"
                )
                metrics.increment(f"api.{provider}.{method_name}.error")
                self.health_tracker.record_failure(provider)

                # Ensure client session is closed
                try:
                    await client.close()
                except Exception:
                    pass

            except Exception as e:
                logger.error(
                    f"Unexpected error with provider {provider} for {method_name}: {e}",
                    exc_info=True,
                )
                metrics.increment(f"api.{provider}.{method_name}.exception")
                self.health_tracker.record_failure(provider)

                # Ensure client session is closed
                try:
                    await client.close()
                except Exception:
                    pass

        # If we get here, all providers failed
        total_duration = time.time() - start_time
        metrics.timing("api.failover.total_duration", total_duration * 1000)
        metrics.increment("api.failover.all_failed")

        error_msg = f"All available providers failed for operation: {method_name}"
        logger.error(error_msg)
        alert_manager.send_alert(
            "API failover exhausted",
            f"All available providers failed for {self.feature} operation: {method_name}",
            level="critical",
        )
        raise ApiError(error_msg)

    # Implement common API methods using failover

    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get a stock quote with automatic failover."""
        result, provider = await self._execute_with_failover("get_stock_quote", symbol)
        result["provider"] = provider  # Add provider information
        return result

    async def get_historical_data(
        self, symbol: str, start_date: str, end_date: str, interval: str = "1d"
    ) -> Dict[str, Any]:
        """Get historical price data with automatic failover."""
        result, provider = await self._execute_with_failover(
            "get_historical_data", symbol, start_date, end_date, interval
        )
        result["provider"] = provider  # Add provider information
        return result

    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile with automatic failover."""
        result, provider = await self._execute_with_failover(
            "get_company_profile", symbol
        )
        result["provider"] = provider  # Add provider information
        return result

    # Add more common methods as needed


def get_api_client(
    provider: ApiProvider,
    api_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> BaseApiClient:
    """Get an API client instance.

    Args:
        provider: The API provider to use
        api_key: Optional API key (falls back to settings if not provided)
        config: Additional configuration options

    Returns:
        An initialized API client
    """
    return api_factory.create(provider, api_key, config)


def get_resilient_client(
    feature: str, config: Optional[Dict[str, Any]] = None
) -> ResilientApiClient:
    """Get a resilient API client with failover capabilities.

    Args:
        feature: The feature or data type being requested (e.g., "market_data")
        config: Optional additional configuration

    Returns:
        A resilient API client instance
    """
    return ResilientApiClient(feature=feature, config=config)

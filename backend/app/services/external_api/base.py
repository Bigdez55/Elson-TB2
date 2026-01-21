"""
Base class for external API clients.

This module provides the abstract base class and common utilities for
all external API client implementations, ensuring consistent error handling,
rate limiting, and metrics collection.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp

from app.core.config import settings
from app.core.metrics import metrics

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Exception for API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        api_response: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with error details."""
        self.message = message
        self.status_code = status_code
        self.api_response = api_response
        super().__init__(self.message)


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(
        self, calls_per_second: float, calls_per_minute: float, calls_per_day: float
    ):
        """Initialize with rate limits."""
        self.calls_per_second = calls_per_second
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day

        # Track call history
        self.recent_calls = []
        self.minute_calls = []
        self.day_calls = []

        # Last throttle time to prevent logging spam
        self.last_throttle_log = 0

    async def wait_if_needed(self, endpoint: str = "default") -> float:
        """Wait if necessary to comply with rate limits.

        Args:
            endpoint: API endpoint being called

        Returns:
            The wait time in seconds (0 if no wait was needed)
        """
        now = time.time()

        # Clean up old call records
        self.recent_calls = [t for t in self.recent_calls if now - t < 1.0]
        self.minute_calls = [t for t in self.minute_calls if now - t < 60.0]
        self.day_calls = [t for t in self.day_calls if now - t < 86400.0]

        # Check rate limits
        second_limit_exceeded = len(self.recent_calls) >= self.calls_per_second
        minute_limit_exceeded = len(self.minute_calls) >= self.calls_per_minute
        day_limit_exceeded = len(self.day_calls) >= self.calls_per_day

        # Determine wait time
        wait_time = 0

        if second_limit_exceeded:
            # Wait until we're under the per-second limit
            oldest_call = self.recent_calls[0]
            wait_time = max(wait_time, oldest_call + 1.0 - now)

        if minute_limit_exceeded:
            # Wait until we're under the per-minute limit
            oldest_minute_call = self.minute_calls[0]
            wait_time = max(wait_time, oldest_minute_call + 60.0 - now)

        if day_limit_exceeded:
            # Wait until we're under the per-day limit
            oldest_day_call = self.day_calls[0]
            wait_time = max(wait_time, oldest_day_call + 86400.0 - now)

        # Add buffer to ensure we're safely under the limit
        wait_time += 0.05

        if wait_time > 0:
            # Log throttling (but not too frequently)
            if now - self.last_throttle_log > 10:
                logger.warning(
                    f"Rate limit approaching for {endpoint}, waiting {wait_time:.2f}s"
                )
                self.last_throttle_log = now

            # Record metrics
            metrics.increment("api.rate_limit.throttled", labels={"endpoint": endpoint})
            metrics.gauge(
                "api.rate_limit.wait_time", wait_time, labels={"endpoint": endpoint}
            )

            # Wait as needed
            await asyncio.sleep(wait_time)

        # Record this call
        now = time.time()  # Update time after potential wait
        self.recent_calls.append(now)
        self.minute_calls.append(now)
        self.day_calls.append(now)

        return wait_time


class BaseApiClient(ABC):
    """Abstract base class for external API clients."""

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize with API key and optional session."""
        self.api_key = api_key
        self.session = session
        self.default_headers = {"Content-Type": "application/json"}

        # Set up rate limiting based on provider-specific limits
        calls_per_second = self.get_rate_limit_config("per_second", 5)
        calls_per_minute = self.get_rate_limit_config("per_minute", 60)
        calls_per_day = self.get_rate_limit_config("per_day", 500)

        self.rate_limiter = RateLimiter(
            calls_per_second=calls_per_second,
            calls_per_minute=calls_per_minute,
            calls_per_day=calls_per_day,
        )

    def get_rate_limit_config(self, limit_type: str, default: int) -> int:
        """Get rate limit configuration for this client."""
        client_name = self.__class__.__name__.lower().replace("client", "")
        setting_name = f"{client_name.upper()}_RATE_LIMIT_{limit_type.upper()}"
        return getattr(settings, setting_name, default)

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of the API provider."""
        pass

    async def ensure_session(self) -> None:
        """Ensure an aiohttp session is available."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.default_headers)

    async def close(self) -> None:
        """Close the session if it exists."""
        if self.session:
            await self.session.close()
            self.session = None

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            ApiError: If the request fails
        """
        return await self._request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request to the API.

        Args:
            endpoint: API endpoint to call
            data: Request body data

        Returns:
            Response data as dictionary

        Raises:
            ApiError: If the request fails
        """
        return await self._request("POST", endpoint, data=data)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint to call
            params: Query parameters
            data: Request body data

        Returns:
            Response data as dictionary

        Raises:
            ApiError: If the request fails
        """
        await self.ensure_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Apply rate limiting
        await self.rate_limiter.wait_if_needed(endpoint)

        start_time = time.time()
        request_id = f"{self.provider_name}:{endpoint}:{start_time}"

        try:
            logger.debug(f"API request {request_id} - {method} {url}")

            # Prepare request
            request_kwargs = {
                "method": method,
                "url": url,
                "params": params,
                "json": data,
            }

            # Add provider-specific authentication
            self._add_auth(request_kwargs)

            # Execute request with timing
            async with self.session.request(**request_kwargs) as response:
                duration = time.time() - start_time

                # Record metrics
                metrics.timing(
                    "api.request.duration",
                    duration * 1000,
                    labels={"provider": self.provider_name, "endpoint": endpoint},
                )
                metrics.increment(
                    "api.request.count",
                    labels={"provider": self.provider_name, "endpoint": endpoint},
                )

                # Log request details
                logger.debug(
                    f"API response {request_id} - {response.status} "
                    f"({duration:.2f}s): {method} {url}"
                )

                # Handle response
                if response.status < 200 or response.status >= 300:
                    response_text = await response.text()

                    # Record error metrics
                    metrics.increment(
                        "api.request.error",
                        labels={
                            "provider": self.provider_name,
                            "endpoint": endpoint,
                            "status": response.status,
                        },
                    )

                    error_msg = f"API error {response.status}: {response_text}"
                    logger.error(f"{request_id} - {error_msg}")

                    raise ApiError(
                        message=error_msg,
                        status_code=response.status,
                        api_response={"text": response_text},
                    )

                # Parse successful response
                try:
                    result = await response.json()
                except Exception as e:
                    response_text = await response.text()
                    logger.warning(f"Failed to parse JSON response: {response_text}")
                    result = {"text": response_text}

                return result

        except aiohttp.ClientError as e:
            # Handle client errors (connection, timeout, etc.)
            duration = time.time() - start_time
            logger.error(f"API client error {request_id} ({duration:.2f}s): {str(e)}")

            metrics.increment(
                "api.request.error",
                labels={
                    "provider": self.provider_name,
                    "endpoint": endpoint,
                    "type": "client_error",
                },
            )

            raise ApiError(
                message=f"API client error: {str(e)}",
                status_code=None,
                api_response=None,
            )

        except asyncio.TimeoutError:
            # Handle timeout errors
            duration = time.time() - start_time
            logger.error(f"API timeout {request_id} ({duration:.2f}s)")

            metrics.increment(
                "api.request.error",
                labels={
                    "provider": self.provider_name,
                    "endpoint": endpoint,
                    "type": "timeout",
                },
            )

            raise ApiError(
                message="API request timed out", status_code=None, api_response=None
            )

        except Exception as e:
            # Handle unexpected errors
            duration = time.time() - start_time
            logger.error(
                f"API unexpected error {request_id} ({duration:.2f}s): {str(e)}",
                exc_info=True,
            )

            metrics.increment(
                "api.request.error",
                labels={
                    "provider": self.provider_name,
                    "endpoint": endpoint,
                    "type": "unexpected",
                },
            )

            raise ApiError(
                message=f"Unexpected API error: {str(e)}",
                status_code=None,
                api_response=None,
            )

    def _add_auth(self, request_kwargs: Dict[str, Any]) -> None:
        """Add authentication to request.

        This default implementation adds the API key as a query parameter.
        Override in subclasses for different authentication methods.

        Args:
            request_kwargs: Request keyword arguments to modify
        """
        # Default implementation adds API key as a query parameter
        params = request_kwargs.get("params", {}) or {}
        params["apikey"] = self.api_key
        request_kwargs["params"] = params

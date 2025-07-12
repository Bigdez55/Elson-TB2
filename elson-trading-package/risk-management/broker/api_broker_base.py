"""API Broker base class implementation.

This module provides a common base class for API-based broker implementations,
with shared functionality for HTTP requests, authentication, and error handling.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings
from app.core.exception_handlers import BrokerError, handle_errors
from app.core.metrics import metrics
from app.models.trade import Trade
from app.services.broker.base import BaseBroker

logger = logging.getLogger(__name__)


class ApiRequestHandler:
    """Handles API requests with retries, error handling, and metrics."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        retry_strategy: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the API request handler.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            retry_strategy: Retry configuration
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_strategy = retry_strategy or {
            "total": 3,
            "backoff_factor": 0.5,
            "status_forcelist": [429, 500, 502, 503, 504],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
        }

        # Create session with configured retry strategy
        self.session = self._create_session()

        # Stats for metrics
        self.request_count = 0
        self.error_count = 0

    def _create_session(self) -> requests.Session:
        """Create a requests session with configured retry logic."""
        session = requests.Session()

        # Configure retry strategy
        retry = Retry(
            total=self.retry_strategy.get("total", 3),
            backoff_factor=self.retry_strategy.get("backoff_factor", 0.5),
            status_forcelist=self.retry_strategy.get(
                "status_forcelist", [429, 500, 502, 503, 504]
            ),
            allowed_methods=self.retry_strategy.get(
                "allowed_methods", ["GET", "POST", "PUT", "DELETE"]
            ),
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def configure_session_headers(self, headers: Dict[str, str]) -> None:
        """Configure session headers for authentication and content type.

        Args:
            headers: Headers to add to session
        """
        self.session.headers.update(headers)

    @handle_errors()
    def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        error_handler: Optional[Callable[[requests.Response], None]] = None,
        metric_prefix: str = "api",
    ) -> Dict[str, Any]:
        """Make an API request with error handling and metrics.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data (will be JSON encoded)
            headers: Additional headers for this request
            timeout: Request timeout override
            error_handler: Custom error handler function
            metric_prefix: Prefix for metrics

        Returns:
            API response as dictionary

        Raises:
            BrokerError: If the API request fails
        """
        url = f"{self.base_url}{endpoint}"
        request_timeout = timeout or self.timeout
        self.request_count += 1

        # Record request metrics
        metrics.increment(
            f"{metric_prefix}.request", tags={"method": method, "endpoint": endpoint}
        )

        start_time = time.time()

        try:
            # Make the request
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=request_timeout,
            )

            # Log request information in debug
            logger.debug(f"API Request: {method} {url}")
            if params:
                logger.debug(f"Query params: {params}")
            if data:
                logger.debug(f"Request data: {json.dumps(data)[:500]}")

            # Record timing metrics
            request_time = (time.time() - start_time) * 1000
            metrics.timing(
                f"{metric_prefix}.latency",
                request_time,
                tags={
                    "method": method,
                    "endpoint": endpoint,
                    "status": response.status_code,
                },
            )

            # Handle error responses
            if not response.ok:
                if error_handler:
                    error_handler(response)
                else:
                    self._handle_error_response(response, metric_prefix)

            # Handle special cases for response parsing
            if method == "DELETE" and response.status_code == 204:
                return {"success": True}

            # Parse JSON response
            if response.content:
                return response.json()
            else:
                return {"success": True}

        except requests.RequestException as e:
            # Handle network and connection errors
            self.error_count += 1
            logger.error(f"API request failed: {str(e)}")
            metrics.increment(
                f"{metric_prefix}.error",
                tags={
                    "error_type": "request_exception",
                    "method": method,
                    "endpoint": endpoint,
                },
            )
            raise BrokerError(message=f"API request failed: {str(e)}")

        except ValueError as e:
            # Handle JSON parsing errors
            self.error_count += 1
            logger.error(f"Failed to parse API response: {str(e)}")
            metrics.increment(
                f"{metric_prefix}.error",
                tags={
                    "error_type": "parse_error",
                    "method": method,
                    "endpoint": endpoint,
                },
            )
            raise BrokerError(message=f"Failed to parse API response: {str(e)}")

    def _handle_error_response(
        self, response: requests.Response, metric_prefix: str
    ) -> None:
        """Default error response handler.

        Args:
            response: Response object with error
            metric_prefix: Prefix for metrics

        Raises:
            BrokerError: With appropriate error details
        """
        self.error_count += 1

        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
            error_code = str(error_data.get("code", response.status_code))
        except Exception:
            error_message = response.text or f"HTTP Error: {response.status_code}"
            error_code = str(response.status_code)

        # Log error details
        logger.error(f"API Error ({response.status_code}): {error_message}")

        # Record error metrics
        metrics.increment(
            f"{metric_prefix}.error",
            tags={"status_code": response.status_code, "error_code": error_code},
        )

        # Raise broker error
        raise BrokerError(
            message=f"API Error: {error_message}",
            error_code=error_code,
            broker_response=error_data if "error_data" in locals() else None,
        )


class ApiBaseBroker(BaseBroker, ABC):
    """Base class for API-based broker implementations.

    This class provides common functionality for API brokers including:
    - Request handling with retries and error handling
    - Authentication management
    - Metrics collection
    """

    def __init__(
        self,
        db=None,
        api_base_url: str = "",
        timeout: int = 30,
        retry_config: Optional[Dict[str, Any]] = None,
        metrics_prefix: str = "broker",
    ):
        """Initialize the API broker base.

        Args:
            db: Database session
            api_base_url: Base URL for API requests
            timeout: Request timeout in seconds
            retry_config: Retry configuration
            metrics_prefix: Prefix for metrics
        """
        self.db = db
        self.base_url = api_base_url
        self.timeout = timeout
        self.metrics_prefix = metrics_prefix

        # Initialize request handler
        self.api = ApiRequestHandler(
            base_url=api_base_url, timeout=timeout, retry_strategy=retry_config
        )

        # Authentication state - subclasses may override for OAuth, etc.
        self.authenticated = False

    @abstractmethod
    def _configure_auth(self) -> None:
        """Configure authentication for API requests.

        This method should be implemented by subclasses to set up the
        appropriate authentication for the broker API.
        """
        pass

    def _api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make an API request with broker-specific metrics.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            headers: Additional headers
            timeout: Request timeout override

        Returns:
            API response as dictionary
        """
        metric_prefix = f"{self.metrics_prefix}.{self.__class__.__name__.lower().replace('broker', '')}"

        # Make sure authentication is configured
        if not self.authenticated:
            self._configure_auth()
            self.authenticated = True

        return self.api.make_request(
            method=method,
            endpoint=endpoint,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout,
            error_handler=getattr(self, "_handle_error_response", None),
            metric_prefix=metric_prefix,
        )

    def _add_pagination_params(
        self,
        params: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add pagination parameters to query params.

        Args:
            params: Existing query parameters
            limit: Maximum number of results
            offset: Offset for results
            page: Page number (alternative to offset)
            page_size: Page size (alternative to limit)

        Returns:
            Updated parameters dict
        """
        # Start with existing params or empty dict
        result = params.copy() if params else {}

        # Add limit/offset style pagination
        if limit is not None:
            result["limit"] = limit
        if offset is not None:
            result["offset"] = offset

        # Add page/page_size style pagination
        if page is not None:
            result["page"] = page
        if page_size is not None:
            result["page_size"] = page_size

        return result

    def _format_date_param(self, date: Union[datetime, str]) -> str:
        """Format a date for API parameters.

        Args:
            date: Datetime object or ISO string

        Returns:
            Formatted date string
        """
        if isinstance(date, datetime):
            return date.isoformat()
        return str(date)

    # Utility methods for common broker operations

    def _map_order_type(self, order_type: str, to_api: bool = True) -> str:
        """Map between platform order types and broker API order types.

        Args:
            order_type: Order type to map
            to_api: True to map from platform to API, False for the reverse

        Returns:
            Mapped order type
        """
        # Override in subclasses
        return order_type

    def _map_order_side(self, order_side: str, to_api: bool = True) -> str:
        """Map between platform order sides and broker API order sides.

        Args:
            order_side: Order side to map
            to_api: True to map from platform to API, False for the reverse

        Returns:
            Mapped order side
        """
        # Override in subclasses
        return order_side

    def _map_order_status(self, status: str, to_api: bool = True) -> str:
        """Map between platform order statuses and broker API statuses.

        Args:
            status: Order status to map
            to_api: True to map from platform to API, False for the reverse

        Returns:
            Mapped order status
        """
        # Override in subclasses
        return status

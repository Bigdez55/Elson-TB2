"""Custom exception classes for the trading platform.

This module provides custom exception classes used throughout the application
for handling various error conditions in a structured way.
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)


class TradingPlatformError(Exception):
    """Base exception for all trading platform errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BrokerError(TradingPlatformError):
    """Exception raised when a broker operation fails."""

    def __init__(
        self,
        message: str,
        broker: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        broker_response: Optional[dict] = None,
        metadata: Optional[dict] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.broker = broker
        self.operation = operation
        self.error_code = error_code
        self.broker_response = broker_response
        self.metadata = metadata or {}


class MarketDataError(TradingPlatformError):
    """Exception raised when market data retrieval fails."""

    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        source: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.symbol = symbol
        self.source = source


class OrderExecutionError(TradingPlatformError):
    """Exception raised when order execution fails."""

    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.order_id = order_id
        self.symbol = symbol
        self.reason = reason


class ResourceNotFoundError(TradingPlatformError):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class AuthenticationError(TradingPlatformError):
    """Exception raised when authentication fails."""

    pass


class AuthorizationError(TradingPlatformError):
    """Exception raised when authorization fails."""

    pass


class ValidationError(TradingPlatformError):
    """Exception raised when data validation fails."""

    pass


class RateLimitError(TradingPlatformError):
    """Exception raised when rate limit is exceeded."""

    pass


class ConfigurationError(TradingPlatformError):
    """Exception raised when configuration is invalid."""

    pass


class ServiceError(TradingPlatformError):
    """Exception raised when a service operation fails."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.service = service
        self.operation = operation


F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: Optional[F] = None) -> Any:
    """Decorator to handle common exceptions and log errors.

    Supports both @handle_errors and @handle_errors() syntax.

    Usage:
        @handle_errors
        async def my_function():
            ...

        @handle_errors()
        async def my_other_function():
            ...
    """
    import asyncio

    def decorator(fn: F) -> F:
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except TradingPlatformError:
                raise  # Re-raise our custom exceptions
            except Exception as e:
                logger.error(f"Error in {fn.__name__}: {str(e)}", exc_info=True)
                raise TradingPlatformError(f"Unexpected error: {str(e)}")

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except TradingPlatformError:
                raise  # Re-raise our custom exceptions
            except Exception as e:
                logger.error(f"Error in {fn.__name__}: {str(e)}", exc_info=True)
                raise TradingPlatformError(f"Unexpected error: {str(e)}")

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    # Support both @handle_errors and @handle_errors()
    if func is not None:
        return decorator(func)
    return decorator


__all__ = [
    "TradingPlatformError",
    "BrokerError",
    "MarketDataError",
    "OrderExecutionError",
    "ResourceNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "RateLimitError",
    "ConfigurationError",
    "ServiceError",
    "handle_errors",
]

"""Broker factory for creating and managing broker instances.

This module provides a centralized way to create broker instances with
proper configuration and safety controls for both paper and live trading.

Features:
- Broker registry and factory pattern
- Health tracking and monitoring
- Automatic failover between brokers
- Safety controls for live trading
"""

import logging
import time
from enum import Enum
from typing import Dict, Optional, Type, List, Tuple, Any

from app.core.config import settings
from app.core.secrets import validate_broker_credentials
from app.services.broker.base import BaseBroker, BrokerError
from app.services.broker.alpaca import AlpacaBroker

logger = logging.getLogger(__name__)


class BrokerType(str, Enum):
    """Types of supported brokers."""

    PAPER = "paper"
    ALPACA = "alpaca"
    SCHWAB = "schwab"
    # Add more broker types as needed


class BrokerHealth:
    """Track health and availability of broker connections."""

    def __init__(self):
        """Initialize broker health tracking."""
        self._health_status = {}
        self._consecutive_failures = {}
        self._last_checked = {}

        # Initialize all broker types with unknown health
        for broker_type in BrokerType:
            self._health_status[broker_type.value] = True  # Assume healthy until proven otherwise
            self._consecutive_failures[broker_type.value] = 0
            self._last_checked[broker_type.value] = time.time()

    def record_success(self, broker_name: str) -> None:
        """Record a successful broker operation."""
        self._health_status[broker_name] = True
        self._consecutive_failures[broker_name] = 0
        self._last_checked[broker_name] = time.time()
        logger.debug(f"Broker {broker_name} marked as healthy")

    def record_failure(self, broker_name: str) -> None:
        """Record a failed broker operation."""
        self._consecutive_failures[broker_name] = self._consecutive_failures.get(broker_name, 0) + 1
        self._last_checked[broker_name] = time.time()

        # Mark as unhealthy after configured number of failures
        failure_threshold = getattr(settings, "BROKER_FAILURE_THRESHOLD", 3)
        if self._consecutive_failures[broker_name] >= failure_threshold:
            if self._health_status.get(broker_name, True):  # Only log on status change
                logger.warning(
                    f"Broker {broker_name} marked as unhealthy after "
                    f"{self._consecutive_failures[broker_name]} consecutive failures"
                )
            self._health_status[broker_name] = False

    def is_healthy(self, broker_name: str) -> bool:
        """Check if a broker is currently healthy."""
        # If it's been too long since we last checked, revert to healthy to force a retry
        retry_interval = getattr(settings, "BROKER_RETRY_INTERVAL", 300)  # 5 minutes default
        time_since_check = time.time() - self._last_checked.get(broker_name, 0)

        if not self._health_status.get(broker_name, True) and time_since_check > retry_interval:
            logger.info(f"Broker {broker_name} retry period elapsed, marking for retry")
            self._health_status[broker_name] = True

        return self._health_status.get(broker_name, True)

    def get_health_report(self) -> Dict[str, Any]:
        """Get a report of all broker health statuses."""
        report = {}
        for broker_name in self._health_status.keys():
            report[broker_name] = {
                "healthy": self._health_status.get(broker_name, False),
                "consecutive_failures": self._consecutive_failures.get(broker_name, 0),
                "last_checked": self._last_checked.get(broker_name, 0)
            }
        return report


# Global health tracker instance
_health_tracker = BrokerHealth()


class BrokerFactory:
    """Factory for creating broker instances with safety controls."""

    # Registry of available brokers
    _brokers: Dict[str, Type[BaseBroker]] = {
        "alpaca": AlpacaBroker,
    }

    @classmethod
    def create_broker(
        cls, broker_name: str, use_paper: bool = True, **kwargs
    ) -> BaseBroker:
        """Create a broker instance with safety controls.

        Args:
            broker_name: Name of the broker ('alpaca', 'schwab', etc.)
            use_paper: Whether to use paper trading (default: True for safety)
            **kwargs: Additional arguments to pass to broker constructor

        Returns:
            Configured broker instance

        Raises:
            BrokerError: If broker creation fails or credentials are invalid
        """
        broker_name = broker_name.lower()

        if broker_name not in cls._brokers:
            available_brokers = ", ".join(cls._brokers.keys())
            raise BrokerError(
                message=f"Unknown broker '{broker_name}'. Available: {available_brokers}",
                error_code="UNKNOWN_BROKER",
            )

        # Validate credentials before creating instance
        if not validate_broker_credentials(broker_name):
            raise BrokerError(
                message=f"Invalid or missing credentials for {broker_name}",
                error_code="INVALID_CREDENTIALS",
            )

        # Safety check: Only allow live trading in production-like environments
        if not use_paper:
            environment = getattr(settings, "ENVIRONMENT", "development")
            if environment not in ["production", "staging"]:
                logger.warning(
                    f"Live trading requested in {environment} environment. "
                    "Forcing paper trading for safety."
                )
                use_paper = True

        broker_class = cls._brokers[broker_name]

        try:
            broker = broker_class(use_paper=use_paper, **kwargs)

            logger.info(
                f"Created {broker_name} broker instance "
                f"(paper={'Yes' if use_paper else 'No'})"
            )

            # Record successful creation
            _health_tracker.record_success(broker_name)

            return broker

        except Exception as e:
            logger.error(f"Failed to create {broker_name} broker: {str(e)}")
            _health_tracker.record_failure(broker_name)
            raise BrokerError(
                message=f"Failed to create {broker_name} broker: {str(e)}",
                error_code="BROKER_CREATION_FAILED",
            ) from e

    @classmethod
    def create_paper_broker(cls, broker_name: str = "alpaca", **kwargs) -> BaseBroker:
        """Create a paper trading broker instance.

        Args:
            broker_name: Name of the broker (default: alpaca)
            **kwargs: Additional arguments to pass to broker constructor

        Returns:
            Paper trading broker instance
        """
        return cls.create_broker(broker_name, use_paper=True, **kwargs)

    @classmethod
    def create_live_broker(cls, broker_name: str = "alpaca", **kwargs) -> BaseBroker:
        """Create a live trading broker instance with extra validation.

        Args:
            broker_name: Name of the broker (default: alpaca)
            **kwargs: Additional arguments to pass to broker constructor

        Returns:
            Live trading broker instance

        Raises:
            BrokerError: If live trading is not properly configured
        """
        # Extra validation for live trading
        environment = getattr(settings, "ENVIRONMENT", "development")

        if environment == "development":
            raise BrokerError(
                message="Live trading is not allowed in development environment",
                error_code="LIVE_TRADING_DISABLED",
            )

        # Require explicit confirmation for live trading
        live_trading_enabled = getattr(settings, "LIVE_TRADING_ENABLED", False)
        if not live_trading_enabled:
            raise BrokerError(
                message="Live trading is not enabled. Set LIVE_TRADING_ENABLED=true",
                error_code="LIVE_TRADING_DISABLED",
            )

        logger.warning(
            f"Creating LIVE trading broker for {broker_name} in {environment} environment"
        )

        return cls.create_broker(broker_name, use_paper=False, **kwargs)

    @classmethod
    def get_default_broker(cls, use_paper: bool = True, **kwargs) -> BaseBroker:
        """Get the default broker instance.

        Args:
            use_paper: Whether to use paper trading
            **kwargs: Additional arguments to pass to broker constructor

        Returns:
            Default broker instance
        """
        default_broker = getattr(settings, "DEFAULT_BROKER", "alpaca")
        return cls.create_broker(default_broker, use_paper=use_paper, **kwargs)

    @classmethod
    def register_broker(cls, name: str, broker_class: Type[BaseBroker]) -> None:
        """Register a new broker type.

        Args:
            name: Name to register the broker under
            broker_class: Broker class that implements BaseBroker
        """
        if not issubclass(broker_class, BaseBroker):
            raise ValueError("Broker class must inherit from BaseBroker")

        cls._brokers[name.lower()] = broker_class
        logger.info(f"Registered broker: {name}")

    @classmethod
    def list_available_brokers(cls) -> list[str]:
        """Get list of available broker names."""
        return list(cls._brokers.keys())

    @classmethod
    def get_health_tracker(cls) -> BrokerHealth:
        """Get the global broker health tracker."""
        return _health_tracker

    @classmethod
    def get_health_report(cls) -> Dict[str, Any]:
        """Get health report for all brokers."""
        return _health_tracker.get_health_report()


class ResilientBroker:
    """A wrapper that provides resilient broker operations with failover."""

    def __init__(self, broker_priority: Optional[List[str]] = None, use_paper: bool = True, **kwargs):
        """Initialize with broker priority list and configuration.

        Args:
            broker_priority: List of broker names in order of preference
            use_paper: Whether to use paper trading
            **kwargs: Additional configuration for brokers
        """
        self.broker_priority = broker_priority or ["alpaca"]
        self.use_paper = use_paper
        self.config = kwargs
        self.health_tracker = _health_tracker

    def _execute_with_failover(
        self, method_name: str, *args, **kwargs
    ) -> Tuple[Any, str]:
        """Execute a broker method with failover capabilities.

        Args:
            method_name: Name of the broker method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Tuple of (result, broker_name)

        Raises:
            BrokerError: If all brokers fail
        """
        start_time = time.time()
        errors = []

        # Try each broker in order of preference
        for broker_name in self.broker_priority:
            # Skip unhealthy brokers
            if not self.health_tracker.is_healthy(broker_name):
                logger.debug(f"Skipping unhealthy broker: {broker_name}")
                continue

            try:
                # Create broker instance
                broker = BrokerFactory.create_broker(
                    broker_name, use_paper=self.use_paper, **self.config
                )

                # Find and call the requested method
                method = getattr(broker, method_name, None)
                if not method:
                    logger.warning(
                        f"Method {method_name} not supported by broker {broker_name}"
                    )
                    continue

                # Execute operation
                result = method(*args, **kwargs)

                # Record successful operation
                self.health_tracker.record_success(broker_name)

                logger.debug(
                    f"Successfully executed {method_name} using broker {broker_name}"
                )
                return result, broker_name

            except BrokerError as e:
                logger.warning(f"Broker {broker_name} operation {method_name} failed: {e}")
                self.health_tracker.record_failure(broker_name)
                errors.append(f"{broker_name}: {str(e)}")

            except Exception as e:
                logger.error(
                    f"Unexpected error with broker {broker_name} for {method_name}: {e}",
                    exc_info=True,
                )
                self.health_tracker.record_failure(broker_name)
                errors.append(f"{broker_name}: {str(e)}")

        # If we get here, all brokers failed
        total_duration = time.time() - start_time
        error_msg = (
            f"All available brokers failed for operation: {method_name}. "
            f"Errors: {'; '.join(errors)}"
        )
        logger.error(error_msg)

        raise BrokerError(
            message=error_msg,
            error_code="ALL_BROKERS_FAILED",
        )

    # Implement common broker interface methods using failover

    def execute_trade(self, trade, **kwargs):
        """Execute a trade with automatic failover."""
        result, broker_name = self._execute_with_failover("execute_trade", trade, **kwargs)
        return result

    def get_account_info(self, account_id, **kwargs):
        """Get account information with automatic failover."""
        return self._execute_with_failover("get_account_info", account_id, **kwargs)[0]

    def get_positions(self, account_id, **kwargs):
        """Get positions with automatic failover."""
        return self._execute_with_failover("get_positions", account_id, **kwargs)[0]

    def get_quote(self, symbol, **kwargs):
        """Get quote with automatic failover."""
        return self._execute_with_failover("get_quote", symbol, **kwargs)[0]


# Convenience functions for common use cases


def get_paper_broker(**kwargs) -> BaseBroker:
    """Get a paper trading broker instance."""
    return BrokerFactory.create_paper_broker(**kwargs)


def get_live_broker(**kwargs) -> BaseBroker:
    """Get a live trading broker instance with safety checks."""
    return BrokerFactory.create_live_broker(**kwargs)


def get_broker(
    broker_name: str = "alpaca", use_paper: bool = True, **kwargs
) -> BaseBroker:
    """Get a broker instance with specified configuration."""
    return BrokerFactory.create_broker(broker_name, use_paper=use_paper, **kwargs)


def get_resilient_broker(
    broker_priority: Optional[List[str]] = None, use_paper: bool = True, **kwargs
) -> ResilientBroker:
    """Get a resilient broker instance with failover capabilities.

    Args:
        broker_priority: List of broker names in order of preference
        use_paper: Whether to use paper trading
        **kwargs: Additional configuration parameters

    Returns:
        A resilient broker instance with failover
    """
    return ResilientBroker(
        broker_priority=broker_priority, use_paper=use_paper, **kwargs
    )


def get_health_report() -> Dict[str, Any]:
    """Get health report for all brokers."""
    return _health_tracker.get_health_report()

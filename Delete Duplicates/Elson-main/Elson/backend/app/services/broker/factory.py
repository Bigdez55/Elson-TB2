"""Broker factory for creating broker instances.

This module provides a factory for creating broker instances based on configuration,
allowing the application to seamlessly switch between different broker implementations.
It also provides a resilient broker router with failover capabilities.
"""

import logging
import time
from enum import Enum
from typing import Optional, Dict, Any, Type, List, Tuple

from sqlalchemy.orm import Session

from app.services.broker.base import BaseBroker, BrokerError
from app.services.broker.paper import PaperBroker
from app.core.config import settings
from app.core.metrics import metrics

# Import alert_manager in the functions that use it to avoid circular dependencies

logger = logging.getLogger(__name__)


class BrokerType(str, Enum):
    """Types of supported brokers."""
    
    PAPER = "paper"
    SCHWAB = "schwab"
    ALPACA = "alpaca"
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
            self._health_status[broker_type] = True  # Assume healthy until proven otherwise
            self._consecutive_failures[broker_type] = 0
            self._last_checked[broker_type] = time.time()
            
    def record_success(self, broker_type: BrokerType) -> None:
        """Record a successful broker operation."""
        self._health_status[broker_type] = True
        self._consecutive_failures[broker_type] = 0
        self._last_checked[broker_type] = time.time()
        # Update metrics
        metrics.gauge(f"broker.health.{broker_type}", 1)
        metrics.gauge(f"broker.consecutive_failures.{broker_type}", 0)
        
    def record_failure(self, broker_type: BrokerType) -> None:
        """Record a failed broker operation."""
        self._consecutive_failures[broker_type] += 1
        self._last_checked[broker_type] = time.time()
        
        # Mark as unhealthy after configured number of failures
        if self._consecutive_failures[broker_type] >= settings.BROKER_FAILURE_THRESHOLD:
            if self._health_status[broker_type]:  # Only log and alert on status change
                logger.warning(f"Broker {broker_type} marked as unhealthy after {self._consecutive_failures[broker_type]} consecutive failures")
                
                # Import here to avoid circular dependency
                from app.core.alerts_manager import alert_manager
                alert_manager.send_alert(
                    f"Broker {broker_type} unavailable",
                    f"Broker {broker_type} has failed {self._consecutive_failures[broker_type]} consecutive operations",
                    level="error"
                )
            self._health_status[broker_type] = False
            
        # Update metrics
        if not self._health_status[broker_type]:
            metrics.gauge(f"broker.health.{broker_type}", 0)
        metrics.gauge(f"broker.consecutive_failures.{broker_type}", self._consecutive_failures[broker_type])
            
    def is_healthy(self, broker_type: BrokerType) -> bool:
        """Check if a broker is currently healthy."""
        # If it's been too long since we last checked, revert to healthy to force a retry
        time_since_check = time.time() - self._last_checked.get(broker_type, 0)
        if not self._health_status[broker_type] and time_since_check > settings.BROKER_RETRY_INTERVAL:
            logger.info(f"Broker {broker_type} retry period elapsed, marking for retry")
            self._health_status[broker_type] = True
            
        return self._health_status[broker_type]
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get a report of all broker health statuses."""
        report = {}
        for broker_type in BrokerType:
            report[broker_type] = {
                "healthy": self._health_status.get(broker_type, False),
                "consecutive_failures": self._consecutive_failures.get(broker_type, 0),
                "last_checked": self._last_checked.get(broker_type, 0)
            }
        return report


class BrokerFactory:
    """Factory for creating broker instances."""
    
    def __init__(self):
        """Initialize with registry of broker implementations."""
        self._registry = {}
        self._health_tracker = BrokerHealth()
        
        # Register built-in broker implementations
        self.register(BrokerType.PAPER, PaperBroker)
        
        # Import and register real broker implementations
        try:
            from app.services.broker.schwab import SchwabBroker
            self.register(BrokerType.SCHWAB, SchwabBroker)
            logger.info("Registered Schwab broker implementation")
        except ImportError as e:
            logger.warning(f"Could not register Schwab broker: {str(e)}")
            
        try:
            from app.services.broker.alpaca import AlpacaBroker
            self.register(BrokerType.ALPACA, AlpacaBroker)
            logger.info("Registered Alpaca broker implementation")
        except ImportError as e:
            logger.warning(f"Could not register Alpaca broker: {str(e)}")
    
    def register(self, broker_type: BrokerType, broker_class: Type[BaseBroker]) -> None:
        """Register a broker implementation."""
        self._registry[broker_type] = broker_class
        logger.info(f"Registered broker implementation: {broker_type}")
    
    def create(self, broker_type: Optional[BrokerType] = None, db: Session = None, 
              config: Optional[Dict[str, Any]] = None) -> BaseBroker:
        """Create a broker instance of the specified type."""
        # Use configured default if not specified
        if not broker_type:
            try:
                broker_type = BrokerType(settings.DEFAULT_BROKER)
            except ValueError:
                logger.warning(f"Invalid default broker: {settings.DEFAULT_BROKER}, falling back to paper")
                broker_type = BrokerType.PAPER
        
        # Get broker class from registry
        broker_class = self._registry.get(broker_type)
        
        if not broker_class:
            logger.error(f"No broker implementation found for: {broker_type}")
            # Fall back to paper trading if the requested type is not available
            broker_class = self._registry.get(BrokerType.PAPER)
            
        if not broker_class:
            raise ValueError(f"No broker implementations available")
        
        # Create and initialize broker instance with proper configuration
        if config is None:
            config = {}
            
        # Add sandbox/paper configuration based on environment
        if broker_type == BrokerType.SCHWAB:
            # Use sandbox in development/staging environments
            config.setdefault('sandbox', not settings.PRODUCTION_ENV)
        elif broker_type == BrokerType.ALPACA:
            # Use paper trading in development/staging environments
            config.setdefault('use_paper', not settings.PRODUCTION_ENV)
        
        return broker_class(db=db, **config)
    
    def get_health_tracker(self) -> BrokerHealth:
        """Get the broker health tracker instance."""
        return self._health_tracker
    
    def get_available_brokers(self) -> List[BrokerType]:
        """Get a list of all available broker types."""
        return list(self._registry.keys())
    
    def get_preferred_broker_order(self) -> List[BrokerType]:
        """Get the list of brokers in preferred order of use."""
        # Default priority order based on production settings
        if settings.PRODUCTION_ENV:
            preferred_order = settings.BROKER_PRIORITY_LIST
        else:
            # In development, prefer paper trading
            preferred_order = [BrokerType.PAPER]
            # Then add any real brokers for testing
            for broker_type in settings.BROKER_PRIORITY_LIST:
                if broker_type != BrokerType.PAPER:
                    preferred_order.append(broker_type)
        
        # Only include registered brokers
        return [broker for broker in preferred_order if broker in self._registry]


# Global factory instance
broker_factory = BrokerFactory()


class ResilientBroker:
    """A wrapper that provides resilient broker operations with failover."""
    
    def __init__(self, db: Session = None, config: Optional[Dict[str, Any]] = None):
        """Initialize with database session and optional configuration."""
        self.db = db
        self.config = config or {}
        self.health_tracker = broker_factory.get_health_tracker()
        
    def _execute_with_failover(self, method_name: str, *args, **kwargs) -> Tuple[Any, BrokerType]:
        """Execute a broker method with failover capabilities."""
        start_time = time.time()
        preferred_brokers = broker_factory.get_preferred_broker_order()
        
        # Try each broker in order of preference
        for broker_type in preferred_brokers:
            # Skip unhealthy brokers
            if not self.health_tracker.is_healthy(broker_type):
                logger.debug(f"Skipping unhealthy broker: {broker_type}")
                continue
            
            try:
                # Create broker instance
                broker = broker_factory.create(broker_type, self.db, self.config)
                
                # Find and call the requested method
                method = getattr(broker, method_name, None)
                if not method:
                    logger.warning(f"Method {method_name} not supported by broker {broker_type}")
                    continue
                
                # Execute operation with timing
                method_start = time.time()
                result = method(*args, **kwargs)
                method_duration = time.time() - method_start
                
                # Record metrics
                metrics.timing(f"broker.{broker_type}.{method_name}", method_duration * 1000)
                metrics.increment(f"broker.{broker_type}.{method_name}.success")
                
                # Record successful operation
                self.health_tracker.record_success(broker_type)
                
                logger.debug(f"Successfully executed {method_name} using broker {broker_type}")
                return result, broker_type
            
            except BrokerError as e:
                logger.warning(f"Broker {broker_type} operation {method_name} failed: {e}")
                metrics.increment(f"broker.{broker_type}.{method_name}.error")
                self.health_tracker.record_failure(broker_type)
            
            except Exception as e:
                logger.error(f"Unexpected error with broker {broker_type} for {method_name}: {e}", exc_info=True)
                metrics.increment(f"broker.{broker_type}.{method_name}.exception")
                self.health_tracker.record_failure(broker_type)
        
        # If we get here, all brokers failed
        total_duration = time.time() - start_time
        metrics.timing("broker.failover.total_duration", total_duration * 1000)
        metrics.increment("broker.failover.all_failed")
        
        error_msg = f"All available brokers failed for operation: {method_name}"
        logger.error(error_msg)
        
        # Import here to avoid circular dependency
        from app.core.alerts_manager import alert_manager
        alert_manager.send_alert(
            "Broker failover exhausted",
            f"All available brokers failed for operation: {method_name}",
            level="critical"
        )
        raise BrokerError(error_msg)
    
    # Implement broker interface methods using failover
    
    def execute_trade(self, trade, **kwargs):
        """Execute a trade with automatic failover."""
        result, broker_type = self._execute_with_failover("execute_trade", trade, **kwargs)
        # Record which broker handled the trade
        trade.executed_by = broker_type.value
        return result
    
    def get_account_info(self, account_id, **kwargs):
        """Get account information with automatic failover."""
        return self._execute_with_failover("get_account_info", account_id, **kwargs)[0]
    
    def get_positions(self, account_id, **kwargs):
        """Get positions with automatic failover."""
        return self._execute_with_failover("get_positions", account_id, **kwargs)[0]
    
    def get_trade_status(self, broker_order_id, **kwargs):
        """Get trade status with automatic failover."""
        return self._execute_with_failover("get_trade_status", broker_order_id, **kwargs)[0]
    
    def cancel_trade(self, broker_order_id, **kwargs):
        """Cancel a trade with automatic failover."""
        return self._execute_with_failover("cancel_trade", broker_order_id, **kwargs)[0]
    
    def get_order_history(self, account_id, **kwargs):
        """Get order history with automatic failover."""
        return self._execute_with_failover("get_order_history", account_id, **kwargs)[0]
    
    def get_trade_execution(self, broker_order_id, **kwargs):
        """Get trade execution details with automatic failover."""
        return self._execute_with_failover("get_trade_execution", broker_order_id, **kwargs)[0]
    
    def get_market_hours(self, market, **kwargs):
        """Get market hours with automatic failover."""
        return self._execute_with_failover("get_market_hours", market, **kwargs)[0]
    
    def get_quote(self, symbol, **kwargs):
        """Get quote with automatic failover."""
        return self._execute_with_failover("get_quote", symbol, **kwargs)[0]


def get_broker(broker_type: Optional[BrokerType] = None, db: Session = None, 
              config: Optional[Dict[str, Any]] = None) -> BaseBroker:
    """Get a broker instance.
    
    Args:
        broker_type: Type of broker to use (defaults to settings.DEFAULT_BROKER)
        db: Database session
        config: Additional configuration parameters
        
    Returns:
        An initialized broker instance
    """
    return broker_factory.create(broker_type, db, config)


def get_resilient_broker(db: Session = None, config: Optional[Dict[str, Any]] = None) -> ResilientBroker:
    """Get a resilient broker instance with failover capabilities.
    
    Args:
        db: Database session
        config: Additional configuration parameters
        
    Returns:
        A resilient broker instance with failover
    """
    return ResilientBroker(db=db, config=config)
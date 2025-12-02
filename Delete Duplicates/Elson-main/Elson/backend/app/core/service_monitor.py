"""
Service monitoring and health check system for the Elson Wealth App.

This module provides functionality to:
1. Monitor critical services (database, Redis, third-party APIs)
2. Detect service degradation or failures
3. Send alerts for service issues
4. Track service health metrics
"""

import logging
import time
import threading
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional, Set, Union, Tuple
from enum import Enum
import traceback
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

from .config import settings
from .metrics import record_metric
from .alerts import (
    AlertCategory,
    AlertSeverity,
    send_error_alert,
    send_critical_alert,
    send_warning_alert,
    send_info_alert,
    alert_from_exception
)

logger = logging.getLogger(__name__)

class ServiceStatus(str, Enum):
    """Possible states for service health."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ServiceType(str, Enum):
    """Types of services being monitored."""
    DATABASE = "database"
    REDIS = "redis"
    API = "api"
    BROKER = "broker"
    MARKET_DATA = "market_data"
    PAYMENT = "payment"
    WEBSOCKET = "websocket"
    QUEUE = "queue"
    CACHE = "cache"
    INTERNAL = "internal"

class ServiceCheck:
    """A check to verify a service's health."""
    
    def __init__(
        self,
        name: str,
        service_type: ServiceType,
        check_function: Callable[[], bool],
        check_interval_seconds: int = 60,
        timeout_seconds: int = 5,
        retry_count: int = 3,
        alert_on_failure: bool = True,
        description: str = "",
        is_critical: bool = False
    ):
        """
        Initialize a service health check.
        
        Args:
            name: Human-readable name for the check
            service_type: Type of service being checked
            check_function: Function that returns True if healthy, False otherwise
            check_interval_seconds: How often to run the check
            timeout_seconds: Maximum time to wait for check to complete
            retry_count: Number of retries before marking as unhealthy
            alert_on_failure: Whether to send alerts on failures
            description: Detailed description of the check
            is_critical: Whether this is a critical service check
        """
        self.name = name
        self.service_type = service_type
        self.check_function = check_function
        self.check_interval_seconds = check_interval_seconds
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.alert_on_failure = alert_on_failure
        self.description = description
        self.is_critical = is_critical
        
        # State tracking
        self.status = ServiceStatus.UNKNOWN
        self.last_check_time = None
        self.last_successful_check_time = None
        self.failure_count = 0
        self.total_checks = 0
        self.total_failures = 0
        self.last_error = None
        self.last_execution_time = 0
        
    def run_check(self) -> bool:
        """
        Run the service check and update status.
        
        Returns:
            True if check passes, False otherwise
        """
        self.last_check_time = datetime.now()
        self.total_checks += 1
        start_time = time.time()
        
        success = False
        error = None
        
        try:
            # Run the check with timeout
            success = self.check_function()
            
            if success:
                self.last_successful_check_time = self.last_check_time
                self.failure_count = 0
                if self.status != ServiceStatus.HEALTHY:
                    self._handle_recovery()
                self.status = ServiceStatus.HEALTHY
            else:
                self.failure_count += 1
                self.total_failures += 1
                if self.failure_count >= self.retry_count:
                    self._handle_failure("Check returned False")
                    self.status = ServiceStatus.UNHEALTHY
                else:
                    self.status = ServiceStatus.DEGRADED
        except Exception as e:
            self.failure_count += 1
            self.total_failures += 1
            error = e
            self.last_error = str(e)
            
            if self.failure_count >= self.retry_count:
                self._handle_failure(f"Check raised exception: {str(e)}")
                self.status = ServiceStatus.UNHEALTHY
            else:
                self.status = ServiceStatus.DEGRADED
        finally:
            execution_time = time.time() - start_time
            self.last_execution_time = execution_time
            
            # Record metrics
            record_metric(
                "service_check", 
                execution_time * 1000,  # convert to ms
                {
                    "service": self.name,
                    "type": self.service_type,
                    "status": self.status,
                    "success": "true" if success else "false"
                }
            )
            
            return success
    
    def _handle_failure(self, error_message: str) -> None:
        """Handle a check failure by sending alerts if configured."""
        if not self.alert_on_failure:
            return
            
        # Prepare metadata for alert
        metadata = {
            "service_type": self.service_type,
            "check_name": self.name,
            "failure_count": self.failure_count,
            "last_successful_check": (
                self.last_successful_check_time.isoformat() 
                if self.last_successful_check_time else "Never"
            ),
            "execution_time": f"{self.last_execution_time:.2f}s"
        }
        
        if self.last_error:
            metadata["error"] = self.last_error
            
        # Format the alert message
        message = f"""
Service check '{self.name}' has failed.

Error: {error_message}

The service has failed {self.failure_count} consecutive times.
Last successful check: {metadata['last_successful_check']}

Description: {self.description}
"""

        # Send appropriate alert based on whether service is critical
        if self.is_critical:
            send_critical_alert(
                title=f"Critical Service Failure: {self.name}",
                message=message,
                category=AlertCategory.INFRASTRUCTURE,
                source=f"service_monitor:{self.service_type}",
                metadata=metadata
            )
        else:
            send_error_alert(
                title=f"Service Check Failed: {self.name}",
                message=message,
                category=AlertCategory.INFRASTRUCTURE,
                source=f"service_monitor:{self.service_type}",
                metadata=metadata
            )
    
    def _handle_recovery(self) -> None:
        """Handle a service recovery after failures."""
        if not self.alert_on_failure or self.total_failures == 0:
            return
            
        # Only send recovery alerts if we previously had an alert-worthy failure
        if self.failure_count < self.retry_count:
            return
            
        message = f"""
Service check '{self.name}' has recovered and is now healthy.

Previous Status: {self.status}
Down Time: {datetime.now() - self.last_successful_check_time if self.last_successful_check_time else 'Unknown'}

Description: {self.description}
"""
        
        send_info_alert(
            title=f"Service Recovered: {self.name}",
            message=message,
            category=AlertCategory.INFRASTRUCTURE,
            source=f"service_monitor:{self.service_type}",
            metadata={
                "service_type": self.service_type,
                "check_name": self.name,
                "previous_status": self.status,
                "is_critical": self.is_critical
            }
        )
        
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the check's current status."""
        return {
            "name": self.name,
            "service_type": self.service_type,
            "status": self.status,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_successful_check": (
                self.last_successful_check_time.isoformat() 
                if self.last_successful_check_time else None
            ),
            "failure_count": self.failure_count,
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "success_rate": (
                (self.total_checks - self.total_failures) / self.total_checks * 100
                if self.total_checks > 0 else 0
            ),
            "last_error": self.last_error,
            "last_execution_time": self.last_execution_time,
            "is_critical": self.is_critical,
            "description": self.description
        }

class ServiceMonitor:
    """
    Monitors critical services with scheduled health checks.
    """
    
    def __init__(self):
        """Initialize the service monitor."""
        self.checks: Dict[str, ServiceCheck] = {}
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._lock = threading.RLock()
        
    def add_check(self, check: ServiceCheck) -> None:
        """Add a service check to the monitor."""
        with self._lock:
            self.checks[check.name] = check
            logger.info(f"Added service check: {check.name} ({check.service_type})")
            
    def remove_check(self, check_name: str) -> bool:
        """Remove a service check from the monitor."""
        with self._lock:
            if check_name in self.checks:
                del self.checks[check_name]
                logger.info(f"Removed service check: {check_name}")
                return True
            return False
            
    def start(self) -> None:
        """Start the monitoring thread."""
        if self.running:
            logger.warning("Service monitor already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        logger.info("Service monitor started")
        
    def stop(self) -> None:
        """Stop the monitoring thread."""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.executor.shutdown(wait=False)
        logger.info("Service monitor stopped")
        
    def _monitoring_loop(self) -> None:
        """Main loop for monitoring services."""
        logger.info("Service monitoring loop started")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Get copy of checks to avoid modifying during iteration
                with self._lock:
                    checks = list(self.checks.values())
                
                # Check which services need to be checked
                for check in checks:
                    # Skip if not time to check yet
                    if (check.last_check_time is not None and 
                        (current_time - check.last_check_time).total_seconds() < check.check_interval_seconds):
                        continue
                        
                    # Submit check to thread pool
                    self.executor.submit(check.run_check)
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                alert_from_exception(
                    error=e,
                    title="Error in Service Monitoring Loop",
                    category=AlertCategory.SYSTEM,
                    source="service_monitor"
                )
                
            # Sleep for a short time before checking again
            time.sleep(1)
            
    def get_service_status(self, service_type: Optional[ServiceType] = None) -> Dict[str, Any]:
        """
        Get the current status of all services.
        
        Args:
            service_type: Optional filter for service type
            
        Returns:
            Dictionary with service status information
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "checks": []
        }
        
        with self._lock:
            for check in self.checks.values():
                if service_type is None or check.service_type == service_type:
                    result["checks"].append(check.get_status_summary())
                    
        # Add overall status
        total_checks = len(result["checks"])
        healthy_checks = sum(1 for c in result["checks"] if c["status"] == ServiceStatus.HEALTHY)
        critical_unhealthy = any(c["is_critical"] and c["status"] == ServiceStatus.UNHEALTHY 
                                for c in result["checks"])
        
        if total_checks == 0:
            result["overall_status"] = ServiceStatus.UNKNOWN
        elif healthy_checks == total_checks:
            result["overall_status"] = ServiceStatus.HEALTHY
        elif critical_unhealthy:
            result["overall_status"] = ServiceStatus.UNHEALTHY
        else:
            result["overall_status"] = ServiceStatus.DEGRADED
            
        result["healthy_count"] = healthy_checks
        result["total_count"] = total_checks
        result["health_percentage"] = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            
        return result
        
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all service checks immediately.
        
        Returns:
            Dictionary with results of all checks
        """
        results = {}
        
        with self._lock:
            for name, check in self.checks.items():
                results[name] = check.run_check()
                
        return results
        
    def run_check(self, check_name: str) -> Optional[bool]:
        """
        Run a specific check immediately.
        
        Args:
            check_name: Name of the check to run
            
        Returns:
            Result of the check or None if check not found
        """
        with self._lock:
            check = self.checks.get(check_name)
            if check:
                return check.run_check()
        return None

# Create standard health checks

def create_database_check() -> ServiceCheck:
    """Create a check for database health."""
    def check_database():
        from ..db.database import engine
        
        try:
            # Simple query to check database connectivity
            with engine.connect() as conn:
                result = conn.execute("SELECT 1").scalar()
                return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name="database_connectivity",
        service_type=ServiceType.DATABASE,
        check_function=check_database,
        check_interval_seconds=30,
        description="Check database connection and basic query functionality",
        is_critical=True
    )
    
def create_redis_check() -> ServiceCheck:
    """Create a check for Redis health."""
    def check_redis():
        from ..db.database import get_redis_connection
        
        try:
            # Test Redis connection with a simple operation
            redis = get_redis_connection()
            redis.set("service_check", "1")
            result = redis.get("service_check")
            redis.delete("service_check")
            return result == b"1"
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name="redis_connectivity",
        service_type=ServiceType.REDIS,
        check_function=check_redis,
        check_interval_seconds=30,
        description="Check Redis connection and basic operations",
        is_critical=True
    )
    
def create_api_provider_check(provider_name: str, api_key_field: str) -> ServiceCheck:
    """
    Create a check for an API provider's health.
    
    Args:
        provider_name: Name of the API provider
        api_key_field: Field name in settings containing the API key
    """
    def check_api_provider():
        from ..services.external_api.factory import get_api_client
        
        # Skip if no API key configured
        api_key = getattr(settings, api_key_field, None)
        if not api_key:
            logger.debug(f"Skipping {provider_name} check - no API key configured")
            return True
            
        try:
            # Get client and test basic functionality
            client = get_api_client(provider_name.lower())
            if not client:
                logger.warning(f"No client available for {provider_name}")
                return False
                
            # For each provider, implement appropriate health check
            if provider_name.lower() == "alpha_vantage":
                # Test a simple quote request
                result = client.get_quote("AAPL")
                return bool(result and "price" in result)
            elif provider_name.lower() == "finnhub":
                # Test company profile
                result = client.get_company_profile("AAPL")
                return bool(result and "name" in result)
            elif provider_name.lower() == "fmp":
                # Test basic market data
                result = client.get_quote("AAPL")
                return bool(result and "price" in result)
            elif provider_name.lower() == "polygon":
                # Test last trade
                result = client.get_last_trade("AAPL")
                return bool(result and "price" in result)
            else:
                # Default check - just verify client exists
                return client is not None
                
        except Exception as e:
            logger.error(f"{provider_name} API health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name=f"{provider_name.lower()}_api",
        service_type=ServiceType.API,
        check_function=check_api_provider,
        check_interval_seconds=300,  # Every 5 minutes to avoid rate limits
        retry_count=2,
        timeout_seconds=10,
        description=f"Check {provider_name} API connectivity and basic functionality",
        is_critical=False  # Not critical since we have fallbacks
    )
    
def create_broker_check(broker_name: str) -> ServiceCheck:
    """Create a check for broker API health."""
    def check_broker():
        from ..services.broker.factory import get_broker
        
        # Skip check if broker is not default
        if settings.DEFAULT_BROKER.lower() != broker_name.lower():
            logger.debug(f"Skipping {broker_name} check - not default broker")
            return True
            
        try:
            # Get broker instance and test connectivity
            broker = get_broker(broker_name.lower())
            if not broker:
                logger.warning(f"No broker available for {broker_name}")
                return False
                
            # Check account status or similar non-destructive operation
            # This will vary depending on the broker API
            if hasattr(broker, "get_account"):
                result = broker.get_account()
                return bool(result)
            elif hasattr(broker, "check_api_status"):
                return broker.check_api_status()
            else:
                logger.warning(f"No suitable health check method for {broker_name}")
                return True
                
        except Exception as e:
            logger.error(f"{broker_name} broker health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name=f"{broker_name.lower()}_broker",
        service_type=ServiceType.BROKER,
        check_function=check_broker,
        check_interval_seconds=300,  # Every 5 minutes
        retry_count=3,
        description=f"Check {broker_name} broker API connectivity",
        is_critical=broker_name.lower() == settings.DEFAULT_BROKER.lower()
    )
    
def create_websocket_server_check() -> ServiceCheck:
    """Create a check for WebSocket server health."""
    def check_websocket_server():
        from ..services.market_data_streaming import get_streaming_service
        
        try:
            # Check if streaming service is running
            service = get_streaming_service()
            return service.stream_active
        except Exception as e:
            logger.error(f"WebSocket server health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name="websocket_server",
        service_type=ServiceType.WEBSOCKET,
        check_function=check_websocket_server,
        check_interval_seconds=60,
        description="Check WebSocket server status",
        is_critical=True
    )
    
def create_background_tasks_check() -> ServiceCheck:
    """Create a check for background task processing."""
    def check_background_tasks():
        from ..core.background import get_queue_status
        
        try:
            # Check if background worker is alive and queue is not backed up
            status = get_queue_status()
            if not status.get("worker_alive", False):
                return False
                
            # Check if queue size is reasonable
            queue_size = status.get("queue_size", 0)
            return queue_size < 100  # Consider health check failed if queue is backed up
        except Exception as e:
            logger.error(f"Background tasks health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name="background_tasks",
        service_type=ServiceType.QUEUE,
        check_function=check_background_tasks,
        check_interval_seconds=60,
        description="Check background task processing system",
        is_critical=True
    )
    
def create_stripe_check() -> ServiceCheck:
    """Create a check for Stripe API health."""
    def check_stripe():
        # Skip if no Stripe API key configured
        if not settings.STRIPE_API_KEY:
            logger.debug("Skipping Stripe check - no API key configured")
            return True
            
        try:
            # Use direct API call to test Stripe connectivity
            import stripe
            stripe.api_key = settings.STRIPE_API_KEY
            
            # List a small number of customers as a simple test
            customers = stripe.Customer.list(limit=1)
            return True
        except ImportError:
            logger.warning("Stripe Python package not installed")
            return False
        except Exception as e:
            logger.error(f"Stripe API health check failed: {str(e)}")
            return False
            
    return ServiceCheck(
        name="stripe_api",
        service_type=ServiceType.PAYMENT,
        check_function=check_stripe,
        check_interval_seconds=300,  # Every 5 minutes
        description="Check Stripe payment processing API",
        is_critical=True if settings.ENVIRONMENT == "production" else False
    )

# Singleton instance
_service_monitor = None

def get_service_monitor() -> ServiceMonitor:
    """Get or create the service monitor singleton."""
    global _service_monitor
    if _service_monitor is None:
        _service_monitor = ServiceMonitor()
        
        # Add standard checks
        _service_monitor.add_check(create_database_check())
        _service_monitor.add_check(create_redis_check())
        
        # Add API provider checks
        _service_monitor.add_check(create_api_provider_check("alpha_vantage", "ALPHA_VANTAGE_API_KEY"))
        _service_monitor.add_check(create_api_provider_check("finnhub", "FINNHUB_API_KEY"))
        _service_monitor.add_check(create_api_provider_check("fmp", "FMP_API_KEY"))
        _service_monitor.add_check(create_api_provider_check("polygon", "POLYGON_API_KEY"))
        
        # Add broker checks
        _service_monitor.add_check(create_broker_check("schwab"))
        _service_monitor.add_check(create_broker_check("alpaca"))
        
        # Add other service checks
        _service_monitor.add_check(create_websocket_server_check())
        _service_monitor.add_check(create_background_tasks_check())
        _service_monitor.add_check(create_stripe_check())
        
    return _service_monitor

def start_service_monitor() -> None:
    """Start the service monitoring system."""
    monitor = get_service_monitor()
    monitor.start()
    
def stop_service_monitor() -> None:
    """Stop the service monitoring system."""
    global _service_monitor
    if _service_monitor:
        _service_monitor.stop()
        _service_monitor = None
    
def get_service_status() -> Dict[str, Any]:
    """Get the current status of all monitored services."""
    monitor = get_service_monitor()
    return monitor.get_service_status()
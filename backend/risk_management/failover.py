"""
Failover Management for Elson Trading Bot Platform.

This module provides automatic service health monitoring and failover capabilities
for critical platform services. It can:
1. Monitor the health of critical services
2. Attempt to restart failed services
3. Switch to redundant instances
4. Send alerts on failures
5. Handle graceful degradation of functionality
6. Integrate with the anomaly detection system for proactive failure prevention

The module uses a health check system to periodically check service availability
and takes appropriate actions based on predefined policies. It also responds to 
anomalies detected by the anomaly detection system, triggering preemptive failover
or degraded operations when anomalous conditions are detected.
"""

import json
import logging
import os
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import redis
import requests

from app.core.alerts import AlertManager
from app.core.alerts_manager import alert_manager
from app.core.config import settings
from prometheus_client import Counter, Gauge
from app.services.anomaly_detector import AnomalySeverity, AnomalyType, anomaly_detector

# Configure logging
logger = logging.getLogger("failover")

# Create metrics
health_check_status = Gauge(
    "health_check_status",
    "Current status of service health checks (1=healthy, 0=unhealthy)",
    ["service"],
)

failover_attempts = Counter(
    "failover_attempts_total", "Number of failover attempts", ["service", "outcome"]
)

time_since_last_healthy = Gauge(
    "time_since_last_healthy_seconds",
    "Time since the service was last healthy",
    ["service"],
)


# Service states
class ServiceState:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    FAILOVER_ACTIVE = "failover_active"
    RECOVERED = "recovered"
    UNKNOWN = "unknown"


# Service types
class ServiceType:
    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    BROKER = "broker"
    TRADING_ENGINE = "trading_engine"
    MARKET_DATA = "market_data"
    AUTHENTICATION = "authentication"


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        service_id: str,
        status: str,
        message: str = "",
        timestamp: Optional[datetime] = None,
        response_time: float = 0.0,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.service_id = service_id
        self.status = status
        self.message = message
        self.timestamp = timestamp or datetime.now()
        self.response_time = response_time
        self.data = data or {}


class HealthCheck:
    """Base class for health checks."""

    def __init__(self, service_id: str, service_type: str, description: str = ""):
        self.service_id = service_id
        self.service_type = service_type
        self.description = description
        self.last_check_time = None
        self.last_status = ServiceState.UNKNOWN
        self.consecutive_failures = 0
        self.last_healthy_time = None

    def check(self) -> HealthCheckResult:
        """Perform the health check and return result."""
        raise NotImplementedError("Subclasses must implement check()")

    def update_status(self, result: HealthCheckResult) -> None:
        """Update the health check status with a new result."""
        self.last_check_time = result.timestamp
        self.last_status = result.status

        if result.status == ServiceState.HEALTHY:
            self.consecutive_failures = 0
            self.last_healthy_time = result.timestamp
            health_check_status.labels(service=self.service_id).set(1)
        else:
            self.consecutive_failures += 1
            health_check_status.labels(service=self.service_id).set(0)

        # Update time since last healthy
        if self.last_healthy_time:
            seconds_since_healthy = (
                datetime.now() - self.last_healthy_time
            ).total_seconds()
            time_since_last_healthy.labels(service=self.service_id).set(
                seconds_since_healthy
            )


class HttpHealthCheck(HealthCheck):
    """HTTP-based health check."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        endpoint: str,
        method: str = "GET",
        timeout: float = 5.0,
        headers: Optional[Dict[str, str]] = None,
        expected_status: int = 200,
        expected_content: Optional[str] = None,
        description: str = "",
    ):
        super().__init__(service_id, service_type, description)
        self.endpoint = endpoint
        self.method = method
        self.timeout = timeout
        self.headers = headers or {}
        self.expected_status = expected_status
        self.expected_content = expected_content

    def check(self) -> HealthCheckResult:
        """Perform HTTP health check."""
        start_time = time.time()

        try:
            response = requests.request(
                method=self.method,
                url=self.endpoint,
                headers=self.headers,
                timeout=self.timeout,
            )

            response_time = time.time() - start_time

            # Check status code
            if response.status_code != self.expected_status:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.FAILED,
                    f"Unexpected status code: {response.status_code} (expected {self.expected_status})",
                    response_time=response_time,
                    data={"status_code": response.status_code},
                )

            # Check content if specified
            if self.expected_content and self.expected_content not in response.text:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.FAILED,
                    f"Expected content not found in response",
                    response_time=response_time,
                )

            # All checks passed
            return HealthCheckResult(
                self.service_id,
                ServiceState.HEALTHY,
                "Service is healthy",
                response_time=response_time,
                data={"status_code": response.status_code},
            )

        except requests.exceptions.Timeout:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Request timed out after {self.timeout}s",
                response_time=time.time() - start_time,
            )
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                "Connection error",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class PostgreSQLHealthCheck(HealthCheck):
    """PostgreSQL health check."""

    def __init__(
        self,
        service_id: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: Optional[str] = None,
        timeout: float = 5.0,
        description: str = "",
    ):
        super().__init__(service_id, ServiceType.DATABASE, description)
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.timeout = timeout

    def check(self) -> HealthCheckResult:
        """Perform PostgreSQL health check."""
        start_time = time.time()

        try:
            import psycopg2

            # Set environment variable for password if provided
            env = os.environ.copy()
            if self.password:
                env["PGPASSWORD"] = self.password

            # Use psycopg2 to connect and run a simple query
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password or "",
                connect_timeout=self.timeout,
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            conn.close()

            response_time = time.time() - start_time

            if result and result[0] == 1:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.HEALTHY,
                    "Database is healthy",
                    response_time=response_time,
                )
            else:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.FAILED,
                    "Unexpected query result",
                    response_time=response_time,
                )

        except psycopg2.OperationalError as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Database connection failed: {str(e)}",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class RedisHealthCheck(HealthCheck):
    """Redis health check."""

    def __init__(
        self,
        service_id: str,
        host: str,
        port: int,
        password: Optional[str] = None,
        timeout: float = 5.0,
        description: str = "",
    ):
        super().__init__(service_id, ServiceType.CACHE, description)
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout

    def check(self) -> HealthCheckResult:
        """Perform Redis health check."""
        start_time = time.time()

        try:
            # Connect to Redis
            r = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout,
            )

            # Set a test key
            test_key = f"health_check:{self.service_id}:{datetime.now().isoformat()}"
            r.set(test_key, "1", ex=60)  # Expire after 60s

            # Verify the key was set
            value = r.get(test_key)

            response_time = time.time() - start_time

            if value and value.decode() == "1":
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.HEALTHY,
                    "Redis is healthy",
                    response_time=response_time,
                    data={"test_key": test_key},
                )
            else:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.FAILED,
                    "Failed to set and retrieve test key",
                    response_time=response_time,
                )

        except redis.exceptions.ConnectionError:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                "Redis connection failed",
                response_time=time.time() - start_time,
            )
        except redis.exceptions.TimeoutError:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Redis operation timed out after {self.timeout}s",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class TCPHealthCheck(HealthCheck):
    """TCP health check."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        host: str,
        port: int,
        timeout: float = 5.0,
        description: str = "",
    ):
        super().__init__(service_id, service_type, description)
        self.host = host
        self.port = port
        self.timeout = timeout

    def check(self) -> HealthCheckResult:
        """Perform TCP health check."""
        start_time = time.time()

        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            # Attempt to connect
            sock.connect((self.host, self.port))
            sock.close()

            response_time = time.time() - start_time

            return HealthCheckResult(
                self.service_id,
                ServiceState.HEALTHY,
                f"TCP connection successful to {self.host}:{self.port}",
                response_time=response_time,
            )

        except socket.timeout:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"TCP connection timed out after {self.timeout}s",
                response_time=time.time() - start_time,
            )
        except ConnectionRefusedError:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"TCP connection refused to {self.host}:{self.port}",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class KubernetesHealthCheck(HealthCheck):
    """Kubernetes pod/service health check."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        namespace: str,
        resource_type: str,  # "pod", "deployment", "statefulset", etc.
        resource_name: str,
        min_ready: int = 1,
        description: str = "",
    ):
        super().__init__(service_id, service_type, description)
        self.namespace = namespace
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.min_ready = min_ready

    def check(self) -> HealthCheckResult:
        """Perform Kubernetes health check."""
        start_time = time.time()

        try:
            # Use kubectl to check resource status
            cmd = [
                "kubectl",
                "get",
                self.resource_type,
                self.resource_name,
                "-n",
                self.namespace,
                "-o",
                "json",
            ]

            process = subprocess.run(cmd, capture_output=True, text=True, check=True)

            response_time = time.time() - start_time

            # Parse JSON output
            resource = json.loads(process.stdout)

            # Check status based on resource type
            if self.resource_type == "pod":
                phase = resource.get("status", {}).get("phase", "")
                if phase == "Running":
                    return HealthCheckResult(
                        self.service_id,
                        ServiceState.HEALTHY,
                        f"Pod {self.resource_name} is running",
                        response_time=response_time,
                        data={"phase": phase},
                    )
                else:
                    return HealthCheckResult(
                        self.service_id,
                        ServiceState.FAILED,
                        f"Pod {self.resource_name} is in {phase} phase",
                        response_time=response_time,
                        data={"phase": phase},
                    )

            elif self.resource_type in ["deployment", "statefulset", "replicaset"]:
                ready_replicas = resource.get("status", {}).get("readyReplicas", 0)
                if ready_replicas >= self.min_ready:
                    return HealthCheckResult(
                        self.service_id,
                        ServiceState.HEALTHY,
                        f"{self.resource_type.capitalize()} {self.resource_name} has {ready_replicas} ready replicas",
                        response_time=response_time,
                        data={"ready_replicas": ready_replicas},
                    )
                else:
                    return HealthCheckResult(
                        self.service_id,
                        ServiceState.FAILED,
                        f"{self.resource_type.capitalize()} {self.resource_name} has only {ready_replicas} ready replicas (min: {self.min_ready})",
                        response_time=response_time,
                        data={"ready_replicas": ready_replicas},
                    )

            else:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.UNKNOWN,
                    f"Unknown resource type: {self.resource_type}",
                    response_time=response_time,
                )

        except subprocess.CalledProcessError as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"kubectl command failed: {e.stderr}",
                response_time=time.time() - start_time,
            )
        except Exception as e:
            return HealthCheckResult(
                self.service_id,
                ServiceState.FAILED,
                f"Health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class AnomalyBasedHealthCheck(HealthCheck):
    """Health check based on anomaly detection results."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        entity_id: str,
        anomaly_types: List[str],
        severity_threshold: str = AnomalySeverity.WARNING,
        lookback_minutes: int = 5,
        description: str = "",
    ):
        super().__init__(service_id, service_type, description)
        self.entity_id = entity_id
        self.anomaly_types = anomaly_types
        self.severity_threshold = severity_threshold
        self.lookback_minutes = lookback_minutes

    def check(self) -> HealthCheckResult:
        """Check for anomalies that would affect service health."""
        start_time = time.time()

        try:
            # Calculate lookback time
            lookback_time = datetime.utcnow() - timedelta(minutes=self.lookback_minutes)

            # Get recent anomalies for this entity
            anomalies = anomaly_detector.get_anomaly_history(
                entity_id=self.entity_id, start_time=lookback_time, limit=10
            )

            # Filter by anomaly types and severity
            relevant_anomalies = []
            severity_levels = {
                AnomalySeverity.INFO: 0,
                AnomalySeverity.WARNING: 1,
                AnomalySeverity.CRITICAL: 2,
            }
            severity_threshold_level = severity_levels.get(self.severity_threshold, 1)

            for anomaly in anomalies:
                if anomaly.get("type") in self.anomaly_types:
                    severity = anomaly.get("severity", AnomalySeverity.INFO)
                    severity_level = severity_levels.get(severity, 0)

                    if severity_level >= severity_threshold_level:
                        relevant_anomalies.append(anomaly)

            response_time = time.time() - start_time

            # Determine state based on anomalies
            if not relevant_anomalies:
                return HealthCheckResult(
                    self.service_id,
                    ServiceState.HEALTHY,
                    f"No significant anomalies detected for {self.entity_id}",
                    response_time=response_time,
                    data={"anomaly_count": 0},
                )
            else:
                # Check if any are critical
                has_critical = any(
                    a.get("severity") == AnomalySeverity.CRITICAL
                    for a in relevant_anomalies
                )

                if has_critical:
                    state = ServiceState.FAILED
                    message = f"Critical anomalies detected for {self.entity_id}"
                else:
                    state = ServiceState.DEGRADED
                    message = f"Warning anomalies detected for {self.entity_id}"

                return HealthCheckResult(
                    self.service_id,
                    state,
                    message,
                    response_time=response_time,
                    data={
                        "anomaly_count": len(relevant_anomalies),
                        "anomalies": relevant_anomalies[
                            :3
                        ],  # Include the first few anomalies in the result
                    },
                )

        except Exception as e:
            logger.error(
                f"Error in anomaly-based health check for {self.service_id}: {e}"
            )
            return HealthCheckResult(
                self.service_id,
                ServiceState.UNKNOWN,
                f"Anomaly health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class CompositeHealthCheck(HealthCheck):
    """Combines multiple health checks with configurable logic."""

    def __init__(
        self,
        service_id: str,
        service_type: str,
        health_checks: List[HealthCheck],
        require_all_healthy: bool = False,  # If True, all checks must pass; if False, at least one must pass
        description: str = "",
        weight_anomaly_checks: bool = True,  # If True, anomaly checks can degrade but not fail the service
    ):
        super().__init__(service_id, service_type, description)
        self.health_checks = health_checks
        self.require_all_healthy = require_all_healthy
        self.weight_anomaly_checks = weight_anomaly_checks

    def check(self) -> HealthCheckResult:
        """Perform all health checks and combine results."""
        start_time = time.time()

        try:
            results = []
            for hc in self.health_checks:
                results.append(hc.check())

            response_time = time.time() - start_time

            # Count statuses
            status_counts = {
                ServiceState.HEALTHY: 0,
                ServiceState.DEGRADED: 0,
                ServiceState.FAILED: 0,
                ServiceState.UNKNOWN: 0,
            }

            for result in results:
                status_counts[result.status] = status_counts.get(result.status, 0) + 1

            # Apply special handling for anomaly-based checks if needed
            anomaly_results = []
            regular_results = []

            if self.weight_anomaly_checks:
                for i, result in enumerate(results):
                    if isinstance(self.health_checks[i], AnomalyBasedHealthCheck):
                        anomaly_results.append(result)
                    else:
                        regular_results.append(result)

                # If we have both types and regular checks pass, anomalies can at worst degrade but not fail
                if regular_results and anomaly_results:
                    regular_failed = any(
                        r.status == ServiceState.FAILED for r in regular_results
                    )
                    anomaly_failed = any(
                        r.status == ServiceState.FAILED for r in anomaly_results
                    )

                    if not regular_failed and anomaly_failed:
                        # Downgrade anomaly failures to degraded
                        for i, result in enumerate(results):
                            if (
                                isinstance(
                                    self.health_checks[i], AnomalyBasedHealthCheck
                                )
                                and result.status == ServiceState.FAILED
                            ):
                                result.status = ServiceState.DEGRADED
                                result.message = (
                                    f"Anomaly degradation: {result.message}"
                                )

                        # Recalculate counts
                        status_counts = {
                            ServiceState.HEALTHY: 0,
                            ServiceState.DEGRADED: 0,
                            ServiceState.FAILED: 0,
                            ServiceState.UNKNOWN: 0,
                        }

                        for result in results:
                            status_counts[result.status] = (
                                status_counts.get(result.status, 0) + 1
                            )

            # Determine overall status
            overall_status = ServiceState.UNKNOWN
            if self.require_all_healthy:
                # All must be healthy for service to be healthy
                if status_counts[ServiceState.FAILED] > 0:
                    overall_status = ServiceState.FAILED
                elif status_counts[ServiceState.DEGRADED] > 0:
                    overall_status = ServiceState.DEGRADED
                elif status_counts[ServiceState.HEALTHY] == len(results):
                    overall_status = ServiceState.HEALTHY
                else:
                    overall_status = ServiceState.UNKNOWN
            else:
                # At least one healthy check required
                if status_counts[ServiceState.HEALTHY] > 0:
                    if status_counts[ServiceState.FAILED] > 0:
                        overall_status = ServiceState.DEGRADED
                    else:
                        overall_status = ServiceState.HEALTHY
                elif status_counts[ServiceState.DEGRADED] > 0:
                    overall_status = ServiceState.DEGRADED
                elif status_counts[ServiceState.FAILED] > 0:
                    overall_status = ServiceState.FAILED
                else:
                    overall_status = ServiceState.UNKNOWN

            # Build message
            if overall_status == ServiceState.HEALTHY:
                message = f"All checks passed for {self.service_id}"
            elif overall_status == ServiceState.DEGRADED:
                message = f"Service {self.service_id} is degraded"
            elif overall_status == ServiceState.FAILED:
                message = f"Service {self.service_id} has failed"
            else:
                message = f"Service {self.service_id} status is unknown"

            # Include details from individual checks
            details = []
            for i, result in enumerate(results):
                check_name = self.health_checks[i].__class__.__name__
                details.append(
                    {
                        "check": check_name,
                        "status": result.status,
                        "message": result.message,
                        "response_time": result.response_time,
                    }
                )

            return HealthCheckResult(
                self.service_id,
                overall_status,
                message,
                response_time=response_time,
                data={"status_counts": status_counts, "details": details},
            )

        except Exception as e:
            logger.error(f"Error in composite health check for {self.service_id}: {e}")
            return HealthCheckResult(
                self.service_id,
                ServiceState.UNKNOWN,
                f"Composite health check failed: {str(e)}",
                response_time=time.time() - start_time,
            )


class FailoverAction:
    """Base class for failover actions."""

    def __init__(self, service_id: str, description: str = ""):
        self.service_id = service_id
        self.description = description

    def execute(self) -> Tuple[bool, str]:
        """Execute the failover action.

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        raise NotImplementedError("Subclasses must implement execute()")


class RestartServiceAction(FailoverAction):
    """Action to restart a service."""

    def __init__(
        self, service_id: str, command: List[str], description: str = "Restart service"
    ):
        super().__init__(service_id, description)
        self.command = command

    def execute(self) -> Tuple[bool, str]:
        """Execute the service restart command."""
        try:
            logger.info(
                f"Executing restart command for {self.service_id}: {' '.join(self.command)}"
            )
            process = subprocess.run(
                self.command, capture_output=True, text=True, check=True
            )

            return (
                True,
                f"Service {self.service_id} restarted successfully: {process.stdout}",
            )

        except subprocess.CalledProcessError as e:
            return False, f"Failed to restart service {self.service_id}: {e.stderr}"

        except Exception as e:
            return False, f"Error restarting service {self.service_id}: {str(e)}"


class SwitchToReplicaAction(FailoverAction):
    """Action to switch to a replica/standby instance."""

    def __init__(
        self,
        service_id: str,
        primary_config_key: str,
        replica_config_key: str,
        description: str = "Switch to replica",
    ):
        super().__init__(service_id, description)
        self.primary_config_key = primary_config_key
        self.replica_config_key = replica_config_key

    def execute(self) -> Tuple[bool, str]:
        """Execute the switch to replica."""
        try:
            # This is a simplified example - in a real implementation,
            # you would update your connection pool, routing layer, etc.

            # Get primary and replica configs
            primary_config = getattr(settings, self.primary_config_key)
            replica_config = getattr(settings, self.replica_config_key)

            # Swap the configs
            setattr(settings, self.primary_config_key, replica_config)
            setattr(settings, self.replica_config_key, primary_config)

            logger.info(f"Switched {self.service_id} from primary to replica")

            return True, f"Switched {self.service_id} to replica successfully"

        except Exception as e:
            return False, f"Failed to switch {self.service_id} to replica: {str(e)}"


class PerformDatabaseFailoverAction(FailoverAction):
    """Action to perform a database failover."""

    def __init__(
        self,
        service_id: str,
        primary_host: str,
        primary_port: int,
        standby_host: str,
        standby_port: int,
        description: str = "Perform database failover",
    ):
        super().__init__(service_id, description)
        self.primary_host = primary_host
        self.primary_port = primary_port
        self.standby_host = standby_host
        self.standby_port = standby_port

    def execute(self) -> Tuple[bool, str]:
        """Execute the database failover."""
        try:
            logger.info(
                f"Initiating failover for database {self.service_id}: "
                + f"{self.primary_host}:{self.primary_port} -> {self.standby_host}:{self.standby_port}"
            )

            # In a real implementation, this might involve:
            # 1. Promoting a standby PostgreSQL server to primary
            # 2. Reconfiguring connection pools
            # 3. Updating DNS or load balancer settings

            # For this example, we'll assume the database has automatic failover
            # and just update the application's configuration

            # Example: Update connection settings
            from app.db.database import update_db_connection_settings

            update_db_connection_settings(
                host=self.standby_host, port=self.standby_port
            )

            # Example: Update config
            settings.DB_HOST = self.standby_host
            settings.DB_PORT = self.standby_port

            return (
                True,
                f"Database failover completed successfully: now using {self.standby_host}:{self.standby_port}",
            )

        except Exception as e:
            return False, f"Database failover failed: {str(e)}"


class AlertAndLogAction(FailoverAction):
    """Action to send alerts and log issues."""

    def __init__(
        self,
        service_id: str,
        alert_level: str,
        alert_message: str,
        alerts_manager: AlertManager,
        description: str = "Send alert and log",
    ):
        super().__init__(service_id, description)
        self.alert_level = alert_level
        self.alert_message = alert_message
        self.alert_manager = alerts_manager

    def execute(self) -> Tuple[bool, str]:
        """Execute the alert and log action."""
        try:
            # Log the issue
            logger.error(f"Service failure: {self.service_id} - {self.alert_message}")

            # Send the alert
            self.alert_manager.send_alert(
                level=self.alert_level,
                title=f"Service Failure: {self.service_id}",
                message=self.alert_message,
                source="failover_service",
                context={
                    "service_id": self.service_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return True, f"Alert sent for {self.service_id}"

        except Exception as e:
            logger.error(f"Failed to send alert for {self.service_id}: {str(e)}")
            return False, f"Failed to send alert: {str(e)}"


class GracefulDegradationAction(FailoverAction):
    """Action to degrade service gracefully."""

    def __init__(
        self,
        service_id: str,
        degradation_mode: str,
        description: str = "Enable graceful degradation",
    ):
        super().__init__(service_id, description)
        self.degradation_mode = degradation_mode

    def execute(self) -> Tuple[bool, str]:
        """Execute graceful degradation."""
        try:
            logger.info(
                f"Enabling graceful degradation for {self.service_id}: mode={self.degradation_mode}"
            )

            # In a real implementation, this might involve:
            # 1. Enabling a simplified mode of operation
            # 2. Using cached data instead of live data
            # 3. Limiting certain features

            # Example: Set a global flag for degraded operation
            from app.core.config import set_degraded_mode

            set_degraded_mode(self.service_id, True, self.degradation_mode)

            return (
                True,
                f"Enabled degraded mode ({self.degradation_mode}) for {self.service_id}",
            )

        except Exception as e:
            return False, f"Failed to enable degraded mode: {str(e)}"


class FailoverPolicy:
    """Defines when and how to perform failover for a service."""

    def __init__(
        self,
        service_id: str,
        health_check: HealthCheck,
        actions: List[FailoverAction],
        failure_threshold: int = 3,
        cooldown_period: int = 300,  # seconds
        auto_recover: bool = True,
        recovery_actions: Optional[List[FailoverAction]] = None,
    ):
        self.service_id = service_id
        self.health_check = health_check
        self.actions = actions
        self.failure_threshold = failure_threshold
        self.cooldown_period = cooldown_period
        self.auto_recover = auto_recover
        self.recovery_actions = recovery_actions or []

        self.last_failover_time = None
        self.in_failover = False

    def should_failover(self) -> bool:
        """Determine if failover should be triggered based on health check status."""
        # Check if cooldown period has elapsed since last failover
        if self.last_failover_time:
            elapsed = (datetime.now() - self.last_failover_time).total_seconds()
            if elapsed < self.cooldown_period:
                logger.info(
                    f"Failover for {self.service_id} in cooldown ({elapsed:.1f}s / {self.cooldown_period}s)"
                )
                return False

        # Check if consecutive failures exceed threshold
        if self.health_check.consecutive_failures >= self.failure_threshold:
            return True

        return False

    def execute_failover(self) -> Tuple[bool, str]:
        """Execute the failover actions."""
        if self.in_failover:
            return False, f"Failover for {self.service_id} already in progress"

        self.in_failover = True
        self.last_failover_time = datetime.now()

        logger.warning(
            f"Executing failover for {self.service_id} after {self.health_check.consecutive_failures} consecutive failures"
        )

        results = []
        overall_success = True

        for action in self.actions:
            success, message = action.execute()
            results.append((success, message))

            if not success:
                overall_success = False
                logger.error(f"Failover action failed for {self.service_id}: {message}")
            else:
                logger.info(
                    f"Failover action succeeded for {self.service_id}: {message}"
                )

        if overall_success:
            failover_attempts.labels(service=self.service_id, outcome="success").inc()
            result_message = f"Failover for {self.service_id} completed successfully"
        else:
            failover_attempts.labels(service=self.service_id, outcome="failure").inc()
            result_message = (
                f"Failover for {self.service_id} failed (some actions failed)"
            )

        return overall_success, result_message

    def check_and_failover(self) -> Tuple[bool, str]:
        """Check service health and perform failover if needed."""
        # Perform health check
        result = self.health_check.check()
        self.health_check.update_status(result)

        # If service is healthy, check if we need to recover
        if result.status == ServiceState.HEALTHY:
            if self.in_failover and self.auto_recover:
                return self.execute_recovery()
            else:
                return True, f"Service {self.service_id} is healthy"

        # Check if we should failover
        if self.should_failover():
            return self.execute_failover()

        return (
            False,
            f"Service {self.service_id} is unhealthy but failover threshold not reached ({self.health_check.consecutive_failures}/{self.failure_threshold})",
        )

    def execute_recovery(self) -> Tuple[bool, str]:
        """Execute recovery actions to revert from failover state."""
        if not self.in_failover:
            return False, f"Service {self.service_id} is not in failover state"

        logger.info(f"Executing recovery for {self.service_id}")

        results = []
        overall_success = True

        for action in self.recovery_actions:
            success, message = action.execute()
            results.append((success, message))

            if not success:
                overall_success = False
                logger.error(f"Recovery action failed for {self.service_id}: {message}")
            else:
                logger.info(
                    f"Recovery action succeeded for {self.service_id}: {message}"
                )

        if overall_success:
            self.in_failover = False
            result_message = f"Recovery for {self.service_id} completed successfully"
        else:
            result_message = (
                f"Recovery for {self.service_id} failed (some actions failed)"
            )

        return overall_success, result_message


class FailoverManager:
    """Manages service health checks and failover operations."""

    def __init__(self, alerts_manager: AlertManager, check_interval: int = 30):
        self.policies: Dict[str, FailoverPolicy] = {}
        self.alert_manager = alerts_manager
        self.check_interval = check_interval
        self.running = False
        self.check_thread = None
        self.executor = ThreadPoolExecutor(max_workers=10)

    def register_policy(self, policy: FailoverPolicy) -> None:
        """Register a failover policy."""
        self.policies[policy.service_id] = policy
        logger.info(f"Registered failover policy for {policy.service_id}")

    def start(self) -> None:
        """Start the failover manager."""
        if self.running:
            logger.warning("Failover manager already running")
            return

        self.running = True
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()

        logger.info(
            f"Failover manager started with check interval {self.check_interval}s"
        )

    def stop(self) -> None:
        """Stop the failover manager."""
        if not self.running:
            logger.warning("Failover manager not running")
            return

        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=5.0)

        logger.info("Failover manager stopped")

    def _check_loop(self) -> None:
        """Main check loop."""
        while self.running:
            try:
                # Check all services in parallel
                futures = {}
                for service_id, policy in self.policies.items():
                    future = self.executor.submit(policy.check_and_failover)
                    futures[future] = service_id

                # Process results as they complete
                for future in futures:
                    service_id = futures[future]
                    try:
                        success, message = future.result()
                        if not success:
                            logger.warning(f"Service check for {service_id}: {message}")
                    except Exception as e:
                        logger.error(f"Error checking service {service_id}: {str(e)}")

            except Exception as e:
                logger.error(f"Error in failover check loop: {str(e)}")

            # Wait for next check interval
            time.sleep(self.check_interval)

    def check_service(self, service_id: str) -> Tuple[bool, str]:
        """Check a specific service immediately."""
        if service_id not in self.policies:
            return False, f"Service {service_id} not registered"

        policy = self.policies[service_id]
        return policy.check_and_failover()

    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered services."""
        status = {}

        for service_id, policy in self.policies.items():
            health_check = policy.health_check

            status[service_id] = {
                "status": health_check.last_status,
                "consecutive_failures": health_check.consecutive_failures,
                "last_check_time": health_check.last_check_time.isoformat()
                if health_check.last_check_time
                else None,
                "last_healthy_time": health_check.last_healthy_time.isoformat()
                if health_check.last_healthy_time
                else None,
                "in_failover": policy.in_failover,
                "last_failover_time": policy.last_failover_time.isoformat()
                if policy.last_failover_time
                else None,
                "service_type": health_check.service_type,
            }

        return status


# Global failover manager instance
failover_manager = None


def init_failover_manager(
    alerts_manager: AlertManager, check_interval: int = 30
) -> FailoverManager:
    """Initialize and configure the failover manager."""
    global failover_manager

    if failover_manager:
        logger.warning("Failover manager already initialized")
        return failover_manager

    failover_manager = FailoverManager(alerts_manager, check_interval)

    # Register failover policies based on settings
    _register_default_policies(failover_manager)

    # Start the failover manager
    failover_manager.start()

    return failover_manager


def _register_default_policies(manager: FailoverManager) -> None:
    """Register default failover policies."""
    # Check if running in Kubernetes
    in_kubernetes = os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount")

    # Register database failover policy
    _register_database_policy(manager)

    # Register Redis failover policy
    _register_redis_policy(manager)

    # Register anomaly detection-based policies
    _register_anomaly_detection_policies(manager)

    # Register services based on environment
    if in_kubernetes:
        _register_kubernetes_service_policies(manager)
    else:
        _register_local_service_policies(manager)


def _register_database_policy(manager: FailoverManager) -> None:
    """Register database failover policy."""
    # Create health check
    db_health_check = PostgreSQLHealthCheck(
        service_id="main_database",
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        description="Main PostgreSQL database",
    )

    # Create failover actions
    actions = []

    # If standby is configured, add failover action
    if hasattr(settings, "DB_STANDBY_HOST") and settings.DB_STANDBY_HOST:
        actions.append(
            PerformDatabaseFailoverAction(
                service_id="main_database",
                primary_host=settings.DB_HOST,
                primary_port=settings.DB_PORT,
                standby_host=settings.DB_STANDBY_HOST,
                standby_port=getattr(settings, "DB_STANDBY_PORT", settings.DB_PORT),
            )
        )

    # Always add alert action
    actions.append(
        AlertAndLogAction(
            service_id="main_database",
            alert_level="critical",
            alert_message="Database is unavailable",
            alert_manager=manager.alert_manager,
        )
    )

    # Add graceful degradation action
    actions.append(
        GracefulDegradationAction(
            service_id="main_database", degradation_mode="read_only"
        )
    )

    # Create recovery actions if we have a standby
    recovery_actions = []
    if hasattr(settings, "DB_STANDBY_HOST") and settings.DB_STANDBY_HOST:
        recovery_actions.append(
            PerformDatabaseFailoverAction(
                service_id="main_database",
                primary_host=settings.DB_STANDBY_HOST,
                primary_port=getattr(settings, "DB_STANDBY_PORT", settings.DB_PORT),
                standby_host=settings.DB_HOST,
                standby_port=settings.DB_PORT,
            )
        )

    # Create the policy
    policy = FailoverPolicy(
        service_id="main_database",
        health_check=db_health_check,
        actions=actions,
        failure_threshold=3,
        cooldown_period=300,
        auto_recover=True,
        recovery_actions=recovery_actions,
    )

    # Register the policy
    manager.register_policy(policy)


def _register_redis_policy(manager: FailoverManager) -> None:
    """Register Redis failover policy."""
    # Skip if Redis is not configured
    if not hasattr(settings, "REDIS_HOST"):
        return

    # Create health check
    redis_health_check = RedisHealthCheck(
        service_id="redis_cache",
        host=settings.REDIS_HOST,
        port=getattr(settings, "REDIS_PORT", 6379),
        password=getattr(settings, "REDIS_PASSWORD", None),
        description="Redis cache",
    )

    # Create failover actions
    actions = []

    # If replica is configured, add failover action
    if hasattr(settings, "REDIS_REPLICA_HOST") and settings.REDIS_REPLICA_HOST:
        actions.append(
            SwitchToReplicaAction(
                service_id="redis_cache",
                primary_config_key="REDIS_HOST",
                replica_config_key="REDIS_REPLICA_HOST",
            )
        )

    # Add alert action
    actions.append(
        AlertAndLogAction(
            service_id="redis_cache",
            alert_level="warning",
            alert_message="Redis cache is unavailable",
            alert_manager=manager.alert_manager,
        )
    )

    # Add graceful degradation action
    actions.append(
        GracefulDegradationAction(service_id="redis_cache", degradation_mode="no_cache")
    )

    # Create the policy
    policy = FailoverPolicy(
        service_id="redis_cache",
        health_check=redis_health_check,
        actions=actions,
        failure_threshold=3,
        cooldown_period=180,
        auto_recover=True,
    )

    # Register the policy
    manager.register_policy(policy)


def _register_kubernetes_service_policies(manager: FailoverManager) -> None:
    """Register policies for services running in Kubernetes."""
    # Example for trading engine service
    if hasattr(settings, "TRADING_ENGINE_NAMESPACE"):
        trading_engine_health_check = KubernetesHealthCheck(
            service_id="trading_engine",
            service_type=ServiceType.TRADING_ENGINE,
            namespace=settings.TRADING_ENGINE_NAMESPACE,
            resource_type="deployment",
            resource_name="trading-engine",
            min_ready=1,
            description="Trading Engine Deployment",
        )

        actions = [
            # Restart action using kubectl
            RestartServiceAction(
                service_id="trading_engine",
                command=[
                    "kubectl",
                    "rollout",
                    "restart",
                    "deployment/trading-engine",
                    "-n",
                    settings.TRADING_ENGINE_NAMESPACE,
                ],
            ),
            # Alert action
            AlertAndLogAction(
                service_id="trading_engine",
                alert_level="critical",
                alert_message="Trading Engine is unavailable",
                alert_manager=manager.alert_manager,
            ),
            # Graceful degradation
            GracefulDegradationAction(
                service_id="trading_engine", degradation_mode="paper_only"
            ),
        ]

        policy = FailoverPolicy(
            service_id="trading_engine",
            health_check=trading_engine_health_check,
            actions=actions,
            failure_threshold=3,
            cooldown_period=300,
        )

        manager.register_policy(policy)

    # Example for market data service
    if hasattr(settings, "MARKET_DATA_NAMESPACE"):
        market_data_health_check = KubernetesHealthCheck(
            service_id="market_data",
            service_type=ServiceType.MARKET_DATA,
            namespace=settings.MARKET_DATA_NAMESPACE,
            resource_type="deployment",
            resource_name="market-data",
            min_ready=1,
            description="Market Data Service Deployment",
        )

        actions = [
            # Restart action
            RestartServiceAction(
                service_id="market_data",
                command=[
                    "kubectl",
                    "rollout",
                    "restart",
                    "deployment/market-data",
                    "-n",
                    settings.MARKET_DATA_NAMESPACE,
                ],
            ),
            # Alert action
            AlertAndLogAction(
                service_id="market_data",
                alert_level="critical",
                alert_message="Market Data Service is unavailable",
                alert_manager=manager.alert_manager,
            ),
            # Graceful degradation - use cached data
            GracefulDegradationAction(
                service_id="market_data", degradation_mode="cached_only"
            ),
        ]

        policy = FailoverPolicy(
            service_id="market_data",
            health_check=market_data_health_check,
            actions=actions,
            failure_threshold=2,
            cooldown_period=240,
        )

        manager.register_policy(policy)


def _register_anomaly_detection_policies(manager: FailoverManager) -> None:
    """Register failover policies based on anomaly detection."""
    # 1. Market data API latency policy
    if hasattr(settings, "MARKET_DATA_PROVIDERS"):
        # For each market data provider, create an anomaly-based policy
        for provider in settings.MARKET_DATA_PROVIDERS:
            # Create anomaly-based health check for API latency
            api_latency_check = AnomalyBasedHealthCheck(
                service_id=f"{provider}_api_latency",
                service_type=ServiceType.MARKET_DATA,
                entity_id=f"{provider}_api",
                anomaly_types=[AnomalyType.API_LATENCY],
                severity_threshold=AnomalySeverity.WARNING,
                lookback_minutes=5,
                description=f"Anomaly detection for {provider} API latency",
            )

            # Create anomaly-based health check for error rates
            error_rate_check = AnomalyBasedHealthCheck(
                service_id=f"{provider}_error_rate",
                service_type=ServiceType.MARKET_DATA,
                entity_id=f"{provider}_api",
                anomaly_types=[AnomalyType.ERROR_RATE],
                severity_threshold=AnomalySeverity.WARNING,
                lookback_minutes=5,
                description=f"Anomaly detection for {provider} error rates",
            )

            # Combine checks
            composite_check = CompositeHealthCheck(
                service_id=f"{provider}_market_data",
                service_type=ServiceType.MARKET_DATA,
                health_checks=[api_latency_check, error_rate_check],
                require_all_healthy=False,  # Only one check needs to fail to trigger
                description=f"Combined anomaly checks for {provider}",
                weight_anomaly_checks=True,
            )

            # Create failover actions
            actions = [
                # Alert action
                AlertAndLogAction(
                    service_id=f"{provider}_market_data",
                    alert_level="warning",
                    alert_message=f"Anomalies detected in {provider} market data API",
                    alert_manager=manager.alert_manager,
                ),
                # Graceful degradation - use alternative provider or cached data
                GracefulDegradationAction(
                    service_id=f"{provider}_market_data",
                    degradation_mode="use_alternative_provider",
                ),
            ]

            # Create and register the policy
            policy = FailoverPolicy(
                service_id=f"{provider}_market_data",
                health_check=composite_check,
                actions=actions,
                failure_threshold=1,  # Anomalies already represent multiple data points
                cooldown_period=180,
                auto_recover=True,
            )

            manager.register_policy(policy)

    # 2. Trading volume anomaly policy
    for symbol in getattr(
        settings, "MONITORED_SYMBOLS", ["SPY", "QQQ", "AAPL", "MSFT"]
    ):
        # Create volume anomaly health check
        volume_check = AnomalyBasedHealthCheck(
            service_id=f"{symbol}_volume_anomaly",
            service_type=ServiceType.MARKET_DATA,
            entity_id=symbol,
            anomaly_types=[AnomalyType.VOLUME_SPIKE],
            severity_threshold=AnomalySeverity.WARNING,
            lookback_minutes=10,
            description=f"Volume anomaly detection for {symbol}",
        )

        # Create price anomaly health check
        price_check = AnomalyBasedHealthCheck(
            service_id=f"{symbol}_price_anomaly",
            service_type=ServiceType.MARKET_DATA,
            entity_id=symbol,
            anomaly_types=[AnomalyType.PRICE_SPIKE, AnomalyType.PRICE_DROP],
            severity_threshold=AnomalySeverity.WARNING,
            lookback_minutes=10,
            description=f"Price anomaly detection for {symbol}",
        )

        # Create volatility anomaly health check
        volatility_check = AnomalyBasedHealthCheck(
            service_id=f"{symbol}_volatility_anomaly",
            service_type=ServiceType.MARKET_DATA,
            entity_id=symbol,
            anomaly_types=[AnomalyType.VOLATILITY_CHANGE],
            severity_threshold=AnomalySeverity.WARNING,
            lookback_minutes=10,
            description=f"Volatility anomaly detection for {symbol}",
        )

        # Combine checks
        composite_check = CompositeHealthCheck(
            service_id=f"{symbol}_market_condition",
            service_type=ServiceType.MARKET_DATA,
            health_checks=[volume_check, price_check, volatility_check],
            require_all_healthy=False,  # Only one check needs to fail to trigger
            description=f"Combined market condition checks for {symbol}",
            weight_anomaly_checks=True,
        )

        # Create actions
        actions = [
            # Alert action
            AlertAndLogAction(
                service_id=f"{symbol}_market_condition",
                alert_level="warning",
                alert_message=f"Abnormal market conditions detected for {symbol}",
                alert_manager=manager.alert_manager,
            ),
            # Circuit breaker action - use a more cautious trading strategy
            GracefulDegradationAction(
                service_id=f"{symbol}_market_condition",
                degradation_mode="reduce_position_sizes",
            ),
        ]

        # Create and register the policy
        policy = FailoverPolicy(
            service_id=f"{symbol}_market_condition",
            health_check=composite_check,
            actions=actions,
            failure_threshold=1,  # Anomalies already represent multiple data points
            cooldown_period=300,
            auto_recover=True,
        )

        manager.register_policy(policy)

    # 3. System metrics anomaly policy
    system_metrics = [
        {"name": "cpu_usage", "description": "CPU usage percentage", "upper_limit": 90},
        {
            "name": "memory_usage",
            "description": "Memory usage percentage",
            "upper_limit": 85,
        },
        {
            "name": "disk_usage",
            "description": "Disk usage percentage",
            "upper_limit": 90,
        },
        {
            "name": "db_connections",
            "description": "Database connection count",
            "upper_limit": None,
        },
        {
            "name": "api_request_rate",
            "description": "API request rate",
            "upper_limit": None,
        },
    ]

    for metric in system_metrics:
        # Create system metric anomaly health check
        metric_check = AnomalyBasedHealthCheck(
            service_id=f"{metric['name']}_anomaly",
            service_type=ServiceType.SYSTEM_RESOURCE,
            entity_id=metric["name"],
            anomaly_types=[AnomalyType.SYSTEM_RESOURCE],
            severity_threshold=AnomalySeverity.WARNING,
            lookback_minutes=15,
            description=f"System metric anomaly detection for {metric['description']}",
        )

        # Create actions
        actions = [
            # Alert action
            AlertAndLogAction(
                service_id=f"{metric['name']}_anomaly",
                alert_level="warning",
                alert_message=f"Abnormal {metric['description']} detected",
                alert_manager=manager.alert_manager,
            ),
        ]

        # Add specific actions based on metric type
        if metric["name"] == "cpu_usage" or metric["name"] == "memory_usage":
            actions.append(
                GracefulDegradationAction(
                    service_id=f"{metric['name']}_anomaly",
                    degradation_mode="reduce_background_tasks",
                )
            )
        elif metric["name"] == "db_connections":
            actions.append(
                GracefulDegradationAction(
                    service_id=f"{metric['name']}_anomaly",
                    degradation_mode="reduce_db_load",
                )
            )

        # Create and register the policy
        policy = FailoverPolicy(
            service_id=f"{metric['name']}_anomaly",
            health_check=metric_check,
            actions=actions,
            failure_threshold=1,  # Anomalies already represent multiple data points
            cooldown_period=240,
            auto_recover=True,
        )

        manager.register_policy(policy)


def _register_local_service_policies(manager: FailoverManager) -> None:
    """Register policies for services running locally."""
    # Example for trading engine service
    if hasattr(settings, "TRADING_ENGINE_HOST"):
        # Create regular health check
        trading_engine_http_check = HttpHealthCheck(
            service_id="trading_engine_http",
            service_type=ServiceType.TRADING_ENGINE,
            endpoint=f"http://{settings.TRADING_ENGINE_HOST}:{settings.TRADING_ENGINE_PORT}/health",
            method="GET",
            timeout=5.0,
            expected_status=200,
            description="Trading Engine Health Endpoint",
        )

        # Create anomaly-based health check
        trading_engine_anomaly_check = AnomalyBasedHealthCheck(
            service_id="trading_engine_anomalies",
            service_type=ServiceType.TRADING_ENGINE,
            entity_id="trading_engine",
            anomaly_types=[AnomalyType.API_LATENCY, AnomalyType.ERROR_RATE],
            severity_threshold=AnomalySeverity.WARNING,
            lookback_minutes=5,
            description="Trading Engine Anomaly Detection",
        )

        # Create composite health check
        trading_engine_health_check = CompositeHealthCheck(
            service_id="trading_engine",
            service_type=ServiceType.TRADING_ENGINE,
            health_checks=[trading_engine_http_check, trading_engine_anomaly_check],
            require_all_healthy=False,
            description="Trading Engine Combined Health Check",
            weight_anomaly_checks=True,
        )

        # Command depends on environment
        restart_cmd = ["docker", "restart", "elson_trading_engine"]
        if os.path.exists("/usr/bin/systemctl"):
            restart_cmd = ["systemctl", "restart", "elson-trading-engine.service"]

        actions = [
            # Restart action
            RestartServiceAction(service_id="trading_engine", command=restart_cmd),
            # Alert action
            AlertAndLogAction(
                service_id="trading_engine",
                alert_level="critical",
                alert_message="Trading Engine is unavailable",
                alert_manager=manager.alert_manager,
            ),
            # Graceful degradation
            GracefulDegradationAction(
                service_id="trading_engine", degradation_mode="paper_only"
            ),
        ]

        policy = FailoverPolicy(
            service_id="trading_engine",
            health_check=trading_engine_health_check,
            actions=actions,
            failure_threshold=3,
            cooldown_period=300,
        )

        manager.register_policy(policy)

    # Example for market data service
    if hasattr(settings, "MARKET_DATA_HOST"):
        # Create regular health check
        market_data_http_check = HttpHealthCheck(
            service_id="market_data_http",
            service_type=ServiceType.MARKET_DATA,
            endpoint=f"http://{settings.MARKET_DATA_HOST}:{settings.MARKET_DATA_PORT}/health",
            method="GET",
            timeout=5.0,
            expected_status=200,
            description="Market Data Service Health Endpoint",
        )

        # Create anomaly-based health check
        market_data_anomaly_check = AnomalyBasedHealthCheck(
            service_id="market_data_anomalies",
            service_type=ServiceType.MARKET_DATA,
            entity_id="market_data_service",
            anomaly_types=[
                AnomalyType.API_LATENCY,
                AnomalyType.ERROR_RATE,
                AnomalyType.DATA_QUALITY,
            ],
            severity_threshold=AnomalySeverity.WARNING,
            lookback_minutes=5,
            description="Market Data Service Anomaly Detection",
        )

        # Create composite health check
        market_data_health_check = CompositeHealthCheck(
            service_id="market_data",
            service_type=ServiceType.MARKET_DATA,
            health_checks=[market_data_http_check, market_data_anomaly_check],
            require_all_healthy=False,
            description="Market Data Service Combined Health Check",
            weight_anomaly_checks=True,
        )

        # Command depends on environment
        restart_cmd = ["docker", "restart", "elson_market_data"]
        if os.path.exists("/usr/bin/systemctl"):
            restart_cmd = ["systemctl", "restart", "elson-market-data.service"]

        actions = [
            # Restart action
            RestartServiceAction(service_id="market_data", command=restart_cmd),
            # Alert action
            AlertAndLogAction(
                service_id="market_data",
                alert_level="critical",
                alert_message="Market Data Service is unavailable",
                alert_manager=manager.alert_manager,
            ),
            # Graceful degradation - use cached data
            GracefulDegradationAction(
                service_id="market_data", degradation_mode="cached_only"
            ),
        ]

        policy = FailoverPolicy(
            service_id="market_data",
            health_check=market_data_health_check,
            actions=actions,
            failure_threshold=2,
            cooldown_period=240,
        )

        manager.register_policy(policy)

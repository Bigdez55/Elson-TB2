"""
Security monitoring system for detecting suspicious activities in Elson Wealth App.

This module provides specialized security checks beyond the basic middleware protection.
It integrates with the service monitoring and alerting system to provide security-focused
monitoring of critical systems.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import threading
from collections import defaultdict
from enum import Enum

from .config import settings

logger = logging.getLogger(__name__)


# Simple alert system for security monitoring
class AlertCategory(str, Enum):
    """Alert categories for different types of alerts."""

    SYSTEM = "system"
    TRADING = "trading"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FINANCIAL = "financial"
    OTHER = "other"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


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
        check_function,
        check_interval_seconds: int = 60,
        description: str = "",
        is_critical: bool = False,
    ):
        self.name = name
        self.service_type = service_type
        self.check_function = check_function
        self.check_interval_seconds = check_interval_seconds
        self.description = description
        self.is_critical = is_critical


# Simple alert functions
def send_warning_alert(
    title: str,
    message: str,
    category: AlertCategory,
    source: str,
    metadata: Optional[Dict] = None,
):
    """Send a warning alert."""
    logger.warning(
        f"SECURITY ALERT [{category.value}]: {title} - {message}",
        extra={"alert_metadata": metadata or {}, "source": source},
    )


def send_error_alert(
    title: str,
    message: str,
    category: AlertCategory,
    source: str,
    metadata: Optional[Dict] = None,
):
    """Send an error alert."""
    logger.error(
        f"SECURITY ERROR [{category.value}]: {title} - {message}",
        extra={"alert_metadata": metadata or {}, "source": source},
    )


def alert_from_exception(
    error: Exception,
    title: str,
    category: AlertCategory,
    source: str,
    metadata: Optional[Dict] = None,
):
    """Send an alert from an exception."""
    logger.error(
        f"SECURITY EXCEPTION [{category.value}]: {title} - {str(error)}",
        extra={
            "alert_metadata": metadata or {},
            "source": source,
            "exception": str(error),
        },
    )


class SecurityMonitor:
    """
    Security monitoring system that detects and alerts on suspicious activities.

    Monitors various security aspects of the application:
    1. Failed login attempts
    2. Account lockouts
    3. Suspicious IP patterns
    4. Failed API key usage
    5. Token verification failures
    """

    def __init__(self):
        """Initialize the security monitoring system."""
        self.security_events = defaultdict(list)
        self.suspicious_ips = set()
        self.account_lockouts = {}
        self._lock = threading.RLock()

        # Configurable thresholds
        self.login_failure_threshold = 10  # Failed logins to track before alerting
        self.api_failure_threshold = 5  # Failed API auth attempts before alerting
        self.suspicious_ip_ttl = 24 * 60 * 60  # 24 hours to keep suspicious IPs

    def record_login_attempt(
        self, user_id: str, ip: str, success: bool, details: Optional[Dict] = None
    ) -> None:
        """
        Record a login attempt and alert if necessary.

        Args:
            user_id: User ID or username
            ip: Client IP address
            success: Whether the login was successful
            details: Additional details about the login attempt
        """
        with self._lock:
            now = time.time()

            # Cleanup old events (older than 1 hour)
            hour_ago = now - 3600
            self.security_events["login_attempts"] = [
                event
                for event in self.security_events.get("login_attempts", [])
                if event.get("timestamp", 0) > hour_ago
            ]

            # Record the event
            event = {
                "user_id": user_id,
                "ip": ip,
                "success": success,
                "timestamp": now,
                "datetime": datetime.now().isoformat(),
                "details": details or {},
            }
            self.security_events["login_attempts"].append(event)

            # Check for suspicious patterns
            if not success:
                # Get recent failed attempts for this user or IP
                recent_failures = [
                    e
                    for e in self.security_events.get("login_attempts", [])
                    if not e.get("success")
                    and (e.get("user_id") == user_id or e.get("ip") == ip)
                ]

                # Alert on excessive failed login attempts
                if len(recent_failures) >= self.login_failure_threshold:
                    send_warning_alert(
                        title="Excessive Login Failures",
                        message=f"Detected {len(recent_failures)} failed login attempts for user "
                        f"{user_id} or IP {ip}",
                        category=AlertCategory.SECURITY,
                        source="security_monitor",
                        metadata={
                            "user_id": user_id,
                            "ip_address": ip,
                            "failure_count": len(recent_failures),
                            "time_window": "1 hour",
                            "latest_attempt": datetime.now().isoformat(),
                        },
                    )

                    # Add to suspicious IPs
                    self.suspicious_ips.add(ip)

    def record_api_key_failure(
        self, ip: str, endpoint: str, details: Optional[Dict] = None
    ) -> None:
        """
        Record a failed API key authentication and alert if necessary.

        Args:
            ip: Client IP address
            endpoint: API endpoint path
            details: Additional details about the API key failure
        """
        with self._lock:
            now = time.time()

            # Cleanup old events (older than 1 hour)
            hour_ago = now - 3600
            self.security_events["api_key_failures"] = [
                event
                for event in self.security_events.get("api_key_failures", [])
                if event.get("timestamp", 0) > hour_ago
            ]

            # Record the event
            event = {
                "ip": ip,
                "endpoint": endpoint,
                "timestamp": now,
                "datetime": datetime.now().isoformat(),
                "details": details or {},
            }
            self.security_events["api_key_failures"].append(event)

            # Check if this IP has multiple failures
            ip_failures = [
                e
                for e in self.security_events.get("api_key_failures", [])
                if e.get("ip") == ip
            ]

            if len(ip_failures) >= self.api_failure_threshold:
                send_warning_alert(
                    title="Multiple API Key Failures",
                    message=f"Detected {len(ip_failures)} failed API key attempts from IP {ip}",
                    category=AlertCategory.SECURITY,
                    source="security_monitor",
                    metadata={
                        "ip_address": ip,
                        "failure_count": len(ip_failures),
                        "endpoints_accessed": list(
                            set(e.get("endpoint") for e in ip_failures)
                        ),
                        "time_window": "1 hour",
                        "latest_attempt": datetime.now().isoformat(),
                    },
                )

                # Add to suspicious IPs
                self.suspicious_ips.add(ip)

    def record_account_lockout(
        self, user_id: str, ip: str, reason: str, duration_seconds: int
    ) -> None:
        """
        Record an account lockout and alert.

        Args:
            user_id: User ID or username
            ip: Client IP address
            reason: Reason for the lockout
            duration_seconds: Lockout duration in seconds
        """
        with self._lock:
            now = datetime.now()

            # Record the lockout with expiration time
            expiry = now + timedelta(seconds=duration_seconds)
            self.account_lockouts[user_id] = expiry

            # Always alert on account lockouts
            send_warning_alert(
                title="Account Lockout",
                message=f"Account {user_id} locked out for {duration_seconds} seconds",
                category=AlertCategory.SECURITY,
                source="security_monitor",
                metadata={
                    "user_id": user_id,
                    "ip_address": ip,
                    "reason": reason,
                    "lockout_duration": duration_seconds,
                    "lockout_expiry": expiry.isoformat(),
                    "timestamp": now.isoformat(),
                },
            )

            # Add to suspicious IPs
            self.suspicious_ips.add(ip)

    def record_token_verification_failure(
        self, ip: str, error_type: str, details: Optional[Dict] = None
    ) -> None:
        """
        Record a token verification failure and alert if necessary.

        Args:
            ip: Client IP address
            error_type: Type of token error
            details: Additional details about the token failure
        """
        with self._lock:
            now = time.time()

            # Cleanup old events (older than 1 hour)
            hour_ago = now - 3600
            self.security_events["token_failures"] = [
                event
                for event in self.security_events.get("token_failures", [])
                if event.get("timestamp", 0) > hour_ago
            ]

            # Record the event
            event = {
                "ip": ip,
                "error_type": error_type,
                "timestamp": now,
                "datetime": datetime.now().isoformat(),
                "details": details or {},
            }
            self.security_events["token_failures"].append(event)

            # Check if this IP has multiple failures
            ip_failures = [
                e
                for e in self.security_events.get("token_failures", [])
                if e.get("ip") == ip
            ]

            if len(ip_failures) >= self.api_failure_threshold:
                send_error_alert(
                    title="Multiple Token Verification Failures",
                    message=f"Detected {len(ip_failures)} token verification failures from IP {ip}",
                    category=AlertCategory.SECURITY,
                    source="security_monitor",
                    metadata={
                        "ip_address": ip,
                        "failure_count": len(ip_failures),
                        "error_types": list(
                            set(e.get("error_type") for e in ip_failures)
                        ),
                        "time_window": "1 hour",
                        "latest_attempt": datetime.now().isoformat(),
                    },
                )

                # Add to suspicious IPs
                self.suspicious_ips.add(ip)

    def record_suspicious_activity(
        self, activity_type: str, ip: str, details: Dict[str, Any]
    ) -> None:
        """
        Record any suspicious activity that doesn't fit other categories.

        Args:
            activity_type: Type of suspicious activity
            ip: Client IP address
            details: Details about the suspicious activity
        """
        with self._lock:
            now = time.time()

            # Cleanup old events (older than 4 hours)
            four_hours_ago = now - 14400
            self.security_events["suspicious_activity"] = [
                event
                for event in self.security_events.get("suspicious_activity", [])
                if event.get("timestamp", 0) > four_hours_ago
            ]

            # Record the event
            event = {
                "activity_type": activity_type,
                "ip": ip,
                "timestamp": now,
                "datetime": datetime.now().isoformat(),
                "details": details,
            }
            self.security_events["suspicious_activity"].append(event)

            # Add to suspicious IPs for certain types
            self.suspicious_ips.add(ip)

            # Always alert on suspicious activity
            send_warning_alert(
                title=f"Suspicious Activity: {activity_type}",
                message=f"Detected suspicious activity from IP {ip}: {activity_type}",
                category=AlertCategory.SECURITY,
                source="security_monitor",
                metadata={
                    "ip_address": ip,
                    "activity_type": activity_type,
                    "timestamp": datetime.now().isoformat(),
                    **details,
                },
            )

    def is_suspicious_ip(self, ip: str) -> bool:
        """
        Check if an IP is in the suspicious list.

        Args:
            ip: IP address to check

        Returns:
            True if the IP is suspicious, False otherwise
        """
        with self._lock:
            return ip in self.suspicious_ips

    def is_account_locked(self, user_id: str) -> Tuple[bool, Optional[timedelta]]:
        """
        Check if an account is locked out.

        Args:
            user_id: User ID to check

        Returns:
            Tuple of (is_locked, remaining_time)
        """
        with self._lock:
            now = datetime.now()

            # Clean up expired lockouts
            expired_users = [
                user for user, expiry in self.account_lockouts.items() if now > expiry
            ]
            for user in expired_users:
                del self.account_lockouts[user]

            # Check if user is locked
            if user_id in self.account_lockouts:
                remaining = self.account_lockouts[user_id] - now
                if remaining.total_seconds() > 0:
                    return True, remaining
                else:
                    del self.account_lockouts[user_id]

            return False, None

    def get_security_summary(self) -> Dict[str, Any]:
        """
        Get a summary of security events.

        Returns:
            Dictionary with security event summary
        """
        with self._lock:
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            # Count events in different time windows
            events_last_hour = {
                k: len(
                    [
                        e
                        for e in v
                        if datetime.fromisoformat(e.get("datetime", "")) > hour_ago
                    ]
                )
                for k, v in self.security_events.items()
            }

            events_last_day = {
                k: len(
                    [
                        e
                        for e in v
                        if datetime.fromisoformat(e.get("datetime", "")) > day_ago
                    ]
                )
                for k, v in self.security_events.items()
            }

            return {
                "timestamp": now.isoformat(),
                "suspicious_ip_count": len(self.suspicious_ips),
                "locked_account_count": len(self.account_lockouts),
                "events_last_hour": events_last_hour,
                "events_last_day": events_last_day,
            }

    def cleanup(self) -> None:
        """Clean up old security events and expired lockouts."""
        with self._lock:
            now = datetime.now()
            day_ago = now - timedelta(days=1)

            # Clean up old events
            for event_type, events in self.security_events.items():
                self.security_events[event_type] = [
                    e
                    for e in events
                    if datetime.fromisoformat(e.get("datetime", "")) > day_ago
                ]

            # Clean up expired lockouts
            expired_users = [
                user for user, expiry in self.account_lockouts.items() if now > expiry
            ]
            for user in expired_users:
                del self.account_lockouts[user]


# Global singleton instance
_security_monitor = None


def get_security_monitor() -> SecurityMonitor:
    """Get or create the security monitor singleton."""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor()
    return _security_monitor


# Simple service monitor placeholder
class ServiceMonitor:
    """Simplified service monitor for security monitoring integration."""

    def __init__(self):
        self.checks = {}

    def add_check(self, check: ServiceCheck) -> None:
        """Add a service check."""
        self.checks[check.name] = check
        logger.info(f"Added security service check: {check.name}")


# Global service monitor instance
_service_monitor = None


def get_service_monitor() -> ServiceMonitor:
    """Get or create the service monitor singleton."""
    global _service_monitor
    if _service_monitor is None:
        _service_monitor = ServiceMonitor()
    return _service_monitor


# Create service checks for the monitoring system


def create_security_monitoring_check() -> ServiceCheck:
    """
    Create a service check for security monitoring.

    This check verifies that the security monitoring system is working properly.
    """

    def check_security_monitoring() -> bool:
        """Verify security monitoring is functioning."""
        try:
            # Get the security monitor
            monitor = get_security_monitor()

            # Verify basic operations work
            monitor.get_security_summary()

            # Verify we can check suspicious IPs
            monitor.is_suspicious_ip("127.0.0.1")

            return True
        except Exception as e:
            logger.error(f"Security monitoring check failed: {str(e)}")
            return False

    return ServiceCheck(
        name="security_monitoring",
        service_type=ServiceType.INTERNAL,
        check_function=check_security_monitoring,
        check_interval_seconds=60,
        description="Check security monitoring system functionality",
        is_critical=True,
    )


def create_failed_login_check() -> ServiceCheck:
    """
    Create a check for excessive failed logins.

    This check looks for spikes in failed login attempts which could indicate
    a brute force attack in progress.
    """

    def check_failed_logins() -> bool:
        """Check for excessive failed logins."""
        try:
            # Get security monitor
            monitor = get_security_monitor()

            # Check for excessive login failures in the last hour
            summary = monitor.get_security_summary()
            login_failures = summary.get("events_last_hour", {}).get(
                "login_attempts", 0
            )

            # Threshold: more than 100 failed logins per hour across system
            threshold = getattr(settings, "SECURITY_LOGIN_FAILURE_THRESHOLD", 100)

            if login_failures > threshold:
                send_warning_alert(
                    title="High System-Wide Login Failure Rate",
                    message=f"Detected {login_failures} failed login attempts in the last hour",
                    category=AlertCategory.SECURITY,
                    source="security_monitor",
                    metadata={
                        "failure_count": login_failures,
                        "threshold": threshold,
                        "time_window": "1 hour",
                    },
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Failed login check failed: {str(e)}")
            return False

    return ServiceCheck(
        name="failed_login_monitoring",
        service_type=ServiceType.INTERNAL,
        check_function=check_failed_logins,
        check_interval_seconds=300,  # Every 5 minutes
        description="Monitor for suspicious login attempt patterns",
        is_critical=True,
    )


def register_security_checks() -> None:
    """
    Register all security-related checks with the service monitor.
    """
    monitor = get_service_monitor()

    # Add security checks
    monitor.add_check(create_security_monitoring_check())
    monitor.add_check(create_failed_login_check())

    logger.info("Security monitoring checks registered")

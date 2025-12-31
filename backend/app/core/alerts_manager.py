"""Alerts Manager for the trading platform.

This module provides a centralized alerts system for monitoring
trading activities and system health.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""
    TRADE = "trade"
    RISK = "risk"
    SYSTEM = "system"
    MARKET = "market"
    RECONCILIATION = "reconciliation"
    SECURITY = "security"


class Alert:
    """Represents a single alert."""

    def __init__(
        self,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        alert_type: AlertType = AlertType.SYSTEM,
        details: Optional[Dict[str, Any]] = None
    ):
        self.id = id(self)
        self.message = message
        self.severity = severity
        self.alert_type = alert_type
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        self.acknowledged = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "message": self.message,
            "severity": self.severity.value,
            "type": self.alert_type.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }


class AlertsManager:
    """Manages alerts for the trading platform."""

    def __init__(self, max_alerts: int = 1000):
        self._alerts: deque = deque(maxlen=max_alerts)
        self._handlers: List[callable] = []

    def add_alert(
        self,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        alert_type: AlertType = AlertType.SYSTEM,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Add a new alert."""
        alert = Alert(message, severity, alert_type, details)
        self._alerts.append(alert)

        # Log based on severity
        log_msg = f"[{alert_type.value}] {message}"
        if severity == AlertSeverity.CRITICAL:
            logger.critical(log_msg)
        elif severity == AlertSeverity.ERROR:
            logger.error(log_msg)
        elif severity == AlertSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Call handlers
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        return alert

    def info(
        self,
        message: str,
        alert_type: AlertType = AlertType.SYSTEM,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Add an info-level alert."""
        return self.add_alert(message, AlertSeverity.INFO, alert_type, details)

    def warning(
        self,
        message: str,
        alert_type: AlertType = AlertType.SYSTEM,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Add a warning-level alert."""
        return self.add_alert(
            message, AlertSeverity.WARNING, alert_type, details
        )

    def error(
        self,
        message: str,
        alert_type: AlertType = AlertType.SYSTEM,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Add an error-level alert."""
        return self.add_alert(message, AlertSeverity.ERROR, alert_type, details)

    def critical(
        self,
        message: str,
        alert_type: AlertType = AlertType.SYSTEM,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Add a critical-level alert."""
        return self.add_alert(
            message, AlertSeverity.CRITICAL, alert_type, details
        )

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent alerts with optional filtering."""
        alerts = list(self._alerts)

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        return [a.to_dict() for a in alerts[-limit:]]

    def acknowledge(self, alert_id: int) -> bool:
        """Acknowledge an alert by ID."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def register_handler(self, handler: callable) -> None:
        """Register a handler to be called when alerts are added."""
        self._handlers.append(handler)

    def clear(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()


# Global alerts manager instance
alert_manager = AlertsManager()


__all__ = [
    "AlertsManager",
    "Alert",
    "AlertSeverity",
    "AlertType",
    "alert_manager",
]

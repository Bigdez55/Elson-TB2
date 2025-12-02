"""Alerting system for critical events and anomalies.

This module handles the alerting mechanisms for system failures, trading
anomalies, and other critical events that require immediate attention.
It supports multiple notification channels including email, SMS, and
integration with external systems like PagerDuty and Slack.
"""

import logging
import time
import json
import smtplib
import requests
from enum import Enum
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Union, Any

from .config import settings
from .secrets import secret_manager

logger = logging.getLogger(__name__)

# Forward declaration for type hinting
class AlertManager:
    pass

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(str, Enum):
    """Alert categories for different types of alerts."""
    
    SYSTEM = "system"          # System-level issues (DB, API, etc.)
    TRADING = "trading"        # Trading-related issues
    SECURITY = "security"      # Security-related issues
    PERFORMANCE = "performance"  # Performance-related issues
    FINANCIAL = "financial"    # Financial-related issues
    OTHER = "other"            # Other issues


class AlertChannel(str, Enum):
    """Alert notification channels."""
    
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


class Alert:
    """Alert model for capturing alert details."""
    
    def __init__(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        category: AlertCategory,
        source: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Initialize a new alert."""
        self.title = title
        self.message = message
        self.severity = severity
        self.category = category
        self.source = source
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "source": self.source,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        """Create alert from dictionary."""
        return cls(
            title=data["title"],
            message=data["message"],
            severity=AlertSeverity(data["severity"]),
            category=AlertCategory(data["category"]),
            source=data["source"],
            details=data["details"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class AlertThrottler:
    """Throttle alerts to prevent alert storms."""
    
    def __init__(self, window_seconds: int = 300, max_alerts: int = 5):
        """Initialize alert throttler with time window and max alerts."""
        self.window_seconds = window_seconds
        self.max_alerts = max_alerts
        self.alert_history: Dict[str, List[float]] = {}
    
    def should_throttle(self, alert_key: str) -> bool:
        """Check if an alert should be throttled."""
        now = time.time()
        
        # Initialize history for this alert if it doesn't exist
        if alert_key not in self.alert_history:
            self.alert_history[alert_key] = []
        
        # Clean up old alerts
        cutoff_time = now - self.window_seconds
        self.alert_history[alert_key] = [
            t for t in self.alert_history[alert_key] if t > cutoff_time
        ]
        
        # Check if we've reached the max alerts
        if len(self.alert_history[alert_key]) >= self.max_alerts:
            return True
        
        # Add this alert to the history
        self.alert_history[alert_key].append(now)
        return False


class AlertRouter:
    """Routes alerts to appropriate channels based on severity and category."""
    
    def __init__(self):
        """Initialize alert router with routing rules."""
        # Default routing table - can be overridden by configuration
        self.routing_table = {
            AlertSeverity.CRITICAL: [
                AlertChannel.EMAIL, 
                AlertChannel.SMS, 
                AlertChannel.PAGERDUTY,
                AlertChannel.SLACK
            ],
            AlertSeverity.HIGH: [
                AlertChannel.EMAIL, 
                AlertChannel.PAGERDUTY,
                AlertChannel.SLACK
            ],
            AlertSeverity.MEDIUM: [
                AlertChannel.EMAIL,
                AlertChannel.SLACK
            ],
            AlertSeverity.LOW: [
                AlertChannel.SLACK
            ],
            AlertSeverity.INFO: [
                AlertChannel.SLACK
            ]
        }
        
        # Special routing for certain categories (overrides severity routing)
        self.category_routing = {
            AlertCategory.SECURITY: {
                AlertSeverity.MEDIUM: [
                    AlertChannel.EMAIL,
                    AlertChannel.PAGERDUTY,
                    AlertChannel.SLACK
                ],
                AlertSeverity.LOW: [
                    AlertChannel.EMAIL,
                    AlertChannel.SLACK
                ]
            },
            AlertCategory.FINANCIAL: {
                AlertSeverity.MEDIUM: [
                    AlertChannel.EMAIL,
                    AlertChannel.SLACK
                ]
            }
        }
    
    def get_channels_for_alert(self, alert: Alert) -> List[AlertChannel]:
        """Determine which channels to send the alert to."""
        # Check if there's a special routing for this category and severity
        if (alert.category in self.category_routing and 
            alert.severity in self.category_routing[alert.category]):
            return self.category_routing[alert.category][alert.severity]
        
        # Otherwise use the default routing for this severity
        return self.routing_table[alert.severity]


class AlertManager:
    """Manages alert generation, throttling, and delivery."""
    
    def __init__(self):
        """Initialize alert manager with needed components."""
        self.throttler = AlertThrottler()
        self.router = AlertRouter()
        
        # Alert handlers for different channels
        self.handlers = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SMS: self._send_sms_alert,
            AlertChannel.SLACK: self._send_slack_alert,
            AlertChannel.PAGERDUTY: self._send_pagerduty_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert
        }
        
        # On-call rotation schedule (could be loaded from a database or config)
        self.on_call_schedule = {
            # day_of_week (0-6, 0 is Monday): email address
            0: "on-call-monday@elson.com",
            1: "on-call-tuesday@elson.com",
            2: "on-call-wednesday@elson.com",
            3: "on-call-thursday@elson.com",
            4: "on-call-friday@elson.com",
            5: "on-call-weekend@elson.com",
            6: "on-call-weekend@elson.com"
        }
        
        # Escalation policy (minutes to wait before escalating)
        self.escalation_delays = {
            AlertSeverity.CRITICAL: 15,  # 15 minutes
            AlertSeverity.HIGH: 30,      # 30 minutes
            AlertSeverity.MEDIUM: 60,    # 1 hour
            AlertSeverity.LOW: 240,      # 4 hours
            AlertSeverity.INFO: None     # No escalation
        }
        
        # Fallback contact for all alerts
        self.fallback_email = "alerts@elson.com"
    
    def trigger_alert(
        self, 
        title: str,
        message: str,
        severity: AlertSeverity,
        category: AlertCategory,
        source: str,
        details: Optional[Dict[str, Any]] = None,
        throttle_key: Optional[str] = None
    ) -> bool:
        """Trigger a new alert with the given parameters."""
        # Create the alert object
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            category=category,
            source=source,
            details=details
        )
        
        # Generate throttle key if not provided
        if not throttle_key:
            throttle_key = f"{category.value}:{source}:{title}"
        
        # Check if alert should be throttled
        if self.throttler.should_throttle(throttle_key):
            logger.info(f"Alert throttled: {throttle_key}")
            return False
        
        # Log the alert
        logger.info(f"Triggering alert: {alert.title} ({alert.severity.value})")
        
        # Determine which channels to send to
        channels = self.router.get_channels_for_alert(alert)
        
        # Send alert to each channel
        for channel in channels:
            try:
                if channel in self.handlers:
                    self.handlers[channel](alert)
            except Exception as e:
                logger.error(f"Failed to send alert to {channel}: {str(e)}")
        
        # Schedule escalation if needed
        self._schedule_escalation(alert)
        
        return True
    
    def _schedule_escalation(self, alert: Alert) -> None:
        """Schedule an escalation for an alert if not acknowledged."""
        # Get escalation delay for this severity
        delay_minutes = self.escalation_delays.get(alert.severity)
        
        # Skip if no escalation is configured for this severity
        if delay_minutes is None:
            return
        
        # In a real implementation, this would schedule a task using Celery or similar
        # For this implementation, we'll just log the escalation plan
        escalation_time = alert.timestamp + timedelta(minutes=delay_minutes)
        logger.info(
            f"Alert {alert.title} will escalate at {escalation_time.isoformat()} "
            f"if not acknowledged"
        )
    
    def _get_current_on_call_email(self) -> str:
        """Get the current on-call person's email based on the schedule."""
        day_of_week = datetime.utcnow().weekday()
        return self.on_call_schedule.get(day_of_week, self.fallback_email)
    
    def _send_email_alert(self, alert: Alert) -> None:
        """Send an alert via email."""
        recipients = [self._get_current_on_call_email()]
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            recipients.append(self.fallback_email)
        
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = "alerts@elson.com"
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        # Create message body
        body = f"""
        Alert Details:
        --------------
        Severity: {alert.severity.value}
        Category: {alert.category.value}
        Source: {alert.source}
        Time: {alert.timestamp.isoformat()}
        
        Message:
        {alert.message}
        
        Additional Details:
        {json.dumps(alert.details, indent=2)}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send the email (commented out as we don't have SMTP configured)
        """
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp_password = secret_manager.get_secret("SMTP_PASSWORD")
                server.login(settings.SMTP_USERNAME, smtp_password)
            server.send_message(msg)
        """
        
        # For testing - log the email instead
        logger.info(f"Would send email: {msg['Subject']} to {msg['To']}")
    
    def _send_sms_alert(self, alert: Alert) -> None:
        """Send an alert via SMS."""
        # This is a placeholder for SMS integration
        # In a real implementation, this would use Twilio or similar service
        logger.info(f"Would send SMS for alert: {alert.title}")
    
    def _send_slack_alert(self, alert: Alert) -> None:
        """Send an alert to Slack."""
        # Prepare the Slack message
        emoji = {
            AlertSeverity.CRITICAL: ":red_circle:",
            AlertSeverity.HIGH: ":orange_circle:",
            AlertSeverity.MEDIUM: ":large_yellow_circle:",
            AlertSeverity.LOW: ":large_blue_circle:",
            AlertSeverity.INFO: ":white_circle:"
        }.get(alert.severity, ":question:")
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {alert.title}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:* {alert.severity.value}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Category:* {alert.category.value}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Source:* {alert.source}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:* {alert.timestamp.isoformat()}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": alert.message
                    }
                }
            ]
        }
        
        # Add details if they exist
        if alert.details:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details:*\n```{json.dumps(alert.details, indent=2)}```"
                }
            })
        
        # Send to Slack (commented out as we don't have webhook configured)
        """
        slack_webhook_url = secret_manager.get_secret("SLACK_WEBHOOK_URL")
        response = requests.post(
            slack_webhook_url,
            json=message,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        """
        
        # For testing - log the message instead
        logger.info(f"Would send Slack message: {message}")
    
    def _send_pagerduty_alert(self, alert: Alert) -> None:
        """Send an alert to PagerDuty."""
        # This is a placeholder for PagerDuty integration
        # In a real implementation, this would use the PagerDuty Events API
        logger.info(f"Would send PagerDuty alert: {alert.title}")
    
    def _send_webhook_alert(self, alert: Alert) -> None:
        """Send an alert to a webhook endpoint."""
        # This is a placeholder for webhook integration
        # In a real implementation, this would send the alert to a configured webhook
        logger.info(f"Would send webhook alert: {alert.title}")


# Note: AlertManager is instantiated in alerts_manager.py to avoid circular dependencies
# See alerts_manager.py for global instance and get_alert_manager function
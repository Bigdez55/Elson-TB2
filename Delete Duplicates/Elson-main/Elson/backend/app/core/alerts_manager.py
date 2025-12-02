"""Alert Manager Module.

This module provides a separate instantiation of the AlertManager
to avoid circular dependencies when importing the alert_manager.
"""

from typing import Dict, Any, Optional
import logging
from .alerts import AlertManager, AlertSeverity, AlertCategory

logger = logging.getLogger(__name__)

# Create a global instance of AlertManager for dependency injection
alert_manager = AlertManager()

def get_alert_manager():
    """Get the global AlertManager instance."""
    return alert_manager

# Add helper method for easier alerting with fewer parameters
def send_alert(
    title: str,
    message: str,
    level: str = "info",
    source: str = "system",
    context: Optional[Dict[str, Any]] = None
):
    """Send an alert with simplified parameters.
    
    Args:
        title: The alert title
        message: The alert message
        level: The alert severity level (info, low, medium, high, critical)
        source: The alert source
        context: Additional context information for the alert
    """
    # Map string level to AlertSeverity
    severity_map = {
        "info": AlertSeverity.INFO,
        "low": AlertSeverity.LOW,
        "medium": AlertSeverity.MEDIUM,
        "high": AlertSeverity.HIGH,
        "critical": AlertSeverity.CRITICAL,
        "error": AlertSeverity.HIGH  # Map error to HIGH for convenience
    }
    
    # Default to INFO if level is not recognized
    severity = severity_map.get(level.lower(), AlertSeverity.INFO)
    
    # Determine the best category based on source
    if "database" in source.lower():
        category = AlertCategory.SYSTEM
    elif "market" in source.lower():
        category = AlertCategory.TRADING
    elif "auth" in source.lower() or "security" in source.lower():
        category = AlertCategory.SECURITY
    elif "performance" in source.lower():
        category = AlertCategory.PERFORMANCE
    elif "payment" in source.lower() or "billing" in source.lower():
        category = AlertCategory.FINANCIAL
    else:
        category = AlertCategory.OTHER
    
    try:
        # Add the alert method to the AlertManager instance if it doesn't exist yet
        if not hasattr(alert_manager, "send_alert"):
            # Monkey patch the send_alert method to the instance
            setattr(alert_manager, "send_alert", send_alert)
            logger.info("Added send_alert method to AlertManager instance")
        
        # Call the trigger_alert method
        return alert_manager.trigger_alert(
            title=title,
            message=message,
            severity=severity,
            category=category,
            source=source,
            details=context
        )
    except Exception as e:
        logger.error(f"Failed to send alert: {str(e)}")
        return False

# Add the send_alert method to the alert_manager instance
setattr(alert_manager, "send_alert", send_alert)
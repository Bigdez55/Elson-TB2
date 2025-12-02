#!/usr/bin/env python3
"""
Script to test the alerting system by sending test alerts of different severities and categories.

Usage:
    python -m app.scripts.test_alerts [severity] [category]

Example:
    python -m app.scripts.test_alerts  # Test all severities and categories
    python -m app.scripts.test_alerts critical system  # Test only critical system alerts
"""

import os
import sys
import logging
import time
from typing import Optional

# Add the parent directory to the path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.alerts import get_alert_manager, AlertSeverity, AlertCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_alerts(severity: Optional[str] = None, category: Optional[str] = None) -> None:
    """Test the alerting system by sending test alerts."""
    alert_manager = get_alert_manager()
    
    # Determine which severities to test
    severities = [s for s in AlertSeverity]
    if severity:
        try:
            severities = [AlertSeverity(severity.lower())]
        except ValueError:
            logger.error(f"Invalid severity: {severity}")
            logger.info(f"Valid severities: {', '.join([s.value for s in AlertSeverity])}")
            sys.exit(1)
    
    # Determine which categories to test
    categories = [c for c in AlertCategory]
    if category:
        try:
            categories = [AlertCategory(category.lower())]
        except ValueError:
            logger.error(f"Invalid category: {category}")
            logger.info(f"Valid categories: {', '.join([c.value for c in AlertCategory])}")
            sys.exit(1)
    
    # Generate test alerts for each combination
    for sev in severities:
        for cat in categories:
            title = f"TEST ALERT - {sev.value.upper()} - {cat.value.upper()}"
            message = f"This is a test alert for {sev.value} severity and {cat.value} category."
            source = "test_alerts.py"
            details = {
                "test": True,
                "timestamp": time.time(),
                "severity": sev.value,
                "category": cat.value
            }
            
            logger.info(f"Sending test alert: {title}")
            result = alert_manager.trigger_alert(
                title=title,
                message=message,
                severity=sev,
                category=cat,
                source=source,
                details=details
            )
            
            if result:
                logger.info(f"Successfully sent alert: {title}")
            else:
                logger.warning(f"Alert was throttled or failed: {title}")
            
            # Add a small delay between alerts to avoid overwhelming the system
            time.sleep(0.5)
    
    logger.info("Alert testing complete")

def main():
    """Main entry point for the script."""
    severity = None
    category = None
    
    if len(sys.argv) > 1:
        severity = sys.argv[1]
    
    if len(sys.argv) > 2:
        category = sys.argv[2]
    
    test_alerts(severity, category)

if __name__ == "__main__":
    main()
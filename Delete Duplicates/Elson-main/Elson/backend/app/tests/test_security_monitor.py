"""
Test module for security monitoring system.

These tests verify that the security monitoring functions work correctly.
"""

import pytest
import time
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.security_monitor import SecurityMonitor, get_security_monitor
from app.core.alerts import AlertCategory, AlertSeverity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_security_monitor_instantiation():
    """Test that security monitor can be instantiated."""
    monitor = SecurityMonitor()
    assert monitor is not None
    assert isinstance(monitor.security_events, dict)
    assert isinstance(monitor.suspicious_ips, set)
    assert isinstance(monitor.account_lockouts, dict)

def test_get_security_monitor_singleton():
    """Test that get_security_monitor returns a singleton instance."""
    monitor1 = get_security_monitor()
    monitor2 = get_security_monitor()
    assert monitor1 is monitor2
    assert isinstance(monitor1, SecurityMonitor)

def test_record_login_attempt():
    """Test recording login attempts."""
    monitor = SecurityMonitor()
    
    # Record a successful login
    monitor.record_login_attempt(
        user_id="testuser", 
        ip="192.168.1.1", 
        success=True,
        details={"browser": "Chrome"}
    )
    
    # Check that it was recorded
    assert len(monitor.security_events["login_attempts"]) == 1
    attempt = monitor.security_events["login_attempts"][0]
    assert attempt["user_id"] == "testuser"
    assert attempt["ip"] == "192.168.1.1"
    assert attempt["success"] is True
    assert attempt["details"].get("browser") == "Chrome"
    
    # Record a failed login
    monitor.record_login_attempt(
        user_id="testuser", 
        ip="192.168.1.1", 
        success=False
    )
    
    # Check that it was recorded
    assert len(monitor.security_events["login_attempts"]) == 2
    attempt = monitor.security_events["login_attempts"][1]
    assert attempt["success"] is False

@patch('app.core.security_monitor.send_warning_alert')
def test_excessive_login_failures(mock_send_alert):
    """Test that excessive login failures trigger an alert."""
    monitor = SecurityMonitor()
    
    # Override the threshold to make testing easier
    monitor.login_failure_threshold = 3
    
    # Record multiple failed login attempts
    for i in range(4):  # One more than the threshold
        monitor.record_login_attempt(
            user_id="testuser", 
            ip="192.168.1.1", 
            success=False
        )
    
    # Check that an alert was sent
    assert mock_send_alert.called
    args, kwargs = mock_send_alert.call_args
    assert kwargs["category"] == AlertCategory.SECURITY
    assert "testuser" in kwargs["message"]
    
    # Check that IP was added to suspicious list
    assert "192.168.1.1" in monitor.suspicious_ips

def test_record_token_verification_failure():
    """Test recording token verification failures."""
    monitor = SecurityMonitor()
    
    # Record a token failure
    monitor.record_token_verification_failure(
        ip="192.168.1.1",
        error_type="expired_token",
        details={"token_type": "access"}
    )
    
    # Check that it was recorded
    assert len(monitor.security_events["token_failures"]) == 1
    failure = monitor.security_events["token_failures"][0]
    assert failure["ip"] == "192.168.1.1"
    assert failure["error_type"] == "expired_token"
    assert failure["details"].get("token_type") == "access"

def test_record_suspicious_activity():
    """Test recording suspicious activity."""
    monitor = SecurityMonitor()
    
    # Record suspicious activity
    monitor.record_suspicious_activity(
        activity_type="sql_injection_attempt",
        ip="192.168.1.1",
        details={
            "query": "SELECT * FROM users WHERE 1=1;--",
            "endpoint": "/api/users"
        }
    )
    
    # Check that it was recorded
    assert len(monitor.security_events["suspicious_activity"]) == 1
    activity = monitor.security_events["suspicious_activity"][0]
    assert activity["activity_type"] == "sql_injection_attempt"
    assert activity["ip"] == "192.168.1.1"
    assert "query" in activity["details"]
    
    # Check that IP was added to suspicious list
    assert "192.168.1.1" in monitor.suspicious_ips

def test_account_lockout():
    """Test account lockout functionality."""
    monitor = SecurityMonitor()
    
    # Lock an account
    monitor.record_account_lockout(
        user_id="testuser",
        ip="192.168.1.1",
        reason="too_many_failed_attempts",
        duration_seconds=300
    )
    
    # Check if account is locked
    is_locked, remaining = monitor.is_account_locked("testuser")
    assert is_locked is True
    assert isinstance(remaining, timedelta)
    assert remaining.total_seconds() <= 300  # Should be less due to processing time
    
    # Check that a non-locked account returns False
    is_locked, remaining = monitor.is_account_locked("otheruser")
    assert is_locked is False
    assert remaining is None

def test_cleanup():
    """Test cleanup of old events and expired lockouts."""
    monitor = SecurityMonitor()
    
    # Add some data
    monitor.record_login_attempt("user1", "192.168.1.1", True)
    monitor.record_token_verification_failure("192.168.1.2", "invalid_signature")
    monitor.record_account_lockout("user1", "192.168.1.1", "testing", 1)  # 1 second lockout
    
    # Wait for the lockout to expire
    time.sleep(1.1)
    
    # Run cleanup
    monitor.cleanup()
    
    # Check that lockout was removed
    is_locked, _ = monitor.is_account_locked("user1")
    assert is_locked is False
    
    # Events should still be there since they're less than a day old
    assert len(monitor.security_events["login_attempts"]) > 0

def test_security_summary():
    """Test getting security event summary."""
    monitor = SecurityMonitor()
    
    # Add some test data
    monitor.record_login_attempt("user1", "192.168.1.1", True)
    monitor.record_login_attempt("user2", "192.168.1.2", False)
    monitor.suspicious_ips.add("192.168.1.100")
    monitor.suspicious_ips.add("192.168.1.101")
    
    # Get summary
    summary = monitor.get_security_summary()
    
    # Check summary structure
    assert "timestamp" in summary
    assert "suspicious_ip_count" in summary
    assert "locked_account_count" in summary
    assert "events_last_hour" in summary
    assert "events_last_day" in summary
    
    # Check values
    assert summary["suspicious_ip_count"] == 2
    assert summary["locked_account_count"] == 0
    assert summary["events_last_hour"].get("login_attempts") == 2

if __name__ == "__main__":
    # Run tests manually
    test_security_monitor_instantiation()
    test_get_security_monitor_singleton()
    test_record_login_attempt()
    test_record_token_verification_failure()
    test_record_suspicious_activity()
    test_account_lockout()
    test_cleanup()
    test_security_summary()
    
    print("All tests passed!")
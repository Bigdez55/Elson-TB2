"""
Test module for security middleware.

These tests verify that the security middleware correctly monitors and responds to security events.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import re

from app.core.middleware import SecurityMiddleware
from app.core.security_monitor import SecurityMonitor

# Define a simple test app
async def test_endpoint(request):
    return JSONResponse({"status": "ok"})

async def auth_endpoint(request):
    # Simulate an unauthorized request
    return JSONResponse({"status": "unauthorized"}, status_code=401)

async def forbidden_endpoint(request):
    # Simulate a forbidden request
    return JSONResponse({"status": "forbidden"}, status_code=403)

async def suspicious_endpoint(request):
    # This will be accessed with suspicious parameters
    return JSONResponse({"status": "ok"})

# Create routes for testing
routes = [
    Route("/test", test_endpoint),
    Route("/auth", auth_endpoint),
    Route("/forbidden", forbidden_endpoint),
    Route("/api/v1/users/search", suspicious_endpoint),
]

# Create application with security middleware - but with empty suspicious patterns
def create_test_app(suspicious_patterns=None, sensitive_paths=None):
    app = Starlette(routes=routes)
    # Configure middleware with test-specific settings
    app.add_middleware(
        SecurityMiddleware, 
        enabled=True,
        suspicious_patterns=suspicious_patterns or [],
        sensitive_paths=sensitive_paths or []
    )
    return app

@pytest.fixture
def clean_client():
    """Client with no suspicious patterns or sensitive paths."""
    app = create_test_app(suspicious_patterns=[], sensitive_paths=[])
    return TestClient(app)

@pytest.fixture
def sensitive_auth_client():
    """Client with /auth in sensitive paths."""
    app = create_test_app(suspicious_patterns=[], sensitive_paths=['/auth'])
    return TestClient(app)

@pytest.fixture
def sensitive_forbidden_client():
    """Client with /forbidden in sensitive paths."""
    app = create_test_app(suspicious_patterns=[], sensitive_paths=['/forbidden'])
    return TestClient(app)

@pytest.fixture
def suspicious_client():
    """Client with SQL injection pattern."""
    app = create_test_app(
        suspicious_patterns=[("sql_injection", re.compile(r"'.*OR.*1.*=.*1.*--"))],
        sensitive_paths=[]
    )
    return TestClient(app)

def test_normal_request(clean_client):
    """Test that normal requests are processed without triggering security alerts."""
    with patch('app.core.middleware.get_security_monitor') as mock_get_monitor:
        # Setup mock
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.is_suspicious_ip.return_value = False
        
        # Make a normal request
        response = clean_client.get("/test")
        
        # Check response
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        # Check security monitor interactions
        mock_monitor.is_suspicious_ip.assert_called_once()
        # No suspicious activity should be recorded for a normal request with no patterns
        mock_monitor.record_suspicious_activity.assert_not_called()

def test_suspicious_ip(clean_client):
    """Test that requests from suspicious IPs are tracked."""
    with patch('app.core.middleware.get_security_monitor') as mock_get_monitor:
        # Setup mock - this IP is suspicious
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.is_suspicious_ip.return_value = True
        
        # Make a request from a "suspicious" IP
        response = clean_client.get("/test")
        
        # Check response - should still work
        assert response.status_code == 200
        
        # Check security monitor interactions
        mock_monitor.is_suspicious_ip.assert_called_once()
        mock_monitor.record_suspicious_activity.assert_called_once()
        # The call should include suspicious_ip_access type
        args, kwargs = mock_monitor.record_suspicious_activity.call_args
        assert kwargs["activity_type"] == "suspicious_ip_access"

def test_authentication_failure(sensitive_auth_client):
    """Test that authentication failures are tracked."""
    with patch('app.core.middleware.get_security_monitor') as mock_get_monitor:
        # Setup mock
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.is_suspicious_ip.return_value = False
        
        # Make a request that will result in 401 Unauthorized to a sensitive path
        response = sensitive_auth_client.get("/auth", headers={"Authorization": "Bearer invalid-token"})
        
        # Check response
        assert response.status_code == 401
        
        # Check security monitor interactions
        mock_monitor.record_token_verification_failure.assert_called_once()
        args, kwargs = mock_monitor.record_token_verification_failure.call_args
        assert kwargs["error_type"] == "bearer_token_invalid"

def test_authorization_failure(sensitive_forbidden_client):
    """Test that authorization failures (403) are tracked."""
    with patch('app.core.middleware.get_security_monitor') as mock_get_monitor:
        # Setup mock
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.is_suspicious_ip.return_value = False
        
        # Make a request that will result in 403 Forbidden to a sensitive path
        response = sensitive_forbidden_client.get("/forbidden", headers={"Authorization": "Bearer valid-but-unauthorized"})
        
        # Check response
        assert response.status_code == 403
        
        # Check security monitor interactions
        mock_monitor.record_suspicious_activity.assert_called_once()
        args, kwargs = mock_monitor.record_suspicious_activity.call_args
        assert kwargs["activity_type"] == "authorization_failure"

def test_suspicious_patterns(suspicious_client):
    """Test that suspicious patterns in requests are detected."""
    with patch('app.core.middleware.get_security_monitor') as mock_get_monitor:
        # Setup mock
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.is_suspicious_ip.return_value = False
        
        # Make a request with a suspicious SQL injection pattern
        response = suspicious_client.get("/api/v1/users/search?query=user' OR 1=1; --")
        
        # Check response - should still work, but be logged
        assert response.status_code == 200
        
        # Check security monitor interactions
        mock_monitor.record_suspicious_activity.assert_called_once()
        args, kwargs = mock_monitor.record_suspicious_activity.call_args
        assert kwargs["activity_type"] == "suspicious_request_pattern"
        assert "patterns_matched" in kwargs["details"]
        assert "sql_injection" in kwargs["details"]["patterns_matched"]

@pytest.mark.asyncio
async def test_exception_handling():
    """Test that exceptions during request processing are tracked."""
    with patch('app.core.middleware.get_security_monitor') as mock_get_monitor:
        # Setup mock
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor
        mock_monitor.is_suspicious_ip.return_value = False
        
        # Setup a mock to raise an exception during processing
        mock_call_next = AsyncMock(side_effect=ValueError("Test exception"))
        # Use empty patterns to prevent the suspicious pattern detection
        middleware = SecurityMiddleware(app=None, suspicious_patterns=[])
        
        # Create a mock request
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.url.path = "/test" 
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.url = MagicMock()
        # Use a URL that won't trigger path traversal detection
        mock_request.url.__str__.return_value = "http://example.com/test"
        
        # Test that the exception is recorded
        with pytest.raises(ValueError):
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Check call count and details to ensure only the exception was recorded
        assert mock_monitor.record_suspicious_activity.call_count == 1
        
        # Get the last call args
        args, kwargs = mock_monitor.record_suspicious_activity.call_args_list[-1]
        assert kwargs["activity_type"] == "request_exception"
        assert kwargs["details"]["error_type"] == "ValueError"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
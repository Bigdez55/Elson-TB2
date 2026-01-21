import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Test the health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # Check essential fields
    assert data["status"] == "healthy"
    assert data["service"] == "elson-trading-platform"
    # Additional fields may include database status
    if "database" in data:
        assert "connected" in data["database"]


def test_root_endpoint():
    """Test the root endpoint."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Elson Personal Trading Platform API"}

"""
Basic tests to verify the environment is set up correctly
"""

def test_health_endpoint(client):
    """Test that the health endpoint returns successfully"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
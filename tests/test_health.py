"""Tests for health check endpoints."""


def test_health_check(client):
    """Test main health endpoint returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "server" in data
    assert "version" in data


def test_readiness_check(client):
    """Test readiness endpoint."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert "timestamp" in data


def test_liveness_check(client):
    """Test liveness endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["alive"] is True
    assert "timestamp" in data


def test_root_endpoint(client):
    """Test root endpoint returns app info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert data["api"] == "/api/v1"

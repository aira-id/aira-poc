"""
Tests for Health Check Endpoints.

This module tests the health and readiness check endpoints
used for monitoring the AIRA application status.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_check_status(client):
    """Test the health check endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_check_contains_app_info(client):
    """Test that health check includes app name and version."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert data["app_name"] == "AIRA Voice Bot Server"
    assert data["version"] == "0.1.0"


def test_health_check_includes_timestamp(client):
    """Test that health check includes a valid timestamp."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data

    # Verify timestamp is valid ISO format
    try:
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert timestamp is not None
    except ValueError:
        pytest.fail("Timestamp is not in valid ISO format")


def test_health_check_response_structure(client):
    """Test the complete structure of health check response."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    required_fields = ["status", "app_name", "version", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_readiness_check_status(client):
    """Test the readiness check endpoint returns ready status."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_readiness_check_services(client):
    """Test that readiness check includes service statuses."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "services" in data

    services = data["services"]
    assert "asr" in services
    assert "llm" in services
    assert "tts" in services


def test_readiness_check_service_states(client):
    """Test that services are in expected states."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()

    services = data["services"]
    # Currently all services should be not_configured
    assert services["asr"] == "not_configured"
    assert services["llm"] == "not_configured"
    assert services["tts"] == "not_configured"


def test_readiness_check_response_structure(client):
    """Test the complete structure of readiness check response."""
    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()

    required_fields = ["status", "services"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_health_check_multiple_calls(client):
    """Test that health check can be called multiple times."""
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_readiness_check_multiple_calls(client):
    """Test that readiness check can be called multiple times."""
    for _ in range(5):
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


def test_health_endpoints_content_type(client):
    """Test that health endpoints return JSON content type."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]

    response = client.get("/health/ready")
    assert "application/json" in response.headers["content-type"]

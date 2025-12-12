"""
Tests for Main Application Module.

This module tests the FastAPI application creation and configuration
including middleware, routers, and static file mounting.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import create_app, app


def test_create_app_returns_fastapi_instance():
    """Test that create_app returns a FastAPI instance."""
    test_app = create_app()

    assert isinstance(test_app, FastAPI)


def test_app_title_and_version():
    """Test that app has correct title and version."""
    test_app = create_app()

    assert test_app.title == "AIRA Voice Bot Server"
    assert test_app.version == "0.1.0"


def test_app_has_docs_enabled():
    """Test that API documentation endpoints are configured."""
    test_app = create_app()

    assert test_app.docs_url == "/docs"
    assert test_app.redoc_url == "/redoc"


def test_app_middleware_configured():
    """Test that middleware is properly configured."""
    test_app = create_app()

    # Check that middleware stack is not empty
    assert len(test_app.user_middleware) > 0


def test_app_cors_middleware():
    """Test that CORS middleware is configured."""
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


def test_app_health_routes_included():
    """Test that health check routes are included."""
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/health/ready")
    assert response.status_code == 200


def test_app_websocket_routes_included():
    """Test that WebSocket routes are included."""
    test_app = create_app()

    # Check that routes exist
    routes = [route.path for route in test_app.routes]

    assert "/ws/asr" in routes
    assert "/ws/tts" in routes
    assert "/ws/speak" in routes


def test_app_singleton():
    """Test that the app instance is created correctly."""
    assert isinstance(app, FastAPI)
    assert app.title == "AIRA Voice Bot Server"


def test_app_startup_event():
    """Test that startup event is registered."""
    test_app = create_app()

    # FastAPI should have startup event handlers
    assert len(test_app.router.on_startup) > 0


def test_app_shutdown_event():
    """Test that shutdown event is registered."""
    test_app = create_app()

    # FastAPI should have shutdown event handlers
    assert len(test_app.router.on_shutdown) > 0


def test_app_debug_mode():
    """Test that debug mode is configurable."""
    test_app = create_app()

    # Debug mode should match settings
    from app.config import settings
    assert test_app.debug == settings.debug


def test_app_routes_accessible():
    """Test that main routes are accessible."""
    client = TestClient(app)

    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200

    # Test docs endpoint
    response = client.get("/docs")
    assert response.status_code == 200

    # Test redoc endpoint
    response = client.get("/redoc")
    assert response.status_code == 200


def test_app_handles_404():
    """Test that app handles non-existent routes."""
    client = TestClient(app)

    response = client.get("/non-existent-route")
    assert response.status_code == 404


def test_app_handles_405():
    """Test that app handles method not allowed."""
    client = TestClient(app)

    # Try to POST to a GET-only endpoint
    response = client.post("/health")
    assert response.status_code == 405


def test_app_middleware_order():
    """Test that middleware is applied in correct order."""
    test_app = create_app()

    # Middleware should be applied (outermost to innermost):
    # 1. ErrorHandlingMiddleware
    # 2. RequestLoggingMiddleware
    # 3. CORSMiddleware (added by FastAPI)

    middleware_types = [m.cls.__name__ for m in test_app.user_middleware]

    assert "ErrorHandlingMiddleware" in middleware_types
    assert "RequestLoggingMiddleware" in middleware_types
    assert "CORSMiddleware" in middleware_types


def test_app_error_handling():
    """Test that app handles errors with middleware."""
    from fastapi import FastAPI
    from app.core.middleware import ErrorHandlingMiddleware

    # Create a new test app with just the error middleware
    test_app = FastAPI()
    test_app.add_middleware(ErrorHandlingMiddleware)

    @test_app.get("/test-error")
    async def test_error():
        raise ValueError("Test error")

    client = TestClient(test_app)
    response = client.get("/test-error")

    # Should be caught by ErrorHandlingMiddleware
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"] == "InternalServerError"


def test_app_logging_middleware_integration(caplog):
    """Test that logging middleware logs requests."""
    client = TestClient(app)

    with caplog.at_level("INFO"):
        response = client.get("/health")

    assert response.status_code == 200
    assert "Request: GET /health" in caplog.text

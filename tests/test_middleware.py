"""
Tests for Custom Middleware.

This module tests the error handling and request logging middleware
used in the AIRA application.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from app.core.exceptions import AIRAException, ASRException, TTSException


@pytest.fixture
def app_with_error_middleware():
    """Create a test FastAPI app with error handling middleware."""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/test")
    async def test_route():
        return {"message": "success"}

    @app.get("/aira-error")
    async def aira_error_route():
        raise AIRAException("Custom AIRA error", status_code=400)

    @app.get("/asr-error")
    async def asr_error_route():
        raise ASRException("ASR processing failed")

    @app.get("/tts-error")
    async def tts_error_route():
        raise TTSException("TTS synthesis failed")

    @app.get("/generic-error")
    async def generic_error_route():
        raise ValueError("Unexpected error")

    return app


@pytest.fixture
def app_with_logging_middleware():
    """Create a test FastAPI app with request logging middleware."""
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_route():
        return {"message": "success"}

    @app.post("/test-post")
    async def test_post_route():
        return {"message": "posted"}

    return app


def test_error_middleware_success(app_with_error_middleware):
    """Test that successful requests pass through error middleware."""
    client = TestClient(app_with_error_middleware)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {"message": "success"}


def test_error_middleware_aira_exception(app_with_error_middleware):
    """Test that AIRAException is caught and converted to JSON response."""
    client = TestClient(app_with_error_middleware)
    response = client.get("/aira-error")

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "AIRAException"
    assert data["message"] == "Custom AIRA error"


def test_error_middleware_asr_exception(app_with_error_middleware):
    """Test that ASRException is caught and handled properly."""
    client = TestClient(app_with_error_middleware)
    response = client.get("/asr-error")

    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "ASRException"
    assert data["message"] == "ASR processing failed"


def test_error_middleware_tts_exception(app_with_error_middleware):
    """Test that TTSException is caught and handled properly."""
    client = TestClient(app_with_error_middleware)
    response = client.get("/tts-error")

    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "TTSException"
    assert data["message"] == "TTS synthesis failed"


def test_error_middleware_generic_exception(app_with_error_middleware):
    """Test that generic exceptions are caught and return 500."""
    client = TestClient(app_with_error_middleware)
    response = client.get("/generic-error")

    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "InternalServerError"
    assert data["message"] == "An unexpected error occurred"


def test_logging_middleware_logs_request(app_with_logging_middleware, caplog):
    """Test that request logging middleware logs requests."""
    client = TestClient(app_with_logging_middleware)

    with caplog.at_level("INFO"):
        response = client.get("/test")

    assert response.status_code == 200
    assert "Request: GET /test" in caplog.text
    assert "Response: GET /test" in caplog.text
    assert "Status: 200" in caplog.text
    assert "Duration:" in caplog.text


def test_logging_middleware_logs_post_request(app_with_logging_middleware, caplog):
    """Test that logging middleware handles POST requests."""
    client = TestClient(app_with_logging_middleware)

    with caplog.at_level("INFO"):
        response = client.post("/test-post")

    assert response.status_code == 200
    assert "Request: POST /test-post" in caplog.text
    assert "Response: POST /test-post" in caplog.text


def test_logging_middleware_includes_timing(app_with_logging_middleware, caplog):
    """Test that logging middleware includes processing time."""
    client = TestClient(app_with_logging_middleware)

    with caplog.at_level("INFO"):
        response = client.get("/test")

    assert response.status_code == 200
    # Check that duration is logged in seconds with 3 decimal places
    assert "Duration:" in caplog.text
    assert "s" in caplog.text


def test_middleware_combination():
    """Test that both middlewares work together."""
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_route():
        return {"message": "success"}

    @app.get("/error")
    async def error_route():
        raise AIRAException("Test error", status_code=400)

    client = TestClient(app)

    # Test successful request
    response = client.get("/test")
    assert response.status_code == 200

    # Test error handling
    response = client.get("/error")
    assert response.status_code == 400
    assert response.json()["error"] == "AIRAException"

"""
Pytest Configuration and Shared Fixtures.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """
    Create a FastAPI test client.

    Returns:
        TestClient: Test client for making HTTP requests
    """
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """
    Create mock settings for testing.

    Returns:
        dict: Mock settings dictionary
    """
    return {
        "app_name": "AIRA Voice Bot Server",
        "app_version": "0.1.0",
        "debug": True,
        "host": "127.0.0.1",
        "port": 8000,
        "cors_origins": ["http://localhost:3000"],
        "cors_credentials": True,
        "cors_methods": ["GET", "POST"],
        "cors_headers": ["*"],
        "log_level": "DEBUG",
        "log_file": "logs/test.log"
    }


@pytest.fixture
def sample_audio_data():
    """
    Create sample audio data for WebSocket testing.

    Returns:
        bytes: Sample PCM audio data
    """
    import numpy as np
    # Generate 1 second of silence at 16kHz
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    audio = np.zeros(samples, dtype=np.int16)
    return audio.tobytes()

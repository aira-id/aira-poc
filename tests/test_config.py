"""
Tests for Application Configuration Settings.

This module tests the configuration loading and validation
using Pydantic Settings.
"""

import pytest
import os
from app.config import Settings


def test_default_settings():
    """Test that default settings are loaded correctly."""
    settings = Settings()

    assert settings.app_name == "AIRA Voice Bot Server"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.cors_origins == ["*"]
    assert settings.cors_credentials is True
    assert settings.cors_methods == ["*"]
    assert settings.cors_headers == ["*"]
    assert settings.log_level == "INFO"
    assert settings.log_file == "logs/aira-server.log"


def test_custom_settings_from_env(monkeypatch):
    """Test that settings can be overridden by environment variables."""
    monkeypatch.setenv("APP_NAME", "Custom AIRA Server")
    monkeypatch.setenv("APP_VERSION", "1.0.0")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.app_name == "Custom AIRA Server"
    assert settings.app_version == "1.0.0"
    assert settings.debug is True
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"


def test_cors_settings(monkeypatch):
    """Test CORS configuration settings."""
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8080"]')
    monkeypatch.setenv("CORS_CREDENTIALS", "false")
    monkeypatch.setenv("CORS_METHODS", '["GET", "POST"]')
    monkeypatch.setenv("CORS_HEADERS", '["Content-Type", "Authorization"]')

    settings = Settings()

    assert "http://localhost:3000" in str(settings.cors_origins)
    assert settings.cors_credentials is False


def test_settings_case_insensitive(monkeypatch):
    """Test that settings are case insensitive."""
    monkeypatch.setenv("app_name", "Test Server")
    monkeypatch.setenv("APP_VERSION", "2.0.0")

    settings = Settings()

    assert settings.app_name == "Test Server"
    assert settings.app_version == "2.0.0"


def test_optional_log_file():
    """Test that log_file can be None."""
    settings = Settings(log_file=None)
    assert settings.log_file is None


def test_settings_validation():
    """Test that invalid settings raise validation errors."""
    with pytest.raises(Exception):
        Settings(port="invalid_port")

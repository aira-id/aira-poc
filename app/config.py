"""
Application Configuration Settings.

This module defines the configuration settings for the AIRA voice bot server.
Settings are loaded from environment variables or .env file using Pydantic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic Settings to validate and load configuration from:
    - Environment variables
    - .env file in the project root

    Settings are organized into groups:
    - Application settings (name, version, debug mode)
    - Server settings (host, port)
    - CORS settings (origins, credentials, methods, headers)
    - Logging settings (level, file path)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = "AIRA Voice Bot Server"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/aira-server.log"


settings = Settings()

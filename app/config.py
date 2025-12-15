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

    # ASR (Automatic Speech Recognition) settings
    asr_model: str = "zipformer"
    asr_lang: str = "id"
    asr_sample_rate: int = 16000
    asr_encoder_filename: str = "encoder-epoch-99-avg-1.onnx"
    asr_decoder_filename: str = "decoder-epoch-99-avg-1.onnx"
    asr_joiner_filename: str = "joiner-epoch-99-avg-1.onnx"
    asr_tokens_filename: str = "tokens.txt"

    # LLM (Large Language Model) settings
    llm_endpoint: str = "http://localhost:8080/v1/chat/completions"
    llm_model: str = "gemma_1b_q8_0"
    llm_system_prompt: str = "You are a helpful assistant."
    llm_max_tokens: int = 150
    llm_temperature: float = 0.7

    # TTS (Text-to-Speech) settings
    tts_model: str = "zipformer"
    tts_speaker: str = "wibowo"
    tts_sample_rate: int = 16000
    tts_speed: float = 1.0
    tts_split: bool = True
    tts_provider: str = "cpu"
    tts_threads: int = 2
    models_root: str = "/home/fitra/Workspaces/aira-server/models"


settings = Settings()

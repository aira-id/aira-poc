from abc import ABC, abstractmethod
from typing import Optional


class ASRBase(ABC):
    """Abstract base class for Automatic Speech Recognition services."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the ASR service."""
        pass

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    async def transcribe_stream(self, audio_stream):
        """
        Transcribe streaming audio data.

        Args:
            audio_stream: Audio stream generator

        Yields:
            Transcribed text chunks
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

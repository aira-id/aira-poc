from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator


class TTSBase(ABC):
    """Abstract base class for Text-to-Speech services."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the TTS service."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Synthesize text to audio.

        Args:
            text: Input text to synthesize
            voice: Voice identifier/name
            **kwargs: Additional TTS-specific parameters

        Returns:
            Audio data as bytes
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize text to streaming audio.

        Args:
            text: Input text to synthesize
            voice: Voice identifier/name
            **kwargs: Additional TTS-specific parameters

        Yields:
            Audio data chunks as bytes
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

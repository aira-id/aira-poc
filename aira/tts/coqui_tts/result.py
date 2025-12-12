"""
TTS Result class for representing synthesis results.
"""

class TTSResult:
    """
    Represents a TTS generation result with metadata.
    """
    def __init__(self, pcm_bytes: bytes, finished: bool):
        """
        Initialize TTS result.

        Args:
            pcm_bytes: Raw PCM audio bytes (int16)
            finished: Whether this is the final result
        """
        self.pcm_bytes = pcm_bytes
        self.finished = finished
        self.progress: float = 0.0
        self.elapsed: float = 0.0
        self.audio_duration: float = 0.0
        self.audio_size: int = 0

    def to_dict(self):
        """Convert result to dictionary for JSON serialization."""
        return {
            "progress": self.progress,
            "finished": self.finished,
            "elapsed": f'{int(self.elapsed * 1000)}ms',
            "duration": f'{self.audio_duration:.2f}s',
            "size": self.audio_size
        }

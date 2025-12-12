"""
ASR recognition result.
"""

from typing import Optional


class ASRResult:
    """
    Represents the result of an ASR (Automatic Speech Recognition) operation.

    Contains the transcribed text along with metadata about the recognition process.
    Can represent either partial results (during streaming) or final results (at endpoint).

    Attributes:
        text (str): The recognized/transcribed text
        finished (bool): Whether this is a final result (True) or partial/interim result (False)
        idx (int): Segment index for tracking multiple utterances in a session
        start (float): Start timestamp of the audio segment in seconds (default: 0.0)
        end (float): End timestamp of the audio segment in seconds (default: 0.0)
        channel (Optional[int]): Audio channel identifier for multi-channel audio (default: None)

    Example:
        >>> partial_result = ASRResult("Hello wor", finished=False, idx=0)
        >>> final_result = ASRResult("Hello world", finished=True, idx=0, start=0.0, end=1.5)
        >>> print(final_result.to_dict())
        {'text': 'Hello world', 'finished': True, 'idx': 0, 'start': 0.0, 'end': 1.5, 'channel': None}
    """

    def __init__(self, text: str, finished: bool, idx: int, start: float = 0.0, end: float = 0.0, channel: Optional[int] = None):
        """
        Initialize an ASR result.

        Args:
            text: The recognized/transcribed text
            finished: Whether this is a final result (True) or partial result (False)
            idx: Segment index for tracking multiple utterances
            start: Start timestamp of the audio segment in seconds (default: 0.0)
            end: End timestamp of the audio segment in seconds (default: 0.0)
            channel: Optional audio channel identifier (default: None)
        """
        self.text = text
        self.finished = finished
        self.idx = idx
        self.start = start
        self.end = end
        self.channel = channel

    def __repr__(self):
        """Return string representation of the ASR result."""
        return f"ASRResult(text={self.text}, finished={self.finished}, idx={self.idx})"

    def to_dict(self):
        """
        Convert the ASR result to a dictionary for JSON serialization.

        Returns:
            dict: Dictionary containing all result fields
        """
        return {
            "text": self.text,
            "finished": self.finished,
            "idx": self.idx,
            "start": self.start,
            "end": self.end,
            "channel": self.channel,
        }

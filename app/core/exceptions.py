"""
Custom Exceptions for AIRA Application.

This module defines exception classes for handling errors across different
components of the AIRA voice bot system. All exceptions inherit from AIRAException
which provides a consistent interface for error handling and HTTP status codes.
"""


class AIRAException(Exception):
    """
    Base exception for AIRA application.

    All custom AIRA exceptions should inherit from this class. It provides
    a consistent interface with error messages and HTTP status codes.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the error response
    """

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize AIRA exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ASRException(AIRAException):
    """
    Exception raised for ASR-related errors.

    Used for errors during speech recognition processing, model loading,
    or audio stream handling.
    """

    def __init__(self, message: str):
        """
        Initialize ASR exception.

        Args:
            message: Human-readable error message
        """
        super().__init__(message, status_code=500)


class TTSException(AIRAException):
    """
    Exception raised for TTS-related errors.

    Used for errors during text-to-speech synthesis, model loading,
    or audio generation.
    """

    def __init__(self, message: str):
        """
        Initialize TTS exception.

        Args:
            message: Human-readable error message
        """
        super().__init__(message, status_code=500)

"""
Tests for Custom Exception Classes.

This module tests the custom exception hierarchy used across
the AIRA application for error handling.
"""

import pytest
from app.core.exceptions import AIRAException, ASRException, TTSException


def test_aira_exception_default():
    """Test AIRAException with default status code."""
    exc = AIRAException("Test error message")

    assert exc.message == "Test error message"
    assert exc.status_code == 500
    assert str(exc) == "Test error message"


def test_aira_exception_custom_status():
    """Test AIRAException with custom status code."""
    exc = AIRAException("Not found error", status_code=404)

    assert exc.message == "Not found error"
    assert exc.status_code == 404


def test_asr_exception():
    """Test ASRException inherits from AIRAException."""
    exc = ASRException("ASR model failed to load")

    assert exc.message == "ASR model failed to load"
    assert exc.status_code == 500
    assert isinstance(exc, AIRAException)
    assert isinstance(exc, Exception)


def test_tts_exception():
    """Test TTSException inherits from AIRAException."""
    exc = TTSException("TTS synthesis failed")

    assert exc.message == "TTS synthesis failed"
    assert exc.status_code == 500
    assert isinstance(exc, AIRAException)
    assert isinstance(exc, Exception)


def test_exception_inheritance():
    """Test that all custom exceptions inherit properly."""
    aira_exc = AIRAException("Base error")
    asr_exc = ASRException("ASR error")
    tts_exc = TTSException("TTS error")

    assert isinstance(asr_exc, AIRAException)
    assert isinstance(tts_exc, AIRAException)
    assert not isinstance(aira_exc, ASRException)
    assert not isinstance(aira_exc, TTSException)


def test_exception_raising():
    """Test that exceptions can be raised and caught properly."""
    with pytest.raises(AIRAException) as exc_info:
        raise AIRAException("Test exception")

    assert exc_info.value.message == "Test exception"

    with pytest.raises(ASRException) as exc_info:
        raise ASRException("ASR error")

    assert exc_info.value.message == "ASR error"

    with pytest.raises(TTSException) as exc_info:
        raise TTSException("TTS error")

    assert exc_info.value.message == "TTS error"


def test_exception_attributes():
    """Test that exception attributes are accessible."""
    exc = AIRAException("Custom error", status_code=400)

    assert hasattr(exc, "message")
    assert hasattr(exc, "status_code")
    assert exc.message == "Custom error"
    assert exc.status_code == 400

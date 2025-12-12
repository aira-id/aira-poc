"""
TTS (Text-to-Speech) module.

This module provides text-to-speech functionality using Coqui TTS library.
It includes:
- G2P (Grapheme-to-Phoneme) conversion for Indonesian
- Number-to-words conversion
- Streaming TTS with real-time audio generation
"""

from aira.tts.base import TTSBase
from aira.tts.service import TTSService, tts_service

__all__ = [
    "TTSBase",
    "TTSService",
    "tts_service",
]

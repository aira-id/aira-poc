"""
ASR (Automatic Speech Recognition) module.

This module provides speech-to-text functionality using sherpa-onnx library.
It supports both online (streaming) and offline ASR with multiple model options.
"""

from aira.asr.base import ASRBase
from aira.asr.service import ASRService, asr_service

__all__ = [
    "ASRBase",
    "ASRService",
    "asr_service",
]

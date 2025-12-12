"""
Sherpa-ONNX ASR implementation.

This module provides speech recognition using sherpa-onnx library with support for:
- Multiple ASR models (zipformer, sensevoice, paraformer, fireredasr)
- Online (streaming) and offline recognition
- Voice Activity Detection (VAD)
- Multiple languages support
"""

from aira.asr.sherpa_onnx.asr import start_asr_stream
from aira.asr.sherpa_onnx.stream import ASRStream
from aira.asr.sherpa_onnx.result import ASRResult

__all__ = ["start_asr_stream", "ASRStream", "ASRResult"]

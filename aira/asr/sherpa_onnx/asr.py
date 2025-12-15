"""
ASR (Automatic Speech Recognition) implementation using sherpa-onnx.

This module provides factory functions for creating different ASR recognizers
and manages engine caching for efficient model loading.

Supported models:
- zipformer: Online streaming recognizer for Indonesian
- sensevoice: Offline multilingual recognizer (Chinese, English, Japanese, Korean, Cantonese)
- paraformer-trilingual: Offline recognizer for Chinese, Cantonese, and English
- paraformer-en: Offline recognizer for English with ITN support
- fireredasr: Offline recognizer for Chinese and English
"""

import logging
import os
import time
import sherpa_onnx

from aira.asr.sherpa_onnx.stream import ASRStream
from app.config import settings

logger = logging.getLogger(__name__)

# Cache for loaded ASR engines
_asr_engines = {}


def create_zipformer(samplerate: int, args) -> sherpa_onnx.OnlineRecognizer:
    """
    Create a Zipformer-based online ASR recognizer for Indonesian.

    Args:
        samplerate: Audio sample rate (e.g., 16000)
        args: Configuration dictionary containing:
            - models_root: Path to models directory
            - asr_provider: Provider for inference (e.g., 'cpu', 'cuda')
            - threads: Number of threads for inference

    Returns:
        sherpa_onnx.OnlineRecognizer: Configured online recognizer with endpoint detection

    Raises:
        ValueError: If model directory is not found
    """
    d = os.path.join(args.get("models_root"), 'sherpa-onnx-streaming-zipformer2-id')

    if not os.path.exists(d):
        raise ValueError(f"ASR: model not found {d}")

    encoder = os.path.join(d, settings.asr_encoder_filename)
    decoder = os.path.join(d, settings.asr_decoder_filename)
    joiner = os.path.join(d, settings.asr_joiner_filename)
    tokens = os.path.join(d, settings.asr_tokens_filename)
    recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=tokens,
        encoder=encoder,
        decoder=decoder,
        joiner=joiner,
        provider=args.get("asr_provider"),
        num_threads=args.get("threads"),
        sample_rate=samplerate,
        feature_dim=80,
        enable_endpoint_detection=True,
        rule1_min_trailing_silence=2.4,
        rule2_min_trailing_silence=1.2,
        rule3_min_utterance_length=20,  # it essentially disables this rule
    )

    return recognizer


def load_asr_engine(samplerate: int, args):
    """
    Load and cache an ASR engine based on the specified model type.

    Automatically loads VAD (Voice Activity Detection) for offline models.
    Engines are cached in memory to avoid reloading on subsequent calls.

    Args:
        samplerate: Audio sample rate (e.g., 16000)
        args: Configuration dictionary containing:
            - asr_model: Model type ('zipformer')
            - models_root: Path to models directory
            - asr_provider: Provider for inference
            - threads: Number of threads
            - asr_lang: Target language (for sensevoice)

    Returns:
        sherpa_onnx.OfflineRecognizer: Configured ASR engine

    Raises:
        ValueError: If asr_model is unknown or model files not found
    """
    asr_model = args.get("asr_model")
    cache_engine = _asr_engines.get(asr_model)

    if cache_engine:
        return cache_engine
    st = time.time()

    if asr_model == 'zipformer':
        cache_engine = create_zipformer(samplerate, args)
    else:
        raise ValueError(f"ASR: unknown model {asr_model}")

    _asr_engines[asr_model] = cache_engine
    logger.info(f"ASR: engine loaded in {time.time() - st:.2f}s")

    return cache_engine


def load_vad_engine(samplerate: int, args, min_silence_duration: float = 0.25, buffer_size_in_seconds: int = 100) -> sherpa_onnx.VoiceActivityDetector:
    """
    Load Voice Activity Detection (VAD) engine using Silero VAD model.

    VAD is used with offline ASR models to detect speech segments in continuous audio.

    Args:
        samplerate: Audio sample rate (e.g., 16000)
        args: Configuration dictionary containing:
            - models_root: Path to models directory
            - asr_provider: Provider for inference (e.g., 'cpu', 'cuda')
            - threads: Number of threads for inference
        min_silence_duration: Minimum silence duration in seconds to trigger endpoint (default: 0.25)
        buffer_size_in_seconds: Maximum audio buffer size in seconds (default: 100)

    Returns:
        sherpa_onnx.VoiceActivityDetector: Configured VAD instance

    Raises:
        ValueError: If VAD model directory is not found
    """
    config = sherpa_onnx.VadModelConfig()
    d = os.path.join(args.get("models_root"), 'silero_vad')

    if not os.path.exists(d):
        raise ValueError(f"VAD: model not found {d}")

    config.silero_vad.model = os.path.join(d, 'silero_vad.onnx')
    config.silero_vad.min_silence_duration = min_silence_duration
    config.sample_rate = samplerate
    config.provider = args.get("asr_provider")
    config.num_threads = args.get("threads")
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=buffer_size_in_seconds)

    return vad


async def start_asr_stream(samplerate: int, args) -> ASRStream:
    """
    Start an ASR stream for real-time speech recognition.

    Initializes an ASR engine and creates a streaming interface for processing audio.

    Args:
        samplerate: Audio sample rate (e.g., 16000)
        args: Configuration dictionary with ASR model settings

    Returns:
        ASRStream: Initialized and started ASR stream ready for audio input

    Example:
        >>> config = {"asr_model": "zipformer", "models_root": "/path/to/models", ...}
        >>> stream = await start_asr_stream(16000, config)
        >>> await stream.write(audio_bytes)
        >>> result = await stream.read()
    """
    stream = ASRStream(load_asr_engine(samplerate, args), samplerate)
    await stream.start()
    return stream

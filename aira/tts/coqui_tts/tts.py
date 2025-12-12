"""
TTS (Text-to-Speech) implementation using coqui-tts.
"""

import os
import time
from TTS.utils.synthesizer import Synthesizer
import logging

from aira.tts.coqui_tts.g2p_id import G2P
from aira.tts.coqui_tts.stream import TTSStream

logger = logging.getLogger(__name__)

# Cache for loaded TTS engines
_tts_engines = {}


def get_tts_engine(args) -> Synthesizer:
    """
    Get or create a cached TTS engine.

    Args:
        args: Configuration dictionary with models_root and tts_model

    Returns:
        Coqui TTS Synthesizer instance
    """
    models_root = args.get("models_root")
    model_path = os.path.join(models_root, "vits-tts-id")
    tts_model = os.path.join(model_path, "checkpoint_1260000-inference.pth")
    tts_config = os.path.join(model_path, "config.json")
    cache_engine = _tts_engines.get(args.get("tts_model"))

    if not os.path.exists(model_path):
        raise ValueError(f"TTS: model not found {model_path}")

    if cache_engine:
        return cache_engine

    st = time.time()
    cache_engine = Synthesizer(
        tts_checkpoint=tts_model,
        tts_config_path=tts_config,
        use_cuda=False
    )
    elapsed = time.time() - st
    logger.info(f'TTS: loaded {args.get("tts_model")} in {elapsed:.2f}s')
    _tts_engines[args.get("tts_model")] = cache_engine

    return cache_engine


async def start_tts_stream(sample_rate: int, speed: float, args):
    """
    Start a TTS stream with the specified configuration.

    Args:
        sample_rate: Target output sample rate
        speed: Speech speed multiplier
        args: Configuration object with TTS settings

    Returns:
        Initialized TTSStream instance
    """
    engine = get_tts_engine(args)
    g2p = G2P()
    return TTSStream(engine, args.get("tts_speaker"), g2p, speed, sample_rate)

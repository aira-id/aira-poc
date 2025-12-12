"""
TTS Stream implementation for real-time audio generation.
"""

import asyncio
import io
import logging
import time
import re
import numpy as np
import soundfile
from scipy.signal import resample

from aira.tts.coqui_tts.num2words import num2words
from aira.tts.coqui_tts.result import TTSResult
from aira.tts.coqui_tts.g2p_id import G2P

logger = logging.getLogger(__name__)

# Regular expression to split text by punctuation marks
splitter = re.compile(r'[.!?;:\n]')


class TTSStream:
    """
    Manages streaming TTS audio generation with real-time processing.
    """
    def __init__(self, engine, speaker: str, g2p: G2P, speed: float = 1.0, sample_rate: int = 16000):
        """
        Initialize TTS stream.

        Args:
            engine: TTS.utils.synthesizer.Synthesizer instance
            speaker: Speaker name for voice selection
            speed: Speech speed multiplier (1.0 = normal)
            sample_rate: Target output sample rate
        """
        self.engine = engine
        self.speaker = speaker
        self.g2p = g2p
        self.speed = speed
        self.outbuf: asyncio.Queue[TTSResult | None] = asyncio.Queue()
        self.is_closed = False
        self.target_sample_rate = sample_rate

    async def write(self, text: str, split: bool, pause: float = 0.2):
        """
        Generate audio from text and stream to output buffer.

        Args:
            text: Text to synthesize
            split: Whether to split text by punctuation
            pause: Pause duration (seconds) between sentences when split=True
        """
        start = time.time()

        text = self.g2p(text)
        text = num2words.convert(text)

        try:
            # Split text by punctuation if requested
            if split:
                texts = re.split(splitter, text)
            else:
                texts = [text]

            audio_duration = 0.0

            for idx, text in enumerate(texts):
                text = text.strip()
                if not text:
                    continue

                sub_start = time.time()

                # Generate audio in a thread to avoid blocking
                audio = await asyncio.to_thread(self.engine.tts, text=text, samplerate=self.target_sample_rate, speaker_name=self.speaker)

                if not audio:
                    logger.error(f"TTS: failed to generate audio for " f"'{text}' (audio={audio})")
                    continue

                audio_buffer = io.BytesIO()

                # Resample to target sample rate
                if self.target_sample_rate != self.engine.output_sample_rate:
                    num_samples = round(len(audio) * float(self.target_sample_rate) / self.engine.output_sample_rate)
                    resampled_audio = resample(audio, num_samples)
                    soundfile.write(audio_buffer, resampled_audio, self.target_sample_rate, format="WAV", subtype="PCM_16")
                else:
                    soundfile.write(audio_buffer, audio, self.target_sample_rate, format="WAV", subtype="PCM_16")

                audio_bytes = audio_buffer.getvalue()
                self.outbuf.put_nowait(TTSResult(audio_bytes, False))
                elapsed_seconds = time.time() - sub_start
                logger.info(f"TTS: generated audio for '{text}', " f"elapsed: {elapsed_seconds:.2f}s")
        except Exception as e:
            logger.error(f"TTS stream error: {e}", exc_info=True)
        finally:
            elapsed_seconds = time.time() - start
            audio_duration = len(audio) / self.engine.output_sample_rate
            logger.info(f"TTS: generated audio in {elapsed_seconds:.2f}s")

        # Send final result with metadata
        r = TTSResult(None, True)
        r.elapsed = elapsed_seconds
        r.audio_duration = audio_duration
        r.progress = 1.0
        r.finished = True
        await self.outbuf.put(r)

    async def close(self):
        """Close the TTS stream and release resources."""
        self.is_closed = True
        self.outbuf.put_nowait(None)
        logger.info("TTS: stream closed")

    async def read(self) -> TTSResult:
        """
        Read next result from the output buffer.

        Returns:
            TTSResult or None if stream is closed
        """
        return await self.outbuf.get()

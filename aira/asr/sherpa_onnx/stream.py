"""
ASR stream for real-time speech recognition.

Provides async interface for streaming audio to sherpa-onnx recognizers
and receiving recognition results in real-time.
"""

import asyncio
import logging
import numpy as np
import sherpa_onnx

from aira.asr.sherpa_onnx.result import ASRResult

logger = logging.getLogger(__name__)


class ASRStream:
    """
    ASR stream for real-time speech recognition using sherpa-onnx recognizers.

    Manages asynchronous audio processing with input/output queues for streaming recognition.
    Supports automatic endpoint detection for segmenting continuous speech.

    The stream processes audio chunks asynchronously, providing both partial results
    (for real-time feedback) and final results (when endpoint is detected).

    Attributes:
        recognizer: sherpa-onnx OnlineRecognizer instance
        sample_rate: Audio sample rate (e.g., 16000)
        inbuf: Async queue for incoming audio samples
        outbuf: Async queue for recognition results
        is_closed: Flag indicating if the stream has been closed

    Example:
        >>> recognizer = load_asr_engine(16000, config)
        >>> stream = ASRStream(recognizer, 16000)
        >>> await stream.start()
        >>> await stream.write(audio_bytes)
        >>> result = await stream.read()  # Get recognition result
        >>> await stream.close()
    """

    def __init__(self, recognizer: sherpa_onnx.OnlineRecognizer, sample_rate: int):
        """
        Initialize ASR stream.

        Args:
            recognizer: sherpa-onnx OnlineRecognizer instance
            sample_rate: Audio sample rate (e.g., 16000)
        """
        self.recognizer = recognizer
        self.sample_rate = sample_rate
        self.inbuf = asyncio.Queue()
        self.outbuf = asyncio.Queue()
        self.is_closed = False

    async def start(self):
        """
        Start the recognition task in the background.

        Creates an async task that continuously processes audio from the input buffer
        and generates recognition results.
        """
        asyncio.create_task(self._run_online())
        logger.info("ASR stream started")

    async def write(self, audio_data: bytes):
        """
        Write audio data to the stream for recognition.

        Converts raw PCM audio bytes to normalized float32 samples and queues them
        for processing by the recognition task.

        Args:
            audio_data: Raw audio bytes in PCM 16-bit format

        Note:
            Audio is automatically normalized from int16 range to float32 range [-1, 1]
            before being fed to the recognizer.
        """
        if self.is_closed:
            return

        # Convert bytes to numpy array (assuming int16 PCM)
        samples = np.frombuffer(audio_data, dtype=np.int16)
        # Normalize to float32 in range [-1, 1]
        samples = samples.astype(np.float32) / 32768.0
        self.inbuf.put_nowait(samples)

    async def read(self) -> ASRResult:
        """
        Read the next recognition result from the stream.

        Waits asynchronously until a result is available in the output buffer.

        Returns:
            ASRResult: Recognition result containing transcribed text and metadata,
                      or None if the stream has been closed

        Note:
            Results can be partial (finished=False) or final (finished=True).
            Partial results are useful for real-time display, while final results
            represent complete utterances after endpoint detection.
        """
        return await self.outbuf.get()

    async def close(self):
        """
        Close the ASR stream and release resources.

        Signals the recognition task to stop and sends a None marker to the output buffer
        to indicate stream closure.
        """
        self.is_closed = True
        self.outbuf.put_nowait(None)
        logger.info("ASR stream closed")

    async def _run_online(self):
        """
        Main recognition loop for online/streaming ASR.

        Continuously processes audio samples from the input buffer, performs recognition,
        and emits both partial and final results to the output buffer.

        The loop:
        1. Reads audio samples from input buffer
        2. Feeds samples to the recognizer
        3. Decodes ready frames
        4. Emits partial results for real-time feedback
        5. Detects endpoints (silence) and emits final results
        6. Resets recognizer for next utterance

        This method runs as a background task and should not be called directly.
        Use start() to initiate the recognition loop.
        """
        stream = self.recognizer.create_stream()
        last_result = ""
        segment_id = 0

        logger.info("ASR: Starting real-time recognizer")

        try:
            while not self.is_closed:
                # Get audio samples from input buffer
                try:
                    samples = await self.inbuf.get()
                except asyncio.TimeoutError:
                    continue

                # Feed audio to the recognizer
                stream.accept_waveform(self.sample_rate, samples)

                # Decode all ready frames
                while self.recognizer.is_ready(stream):
                    self.recognizer.decode_stream(stream)

                # Check if we've reached an endpoint (silence detected)
                is_endpoint = self.recognizer.is_endpoint(stream)

                # Get current recognition result
                result = self.recognizer.get_result(stream)

                # Emit partial results (for streaming display)
                if result and (last_result != result):
                    last_result = result
                    logger.debug(f"ASR partial result [{segment_id}]: {result}")
                    self.outbuf.put_nowait(
                        ASRResult(result, False, segment_id))

                # Emit final result when endpoint is detected
                if is_endpoint:
                    if result:
                        logger.info(f'{segment_id}: {result}')
                        self.outbuf.put_nowait(
                            ASRResult(result, True, segment_id))
                        segment_id += 1

                    # Reset stream for next utterance
                    self.recognizer.reset(stream)
                    last_result = ""
        except Exception as e:
            logger.error(f"ASR stream error: {e}", exc_info=True)
        finally:
            logger.info("ASR: Recognition loop ended")

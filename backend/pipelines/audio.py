"""
Audio streaming pipeline for ATOM
Captures microphone input and streams to Gemini Live API
"""

import asyncio
import logging
from typing import Any, Optional

try:
    import pyaudio  # type: ignore[import-untyped]
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

logger = logging.getLogger(__name__)


class AudioPipeline:
    """
    Captures microphone audio and streams it to ATOM session.
    Audio format: 16-bit PCM, 16kHz sample rate, mono channel.
    Degrades gracefully when PyAudio is not available.
    """

    CHUNK_SIZE = 1024
    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self) -> None:
        """Initialize audio pipeline."""
        self.is_streaming = False
        self._audio: Any = None
        self._audio_stream: Any = None

        if HAS_PYAUDIO:
            import pyaudio as _pa  # type: ignore[import-untyped]

            self._audio = _pa.PyAudio()
            self._format = _pa.paInt16
        else:
            self._format = 8  # paInt16 constant fallback
            logger.warning("⚠️  PyAudio not installed – audio pipeline disabled")

    async def start_streaming(self, session: Any) -> None:
        """
        Continuously capture and stream audio chunks.

        Args:
            session: ATOMSession instance to send audio to
        """
        if not HAS_PYAUDIO or self._audio is None:
            logger.warning("Audio pipeline skipped (PyAudio unavailable)")
            return

        self.is_streaming = True

        try:
            # Open microphone stream
            self._audio_stream = self._audio.open(
                format=self._format,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE,
            )

            logger.info(
                f"🎤 Audio pipeline started - {self.SAMPLE_RATE}Hz, "
                f"{self.CHANNELS} channel"
            )

            while self.is_streaming and session.is_active:
                try:
                    # Capture audio chunk
                    chunk = self._audio_stream.read(
                        self.CHUNK_SIZE, exception_on_overflow=False
                    )

                    # Send to ATOM session
                    await session.send_audio(chunk)

                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.01)

                except Exception as e:
                    logger.error(f"Error reading audio chunk: {e}")
                    await asyncio.sleep(0.1)

            logger.info("✓ Audio pipeline stopped gracefully")

        except Exception as e:
            logger.error(f"✗ Audio pipeline error: {e}")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Gracefully shutdown audio pipeline.
        """
        self.is_streaming = False

        if self._audio_stream is not None:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
            self._audio_stream = None

        if self._audio is not None:
            try:
                self._audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            self._audio = None

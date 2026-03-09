"""
Audio streaming pipeline for ATOM
Captures microphone input (or simulates audio in cloud deployment)
and streams to Gemini Live API
"""

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AudioPipeline:
    """
    Captures microphone audio and streams it to ATOM session.
    Audio format: 16-bit PCM, 16kHz sample rate, mono channel.
    
    In cloud deployment (Cloud Run), simulates audio chunks since
    no microphone hardware is available.
    """

    CHUNK_SIZE = 1024
    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self) -> None:
        """Initialize audio pipeline."""
        self.is_streaming = False
        logger.info("🎤 Audio pipeline initialized (mock mode for cloud deployment)")

    async def start_streaming(self, session: Any) -> None:
        """
        Simulate audio streaming with mock chunks.
        In production, would capture from microphone.

        Args:
            session: ATOMSession instance to send audio to
        """
        self.is_streaming = True

        try:
            logger.info(
                f"🎤 Audio pipeline started (simulating) - {self.SAMPLE_RATE}Hz, "
                f"{self.CHANNELS} channel"
            )

            while self.is_streaming and session.is_active:
                try:
                    # Simulate audio chunk (would come from microphone in production)
                    # Create a few bytes of dummy PCM data
                    mock_chunk = b'\x00' * self.CHUNK_SIZE
                    
                    # Send to ATOM session
                    await session.send_audio(mock_chunk)

                    # Small delay to simulate microphone capture
                    await asyncio.sleep(0.05)  # 50ms chunks

                except Exception as e:
                    logger.error(f"Error sending audio chunk: {e}")
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
        logger.info("Audio pipeline stopped")

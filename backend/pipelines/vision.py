"""
Vision pipeline for ATOM
Captures screenshots and streams to Gemini Live API
"""

import asyncio
import base64
import logging
import sys
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image, ImageGrab  # type: ignore[import-untyped]
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

logger = logging.getLogger(__name__)


class VisionPipeline:
    """
    Captures full screen screenshots at regular intervals and streams to ATOM.
    Images are compressed to max 1280x720 and encoded as JPEG base64.
    """

    CAPTURE_INTERVAL = 5  # seconds
    MAX_WIDTH = 1280
    MAX_HEIGHT = 720
    JPEG_QUALITY = 75

    def __init__(self):
        """Initialize vision pipeline."""
        self.is_streaming = False
        self.frame_count = 0

    async def stream(self, session) -> None:
        """
        Continuously capture and stream screenshot frames.
        
        Args:
            session: ATOMSession instance to send images to
        """
        if not HAS_PILLOW:
            logger.warning("Vision pipeline skipped (Pillow/ImageGrab unavailable)")
            return

        self.is_streaming = True
        
        try:
            logger.info(f"📹 Vision pipeline started - capturing every {self.CAPTURE_INTERVAL}s")
            
            while self.is_streaming and session.is_active:
                try:
                    # Capture full screen
                    screenshot = ImageGrab.grab()
                    
                    # Compress image
                    screenshot.thumbnail((self.MAX_WIDTH, self.MAX_HEIGHT), Image.Resampling.LANCZOS)
                    
                    # Encode to JPEG bytes
                    jpeg_buffer = BytesIO()
                    screenshot.save(jpeg_buffer, format="JPEG", quality=self.JPEG_QUALITY)
                    jpeg_bytes = jpeg_buffer.getvalue()
                    
                    # Convert to base64
                    image_base64 = base64.b64encode(jpeg_bytes).decode("utf-8")
                    
                    # Send to ATOM
                    await session.send_image(image_base64)
                    
                    self.frame_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    logger.debug(f"📹 Frame {self.frame_count} sent at {timestamp} ({len(image_base64)} bytes)")
                    
                    # Wait for next capture
                    await asyncio.sleep(self.CAPTURE_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"Error capturing frame: {e}")
                    await asyncio.sleep(1)
            
            logger.info(f"✓ Vision pipeline stopped ({self.frame_count} frames sent)")
            
        except Exception as e:
            logger.error(f"✗ Vision pipeline error: {e}")
        finally:
            self.is_streaming = False

    async def stop(self) -> None:
        """Gracefully shutdown vision pipeline."""
        self.is_streaming = False

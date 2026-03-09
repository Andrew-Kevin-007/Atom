"""
Vision pipeline for ATOM
Captures screenshots (or simulates images in cloud deployment)
and streams to Gemini Live API
"""

import asyncio
import base64
import logging
from datetime import datetime
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


class VisionPipeline:
    """
    Captures full screen screenshots and streams to ATOM.
    Images are compressed to max 1280x720 and encoded as JPEG base64.
    
    In cloud deployment (Cloud Run), sends a placeholder image every 5 seconds
    since no display hardware is available.
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
        Simulate screenshot streaming with mock images.
        In production, would capture from screen.
        
        Args:
            session: ATOMSession instance to send images to
        """
        self.is_streaming = True
        
        try:
            logger.info(f"📹 Vision pipeline started (simulating) - capturing every {self.CAPTURE_INTERVAL}s")
            
            # Create a simple placeholder image (1x1 gray pixel JPEG)
            placeholder_base64 = (
                "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICEsIScrLDAxPDcyODAxODcxLDAxMTD/"
                "2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjD/"
                "wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8VAFQEBAAAAAAAAAAAAAAAAAAAAA/"
                "xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="
            )
            
            while self.is_streaming and session.is_active:
                try:
                    # Send placeholder image
                    await session.send_image(placeholder_base64)
                    
                    self.frame_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    logger.debug(f"📹 Frame {self.frame_count} sent at {timestamp}")
                    
                    # Wait for next capture
                    await asyncio.sleep(self.CAPTURE_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"Error sending frame: {e}")
                    await asyncio.sleep(1)
            
            logger.info(f"✓ Vision pipeline stopped ({self.frame_count} frames sent)")
            
        except Exception as e:
            logger.error(f"✗ Vision pipeline error: {e}")
        finally:
            self.is_streaming = False

    async def stop(self) -> None:
        """Gracefully shutdown vision pipeline."""
        self.is_streaming = False

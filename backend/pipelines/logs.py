"""
Log streaming pipeline for ATOM
Simulates live incident logs and streams to Gemini Live API
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class LogPipeline:
    """
    Streams production log messages to ATOM.
    Includes simulation mode for demo incidents.
    """

    # Demo incident log sequence
    DEMO_LOGS = [
        "INFO: Deployment auth-v2 initiated by CI pipeline",
        "INFO: auth-v2 deployment completed successfully",
        "WARNING: Error rate on /api/auth endpoint rising — 2.3% errors",
        "ERROR: Error rate on /api/auth endpoint critical — 18.7% errors",
        "ERROR: Database connection pool exhaustion detected — 94% utilized",
        "CRITICAL: Payments service latency exceeding SLA threshold — p99 at 4200ms",
        "CRITICAL: SLA breach imminent — 180 seconds to breach on payments service",
        "CRITICAL: SLA breach imminent — 90 seconds to breach on payments service",
        "INFO: Rollback of auth-v2 initiated",
        "INFO: Rollback complete — error rates normalizing",
        "INFO: All systems nominal — incident resolved",
    ]

    DEMO_LOG_INTERVAL = 15  # seconds between log messages

    def __init__(self, on_log: Optional[Callable[[str, str, str], Any]] = None):
        """
        Initialize log pipeline.
        
        Args:
            on_log: Callback function when log arrives (log_message, timestamp, severity)
        """
        self.is_streaming = False
        self.on_log = on_log

    async def simulate_incident(self, session, firestore_manager, incident_id: str) -> None:
        """
        Simulate a realistic incident with logs at regular intervals.
        
        Args:
            session: ATOMSession instance
            firestore_manager: FirestoreManager for persistence
            incident_id: Current incident ID
        """
        self.is_streaming = True
        
        try:
            logger.info(f"🎬 Starting incident simulation ({len(self.DEMO_LOGS)} logs)")
            
            for i, log_message in enumerate(self.DEMO_LOGS):
                if not self.is_streaming:
                    break
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Extract severity
                if "CRITICAL" in log_message:
                    severity = "CRITICAL"
                elif "ERROR" in log_message:
                    severity = "ERROR"
                elif "WARNING" in log_message:
                    severity = "WARNING"
                else:
                    severity = "INFO"
                
                # Send to ATOM
                await session.send_log(log_message)
                
                # Log locally
                logger.info(f"📝 [{timestamp}] {log_message}")
                
                # Notify callback
                if self.on_log:
                    self.on_log(log_message, timestamp, severity)
                
                # Save to Firestore
                if firestore_manager:
                    await firestore_manager.add_timeline_event(
                        incident_id,
                        "LOG",
                        log_message,
                        "LOGS"
                    )
                
                # Wait before next log (except last one)
                if i < len(self.DEMO_LOGS) - 1:
                    await asyncio.sleep(self.DEMO_LOG_INTERVAL)
            
            logger.info("✓ Incident simulation completed")
            
        except Exception as e:
            logger.error(f"✗ Log pipeline error: {e}")
        finally:
            self.is_streaming = False

    async def stop(self) -> None:
        """Gracefully shutdown log pipeline."""
        self.is_streaming = False

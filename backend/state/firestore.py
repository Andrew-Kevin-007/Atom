"""
Google Firestore state manager for ATOM
Persists incident timeline, hypotheses, and postmortem
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from google.cloud import firestore as _firestore  # type: ignore[import-untyped]
    HAS_FIRESTORE = True
except ImportError:
    HAS_FIRESTORE = False
    _firestore = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class FirestoreManager:
    """
    Manages incident state in Google Firestore.
    Handles timeline events, hypotheses, SLA tracking, and postmortems.
    """

    def __init__(self, project_id: str, collection: str = "incidents"):
        """
        Initialize Firestore manager.
        
        Args:
            project_id: GCP project ID
            collection: Firestore collection name
        """
        self.db: Any = None
        self.collection = collection
        if not HAS_FIRESTORE or _firestore is None:
            logger.warning("⚠️  google-cloud-firestore not installed – state disabled")
            return
        try:
            self.db = _firestore.Client(project=project_id)
            logger.info(f"✓ Firestore connected to project '{project_id}'")
        except Exception as e:
            logger.error(f"✗ Firestore initialization failed: {e}")
            self.db = None

    async def create_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Create a new incident document.
        
        Args:
            incident_id: Unique incident identifier
            
        Returns:
            Incident document data, or None on failure
        """
        if not self.db:
            return None

        try:
            incident_data = {
                "id": incident_id,
                "status": "active",
                "created_at": datetime.now(),
                "sla_deadline": None,
                "timeline": [],
                "hypotheses": [],
                "postmortem": {},
            }
            
            await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).set(incident_data)
            )
            logger.info(f"✓ Incident '{incident_id}' created in Firestore")
            
            return incident_data
            
        except Exception as e:
            logger.error(f"✗ Failed to create incident: {e}")
            return None

    async def add_timeline_event(
        self,
        incident_id: str,
        event_type: str,
        message: str,
        source: str,
    ) -> bool:
        """
        Append event to incident timeline.
        
        Args:
            incident_id: Incident ID
            event_type: Type of event (LOG, ATOM, ENGINEER)
            message: Event message
            source: Source of event (LOGS, ATOM, GOOGLE_CLOUD, etc)
            
        Returns:
            True if successful
        """
        if not self.db:
            return False

        try:
            event = {
                "timestamp": datetime.now(),
                "type": event_type,
                "message": message,
                "source": source,
            }
            
            await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).update({
                    "timeline": _firestore.ArrayUnion([event])  # type: ignore[union-attr]
                })
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding timeline event: {e}")
            return False

    async def update_sla_deadline(self, incident_id: str, seconds_remaining: int) -> bool:
        """
        Update SLA countdown timer.
        
        Args:
            incident_id: Incident ID
            seconds_remaining: Seconds until SLA breach
            
        Returns:
            True if successful
        """
        if not self.db:
            return False

        try:
            await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).update({
                    "sla_remaining_seconds": seconds_remaining
                })
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating SLA deadline: {e}")
            return False

    async def add_hypothesis(
        self,
        incident_id: str,
        hypothesis: str,
        confidence: float = 0.5,
    ) -> bool:
        """
        Add root cause hypothesis.
        
        Args:
            incident_id: Incident ID
            hypothesis: Root cause hypothesis text
            confidence: Confidence level (0.0 - 1.0)
            
        Returns:
            True if successful
        """
        if not self.db:
            return False

        try:
            hyp_entry = {
                "timestamp": datetime.now(),
                "hypothesis": hypothesis,
                "confidence": confidence,
            }
            
            await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).update({
                    "hypotheses": _firestore.ArrayUnion([hyp_entry])  # type: ignore[union-attr]
                })
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding hypothesis: {e}")
            return False

    async def update_postmortem(self, incident_id: str, content: Dict[str, Any]) -> bool:
        """
        Update postmortem document.
        
        Args:
            incident_id: Incident ID
            content: Postmortem content dictionary
            
        Returns:
            True if successful
        """
        if not self.db:
            return False

        try:
            await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).update({
                    "postmortem": content
                })
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating postmortem: {e}")
            return False

    async def resolve_incident(self, incident_id: str, summary: str) -> bool:
        """
        Mark incident as resolved.
        
        Args:
            incident_id: Incident ID
            summary: Resolution summary
            
        Returns:
            True if successful
        """
        if not self.db:
            return False

        try:
            await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).update({
                    "status": "resolved",
                    "resolved_at": datetime.now(),
                    "resolution_summary": summary,
                })
            )
            
            logger.info(f"✓ Incident '{incident_id}' marked as resolved")
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving incident: {e}")
            return False

    async def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve current incident state.
        
        Args:
            incident_id: Incident ID
            
        Returns:
            Incident document data
        """
        if not self.db:
            return None

        try:
            doc = await asyncio.to_thread(
                lambda: self.db.collection(self.collection).document(incident_id).get()
            )
            
            if doc.exists:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving incident: {e}")
            return None

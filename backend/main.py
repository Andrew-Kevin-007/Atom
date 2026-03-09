"""
ATOM Backend - Main FastAPI Application
Real-time incident intelligence agent with Gemini Live API integration
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))
import asyncio
import logging
import re
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import dotenv

from gemini.session import ATOMSession
from pipelines.audio import AudioPipeline
from pipelines.vision import VisionPipeline
from pipelines.logs import LogPipeline
from state.firestore import FirestoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables — resolve .env relative to this file so it works
# regardless of which directory uvicorn is launched from.
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if not os.path.isfile(_env_path):
    # Also try workspace root (one level up from backend/)
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
dotenv.load_dotenv(_env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")


class IncidentRequest(BaseModel):
    """Request model for starting incident"""
    incident_type: str = "simulated"
    name: str = "Production Incident"


class IncidentResponse(BaseModel):
    """Response model for incident operations"""
    incident_id: str
    status: str
    message: str


# Global state
active_incidents: Dict[str, Dict] = {}


class ConnectionManager:
    """Manages WebSocket connections with proper lifecycle and keepalive."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to accept
        """
        print(f"[WS] Attempting to accept WebSocket...")
        try:
            await websocket.accept()
            print(f"[WS] ✓ WebSocket accepted successfully")
            self.active_connections.append(websocket)
            print(f"[WS] ✓ Connection registered ({len(self.active_connections)} total)")
            logger.info(f"📡 New WebSocket client connected ({len(self.active_connections)} total)")
        except Exception as e:
            print(f"[WS] ✗ Failed to accept WebSocket: {e}")
            logger.error(f"Failed to accept WebSocket: {e}")
            raise
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister and close a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to disconnect
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WS] ✓ Connection disconnected ({len(self.active_connections)} remaining)")
            logger.info(f"📡 Client disconnected ({len(self.active_connections)} remaining)")
    
    async def broadcast(self, message: Dict) -> None:
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Dictionary to broadcast as JSON
        """
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS] Warning: Failed to send to client: {e}")
                logger.warning(f"Failed to broadcast to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)


# Initialize connection manager
manager = ConnectionManager()


async def broadcast_to_clients(message: Dict) -> None:
    """
    Broadcast message to all connected WebSocket clients.
    Uses the ConnectionManager to handle the actual broadcasting.
    
    Args:
        message: Dictionary to broadcast as JSON
    """
    await manager.broadcast(message)


async def on_atom_response(incident_id: str, text: str) -> None:
    """
    Callback when ATOM speaks. Broadcasts to frontend.
    
    Args:
        incident_id: Current incident ID
        text: ATOM's spoken response
    """
    await broadcast_to_clients({
        "type": "atom_response",
        "incident_id": incident_id,
        "text": text,
        "timestamp": "",  # Frontend will add timestamp
    })


async def on_log_received(
    incident_id: str,
    log_message: str,
    timestamp: str,
    severity: str
) -> None:
    """
    Callback when log message received.
    Broadcasts to WebSocket clients and handles SLA updates.
    
    Args:
        incident_id: Current incident ID
        log_message: Log text
        timestamp: Timestamp string
        severity: Log severity (INFO, WARNING, ERROR, CRITICAL)
    """
    print(f"[CALLBACK] on_log_received: {severity} - {log_message[:60]}...")
    
    # Broadcast log event to all WebSocket clients
    await broadcast_to_clients({
        "type": "log_event",
        "incident_id": incident_id,
        "message": log_message,
        "timestamp": timestamp,
        "severity": severity,
    })
    print(f"[CALLBACK] Broadcasted to WebSocket clients")
    
    # Handle SLA deadline updates
    if "SLA breach imminent" in log_message and incident_id in active_incidents:
        match = re.search(r'(\d+)\s+seconds', log_message)
        if match:
            sla_seconds = int(match.group(1))
            incident_state = active_incidents[incident_id]
            firestore_manager = incident_state.get("firestore")
            if firestore_manager:
                await firestore_manager.update_sla_deadline(incident_id, sla_seconds)
                print(f"[CALLBACK] Updated SLA deadline: {sla_seconds} seconds")
                
                # Broadcast SLA update to frontend
                await broadcast_to_clients({
                    "type": "sla_update",
                    "incident_id": incident_id,
                    "sla_seconds_remaining": sla_seconds,
                    "timestamp": timestamp,
                })
                print(f"[CALLBACK] Broadcasted SLA update to frontend")


async def run_incident(incident_id: str) -> None:
    """
    Main incident orchestration coroutine.
    Starts ATOM session and all pipelines.
    
    Args:
        incident_id: Unique incident identifier
    """
    try:
        # Initialize services
        atom_session = ATOMSession(
            api_key=GEMINI_API_KEY,
            on_response=lambda text: asyncio.create_task(
                on_atom_response(incident_id, text)
            )
        )
        
        firestore_manager = FirestoreManager(
            project_id=GCP_PROJECT_ID,
            collection="incidents"
        )
        
        # Create incident in Firestore
        await firestore_manager.create_incident(incident_id)
        
        # Try to start ATOM session (non-fatal — runs in degraded mode if Gemini is unavailable)
        gemini_active = False
        try:
            await atom_session.start()
            gemini_active = True
        except Exception as e:
            logger.warning(f"⚠️  Gemini Live session failed: {e}")
            logger.warning("Continuing in degraded mode (logs/SLA will still run)")
            await broadcast_to_clients({
                "type": "atom_response",
                "incident_id": incident_id,
                "text": f"⚠️ Gemini Live unavailable — running in log-only mode.",
                "timestamp": "",
            })
        
        # Create pipelines with callbacks
        audio_pipeline = AudioPipeline()
        vision_pipeline = VisionPipeline()
        log_pipeline = LogPipeline(
            on_log=lambda msg, ts, sev: asyncio.create_task(
                on_log_received(incident_id, msg, ts, sev)
            )
        )
        
        # Store incident state
        active_incidents[incident_id] = {
            "session": atom_session,
            "firestore": firestore_manager,
            "audio": audio_pipeline,
            "vision": vision_pipeline,
            "logs": log_pipeline,
        }
        
        # Start audio/vision as background tasks (only if Gemini is active)
        logger.info(f"🚀 Starting all pipelines for incident {incident_id}")
        print(f"[INCIDENT] Starting pipelines (gemini={'ON' if gemini_active else 'OFF'})")
        
        audio_task = None
        vision_task = None
        if gemini_active:
            audio_task = asyncio.create_task(audio_pipeline.start_streaming(atom_session))
            vision_task = asyncio.create_task(vision_pipeline.stream(atom_session))
        
        # Run log simulation (completes after all demo logs)
        await log_pipeline.simulate_incident(atom_session, firestore_manager, incident_id)
        print(f"[INCIDENT] Log simulation complete, stopping pipelines")
        
        # Stop audio/vision pipelines
        await audio_pipeline.stop()
        await vision_pipeline.stop()
        if audio_task and vision_task:
            await asyncio.gather(audio_task, vision_task, return_exceptions=True)
        
        # Generate postmortem via Gemini
        print(f"[INCIDENT] Generating postmortem...")
        postmortem = await atom_session.generate_postmortem(LogPipeline.DEMO_LOGS)
        
        # Broadcast postmortem to frontend
        await broadcast_to_clients({
            "type": "postmortem_update",
            "incident_id": incident_id,
            "content": postmortem,
        })
        await firestore_manager.update_postmortem(incident_id, postmortem)
        
        # Announce resolution
        await broadcast_to_clients({
            "type": "atom_response",
            "incident_id": incident_id,
            "text": "Incident resolved. Postmortem generated.",
            "timestamp": "",
        })
        
        # Resolve incident
        await firestore_manager.resolve_incident(incident_id, "Incident resolved successfully")
        await broadcast_to_clients({
            "type": "incident_resolved",
            "incident_id": incident_id,
        })
        print(f"[INCIDENT] Incident {incident_id} fully resolved")
        
    except asyncio.CancelledError:
        logger.info(f"Incident {incident_id} cancelled")
    except Exception as e:
        logger.error(f"Error in incident orchestration: {e}")
        # Notify frontend of failure (WB-3)
        try:
            await broadcast_to_clients({
                "type": "incident_error",
                "incident_id": incident_id,
                "error": str(e),
            })
        except Exception:
            pass
    finally:
        # Cleanup
        if incident_id in active_incidents:
            try:
                await active_incidents[incident_id]["session"].stop()
            except Exception:
                pass
            del active_incidents[incident_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("🔥 ATOM Backend Starting")
    
    # Startup
    if not GEMINI_API_KEY:
        logger.warning("⚠️  GEMINI_API_KEY not set in .env")
    if not GCP_PROJECT_ID:
        logger.warning("⚠️  GCP_PROJECT_ID not set in .env")
    
    yield
    
    # Shutdown
    logger.info("🛑 ATOM Backend Stopping")
    
    # Stop all active incidents
    for incident_id in list(active_incidents.keys()):
        try:
            incident_state = active_incidents[incident_id]
            
            # Stop pipelines
            await incident_state["audio"].stop()
            await incident_state["vision"].stop()
            await incident_state["logs"].stop()
            
            # Stop session
            await incident_state["session"].stop()
            
            del active_incidents[incident_id]
            
        except Exception as e:
            logger.error(f"Error cleaning up incident {incident_id}: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="ATOM - Autonomous Threat & Operations Monitor",
    description="Real-time incident intelligence agent with Gemini Live API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/incident/start", response_model=IncidentResponse)
async def start_incident(request: IncidentRequest) -> IncidentResponse:
    """
    Start a new incident and launch ATOM monitoring.
    
    Returns:
        Incident ID and status
    """
    if active_incidents:
        raise HTTPException(status_code=409, detail="An incident is already active")
    
    incident_id = str(uuid.uuid4())[:8]
    
    logger.info(f"📍 Starting incident: {incident_id}")
    
    # Reserve the slot immediately so duplicate starts are blocked
    active_incidents[incident_id] = {"status": "starting"}
    
    # Start incident orchestration in background
    asyncio.create_task(run_incident(incident_id))
    
    # Broadcast incident started
    await broadcast_to_clients({
        "type": "incident_started",
        "incident_id": incident_id,
        "name": request.name,
        "timestamp": "",
    })
    
    return IncidentResponse(
        incident_id=incident_id,
        status="active",
        message=f"Incident {incident_id} started. ATOM is now monitoring.",
    )


@app.post("/incident/{incident_id}/stop", response_model=IncidentResponse)
async def stop_incident(incident_id: str) -> IncidentResponse:
    """
    Stop an active incident and cleanup resources.
    
    Args:
        incident_id: Incident ID to stop
        
    Returns:
        Status confirmation
    """
    if incident_id not in active_incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    logger.info(f"⏹️  Stopping incident: {incident_id}")
    
    try:
        incident_state = active_incidents[incident_id]
        
        # Stop all pipelines
        await incident_state["audio"].stop()
        await incident_state["vision"].stop()
        await incident_state["logs"].stop()
        
        # Stop ATOM session
        await incident_state["session"].stop()
        
        # Cleanup
        del active_incidents[incident_id]
        
        return IncidentResponse(
            incident_id=incident_id,
            status="stopped",
            message="Incident stopped successfully",
        )
        
    except Exception as e:
        logger.error(f"Error stopping incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incident/{incident_id}")
async def get_incident(incident_id: str) -> Dict:
    """
    Get current incident status and state.
    
    Args:
        incident_id: Incident ID to retrieve
        
    Returns:
        Current incident state from Firestore
    """
    if incident_id not in active_incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        firestore_manager = active_incidents[incident_id]["firestore"]
        incident_data = await firestore_manager.get_incident(incident_id)
        
        return incident_data or {"error": "Could not retrieve incident"}
        
    except Exception as e:
        logger.error(f"Error retrieving incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/test-postmortem")
async def debug_test_postmortem():
    """Diagnostic: test if Gemini generate_content works."""
    from google import genai
    key = GEMINI_API_KEY
    raw = os.getenv("GEMINI_API_KEY", "")
    result = {
        "key_present": bool(key),
        "key_length": len(key),
        "raw_length": len(raw),
        "key_first3": key[:3] if key else "",
        "key_last3": key[-3:] if key else "",
        "raw_repr_ends": repr(raw[:5]) + "..." + repr(raw[-5:]) if raw else "",
    }
    if not key:
        return result
    try:
        client = genai.Client(api_key=key)
        resp = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say hello in one word. Respond with only that word.",
        )
        result["gemini-2.0-flash"] = {"success": True, "text": resp.text[:200]}
    except Exception as e:
        result["gemini-2.0-flash"] = {"success": False, "error": f"{type(e).__name__}: {e}"}
    return result


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time incident updates.
    Handles connection lifecycle with keepalive ping/pong.
    
    Args:
        websocket: WebSocket connection from frontend
    """
    print(f"[WS] New WebSocket connection request received")
    
    # Attempt to accept connection
    try:
        await manager.connect(websocket)
    except Exception as e:
        print(f"[WS] ✗ Failed to establish connection: {e}")
        return
    
    # Keepalive task to send periodic pings
    async def keepalive():
        """Send periodic pings to keep connection alive."""
        try:
            while websocket in manager.active_connections:
                await asyncio.sleep(30)  # Ping every 30 seconds
                try:
                    await websocket.send_json({"type": "ping"})
                    print(f"[WS] ✓ Keepalive ping sent")
                except Exception as e:
                    print(f"[WS] Keepalive ping failed: {e}")
                    break
        except asyncio.CancelledError:
            pass
    
    # Start keepalive task
    keepalive_task = asyncio.create_task(keepalive())
    
    try:
        print(f"[WS] Entering receive loop...")
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                print(f"[WS] Received from client: {data}")
                
                # Handle client messages
                if data == "ping":
                    print(f"[WS] Client ping received, sending pong")
                    try:
                        await websocket.send_text("pong")
                    except Exception as e:
                        print(f"[WS] Failed to send pong: {e}")
                        break
                        
            except WebSocketDisconnect:
                print(f"[WS] Client explicitly disconnected")
                break
            except Exception as e:
                print(f"[WS] Error in receive loop: {e}")
                if "closed" in str(e).lower():
                    break
                await asyncio.sleep(0.1)
    
    except Exception as e:
        print(f"[WS] ✗ WebSocket handler error: {e}")
        logger.error(f"WebSocket handler error: {e}")
    
    finally:
        print(f"[WS] Cleaning up connection...")
        # Cancel keepalive task
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
        
        # Disconnect from manager
        await manager.disconnect(websocket)
        print(f"[WS] Connection cleanup complete")


@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_incidents": len(active_incidents),
        "connected_clients": len(manager.active_connections),
    }


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root() -> Dict:
    """Root endpoint with API documentation."""
    return {
        "title": "ATOM — Autonomous Threat & Operations Monitor",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "start_incident": "POST /incident/start",
            "stop_incident": "POST /incident/{id}/stop",
            "get_incident": "GET /incident/{id}",
            "websocket": "WS /ws",
            "health": "GET /health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    # Read PORT from environment (Cloud Run sets this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )

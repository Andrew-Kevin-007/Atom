"""
ATOM Backend - Main FastAPI Application
Real-time incident intelligence agent with Gemini Live API integration
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))
import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional, Set

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
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
websocket_clients: Set[WebSocket] = set()


async def broadcast_to_clients(message: Dict) -> None:
    """
    Broadcast message to all connected WebSocket clients.
    
    Args:
        message: Dictionary to broadcast as JSON
    """
    disconnected = set()
    
    for client in websocket_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            disconnected.add(client)
    
    # Clean up disconnected clients
    for client in disconnected:
        websocket_clients.discard(client)


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
    
    Args:
        incident_id: Current incident ID
        log_message: Log text
        timestamp: Timestamp string
        severity: Log severity (INFO, WARNING, ERROR, CRITICAL)
    """
    await broadcast_to_clients({
        "type": "log_event",
        "incident_id": incident_id,
        "message": log_message,
        "timestamp": timestamp,
        "severity": severity,
    })


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
        
        # Start ATOM session
        await atom_session.start()
        
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
            "tasks": [],
        }
        
        # Start all pipelines concurrently
        logger.info(f"🚀 Starting all pipelines for incident {incident_id}")
        
        # Create tasks
        audio_task = asyncio.create_task(audio_pipeline.start_streaming(atom_session))
        vision_task = asyncio.create_task(vision_pipeline.stream(atom_session))
        log_task = asyncio.create_task(
            log_pipeline.simulate_incident(atom_session, firestore_manager, incident_id)
        )
        
        # Wait for all tasks to complete
        await asyncio.gather(audio_task, vision_task, log_task, return_exceptions=True)
        
        # Announce resolution
        await on_atom_response(incident_id, "INCIDENT RESOLVED. Generating postmortem...")
        
        # Update status
        await firestore_manager.resolve_incident(incident_id, "Incident resolved successfully")
        
        # Broadcast incident resolved event
        await broadcast_to_clients({
            "type": "incident_resolved",
            "incident_id": incident_id,
        })
        
    except asyncio.CancelledError:
        logger.info(f"Incident {incident_id} cancelled")
    except Exception as e:
        logger.error(f"Error in incident orchestration: {e}")
    finally:
        # Cleanup
        if incident_id in active_incidents:
            try:
                await active_incidents[incident_id]["session"].stop()
            except Exception as e:
                logger.error(f"Error stopping session: {e}")


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
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
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
    incident_id = str(uuid.uuid4())[:8]
    
    logger.info(f"📍 Starting incident: {incident_id}")
    
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time incident updates.
    
    Args:
        websocket: WebSocket connection from frontend
    """
    await websocket.accept()
    websocket_clients.add(websocket)
    
    logger.info(f"📡 New WebSocket client connected ({len(websocket_clients)} total)")
    
    try:
        while True:
            # Keep connection alive and receive any incoming messages
            data = await websocket.receive_text()
            
            # Echo back or handle commands if needed
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        logger.info(f"📡 Client disconnected ({len(websocket_clients)-1} remaining)")
        websocket_clients.discard(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_clients.discard(websocket)


@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_incidents": len(active_incidents),
        "connected_clients": len(websocket_clients),
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
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

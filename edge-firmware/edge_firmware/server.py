"""
Local HTTP server for Smart Glove Edge Firmware.

Provides endpoints for the mobile app to trigger scan sessions.
Uses FastAPI for async request handling.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time

from .config import config


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models
class TriggerRequest(BaseModel):
    """Request model for /trigger endpoint."""
    scan_id: str = Field(..., description="Unique scan session ID")
    OwnerId: str = Field(..., description="Owner ID for validation")
    PatientId: str = Field(..., description="Patient ID")
    IsPregnant: bool = Field(default=False, description="Whether patient is pregnant")
    CaptureTimestamp: int = Field(..., description="Unix timestamp when image was captured")
    SyncTimestamp: int = Field(..., description="Unix timestamp when sync started")


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    OwnerId: Optional[str] = None
    backend: str
    camera_backend: str
    last_upload: Optional[str] = None
    queue_depth: int = 0


class TriggerResponse(BaseModel):
    """Response model for /trigger endpoint."""
    status: str
    message: str
    scan_id: str


# Global state
last_upload_time: Optional[datetime] = None
queue_depth: int = 0
is_busy: bool = False


# Create FastAPI app
app = FastAPI(
    title="Smart Glove Edge Firmware",
    description="Local HTTP server for Smart Glove Raspberry Pi",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_scan_task(request: TriggerRequest):
    """
    Background task to process a scan request.
    
    This function runs in the background after the /trigger endpoint returns 202.
    It handles the full capture → encrypt → upload pipeline.
    """
    global is_busy, last_upload_time, queue_depth
    
    try:
        logger.info(f"Processing scan {request.scan_id} for patient {request.PatientId}")
        
        # Import here to avoid circular imports
        from .capture import capture_finger_image
        from .crypto import encrypt_image
        from .uploader import upload_to_backend
        
        # Step 1: Capture image
        logger.info("Capturing image...")
        capture_result = capture_finger_image()
        
        if not capture_result.success:
            logger.error(f"Capture failed: {capture_result.error}")
            # Could add to cache here for retry
            return
        
        logger.info(f"Image captured: {len(capture_result.image_bytes)} bytes")
        
        # Step 2: Encrypt image
        logger.info("Encrypting image...")
        encrypted_image = encrypt_image(capture_result.image_bytes)
        logger.info(f"Image encrypted: {len(encrypted_image)} bytes")
        
        # Step 3: Upload to backend
        logger.info("Uploading to backend...")
        upload_result = await upload_to_backend(
            scan_id=request.scan_id,
            encrypted_image=encrypted_image,
            OwnerId=request.OwnerId,
            PatientId=request.PatientId,
            IsPregnant=request.IsPregnant,
            CaptureTimestamp=request.CaptureTimestamp,
            SyncTimestamp=request.SyncTimestamp
        )
        
        if upload_result.success:
            logger.info(f"Upload successful: {upload_result.reading_id}")
            last_upload_time = datetime.now()
        else:
            logger.error(f"Upload failed: {upload_result.error}")
            # Could add to cache here for retry
            
    except Exception as e:
        logger.exception(f"Error processing scan {request.scan_id}: {str(e)}")
    finally:
        is_busy = False
        queue_depth = max(0, queue_depth - 1)


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Returns firmware status, camera backend info, and queue depth.
    """
    # Get camera backend info
    from .capture import CameraCapture
    camera = CameraCapture()
    backend_info = camera.get_backend_info()
    
    return HealthResponse(
        status="ok",
        owner_id=config.OWNER_ID,
        backend=config.BACKEND_BASE_URL,
        camera_backend=backend_info["backend"],
        last_upload=last_upload_time.isoformat() if last_upload_time else None,
        queue_depth=queue_depth
    )


@app.post("/trigger", response_model=TriggerResponse)
async def trigger_scan(
    request: TriggerRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger a scan session.
    
    Called by the mobile app to initiate a scan. Validates the owner_id
    and starts the capture → encrypt → upload pipeline in the background.
    
    Returns 202 Accepted immediately if validation passes.
    """
    global is_busy, queue_depth
    
    # Validate OwnerId matches provisioned credentials
    if request.OwnerId != config.OWNER_ID:
        logger.warning(f"Invalid OwnerId: {request.OwnerId} (expected {config.OWNER_ID})")
        raise HTTPException(status_code=403, detail="Invalid Owner ID")
    
    # Check if already busy
    if is_busy:
        logger.warning("Scan already in progress, rejecting new request")
        raise HTTPException(status_code=503, detail="Scan already in progress")
    
    # Validate timestamps
    current_time = int(time.time())
    if abs(request.SyncTimestamp - current_time) > 300:  # 5 minute tolerance
        logger.warning(f"Invalid SyncTimestamp: {request.SyncTimestamp} (current: {current_time})")
        raise HTTPException(status_code=400, detail="Invalid timestamp")
    
    # Mark as busy and increment queue
    is_busy = True
    queue_depth += 1
    
    logger.info(f"Triggered scan {request.scan_id} for patient {request.PatientId}")
    
    # Start background task
    background_tasks.add_task(process_scan_task, request)
    
    return TriggerResponse(
        status="accepted",
        message="Scan started",
        scan_id=request.scan_id
    )


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Smart Glove Edge Firmware",
        "version": "1.0.0",
        "status": "running",
        "OwnerId": config.OWNER_ID
    }


def start_server():
    """
    Start the HTTP server.
    
    This function blocks and runs the server until interrupted.
    """
    import uvicorn
    
    logger.info(f"Starting server on {config.SERVER_HOST}:{config.SERVER_PORT}")
    logger.info(f"Owner ID: {config.OWNER_ID}")
    logger.info(f"Backend: {config.BACKEND_BASE_URL}")
    
    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level=config.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    start_server()

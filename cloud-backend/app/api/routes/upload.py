from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Request
from app.api.dependencies import get_current_active_user
from app.schemas.history import UploadMetadata
from app.services.cloudinary_service import storage_service
from app.services.db import get_database
from app.core.security import decrypt_image_payload
from app.utils.rate_limit import limiter
from pydantic import ValidationError
import uuid
import time
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
@limiter.limit("100/minute")
async def upload_reading(
    request: Request,
    image: UploadFile = File(...),
    metadata: str = Form(...),
    current_user: dict = Depends(get_current_active_user)
):
    try:
        # 1. Parse Metadata JSON
        meta_obj = UploadMetadata.model_validate_json(metadata)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid metadata: {e.errors()}")
        
    try:
        # 2. Read and Decrypt Image
        image_bytes = await image.read()
        
        # Free Tier Safeguard (5MB limit)
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Payload too large. Max 5MB.")
            
        # Decrypt payload in memory
        decrypted_image = decrypt_image_payload(image_bytes)
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to decrypt image payload.")
        
    # 3. Relative Offset Logic for True Timestamp
    current_server_time = int(time.time())
    # offset = time sync started - time captured
    offset = meta_obj.sync_timestamp - meta_obj.capture_timestamp
    
    if offset < 0:
        offset = 0 # Fallback if clocks are somehow extremely weird
        
    true_timestamp_unix = current_server_time - offset
    true_timestamp = datetime.fromtimestamp(true_timestamp_unix, tz=timezone.utc)
    
    # 4. Upload to Cloudinary
    patient_id = current_user["patient_id"]
    public_id = f"smart-glove/{patient_id}/{uuid.uuid4()}"
    
    try:
        saved_public_id = storage_service.upload_file(decrypted_image, public_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload image to Cloudinary.")
        
    # 5. Save to MongoDB
    db = get_database()
    history_doc = {
        "patient_id": patient_id,
        "true_timestamp": true_timestamp,
        "edge_capture_timestamp": meta_obj.capture_timestamp,
        "s3_image_key": saved_public_id, # keeping the same DB field name for now
        "hemoglobin_level": meta_obj.hemoglobin_level
    }
    
    await db.history.insert_one(history_doc)
    
    return {"message": "Upload successful", "true_timestamp": true_timestamp}

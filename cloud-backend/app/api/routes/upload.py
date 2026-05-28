from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Request
from app.api.dependencies import get_current_active_user
from app.schemas.history import UploadMetadata
from app.services.cloudinary_service import storage_service
from app.services.db import get_database
from app.core.security import decrypt_image_payload
from app.services.hemoglobin import is_anemic
from app.services.model import predict_hemoglobin_from_image, ModelPredictionError
from app.services.image_processing import preprocess_for_model, ImageProcessingError
from app.core.config import settings
from app.utils.rate_limit import limiter
from pydantic import ValidationError
import uuid
import time
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "application/octet-stream"}
MAX_DECRYPTED_BYTES = 10 * 1024 * 1024

@router.post("/", deprecated=True)
@limiter.limit("100/minute")
async def upload_reading(
    request: Request,
    image: UploadFile = File(...),
    metadata: str = Form(...),
    current_user: dict = Depends(get_current_active_user)
):
    # 1) Parse metadata (JSON string -> Pydantic)
    try:
        meta = UploadMetadata.model_validate_json(metadata)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid metadata: {e}")

    # 2) Verify patient exists and belongs to this owner
    db = get_database()
    patient = await db.patients.find_one({"patient_id": meta.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.get("owner_id") != current_user.get("owner_id"):
        raise HTTPException(status_code=403, detail="Not authorized to upload for this patient")

    if image.content_type and image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported content type")

    # 3) Read and decrypt image bytes, enforce size limit
    try:
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Payload too large. Max 5MB.")
        decrypted = decrypt_image_payload(image_bytes)
        if len(decrypted) > MAX_DECRYPTED_BYTES:
            raise HTTPException(status_code=413, detail="Decrypted payload too large.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to read/decrypt image")
        raise HTTPException(status_code=400, detail="Failed to process image payload")

    processed_bytes = decrypted
    if settings.IMAGE_PROCESSING_ENABLED:
        try:
            processed_bytes, _fmt = preprocess_for_model(decrypted, size=settings.MODEL_IMAGE_SIZE)
        except ImageProcessingError as e:
            raise HTTPException(status_code=422, detail=f"Image processing failed: {e}")
        except Exception:
            logger.exception("Unexpected image processing failure")
            raise HTTPException(status_code=500, detail="Image processing failed")

    # 4) Compute true timestamp
    now_unix = int(time.time())
    offset = meta.sync_timestamp - meta.capture_timestamp
    if offset < 0:
        offset = 0
    true_ts_unix = now_unix - offset
    true_timestamp = datetime.fromtimestamp(true_ts_unix, tz=timezone.utc)

    # 5) Upload image to cloudinary (or existing storage service)
    owner_id = current_user["owner_id"]
    public_id = f"smart-glove/{owner_id}/{meta.patient_id}/{uuid.uuid4()}"
    try:
        uploaded_url = storage_service.upload_file(decrypted, public_id)
    except Exception:
        logger.exception("Cloud upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload image to storage")

    # 6) Calculate anemia (use patient demographics, and is_pregnant from metadata)
    hb = None
    if meta.hemoglobin_level is not None:
        try:
            hb = float(meta.hemoglobin_level)
        except Exception:
            hb = None
    if hb is None:
        try:
            prediction = await predict_hemoglobin_from_image(processed_bytes)
            hb = float(prediction.hemoglobin_level)
        except ModelPredictionError as e:
            raise HTTPException(status_code=502, detail=f"Model prediction failed: {e}")
        except Exception:
            logger.exception("Unexpected model prediction failure")
            raise HTTPException(status_code=500, detail="Model prediction failed")
    patient_age = int(patient.get("age", 0))
    patient_gender = patient.get("gender", "female")
    anemic_flag = is_anemic(hb, patient_age, patient_gender, meta.is_pregnant)
    status_text = "Anemic" if anemic_flag else "Normal"

    # 7) Persist reading to hemoglobin_readings collection
    reading_doc = {
        "reading_id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "patient_id": meta.patient_id,
        "patient_age": patient_age,
        "patient_gender": patient_gender,
        "is_pregnant": bool(meta.is_pregnant),
        "hemoglobin_level": hb,
        "true_timestamp": true_timestamp,
        "edge_capture_timestamp": meta.capture_timestamp,
        "image_url": uploaded_url,
        "is_anemic": anemic_flag,
        "status_text": status_text,
        "created_at": datetime.now(timezone.utc)
    }
    await db.hemoglobin_readings.insert_one(reading_doc)

    # 8) Return a concise success payload
    return {
        "message": "Upload successful",
        "warning": "Deprecated endpoint. Prefer /api/v1/scan/sessions/{scan_id}/upload",
        "reading_id": reading_doc["reading_id"],
        "true_timestamp": true_timestamp.isoformat()
    }
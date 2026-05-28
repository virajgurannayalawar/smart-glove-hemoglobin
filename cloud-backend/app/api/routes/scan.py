from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from datetime import datetime, timezone
import time
import uuid
import logging
import asyncio

from app.api.dependencies import get_current_active_user
from app.schemas.scan import (
    ScanSessionCreate,
    ScanSessionResponse,
    ScanResultResponse,
    GloveUploadMetadata,
)
from app.services.scan_sessions import scan_session_store
from app.services.db import get_database
from app.services.scan_events import record_scan_event
from app.core.security import decrypt_image_payload
from app.services.cloudinary_service import storage_service
from app.services.hemoglobin import is_anemic
from app.services.model import predict_hemoglobin_from_image, ModelPredictionError
from app.services.image_processing import preprocess_for_model, ImageProcessingError
from app.core.config import settings
from app.utils.rate_limit import limiter
import secrets


logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "application/octet-stream"}
MAX_DECRYPTED_BYTES = 10 * 1024 * 1024


@router.get("/owner-id")
async def get_owner_id(current_user: dict = Depends(get_current_active_user)):
    return {"owner_id": current_user.get("owner_id")}


@router.get("/glove-key")
async def get_glove_key(current_user: dict = Depends(get_current_active_user)):
    """
    Returns the current glove API key for this owner.
    Use this during provisioning (send to Raspberry Pi over BLE).
    """
    key = current_user.get("glove_api_key")
    if not key:
        # Backfill for older users created before glove key existed.
        db = get_database()
        key = secrets.token_urlsafe(32)
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"glove_api_key": key}})
    return {"glove_api_key": key}


@router.post("/glove-key/rotate")
async def rotate_glove_key(current_user: dict = Depends(get_current_active_user)):
    """
    Rotates glove API key for this owner.
    After rotation, re-provision the glove with the new key.
    """
    db = get_database()
    new_key = secrets.token_urlsafe(32)
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"glove_api_key": new_key}})
    return {"glove_api_key": new_key}


@router.post("/sessions", response_model=ScanSessionResponse)
async def create_scan_session(
    request: Request,
    payload: ScanSessionCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    owner_id = current_user["owner_id"]

    patient = await db.patients.find_one({"patient_id": payload.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.get("owner_id") != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized for this patient")

    session = await scan_session_store.create_session(
        owner_id=owner_id,
        patient_id=payload.patient_id,
        is_pregnant=payload.is_pregnant,
        ttl_seconds=120,
    )

    await record_scan_event(
        scan_id=session.scan_id,
        owner_id=owner_id,
        patient_id=payload.patient_id,
        event="session_created",
        request_id=getattr(request.state, "request_id", None),
        detail={"ttl_seconds": 120},
    )

    return ScanSessionResponse(
        scan_id=session.scan_id,
        owner_id=session.owner_id,
        patient_id=session.patient_id,
        is_pregnant=session.is_pregnant,
        status=session.status,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.get("/sessions/{scan_id}/result", response_model=ScanResultResponse)
@limiter.limit("60/minute")
async def get_scan_result(
    request: Request,
    scan_id: str,
    timeout_seconds: int = 30,
    current_user: dict = Depends(get_current_active_user),
):
    owner_id = current_user["owner_id"]
    request_id = getattr(request.state, "request_id", None)
    session = await scan_session_store.get(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")
    if session.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized for this scan session")

    session = await scan_session_store.expire_if_needed(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    if session.status == "pending":
        await record_scan_event(
            scan_id=scan_id,
            owner_id=owner_id,
            patient_id=session.patient_id,
            event="result_long_poll_started",
            request_id=request_id,
            detail={"timeout_seconds": timeout_seconds},
        )
        try:
            await asyncio.wait_for(session.event.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            await record_scan_event(
                scan_id=scan_id,
                owner_id=owner_id,
                patient_id=session.patient_id,
                event="result_long_poll_timeout",
                request_id=request_id,
                detail={"timeout_seconds": timeout_seconds},
            )
            return ScanResultResponse(scan_id=scan_id, status="pending")

    session = await scan_session_store.expire_if_needed(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    if session.status != "completed":
        return ScanResultResponse(scan_id=scan_id, status=session.status, error=session.error)

    result = session.result or {}
    return ScanResultResponse(
        scan_id=scan_id,
        status="completed",
        hemoglobin_level=result.get("hemoglobin_level"),
        is_anemic=result.get("is_anemic"),
        status_text=result.get("status_text"),
        reading_id=result.get("reading_id"),
        true_timestamp=result.get("true_timestamp"),
        image_url=result.get("image_url"),
        error=session.error,
    )


@router.post("/sessions/{scan_id}/upload")
@limiter.limit("100/minute")
async def glove_upload_for_session(
    request: Request,
    scan_id: str,
    image: UploadFile = File(...),
    metadata: str = Form(...),
):
    """
    New workflow: glove uploads without JWT.
    Validation is based on owner_id provisioned to the glove + active scan session.
    """
    try:
        meta = GloveUploadMetadata.model_validate_json(metadata)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid metadata: {e}")

    glove_key = request.headers.get("x-glove-key")
    if not glove_key:
        raise HTTPException(status_code=401, detail="Missing glove authentication header: X-Glove-Key")
    request_id = getattr(request.state, "request_id", None)

    session = await scan_session_store.get(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    session = await scan_session_store.expire_if_needed(scan_id)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")
    if session.status != "pending":
        raise HTTPException(status_code=409, detail=f"Scan session already {session.status}")

    if meta.owner_id != session.owner_id:
        raise HTTPException(status_code=403, detail="Owner ID does not match scan session")
    if meta.patient_id != session.patient_id:
        raise HTTPException(status_code=403, detail="Patient ID does not match scan session")

    db = get_database()
    owner = await db.users.find_one({"owner_id": meta.owner_id})
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    if owner.get("glove_api_key") != glove_key:
        raise HTTPException(status_code=401, detail="Invalid glove API key")

    patient = await db.patients.find_one({"patient_id": meta.patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.get("owner_id") != meta.owner_id:
        raise HTTPException(status_code=403, detail="Patient does not belong to this owner")

    await record_scan_event(
        scan_id=scan_id,
        owner_id=meta.owner_id,
        patient_id=meta.patient_id,
        event="glove_upload_received",
        request_id=request_id,
        detail={"content_type": image.content_type, "filename": image.filename},
    )

    if image.content_type and image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported content type")

    try:
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Payload too large. Max 5MB.")
        decrypted = decrypt_image_payload(image_bytes)
        if len(decrypted) > MAX_DECRYPTED_BYTES:
            raise HTTPException(status_code=413, detail="Decrypted payload too large.")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to read/decrypt image")
        raise HTTPException(status_code=400, detail="Failed to process image payload")

    await record_scan_event(
        scan_id=scan_id,
        owner_id=meta.owner_id,
        patient_id=meta.patient_id,
        event="image_decrypted",
        request_id=request_id,
        detail={"encrypted_bytes": len(image_bytes), "decrypted_bytes": len(decrypted)},
    )

    processed_bytes = decrypted
    if settings.IMAGE_PROCESSING_ENABLED:
        try:
            processed_bytes, _fmt = preprocess_for_model(decrypted, size=settings.MODEL_IMAGE_SIZE)
        except ImageProcessingError as e:
            raise HTTPException(status_code=422, detail=f"Image processing failed: {e}")
        except Exception:
            logger.exception("Unexpected image processing failure")
            raise HTTPException(status_code=500, detail="Image processing failed")
        await record_scan_event(
            scan_id=scan_id,
            owner_id=meta.owner_id,
            patient_id=meta.patient_id,
            event="image_preprocessed",
            request_id=request_id,
            detail={"processed_bytes": len(processed_bytes), "model_image_size": settings.MODEL_IMAGE_SIZE},
        )

    now_unix = int(time.time())
    offset = meta.sync_timestamp - meta.capture_timestamp
    if offset < 0:
        offset = 0
    true_ts_unix = now_unix - offset
    true_timestamp = datetime.fromtimestamp(true_ts_unix, tz=timezone.utc)

    public_id = f"smart-glove/{meta.owner_id}/{meta.patient_id}/{uuid.uuid4()}"
    try:
        uploaded_url = storage_service.upload_file(decrypted, public_id)
    except Exception:
        logger.exception("Cloud upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload image to storage")
    await record_scan_event(
        scan_id=scan_id,
        owner_id=meta.owner_id,
        patient_id=meta.patient_id,
        event="image_uploaded",
        request_id=request_id,
        detail={"image_public_id": uploaded_url},
    )

    try:
        prediction = await predict_hemoglobin_from_image(processed_bytes)
        hb_level = float(prediction.hemoglobin_level)
    except ModelPredictionError as e:
        await scan_session_store.fail(scan_id, f"Model prediction failed: {e}")
        raise HTTPException(status_code=502, detail=f"Model prediction failed: {e}")
    except Exception:
        logger.exception("Unexpected model prediction failure")
        await scan_session_store.fail(scan_id, "Model prediction failed")
        raise HTTPException(status_code=500, detail="Model prediction failed")
    await record_scan_event(
        scan_id=scan_id,
        owner_id=meta.owner_id,
        patient_id=meta.patient_id,
        event="model_predicted",
        request_id=request_id,
        detail={"hemoglobin_level": hb_level},
    )

    patient_age = int(patient.get("age", 0))
    patient_gender = patient.get("gender", "female")
    anemic_flag = is_anemic(hb_level, patient_age, patient_gender, meta.is_pregnant)
    status_text = "Anemic" if anemic_flag else "Normal"

    reading_doc = {
        "reading_id": str(uuid.uuid4()),
        "owner_id": meta.owner_id,
        "patient_id": meta.patient_id,
        "patient_age": patient_age,
        "patient_gender": patient_gender,
        "is_pregnant": bool(meta.is_pregnant),
        "hemoglobin_level": hb_level,
        "true_timestamp": true_timestamp,
        "edge_capture_timestamp": meta.capture_timestamp,
        "image_url": uploaded_url,
        "is_anemic": anemic_flag,
        "status_text": status_text,
        "created_at": datetime.now(timezone.utc),
    }
    await db.hemoglobin_readings.insert_one(reading_doc)
    await record_scan_event(
        scan_id=scan_id,
        owner_id=meta.owner_id,
        patient_id=meta.patient_id,
        event="reading_persisted",
        request_id=request_id,
        detail={"reading_id": reading_doc["reading_id"]},
    )

    await scan_session_store.complete(
        scan_id,
        {
            "hemoglobin_level": hb_level,
            "is_anemic": anemic_flag,
            "status_text": status_text,
            "reading_id": reading_doc["reading_id"],
            "true_timestamp": true_timestamp.isoformat(),
            "image_url": uploaded_url,
        },
    )
    await record_scan_event(
        scan_id=scan_id,
        owner_id=meta.owner_id,
        patient_id=meta.patient_id,
        event="session_completed",
        request_id=request_id,
        detail={"status_text": status_text, "is_anemic": anemic_flag},
    )

    return {"message": "Upload successful", "scan_id": scan_id, "reading_id": reading_doc["reading_id"]}


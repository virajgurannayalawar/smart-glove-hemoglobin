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


@router.get("/OwnerId")
async def get_OwnerId(current_user: dict = Depends(get_current_active_user)):
    return {"OwnerId": current_user.get("OwnerId")}


@router.get("/glove-key")
async def get_glove_key(current_user: dict = Depends(get_current_active_user)):
    """
    Returns the current glove API key for this owner.
    Use this during provisioning (send to Raspberry Pi over BLE).
    """
    key = current_user.get("GloveApiKey")
    if not key:
        # Backfill for older users created before glove key existed.
        db = get_database()
        key = secrets.token_urlsafe(32)
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"GloveApiKey": key}})
    return {"GloveApiKey": key}


@router.post("/glove-key/rotate")
async def rotate_glove_key(current_user: dict = Depends(get_current_active_user)):
    """
    Rotates glove API key for this owner.
    After rotation, re-provision the glove with the new key.
    """
    db = get_database()
    new_key = secrets.token_urlsafe(32)
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"GloveApiKey": new_key}})
    return {"GloveApiKey": new_key}


@router.post("/sessions", response_model=ScanSessionResponse)
async def create_scan_session(
    request: Request,
    payload: ScanSessionCreate,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    OwnerId = current_user["OwnerId"]

    patient = await db.patients.find_one({"PatientId": payload.PatientId})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.get("OwnerId") != OwnerId:
        raise HTTPException(status_code=403, detail="Not authorized for this patient")

    session = await scan_session_store.create_session(
        OwnerId=OwnerId,
        PatientId=payload.PatientId,
        is_pregnant=payload.IsPregnant,
        ttl_seconds=120,
    )

    await record_scan_event(
        ScanId=session.ScanId,
        OwnerId=OwnerId,
        PatientId=payload.PatientId,
        event="session_created",
        request_id=getattr(request.state, "request_id", None),
        detail={"ttl_seconds": 120},
    )

    return ScanSessionResponse(
        ScanId=session.ScanId,
        OwnerId=session.OwnerId,
        PatientId=session.PatientId,
        IsPregnant=session.IsPregnant,
        Status=session.Status,
        CreatedAt=session.CreatedAt,
        ExpiresAt=session.ExpiresAt,
    )


@router.get("/sessions/{ScanId}/result", response_model=ScanResultResponse)
@limiter.limit("60/minute")
async def get_scan_result(
    request: Request,
    ScanId: str,
    timeout_seconds: int = 30,
    current_user: dict = Depends(get_current_active_user),
):
    OwnerId = current_user["OwnerId"]
    request_id = getattr(request.state, "request_id", None)
    session = await scan_session_store.get(ScanId)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")
    if session.OwnerId != OwnerId:
        raise HTTPException(status_code=403, detail="Not authorized for this scan session")

    session = await scan_session_store.expire_if_needed(ScanId)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    if session.Status == "pending":
        await record_scan_event(
            ScanId=ScanId,
            OwnerId=OwnerId,
            PatientId=session.PatientId,
            event="result_long_poll_started",
            request_id=request_id,
            detail={"timeout_seconds": timeout_seconds},
        )
        try:
            await asyncio.wait_for(session.Event.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            await record_scan_event(
                ScanId=ScanId,
                OwnerId=OwnerId,
                PatientId=session.PatientId,
                event="result_long_poll_timeout",
                request_id=request_id,
                detail={"timeout_seconds": timeout_seconds},
            )
            return ScanResultResponse(ScanId=ScanId, Status="pending")

    session = await scan_session_store.expire_if_needed(ScanId)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    if session.Status != "completed":
        return ScanResultResponse(ScanId=ScanId, Status=session.Status, Error=session.Error)

    result = session.Result or {}
    return ScanResultResponse(
        ScanId=ScanId,
        Status="completed",
        HemoglobinLevel=result.get("HemoglobinLevel"),
        IsAnemic=result.get("IsAnemic"),
        StatusText=result.get("StatusText"),
        ReadingId=result.get("ReadingId"),
        TrueTimestamp=result.get("TrueTimestamp"),
        ImageUrl=result.get("ImageUrl"),
        Error=session.Error,
    )


@router.post("/sessions/{ScanId}/upload")
@limiter.limit("100/minute")
async def glove_upload_for_session(
    request: Request,
    ScanId: str,
    image: UploadFile = File(...),
    metadata: str = Form(...),
):
    """
    New workflow: glove uploads without JWT.
    Validation is based on OwnerId provisioned to the glove + active scan session.

    """
    try:
        meta = GloveUploadMetadata.model_validate_json(metadata)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid metadata: {e}")

    glove_key = request.headers.get("x-glove-key")
    if not glove_key:
        raise HTTPException(status_code=401, detail="Missing glove authentication header: X-Glove-Key")
    request_id = getattr(request.state, "request_id", None)

    session = await scan_session_store.get(ScanId)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    session = await scan_session_store.expire_if_needed(ScanId)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")
    if session.Status != "pending":
        raise HTTPException(status_code=409, detail=f"Scan session already {session.Status}")

    if meta.OwnerId != session.OwnerId:
        raise HTTPException(status_code=403, detail="Owner ID does not match scan session")
    if meta.PatientId != session.PatientId:
        raise HTTPException(status_code=403, detail="Patient ID does not match scan session")

    db = get_database() 
    owner = await db.users.find_one({"OwnerId": meta.OwnerId})
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    if owner.get("GloveApiKey") != glove_key:
        raise HTTPException(status_code=401, detail="Invalid glove API key")

    patient = await db.patients.find_one({"PatientId": meta.PatientId})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient.get("OwnerId") != meta.OwnerId:
        raise HTTPException(status_code=403, detail="Patient does not belong to this owner")

    await record_scan_event(
        ScanId=ScanId,
        OwnerId=meta.OwnerId,
        PatientId=meta.PatientId,
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
        ScanId=ScanId,
        OwnerId=meta.OwnerId,
        PatientId=meta.PatientId,
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
            ScanId=ScanId,
            OwnerId=meta.OwnerId,
            PatientId=meta.PatientId,
            event="image_preprocessed",
            request_id=request_id,
            detail={"processed_bytes": len(processed_bytes), "model_image_size": settings.MODEL_IMAGE_SIZE},
        )

    now_unix = int(time.time())
    offset = meta.SyncTimestamp - meta.CaptureTimestamp
    if offset < 0:
        offset = 0
    true_ts_unix = now_unix - offset
    true_timestamp = datetime.fromtimestamp(true_ts_unix, tz=timezone.utc)

    public_id = f"smart-glove/{meta.OwnerId}/{meta.PatientId}/{uuid.uuid4()}"
    try:
        uploaded_url = storage_service.upload_file(decrypted, public_id)
    except Exception:
        logger.exception("Cloud upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload image to storage")
    await record_scan_event(
        ScanId=ScanId,
        OwnerId=meta.OwnerId,
        PatientId=meta.PatientId,
        event="image_uploaded",
        request_id=request_id,
        detail={"ImagePublicId": uploaded_url},
    )

    try:
        prediction = await predict_hemoglobin_from_image(processed_bytes)
        hb_level = float(prediction.HemoglobinLevel)
    except ModelPredictionError as e:
        await scan_session_store.fail(ScanId, f"Model prediction failed: {e}")
        raise HTTPException(status_code=502, detail=f"Model prediction failed: {e}")
    except Exception:
        logger.exception("Unexpected model prediction failure")
        await scan_session_store.fail(ScanId, "Model prediction failed")
        raise HTTPException(status_code=500, detail="Model prediction failed")
    await record_scan_event(
        ScanId=ScanId,
        OwnerId=meta.OwnerId,
        PatientId=meta.PatientId,
        event="model_predicted",
        request_id=request_id,
        detail={"HemoglobinLevel": hb_level},
    )

    patient_age = int(patient.get("Age", 0))
    patient_gender = patient.get("Gender", "female")
    anemic_flag = is_anemic(hb_level, patient_age, patient_gender, meta.IsPregnant)
    status_text = "Anemic" if anemic_flag else "Normal"

    reading_doc = {
        "ReadingId": str(uuid.uuid4()),
        "OwnerId": meta.OwnerId,
        "PatientId": meta.PatientId,
        "PatientAge": patient_age,
        "PatientGender": patient_gender,
        "IsPregnant": bool(meta.IsPregnant),
        "HemoglobinLevel": hb_level,
        "TrueTimestamp": true_timestamp,
        "EdgeCaptureTimestamp": meta.CaptureTimestamp,
        "ImageUrl": uploaded_url,
        "IsAnemic": anemic_flag,
        "StatusText": status_text,
        "CreatedAt": datetime.now(timezone.utc),
    }
    await db.hemoglobin_readings.insert_one(reading_doc)
    await record_scan_event(
        ScanId=ScanId,
        OwnerId=meta.OwnerId,
        PatientId=meta.PatientId,
        event="reading_persisted",
        request_id=request_id,
        detail={"ReadingId": reading_doc["ReadingId"]},
    )

    await scan_session_store.complete(
        ScanId,
        {
            "HemoglobinLevel": hb_level,
            "IsAnemic": anemic_flag,
            "StatusText": status_text,
            "ReadingId": reading_doc["ReadingId"],
            "TrueTimestamp": true_timestamp.isoformat(),
            "ImageUrl": uploaded_url,
        },
    )
    await record_scan_event(
        ScanId=ScanId,
        OwnerId=meta.OwnerId,
        PatientId=meta.PatientId,
        event="session_completed",
        request_id=request_id,
        detail={"StatusText": status_text, "IsAnemic": anemic_flag},
    )

    return {"message": "Upload successful", "ScanId": ScanId, "reading_id": reading_doc["ReadingId"]}


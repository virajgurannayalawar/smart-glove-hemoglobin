from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.dependencies import get_current_active_user
from app.schemas.history import HistoryResponse
from app.services.db import get_database
from app.services.hemoglobin import is_anemic as is_anemic_service

router = APIRouter()

@router.get("", response_model=List[HistoryResponse])
async def get_history(
    patient_id: str | None = None,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    owner_id = current_user["owner_id"]

    query = {"owner_id": owner_id}

    if patient_id:
        patient = await db.patients.find_one({"patient_id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        if patient.get("owner_id") != owner_id:
            raise HTTPException(status_code=403, detail="Not authorized for this patient")
        query["patient_id"] = patient_id
    
    # Query readings, sorted by true_timestamp descending
    cursor = db.hemoglobin_readings.find(query).sort("true_timestamp", -1)
    
    results = []
    async for doc in cursor:
        hb_level = doc["hemoglobin_level"]
        record_age = int(doc.get("patient_age") or 0)
        record_gender = doc.get("patient_gender") or "female"
        record_is_pregnant = bool(doc.get("is_pregnant", False))

        is_anemic = bool(doc.get("is_anemic"))
        status_text = doc.get("status_text")
        if status_text is None:
            is_anemic = is_anemic_service(hb_level, record_age, record_gender, record_is_pregnant)
            status_text = "Anemic" if is_anemic else "Normal"
        
        history_item = HistoryResponse(
            _id=str(doc["_id"]),
            date=doc["true_timestamp"],
            hemoglobinLevel=hb_level,
            isAnemic=is_anemic,
            statusText=status_text,
            readingId=doc.get("reading_id"),
            patientId=doc.get("patient_id"),
            imageUrl=doc.get("image_url"),
        )
        results.append(history_item)
        
    return results

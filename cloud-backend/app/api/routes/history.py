from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.dependencies import get_current_active_user
from app.schemas.history import HistoryResponse
from app.services.db import get_database
from app.services.hemoglobin import is_anemic as is_anemic_service

router = APIRouter()

@router.get("", response_model=List[HistoryResponse])
async def get_history(
    PatientId: str | None = None,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    OwnerId = current_user["OwnerId"]

    query = {"OwnerId": OwnerId}

    if PatientId:
        patient = await db.patients.find_one({"PatientId": PatientId})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        if patient.get("OwnerId") != OwnerId:
            raise HTTPException(status_code=403, detail="Not authorized for this patient")
        query["PatientId"] = PatientId
    
    # Query readings, sorted by TrueTimestamp descending
    cursor = db.hemoglobin_readings.find(query).sort("TrueTimestamp", -1)
    
    results = []
    async for doc in cursor:
        hb_level = doc["HemoglobinLevel"]
        record_age = int(doc.get("PatientAge") or 0)
        record_gender = doc.get("PatientGender") or "female"
        record_is_pregnant = bool(doc.get("IsPregnant", False))

        is_anemic = bool(doc.get("IsAnemic"))
        status_text = doc.get("StatusText")
        if status_text is None:
            is_anemic = is_anemic_service(hb_level, record_age, record_gender, record_is_pregnant)
            status_text = "Anemic" if is_anemic else "Normal"
        
        history_item = HistoryResponse(
            _id=str(doc["_id"]),
            date=doc["TrueTimestamp"],
            hemoglobinLevel=hb_level,
            isAnemic=is_anemic,
            statusText=status_text,
            readingId=doc.get("ReadingId"),
            patientId=doc.get("PatientId"),
            imageUrl=doc.get("ImageUrl"),
        )
        results.append(history_item)
        
    return results

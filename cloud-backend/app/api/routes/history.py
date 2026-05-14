from fastapi import APIRouter, Depends
from typing import List
from app.api.dependencies import get_current_active_user
from app.schemas.history import HistoryResponse
from app.services.db import get_database
from app.services.cloudinary_service import storage_service

router = APIRouter()

@router.get("/", response_model=List[HistoryResponse])
async def get_history(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    patient_id = current_user["patient_id"]
    
    # Query history, sorted by true_timestamp descending
    cursor = db.history.find({"patient_id": patient_id}).sort("true_timestamp", -1)
    
    results = []
    async for doc in cursor:
        # Generate Cloudinary signed URL for the image
        image_url = ""
        if doc.get("s3_image_key"): # We kept the DB field name as s3_image_key for simplicity
            image_url = storage_service.generate_signed_url(doc["s3_image_key"])
            
        history_item = HistoryResponse(
            _id=str(doc["_id"]),
            patient_id=doc["patient_id"],
            true_timestamp=doc["true_timestamp"],
            hemoglobin_level=doc["hemoglobin_level"],
            image_url=image_url
        )
        results.append(history_item)
        
    return results

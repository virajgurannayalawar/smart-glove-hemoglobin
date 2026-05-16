from fastapi import APIRouter, Depends
from typing import List
from app.api.dependencies import get_current_active_user
from app.schemas.history import HistoryResponse
from app.services.db import get_database

router = APIRouter()

def check_anemia(hb_level: float, age: int, gender: str) -> bool:
    # WHO guidelines threshold
    gender_lower = gender.lower()
    if age < 5:
        return hb_level < 11.0
    elif age < 12:
        return hb_level < 11.5
    elif age < 15:
        return hb_level < 12.0
    else:
        if gender_lower in ["male", "m"]:
            return hb_level < 13.0
        else:
            return hb_level < 12.0

@router.get("", response_model=List[HistoryResponse])
async def get_history(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    patient_id = current_user["patient_id"]
    user_age = current_user.get("age", 25)
    user_gender = current_user.get("gender", "Female")
    
    # Query history, sorted by true_timestamp descending
    cursor = db.history.find({"patient_id": patient_id}).sort("true_timestamp", -1)
    
    results = []
    async for doc in cursor:
        hb_level = doc["hemoglobin_level"]
        is_anemic = check_anemia(hb_level, user_age, user_gender)
        status_text = "Anemic" if is_anemic else "Normal"
        
        history_item = HistoryResponse(
            _id=str(doc["_id"]),
            date=doc["true_timestamp"],
            hemoglobinLevel=hb_level,
            isAnemic=is_anemic,
            statusText=status_text
        )
        results.append(history_item)
        
    return results

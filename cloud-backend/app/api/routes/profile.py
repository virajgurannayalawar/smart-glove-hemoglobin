from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_current_active_user
from app.schemas.user import UserResponse
from app.services.db import get_database
from pydantic import BaseModel

router = APIRouter()

class ProfileUpdate(BaseModel):
    name: str
    age: int
    gender: str

@router.get("", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_active_user)):
    current_user["_id"] = str(current_user["_id"])
    return UserResponse(**current_user)

@router.put("", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdate, 
    current_user: dict = Depends(get_current_active_user)
):
    db = get_database()
    
    update_data = {
        "name": profile_data.name,
        "age": profile_data.age,
        "gender": profile_data.gender
    }
    
    result = await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Fetch updated user
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    updated_user["_id"] = str(updated_user["_id"])
    
    return UserResponse(**updated_user)

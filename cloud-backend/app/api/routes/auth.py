from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.user import UserCreate, UserResponse, LoginRequest
from app.services.db import get_database
from datetime import timedelta, datetime, timezone
from app.core.config import settings
import uuid

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate):
    db = get_database()
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    patient_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_in.password)
    
    user_doc = {
        "patient_id": patient_id,
        "email": user_in.email,
        "name": user_in.name,
        "age": user_in.age,
        "gender": user_in.gender,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    return user_doc

@router.post("/login")
async def login(login_req: LoginRequest):
    db = get_database()
    user = await db.users.find_one({"email": login_req.email})
    if not user or not verify_password(login_req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["patient_id"]}, expires_delta=access_token_expires
    )
    
    user["_id"] = str(user["_id"])
    return {
        "token": access_token,
        "user": UserResponse(**user).model_dump(by_alias=True)
    }

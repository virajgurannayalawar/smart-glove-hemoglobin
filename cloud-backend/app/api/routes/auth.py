from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.user import UserCreate, UserResponse, Token
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
    
    await db.users.insert_one(user_doc)
    return user_doc

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    # Assume username field contains the email for this implementation
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["patient_id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from app.core.config import settings
from app.schemas.user import TokenData
from app.services.db import get_database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        patient_id: str = payload.get("sub")
        if patient_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        token_data = TokenData(patient_id=patient_id)
    except (jwt.ExpiredSignatureError, jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    db = get_database()
    user = await db.users.find_one({"patient_id": token_data.patient_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

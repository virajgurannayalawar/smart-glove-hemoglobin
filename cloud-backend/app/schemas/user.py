from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., gt=0)
    gender: str

class UserResponse(BaseModel):
    patient_id: str
    name: str
    email: str
    age: int
    gender: str
    is_active: bool
    created_at: datetime
    
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    patient_id: Optional[str] = None

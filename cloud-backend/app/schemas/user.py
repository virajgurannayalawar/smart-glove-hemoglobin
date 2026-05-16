from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., gt=0)
    gender: str

class UserResponse(BaseModel):
    id: str = Field(alias="_id", default="")
    patientId: str = Field(alias="patient_id")
    name: str
    email: str
    age: int
    gender: str
    is_active: bool = True
    created_at: datetime = None
    
    class Config:
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    patient_id: Optional[str] = None

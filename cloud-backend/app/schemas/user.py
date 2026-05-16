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
    id: str = Field(validation_alias="_id", default="")
    patientId: str = Field(validation_alias="patient_id")
    #However, my backend code sent the JSON keys back as _id and patient_id. The Flutter app strictly expects the keys to be exactly id and patientId so i renamed them in the above two lines.#
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

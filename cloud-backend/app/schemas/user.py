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
    contact_number: str = Field(..., min_length=10)

class UserResponse(BaseModel):
    Id: str = Field(validation_alias="_id", default="")
    OwnerId: str
    Name: str
    Email: str
    Age: int
    Gender: str  
    ContactNumber: str
    IsActive: bool = True
    CreatedAt: datetime = None
    
    class Config:
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    OwnerId: Optional[str] = None

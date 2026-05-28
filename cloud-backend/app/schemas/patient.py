from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class PatientCreate(BaseModel):
    """
    INPUT model - what mobile app sends when registering a patient
    """
    name: str = Field(..., min_length=1, description="Patient's full name")
    age: int = Field(..., gt=0, le=120, description="Patient's age in years")
    gender: str = Field(..., description="male, female, or other")
    contact_number: str = Field(..., min_length=10, description="Phone number")
    email: EmailStr = Field(..., description="Patient's email")
    # removing pregnency:bool because a women cannot be always a pregnent
    notes: Optional[str] = Field(None, description="Optional clinical notes")
    

    class Config:
        json_schema_extra={
            "example":{
                "name":"Viraj Guranna Yalawar",
                "age":45,
                "gender": "male",
                "contact_number": "+91-9845497179",
                "email": "virajgyalawar05@gmail.com",
                "notes": "Regular checkup"
            }
        }

class PatientResponse(BaseModel):
    """
    OUTPUT model - what API returns after registering patient
    """
    id: str = Field(alias="_id", default="")
    patient_id: str = Field(alias="patient_id")  # Unique ID for this patient
    name: str
    age: int
    gender: str
    contact_number: str
    email: str
    notes: Optional[str] = None
    created_at: datetime
    owner_id: str  # Who registered/owns this patient
    
    class Config:
        populate_by_name = True
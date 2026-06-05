from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class PatientCreate(BaseModel):
    """
    INPUT model - what mobile app sends when registering a patient
    """
    Name: str = Field(..., min_length=1, description="Patient's full name")
    Age: int = Field(..., gt=0, le=120, description="Patient's age in years")
    Gender: str = Field(..., description="male, female, or other")
    ContactNumber: str = Field(..., min_length=10, description="Phone number")
    Email: EmailStr = Field(..., description="Patient's email")
    # removing pregnency:bool because a women cannot be always a pregnent
    Notes: Optional[str] = Field(None, description="Optional clinical notes")
    

    class Config:
        json_schema_extra={
            "example":{ 
                "Name":"Viraj Guranna Yalawar",
                "Age":45,
                "Gender": "male",
                "ContactNumber": "+91-9845497179",
                "Email": "virajgyalawar05@gmail.com",
                "Notes": "Regular checkup"
            }
        }

class PatientResponse(BaseModel):
    """
    OUTPUT model - what API returns after registering patient
    """
    Id: str = Field(alias="_id", default="")
    PatientId: str = Field(alias="patient_id")  # Unique ID for this patient
    Name: str
    Age: int
    Gender: str
    ContactNumber: str
    Email: str
    Notes: Optional[str] = None
    CreatedAt: datetime
    OwnerId: str  # Who registered/owns this patient
    
    class Config:
        populate_by_name = True
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class ScannerDetails(BaseModel):
    """Details of the person who performed the scan"""
    Name: str
    Email: str
    ContactNumber: str
    
class PatientDetails(BaseModel):
    """Details of the patient who was scanned"""
    PatientId: str
    Name: str
    Age: int
    Gender: str
    ContactNumber: str
    Email: str
    IsPregnant: bool = False  # NEW: From scan, not stored in patient record

class HemoglobinReportCreate(BaseModel):
    """
    INPUT model - what frontend sends when requesting report generation
    """
    ReadingId: str = Field(..., description="ID of hemoglobin reading")
    IsPregnant: bool = Field(False, description="Is patient pregnant?")
    Notes: Optional[str] = Field(None, description="Additional clinical notes")

class HemoglobinReportResponse(BaseModel):
    """
    OUTPUT model - complete report with all details
    """
    Id: str = Field(alias="_id", default="")
    ReportId: str = Field(alias="report_id")
    ReadingId: str
    
    # Patient Information
    PatientDetails: PatientDetails
    
    # Scanner Information
    ScannerDetails: ScannerDetails
    
    # Hemoglobin Result
    HemoglobinLevel: float
    IsAnemic: bool
    StatusText: str  # "Anemic" or "Normal"
    
    # Timestamps
    ScanTimestamp: datetime
    ReportGeneratedAt: datetime
    
    # PDF Path (after generation)
    PdfUrl: Optional[str] = None
    
    class Config:
        populate_by_name = True

"""WHY SEPARATE SCANNER AND PATIENT DETAILS?
- Scanner = Owner who performed scan (from JWT token)
- Patient = Person being scanned (from patients collection)
- This is crucial for reports!"""
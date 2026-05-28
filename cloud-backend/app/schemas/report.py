from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class ScannerDetails(BaseModel):
    """Details of the person who performed the scan"""
    name: str
    email: str
    contact_number: str
    
class PatientDetails(BaseModel):
    """Details of the patient who was scanned"""
    patient_id: str
    name: str
    age: int
    gender: str
    contact_number: str
    email: str
    is_pregnant: bool = False  # NEW: From scan, not stored in patient record

class HemoglobinReportCreate(BaseModel):
    """
    INPUT model - what frontend sends when requesting report generation
    """
    reading_id: str = Field(..., description="ID of hemoglobin reading")
    is_pregnant: bool = Field(False, description="Is patient pregnant?")
    notes: Optional[str] = Field(None, description="Additional clinical notes")

class HemoglobinReportResponse(BaseModel):
    """
    OUTPUT model - complete report with all details
    """
    id: str = Field(alias="_id", default="")
    report_id: str = Field(alias="report_id")
    reading_id: str
    
    # Patient Information
    patient_details: PatientDetails
    
    # Scanner Information
    scanner_details: ScannerDetails
    
    # Hemoglobin Result
    hemoglobin_level: float
    is_anemic: bool
    status_text: str  # "Anemic" or "Normal"
    
    # Timestamps
    scan_timestamp: datetime
    report_generated_at: datetime
    
    # PDF Path (after generation)
    pdf_url: Optional[str] = None
    
    class Config:
        populate_by_name = True

"""WHY SEPARATE SCANNER AND PATIENT DETAILS?
- Scanner = Owner who performed scan (from JWT token)
- Patient = Person being scanned (from patients collection)
- This is crucial for reports!"""
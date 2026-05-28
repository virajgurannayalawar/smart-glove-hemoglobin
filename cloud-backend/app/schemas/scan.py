from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ScanSessionCreate(BaseModel):
    patient_id: str = Field(..., description="Patient being scanned")
    is_pregnant: bool = Field(False, description="Pregnancy status for this scan only")


class ScanSessionResponse(BaseModel):
    scan_id: str
    owner_id: str
    patient_id: str
    is_pregnant: bool
    status: str = Field(..., description="pending|completed|expired")
    created_at: datetime
    expires_at: datetime


class ScanResultResponse(BaseModel):
    scan_id: str
    status: str = Field(..., description="pending|completed|expired")
    hemoglobin_level: Optional[float] = None
    is_anemic: Optional[bool] = None
    status_text: Optional[str] = None
    reading_id: Optional[str] = None
    true_timestamp: Optional[str] = None
    image_url: Optional[str] = None
    error: Optional[str] = None


class GloveUploadMetadata(BaseModel):
    owner_id: str = Field(..., description="Owner ID provisioned to glove")
    patient_id: str = Field(..., description="Which patient was scanned")
    capture_timestamp: int = Field(..., description="Unix timestamp when image was captured on glove")
    sync_timestamp: int = Field(..., description="Unix timestamp when glove started sync")
    is_pregnant: bool = Field(False, description="Pregnancy status for this scan only")

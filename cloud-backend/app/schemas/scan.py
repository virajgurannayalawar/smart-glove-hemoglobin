from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ScanSessionCreate(BaseModel):
    PatientId: str = Field(..., description="Patient being scanned")
    IsPregnant: bool = Field(False, description="Pregnancy status for this scan only")


class ScanSessionResponse(BaseModel):
    ScanId: str
    OwnerId: str
    PatientId: str
    IsPregnant: bool
    Status: str = Field(..., description="pending|completed|expired")
    CreatedAt: datetime
    ExpiresAt: datetime


class ScanResultResponse(BaseModel):
    ScanId: str
    Status: str = Field(..., description="pending|completed|expired")
    HemoglobinLevel: Optional[float] = None
    IsAnemic: Optional[bool] = None
    StatusText: Optional[str] = None
    ReadingId: Optional[str] = None
    TrueTimestamp: Optional[str] = None
    ImageUrl: Optional[str] = None
    Error: Optional[str] = None


class GloveUploadMetadata(BaseModel):
    OwnerId: str = Field(..., description="Owner ID provisioned to glove")
    PatientId: str = Field(..., description="Which patient was scanned")
    CaptureTimestamp: int = Field(..., description="Unix timestamp when image was captured on glove")
    SyncTimestamp: int = Field(..., description="Unix timestamp when glove started sync")
    IsPregnant: bool = Field(False, description="Pregnancy status for this scan only")

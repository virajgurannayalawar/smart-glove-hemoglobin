from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UploadMetadata(BaseModel):
    HemoglobinLevel: Optional[float] = Field(
        default=None,
        description="Optional hemoglobin level. Prefer backend model prediction in new workflow.",
    )
    CaptureTimestamp: int = Field(..., description="Unix timestamp when image was captured on edge device")
    SyncTimestamp: int = Field(..., description="Unix timestamp when the sync process started on edge device")
    PatientId: str = Field(..., description="Which patient was scanned")
    IsPregnant: bool = Field(False, description="Is patient pregnant for anemia calc?")

class HistoryResponse(BaseModel):
    id: str = Field(alias="_id", default="")
    readingId: Optional[str] = None
    patientId: Optional[str] = None
    date: datetime
    hemoglobinLevel: float
    isAnemic: bool
    statusText: str
    imageUrl: Optional[str] = None
    
    class Config:
        populate_by_name = True

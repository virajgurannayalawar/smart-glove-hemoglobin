from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UploadMetadata(BaseModel):
    hemoglobin_level: Optional[float] = Field(
        default=None,
        description="Optional hemoglobin level. Prefer backend model prediction in new workflow.",
    )
    capture_timestamp: int = Field(..., description="Unix timestamp when image was captured on edge device")
    sync_timestamp: int = Field(..., description="Unix timestamp when the sync process started on edge device")
    patient_id: str = Field(..., description="Which patient was scanned")
    is_pregnant: bool = Field(False, description="Is patient pregnant for anemia calc?")

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

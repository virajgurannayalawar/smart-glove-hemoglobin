from pydantic import BaseModel, Field
from datetime import datetime

class UploadMetadata(BaseModel):
    hemoglobin_level: float = Field(..., description="Pre-calculated hemoglobin level from edge device")
    capture_timestamp: int = Field(..., description="Unix timestamp when image was captured on edge device")
    sync_timestamp: int = Field(..., description="Unix timestamp when the sync process started on edge device")

class HistoryResponse(BaseModel):
    id: str = Field(alias="_id", default="")
    date: datetime
    hemoglobinLevel: float
    isAnemic: bool
    statusText: str
    
    class Config:
        populate_by_name = True

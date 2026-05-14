from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UploadMetadata(BaseModel):
    hemoglobin_level: float = Field(..., description="Pre-calculated hemoglobin level from edge device")
    capture_timestamp: int = Field(..., description="Unix timestamp when image was captured on edge device")
    sync_timestamp: int = Field(..., description="Unix timestamp when the sync process started on edge device")

class HistoryResponse(BaseModel):
    id: str = Field(alias="_id")
    patient_id: str
    true_timestamp: datetime
    hemoglobin_level: float
    image_url: str # This will be the S3 Presigned URL
    
    class Config:
        populate_by_name = True

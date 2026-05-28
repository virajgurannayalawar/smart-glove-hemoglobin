from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier (stable across reboots)")
    firmware_version: Optional[str] = None
    hardware: Optional[str] = None


class DeviceHeartbeatRequest(BaseModel):
    firmware_version: Optional[str] = None
    ip: Optional[str] = None
    wifi_ssid: Optional[str] = None


class DeviceResponse(BaseModel):
    id: str = Field(alias="_id", default="")
    device_id: str
    owner_id: str
    firmware_version: Optional[str] = None
    hardware: Optional[str] = None
    ip: Optional[str] = None
    wifi_ssid: Optional[str] = None
    last_seen: datetime
    created_at: datetime

    class Config:
        populate_by_name = True


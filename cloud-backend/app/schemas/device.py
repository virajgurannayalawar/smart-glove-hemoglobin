from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DeviceRegisterRequest(BaseModel):
    DeviceId: str = Field(..., description="Unique device identifier (stable across reboots)")
    FirmwareVersion: Optional[str] = None
    Hardware: Optional[str] = None


class DeviceHeartbeatRequest(BaseModel):
    FirmwareVersion: Optional[str] = None
    Ip: Optional[str] = None
    WifiSsid: Optional[str] = None


class DeviceResponse(BaseModel):
    Id: str = Field(alias="_id", default="")
    DeviceId: str
    OwnerId: str
    FirmwareVersion: Optional[str] = None
    Hardware: Optional[str] = None
    Ip: Optional[str] = None
    WifiSsid: Optional[str] = None
    LastSeen: datetime
    CreatedAt: datetime

    class Config:
        populate_by_name = True


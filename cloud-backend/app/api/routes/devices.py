from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import get_current_active_user
from app.schemas.device import DeviceHeartbeatRequest, DeviceRegisterRequest, DeviceResponse
from app.services.db import get_database
from app.utils.rate_limit import limiter


router = APIRouter()


@router.post("/register", response_model=DeviceResponse)
@limiter.limit("30/minute")
async def register_device(
    request: Request,
    payload: DeviceRegisterRequest,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    OwnerId = current_user["OwnerId"]
    now = datetime.now(timezone.utc)

    existing = await db.devices.find_one({"OwnerId": OwnerId, "DeviceId": payload.DeviceId})
    if existing:
        await db.devices.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "FirmwareVersion": payload.FirmwareVersion,
                    "Hardware": payload.Hardware,
                    "LastSeen": now,
                }
            },
        )
        updated = await db.devices.find_one({"_id": existing["_id"]})
        updated["_id"] = str(updated["_id"])
        return updated

    doc = {
        "OwnerId": OwnerId,
        "DeviceId": payload.DeviceId,
        "FirmwareVersion": payload.FirmwareVersion,
        "Hardware": payload.Hardware,
        "Ip": None,
        "WifiSsid": None,
        "LastSeen": now,
        "CreatedAt": now,
    }
    res = await db.devices.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc


@router.post("/{device_id}/heartbeat", response_model=DeviceResponse)
@limiter.limit("120/minute")
async def heartbeat(
    request: Request,
    device_id: str,
    payload: DeviceHeartbeatRequest,
    current_user: dict = Depends(get_current_active_user),
):
    db = get_database()
    OwnerId = current_user["OwnerId"]
    now = datetime.now(timezone.utc)

    device = await db.devices.find_one({"OwnerId": OwnerId, "DeviceId": device_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update = {
        "LastSeen": now,
        "FirmwareVersion": payload.FirmwareVersion or device.get("FirmwareVersion"),
        "Ip": payload.Ip or device.get("Ip"),
        "WifiSsid": payload.WifiSsid or device.get("WifiSsid"),
    }
    await db.devices.update_one({"_id": device["_id"]}, {"$set": update})
    updated = await db.devices.find_one({"_id": device["_id"]})
    updated["_id"] = str(updated["_id"])
    return updated


@router.get("", response_model=list[DeviceResponse])
async def list_devices(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    OwnerId = current_user["OwnerId"]
    cursor = db.devices.find({"OwnerId": OwnerId}).sort("LastSeen", -1)
    results: list[dict] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


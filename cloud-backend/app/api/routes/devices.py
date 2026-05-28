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
    owner_id = current_user["owner_id"]
    now = datetime.now(timezone.utc)

    existing = await db.devices.find_one({"owner_id": owner_id, "device_id": payload.device_id})
    if existing:
        await db.devices.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "firmware_version": payload.firmware_version,
                    "hardware": payload.hardware,
                    "last_seen": now,
                }
            },
        )
        updated = await db.devices.find_one({"_id": existing["_id"]})
        updated["_id"] = str(updated["_id"])
        return updated

    doc = {
        "owner_id": owner_id,
        "device_id": payload.device_id,
        "firmware_version": payload.firmware_version,
        "hardware": payload.hardware,
        "ip": None,
        "wifi_ssid": None,
        "last_seen": now,
        "created_at": now,
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
    owner_id = current_user["owner_id"]
    now = datetime.now(timezone.utc)

    device = await db.devices.find_one({"owner_id": owner_id, "device_id": device_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update = {
        "last_seen": now,
        "firmware_version": payload.firmware_version or device.get("firmware_version"),
        "ip": payload.ip or device.get("ip"),
        "wifi_ssid": payload.wifi_ssid or device.get("wifi_ssid"),
    }
    await db.devices.update_one({"_id": device["_id"]}, {"$set": update})
    updated = await db.devices.find_one({"_id": device["_id"]})
    updated["_id"] = str(updated["_id"])
    return updated


@router.get("", response_model=list[DeviceResponse])
async def list_devices(current_user: dict = Depends(get_current_active_user)):
    db = get_database()
    owner_id = current_user["owner_id"]
    cursor = db.devices.find({"owner_id": owner_id}).sort("last_seen", -1)
    results: list[dict] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


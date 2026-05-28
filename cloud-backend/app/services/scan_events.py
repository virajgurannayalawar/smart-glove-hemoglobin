from datetime import datetime, timezone
from typing import Any, Optional

from app.services.db import get_database


async def record_scan_event(
    *,
    scan_id: str,
    owner_id: str,
    patient_id: Optional[str],
    event: str,
    request_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    db = get_database()
    await db.scan_events.insert_one(
        {
            "scan_id": scan_id,
            "owner_id": owner_id,
            "patient_id": patient_id,
            "event": event,
            "request_id": request_id,
            "detail": detail or {},
            "created_at": datetime.now(timezone.utc),
        }
    )


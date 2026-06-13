from datetime import datetime, timezone
from typing import Any, Optional

from app.services.db import get_database


async def record_scan_event(
    *,
    ScanId: str,
    OwnerId: str,
    PatientId: Optional[str],
    event: str,
    request_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    db = get_database()
    await db.scan_events.insert_one(
        {
            "ScanId": ScanId,
            "OwnerId": OwnerId,
            "PatientId": PatientId,
            "Event": event,
            "RequestId": request_id,
            "Detail": detail or {},
            "CreatedAt": datetime.now(timezone.utc),
        }
    )


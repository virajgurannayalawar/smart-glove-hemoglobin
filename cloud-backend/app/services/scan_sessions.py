import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import uuid

from app.services.db import get_database


@dataclass
class ScanSession:
    scan_id: str
    owner_id: str
    patient_id: str
    is_pregnant: bool
    created_at: datetime
    expires_at: datetime
    status: str  # pending|completed|expired|failed
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    event: asyncio.Event


class ScanSessionStore:
    """
    MongoDB-backed scan session store (chunk-7).

    We keep an in-memory asyncio.Event per scan_id to quickly wake long-poll
    requests in the same process, while the source of truth is MongoDB.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._events: Dict[str, asyncio.Event] = {}

    async def _get_event(self, scan_id: str) -> asyncio.Event:
        async with self._lock:
            ev = self._events.get(scan_id)
            if ev is None:
                ev = asyncio.Event()
                self._events[scan_id] = ev
            return ev

    def _doc_to_session(self, doc: Dict[str, Any], event: asyncio.Event) -> ScanSession:
        return ScanSession(
            scan_id=doc["scan_id"],
            owner_id=doc["owner_id"],
            patient_id=doc["patient_id"],
            is_pregnant=bool(doc.get("is_pregnant", False)),
            created_at=doc["created_at"],
            expires_at=doc["expires_at"],
            status=doc.get("status", "pending"),
            result=doc.get("result"),
            error=doc.get("error"),
            event=event,
        )

    async def create_session(
        self,
        *,
        owner_id: str,
        patient_id: str,
        is_pregnant: bool,
        ttl_seconds: int = 120,
    ) -> ScanSession:
        db = get_database()
        now = datetime.now(timezone.utc)
        scan_id = str(uuid.uuid4())
        expires_at = now + timedelta(seconds=ttl_seconds)
        doc = {
            "scan_id": scan_id,
            "owner_id": owner_id,
            "patient_id": patient_id,
            "is_pregnant": bool(is_pregnant),
            "created_at": now,
            "expires_at": expires_at,
            "status": "pending",
            "result": None,
            "error": None,
        }
        await db.scan_sessions.insert_one(doc)
        event = await self._get_event(scan_id)
        return self._doc_to_session(doc, event)

    async def get(self, scan_id: str) -> Optional[ScanSession]:
        db = get_database()
        doc = await db.scan_sessions.find_one({"scan_id": scan_id})
        if not doc:
            return None
        event = await self._get_event(scan_id)
        return self._doc_to_session(doc, event)

    async def expire_if_needed(self, scan_id: str) -> Optional[ScanSession]:
        db = get_database()
        now = datetime.now(timezone.utc)
        await db.scan_sessions.update_one(
            {"scan_id": scan_id, "status": "pending", "expires_at": {"$lte": now}},
            {"$set": {"status": "expired"}},
        )
        session = await self.get(scan_id)
        if session and session.status in ("expired", "completed", "failed"):
            session.event.set()
        return session

    async def complete(self, scan_id: str, result: Dict[str, Any]) -> Optional[ScanSession]:
        db = get_database()
        await db.scan_sessions.update_one(
            {"scan_id": scan_id, "status": "pending"},
            {"$set": {"status": "completed", "result": result, "error": None}},
        )
        session = await self.get(scan_id)
        if session:
            session.event.set()
        return session

    async def fail(self, scan_id: str, error: str) -> Optional[ScanSession]:
        db = get_database()
        await db.scan_sessions.update_one(
            {"scan_id": scan_id, "status": "pending"},
            {"$set": {"status": "failed", "error": error}},
        )
        session = await self.get(scan_id)
        if session:
            session.event.set()
        return session


scan_session_store = ScanSessionStore()

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import uuid

from app.services.db import get_database


@dataclass
class ScanSession:
    ScanId: str
    OwnerId: str
    PatientId: str
    IsPregnant: bool
    CreatedAt: datetime
    ExpiresAt: datetime
    Status: str  # pending|completed|expired|failed
    Result: Optional[Dict[str, Any]]
    Error: Optional[str]
    Event: asyncio.Event


class ScanSessionStore:
    """
    MongoDB-backed scan session store (chunk-7).

    We keep an in-memory asyncio.Event per ScanId to quickly wake long-poll
    requests in the same process, while the source of truth is MongoDB.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._events: Dict[str, asyncio.Event] = {}

    async def _get_event(self, ScanId: str) -> asyncio.Event:
        async with self._lock:
            ev = self._events.get(ScanId)
            if ev is None:
                ev = asyncio.Event()
                self._events[ScanId] = ev
            return ev

    def _doc_to_session(self, doc: Dict[str, Any], event: asyncio.Event) -> ScanSession:
        return ScanSession(
            ScanId=doc["ScanId"],
            OwnerId=doc["OwnerId"],
            PatientId=doc["PatientId"],
            IsPregnant=bool(doc.get("IsPregnant", False)),
            CreatedAt=doc["CreatedAt"],
            ExpiresAt=doc["ExpiresAt"],
            Status=doc.get("Status", "pending"),
            Result=doc.get("Result"),
            Error=doc.get("Error"),
            Event=event,
        )

    async def create_session(
        self,
        *,
        OwnerId: str,
        PatientId: str,
        is_pregnant: bool,
        ttl_seconds: int = 120,
    ) -> ScanSession:
        db = get_database()
        now = datetime.now(timezone.utc)
        ScanId = str(uuid.uuid4())
        expires_at = now + timedelta(seconds=ttl_seconds)
        doc = {
            "ScanId": ScanId,
            "OwnerId": OwnerId,
            "PatientId": PatientId,
            "IsPregnant": bool(is_pregnant),
            "CreatedAt": now,
            "ExpiresAt": expires_at,
            "Status": "pending",
            "Result": None,
            "Error": None,
        }
        await db.scan_sessions.insert_one(doc)
        event = await self._get_event(ScanId)
        return self._doc_to_session(doc, event)

    async def get(self, ScanId: str) -> Optional[ScanSession]:
        db = get_database()
        doc = await db.scan_sessions.find_one({"ScanId": ScanId})
        if not doc:
            return None
        event = await self._get_event(ScanId)
        return self._doc_to_session(doc, event)

    async def expire_if_needed(self, ScanId: str) -> Optional[ScanSession]:
        db = get_database()
        now = datetime.now(timezone.utc)
        await db.scan_sessions.update_one(
            {"ScanId": ScanId, "Status": "pending", "ExpiresAt": {"$lte": now}},
            {"$set": {"Status": "expired"}},
        )
        session = await self.get(ScanId)
        if session and session.Status in ("expired", "completed", "failed"):
            session.Event.set()
        return session

    async def complete(self, ScanId: str, result: Dict[str, Any]) -> Optional[ScanSession]:
        db = get_database()
        await db.scan_sessions.update_one(
            {"ScanId": ScanId, "Status": "pending"},
            {"$set": {"Status": "completed", "Result": result, "Error": None}},
        )
        session = await self.get(ScanId)
        if session:
            session.Event.set()
        return session

    async def fail(self, ScanId: str, error: str) -> Optional[ScanSession]:
        db = get_database()
        await db.scan_sessions.update_one(
            {"ScanId": ScanId, "Status": "pending"},
            {"$set": {"Status": "failed", "Error": error}},
        )
        session = await self.get(ScanId)
        if session:
            session.Event.set()
        return session


scan_session_store = ScanSessionStore()

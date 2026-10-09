"""
Audit service with hash-chained immutable log.

Provides tamper-evident audit trail for all validation and
self-assessment events. Uses SHA-256 hash chaining.
Persisted to SQLite for durability across restarts.
"""
from __future__ import annotations

import hashlib
import json
import structlog
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory
from app.db.models import AuditEntryModel
from app.models.disease import AuditEntry, AuditTrail

logger = structlog.get_logger()


class AuditService:
    """Immutable audit log with hash chaining, persisted to SQLite."""

    def __init__(self):
        self._cache: Dict[str, List[AuditEntry]] = {}

    @staticmethod
    def _compute_hash(entry: AuditEntry, previous_hash: str = "") -> str:
        """Compute SHA-256 hash for an audit entry, chained to previous."""
        data = {
            "timestamp": entry.timestamp,
            "type": entry.type,
            "user": entry.user,
            "data": entry.data,
            "previous_hash": previous_hash,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    async def add_entry(
        self,
        session_id: str,
        entry_type: str,
        user: str,
        data: dict,
    ) -> AuditEntry:
        """Add an entry to the audit log with hash chaining, persisted to SQLite."""
        from app.db.database import _ensure_tables
        await _ensure_tables()
        async with async_session_factory() as db:
            # Get previous hash from DB
            result = await db.execute(
                select(AuditEntryModel)
                .where(AuditEntryModel.session_id == session_id)
                .order_by(AuditEntryModel.id.desc())
                .limit(1)
            )
            prev_entry = result.scalar_one_or_none()
            previous_hash = prev_entry.hash if prev_entry else ""

            entry = AuditEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                type=entry_type,
                user=user,
                data=data,
                hash="",
            )
            entry.hash = self._compute_hash(entry, previous_hash)

            # Persist to SQLite
            db_entry = AuditEntryModel(
                session_id=session_id,
                timestamp=entry.timestamp,
                type=entry_type,
                user=user,
                data=data,
                hash=entry.hash,
                previous_hash=previous_hash,
            )
            db.add(db_entry)
            await db.commit()

            # Update cache
            if session_id not in self._cache:
                self._cache[session_id] = []
            self._cache[session_id].append(entry)

            logger.info("audit_entry_added", session_id=session_id, type=entry_type, user=user)
            return entry

    async def get_trail(self, session_id: str) -> Optional[AuditTrail]:
        """Get audit trail for a session from SQLite."""
        # Check cache first
        if session_id in self._cache:
            return AuditTrail(session_id=session_id, entries=self._cache[session_id])

        # Load from DB
        async with async_session_factory() as db:
            result = await db.execute(
                select(AuditEntryModel)
                .where(AuditEntryModel.session_id == session_id)
                .order_by(AuditEntryModel.id.asc())
            )
            entries = []
            for row in result.scalars():
                entry = AuditEntry(
                    timestamp=row.timestamp,
                    type=row.type,
                    user=row.user,
                    data=row.data,
                    hash=row.hash,
                )
                entries.append(entry)

            if not entries:
                return None

            # Populate cache
            self._cache[session_id] = entries
            return AuditTrail(session_id=session_id, entries=entries)

    async def verify(self, session_id: str) -> Dict[str, Any]:
        """Verify the integrity of an audit trail."""
        trail = await self.get_trail(session_id)
        if trail is None:
            return {"session_id": session_id, "valid": False, "message": "Session not found"}

        entries = trail.entries
        previous_hash = ""
        for i, entry in enumerate(entries):
            expected_hash = self._compute_hash(entry, previous_hash)
            if entry.hash != expected_hash:
                return {
                    "session_id": session_id,
                    "valid": False,
                    "failed_at_index": i,
                    "message": f"Hash mismatch at entry {i}",
                }
            previous_hash = entry.hash

        return {
            "session_id": session_id,
            "valid": True,
            "entry_count": len(entries),
            "message": "Audit trail integrity verified",
        }

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs from SQLite."""
        async with async_session_factory() as db:
            result = await db.execute(
                select(AuditEntryModel.session_id).distinct()
            )
            return [row[0] for row in result]

    def clear(self):
        """Clear all audit logs from cache (testing only)."""
        self._cache.clear()
        logger.warning("audit_log_cache_cleared")


_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Module-level singleton."""
    global _service
    if _service is None:
        _service = AuditService()
    return _service

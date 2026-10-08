"""
Audit service with hash-chained immutable log.

Provides tamper-evident audit trail for all validation and
self-assessment events. Uses SHA-256 hash chaining.
"""
from __future__ import annotations

import hashlib
import json
import structlog
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.models.disease import AuditEntry, AuditTrail

logger = structlog.get_logger()


class AuditService:
    """Immutable audit log with hash chaining."""

    def __init__(self):
        self._audit_log: Dict[str, List[AuditEntry]] = {}

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

    def add_entry(
        self,
        session_id: str,
        entry_type: str,
        user: str,
        data: dict,
    ) -> AuditEntry:
        """Add an entry to the audit log with hash chaining."""
        if session_id not in self._audit_log:
            self._audit_log[session_id] = []

        previous_hash = self._audit_log[session_id][-1].hash if self._audit_log[session_id] else ""

        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            type=entry_type,
            user=user,
            data=data,
            hash="",
        )
        entry.hash = self._compute_hash(entry, previous_hash)
        self._audit_log[session_id].append(entry)
        return entry

    def get_trail(self, session_id: str) -> Optional[AuditTrail]:
        """Get audit trail for a session."""
        if session_id not in self._audit_log:
            return None
        return AuditTrail(session_id=session_id, entries=self._audit_log[session_id])

    def verify(self, session_id: str) -> Dict[str, Any]:
        """Verify the integrity of an audit trail."""
        if session_id not in self._audit_log:
            return {"session_id": session_id, "valid": False, "message": "Session not found"}

        entries = self._audit_log[session_id]
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

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        return list(self._audit_log.keys())

    def clear(self):
        """Clear all audit logs (testing only)."""
        self._audit_log.clear()
        logger.warning("audit_log_cleared")


_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Module-level singleton."""
    global _service
    if _service is None:
        _service = AuditService()
    return _service

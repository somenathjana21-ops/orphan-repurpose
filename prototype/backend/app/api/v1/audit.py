from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
import structlog
import hashlib
import json
import uuid
from app.models.disease import AuditEntry, AuditTrail

logger = structlog.get_logger()
router = APIRouter()

# Shared in-memory audit log (same as validation.py — prototype only)
_audit_log: dict[str, List[AuditEntry]] = {}


def _compute_hash(entry: AuditEntry, previous_hash: str = "") -> str:
    """Compute hash for an audit entry, chaining to previous entry."""
    data = {
        "timestamp": entry.timestamp,
        "type": entry.type,
        "user": entry.user,
        "data": entry.data,
        "previous_hash": previous_hash,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _add_entry(session_id: str, entry_type: str, user: str, data: dict) -> AuditEntry:
    """Add an entry to the audit log with hash chaining."""
    if session_id not in _audit_log:
        _audit_log[session_id] = []
    
    previous_hash = _audit_log[session_id][-1].hash if _audit_log[session_id] else ""
    
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        type=entry_type,
        user=user,
        data=data,
        hash="",
    )
    entry.hash = _compute_hash(entry, previous_hash)
    _audit_log[session_id].append(entry)
    return entry


@router.get("/{session_id}", response_model=AuditTrail)
async def get_audit_trail(session_id: str):
    """Get audit trail for a session."""
    try:
        if session_id not in _audit_log:
            raise HTTPException(status_code=404, detail=f"Audit trail for session {session_id} not found")
        return AuditTrail(session_id=session_id, entries=_audit_log[session_id])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_trail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")


@router.get("/{session_id}/verify")
async def verify_audit_trail(session_id: str):
    """Verify the integrity of an audit trail by checking hash chain."""
    try:
        if session_id not in _audit_log:
            raise HTTPException(status_code=404, detail=f"Audit trail for session {session_id} not found")
        
        entries = _audit_log[session_id]
        previous_hash = ""
        for i, entry in enumerate(entries):
            expected_hash = _compute_hash(entry, previous_hash)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_verification_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to verify audit trail")


@router.post("/log")
async def log_event(session_id: str, entry_type: str, user: str, data: dict):
    """Log an event to the audit trail."""
    try:
        entry = _add_entry(session_id, entry_type, user, data)
        return {"session_id": session_id, "entry": entry}
    except Exception as e:
        logger.error("audit_log_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to log event")

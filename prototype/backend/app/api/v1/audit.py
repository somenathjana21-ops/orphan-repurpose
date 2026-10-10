from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException

from app.models.disease import AuditTrail
from app.services.audit_service import get_audit_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/sessions")
async def list_sessions() -> dict[str, list[str]]:
    """List all audit session IDs."""
    try:
        svc = get_audit_service()
        return {"sessions": await svc.get_all_sessions()}
    except Exception as e:
        logger.error("audit_list_sessions_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list sessions") from e


@router.get("/{session_id}", response_model=AuditTrail)
async def get_audit_trail(session_id: str):
    """Get audit trail for a session."""
    try:
        svc = get_audit_service()
        trail = await svc.get_trail(session_id)
        if trail is None:
            raise HTTPException(
                status_code=404, detail=f"Audit trail for session {session_id} not found"
            )
        return trail
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_trail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail") from e


@router.get("/{session_id}/verify")
async def verify_audit_trail(session_id: str):
    """Verify the integrity of an audit trail by checking hash chain."""
    try:
        svc = get_audit_service()
        result = await svc.verify(session_id)
        if not result.get("valid") and result.get("message") == "Session not found":
            raise HTTPException(
                status_code=404, detail=f"Audit trail for session {session_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_verification_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to verify audit trail") from e


@router.post("/log")
async def log_event(session_id: str, entry_type: str, user: str, data: dict):
    """Log an event to the audit trail."""
    try:
        svc = get_audit_service()
        entry = await svc.add_entry(session_id, entry_type, user, data)
        return {"session_id": session_id, "entry": entry}
    except Exception as e:
        logger.error("audit_log_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to log event") from e

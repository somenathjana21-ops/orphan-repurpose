from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
import structlog
import uuid
from app.models.disease import ValidationRequest, SelfAssessmentRequest, AuditEntry, AuditTrail
from app.services.audit_service import get_audit_service

logger = structlog.get_logger()
router = APIRouter()


@router.post("/candidates/{candidate_id}/validate")
async def validate_candidate(candidate_id: str, request: ValidationRequest):
    """Record expert validation of a candidate."""
    try:
        session_id = str(uuid.uuid4())
        svc = get_audit_service()
        entry = svc.add_entry(
            session_id=session_id,
            entry_type="validation",
            user=request.validator,
            data={
                "candidate_id": candidate_id,
                "assessment": request.assessment,
                "rationale": request.rationale,
            },
        )
        logger.info("validation_recorded", candidate_id=candidate_id, validator=request.validator)
        return {
            "candidate_id": candidate_id,
            "session_id": session_id,
            "entry": entry,
            "message": "Validation recorded successfully",
        }
    except Exception as e:
        logger.error("validation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to record validation")


@router.post("/candidates/{candidate_id}/assess")
async def self_assess_candidate(candidate_id: str, request: SelfAssessmentRequest):
    """Record self-assessment of a candidate."""
    try:
        session_id = str(uuid.uuid4())
        svc = get_audit_service()
        entry = svc.add_entry(
            session_id=session_id,
            entry_type="self_assessment",
            user="self",
            data={
                "candidate_id": candidate_id,
                "efficacy": request.efficacy,
                "safety": request.safety,
                "feasibility": request.feasibility,
                "notes": request.notes,
            },
        )
        logger.info("self_assessment_recorded", candidate_id=candidate_id)
        return {
            "candidate_id": candidate_id,
            "session_id": session_id,
            "entry": entry,
            "message": "Self-assessment recorded successfully",
        }
    except Exception as e:
        logger.error("self_assessment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to record self-assessment")


@router.get("/{session_id}", response_model=AuditTrail)
async def get_audit_trail(session_id: str):
    """Get audit trail for a session."""
    try:
        svc = get_audit_service()
        trail = svc.get_trail(session_id)
        if trail is None:
            raise HTTPException(status_code=404, detail=f"Audit trail for session {session_id} not found")
        return trail
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_trail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")


@router.get("/{session_id}/verify")
async def verify_audit_trail(session_id: str):
    """Verify the integrity of an audit trail by checking hash chain."""
    try:
        svc = get_audit_service()
        result = svc.verify(session_id)
        if not result.get("valid") and result.get("message") == "Session not found":
            raise HTTPException(status_code=404, detail=f"Audit trail for session {session_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_verification_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to verify audit trail")

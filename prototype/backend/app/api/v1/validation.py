from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
import structlog
import hashlib
import json
import uuid
from app.models.disease import ValidationRequest, SelfAssessmentRequest, AuditEntry, AuditTrail
from app.api.v1.audit import _audit_log, _add_entry

logger = structlog.get_logger()
router = APIRouter()


@router.post("/candidates/{candidate_id}/validate")
async def validate_candidate(candidate_id: str, request: ValidationRequest):
    """Record expert validation of a candidate."""
    try:
        session_id = str(uuid.uuid4())
        entry = _add_entry(
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
        entry = _add_entry(
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

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException

from app.db.database import async_session_factory
from app.db.models import SelfAssessmentModel, ValidationModel
from app.models.disease import AuditTrail, SelfAssessmentRequest, ValidationRequest
from app.services.audit_service import get_audit_service

logger = structlog.get_logger()
router = APIRouter()


@router.post("/candidates/{candidate_id}/validate")
async def validate_candidate(candidate_id: str, request: ValidationRequest):
    """Record expert validation of a candidate."""
    try:
        session_id = str(uuid.uuid4())
        svc = get_audit_service()
        entry = await svc.add_entry(
            session_id=session_id,
            entry_type="validation",
            user=request.validator,
            data={
                "candidate_id": candidate_id,
                "assessment": request.assessment,
                "rationale": request.rationale,
            },
        )

        # Also store in validations table
        from app.db.database import _ensure_tables

        await _ensure_tables()
        async with async_session_factory() as db:
            validation = ValidationModel(
                candidate_id=candidate_id,
                validator=request.validator,
                assessment=request.assessment,
                rationale=request.rationale,
                session_id=session_id,
            )
            db.add(validation)
            await db.commit()

        logger.info("validation_recorded", candidate_id=candidate_id, validator=request.validator)
        return {
            "candidate_id": candidate_id,
            "session_id": session_id,
            "entry": entry,
            "message": "Validation recorded successfully",
        }
    except Exception as e:
        logger.error("validation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to record validation") from e


@router.post("/candidates/{candidate_id}/assess")
async def self_assess_candidate(candidate_id: str, request: SelfAssessmentRequest):
    """Record self-assessment of a candidate."""
    try:
        session_id = str(uuid.uuid4())
        svc = get_audit_service()
        entry = await svc.add_entry(
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

        # Also store in self_assessments table
        from app.db.database import _ensure_tables

        await _ensure_tables()
        async with async_session_factory() as db:
            assessment = SelfAssessmentModel(
                candidate_id=candidate_id,
                efficacy=request.efficacy,
                safety=request.safety,
                feasibility=request.feasibility,
                notes=request.notes,
                session_id=session_id,
            )
            db.add(assessment)
            await db.commit()

        logger.info("self_assessment_recorded", candidate_id=candidate_id)
        return {
            "candidate_id": candidate_id,
            "session_id": session_id,
            "entry": entry,
            "message": "Self-assessment recorded successfully",
        }
    except Exception as e:
        logger.error("self_assessment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to record self-assessment") from e


@router.get("/sessions")
async def list_sessions() -> dict[str, list[str]]:
    """List all audit session IDs."""
    try:
        svc = get_audit_service()
        sessions = await svc.get_all_sessions()
        return {"sessions": sessions}
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

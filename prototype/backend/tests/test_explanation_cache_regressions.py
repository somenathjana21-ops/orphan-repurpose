"""Explanation cache entries must match the complete prediction context."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.services.explanation_service import ExplanationService


@pytest.mark.parametrize(
    "field,value",
    [
        ("probability", 0.2),
        ("drug_name", "Updated drug"),
        ("disease_name", "Updated disease"),
        ("moa_summary", "Updated mechanism"),
    ],
)
def test_context_changes_refresh_explanation(field, value):
    service = ExplanationService()
    service._explainer = Mock()
    service._explainer.explain.side_effect = [{"llm_rationale": "old"}, {"llm_rationale": "new"}]
    context = {
        "drug_id": "drug:1",
        "disease_id": "ORPHA:646",
        "drug_name": "Drug",
        "disease_name": "NPC",
        "probability": 0.8,
        "moa_summary": "Mechanism",
    }
    assert service.explain_candidate(**context)["llm_rationale"] == "old"
    context[field] = value
    assert service.explain_candidate(**context)["llm_rationale"] == "new"
    assert service.explain_candidate(**context)["llm_rationale"] == "new"
    assert service._explainer.explain.call_count == 2
    assert service.get_cached("drug:1", "ORPHA:646")["llm_rationale"] == "new"
    service.clear_cache()
    assert service.get_cached("drug:1", "ORPHA:646") is None


def test_refresh_failure_does_not_leave_previous_prediction_cached():
    service = ExplanationService()
    service._explainer = Mock()
    service._explainer.explain.side_effect = [{"llm_rationale": "old"}, RuntimeError("unavailable")]
    args = ("drug:1", "ORPHA:646", "Drug", "NPC")
    service.explain_candidate(*args, 0.8, "Mechanism")
    refreshed = service.explain_candidate(*args, 0.2, "New mechanism")
    assert "20%" in refreshed["llm_rationale"]
    assert "New mechanism" in refreshed["llm_rationale"]
    assert service.get_cached("drug:1", "ORPHA:646") is None

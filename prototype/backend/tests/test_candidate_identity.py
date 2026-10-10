"""Candidate identifiers must preserve disease and drug identity."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import database
from app.services import indication_service
from app.services.dossier_service import DossierService


@pytest.fixture
async def candidate_db(tmp_path, monkeypatch):
    """Keep generated candidates out of the application's database."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'candidates.db'}")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "async_session_factory", async_sessionmaker(engine))
    monkeypatch.setattr(database, "_tables_created", False)
    try:
        yield
    finally:
        await engine.dispose()


@pytest.mark.parametrize("other_disease", ["ORPHA:793", "ORPHA:98065"])
async def test_generating_another_disease_preserves_candidate(
    candidate_db, monkeypatch, async_client, other_disease
):
    service = Mock()
    service.is_ready.return_value = False
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)

    first = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"}
    )
    second = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": other_disease}
    )
    assert first.status_code == second.status_code == 200
    candidate = first.json()["candidates"][0]
    other = second.json()["candidates"][0]
    assert candidate["candidate_id"] != other["candidate_id"]
    detail = await async_client.get(f"/api/v1/candidates/{candidate['candidate_id']}")
    assert detail.status_code == 200
    assert detail.json()["drug_id"] == candidate["drug_id"]
    assert detail.json()["indication_probability"] == candidate["indication_probability"]


async def test_ranking_changes_preserve_drug_identity(candidate_db, monkeypatch, async_client):
    service = Mock()
    service.is_ready.return_value = True
    scores = [
        {"drug_id": "drugcentral:1001", "probability": 0.8, "ci_lower": 0.7, "ci_upper": 0.9},
        {"drug_id": "drugcentral:1002", "probability": 0.6, "ci_lower": 0.5, "ci_upper": 0.7},
    ]
    service.score_all_for_orpha.side_effect = [scores, list(reversed(scores))]
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    first = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"}
    )
    second = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"}
    )
    assert first.status_code == second.status_code == 200
    first_ids = {c["drug_id"]: c["candidate_id"] for c in first.json()["candidates"]}
    second_ids = {c["drug_id"]: c["candidate_id"] for c in second.json()["candidates"]}
    assert first_ids == second_ids


@pytest.mark.parametrize("selection", ["candidate_id", "drug_id"])
@pytest.mark.parametrize("model_ready", [False, True])
async def test_dossier_keeps_selected_candidates(
    candidate_db, monkeypatch, async_client, selection, model_ready
):
    service = Mock()
    service.is_ready.return_value = model_ready
    service.score_all_for_orpha.return_value = [
        {"drug_id": "drugcentral:1001", "probability": 0.8, "ci_lower": 0.7, "ci_upper": 0.9}
    ]
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    monkeypatch.setattr(DossierService, "_html_to_pdf", lambda self, html: b"%PDF-test")
    generated = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"}
    )
    candidate = generated.json()["candidates"][0]
    response = await async_client.post(
        "/api/v1/dossier/generate",
        json={
            "disease_id": "ORPHA:635",
            "candidate_ids": [candidate[selection]],
            "include_sections": ["drug_profile"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["dossier_json"]["candidates"] == [candidate]
    if model_ready:
        service.score_all_for_orpha.assert_called_with("UMLS:C0028042", top_k=20)


async def test_dossier_rejects_unknown_candidate(candidate_db, monkeypatch, async_client):
    service = Mock()
    service.is_ready.return_value = False
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    response = await async_client.post(
        "/api/v1/dossier/generate",
        json={
            "disease_id": "ORPHA:635",
            "candidate_ids": ["unknown-candidate"],
            "include_sections": ["drug_profile"],
        },
    )
    assert response.status_code == 400
    assert "unknown-candidate" in response.json()["detail"]


async def test_candidate_details_preserve_generated_evidence(
    candidate_db, monkeypatch, async_client
):
    """Loading detail must retain safety flags and the generated explanation evidence."""
    service = Mock()
    service.is_ready.return_value = False
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    response = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"}
    )
    assert response.status_code == 200
    for candidate in response.json()["candidates"]:
        detail = await async_client.get(f"/api/v1/candidates/{candidate['candidate_id']}")
        assert detail.status_code == 200
        assert detail.json() == candidate


async def test_candidate_explanation_uses_disease_context(candidate_db, monkeypatch, async_client):
    """An explanation must refer to the original candidate and its disease."""
    from app.services import explanation_service

    service = Mock()
    service.is_ready.return_value = False
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    explainer = Mock()
    explainer.explain_candidate.return_value = {
        "candidate_id": "internal-explanation-key", "kg_paths": [], "shap_values": {},
        "counterfactuals": [], "llm_rationale": "Test explanation",
    }
    monkeypatch.setattr(explanation_service, "get_explanation_service", lambda: explainer)
    response = await async_client.post(
        "/api/v1/candidates/generate", json={"disease_id": "ORPHA:793"}
    )
    candidate = response.json()["candidates"][0]
    explanation = await async_client.get(
        f"/api/v1/candidates/{candidate['candidate_id']}/explanation"
    )
    assert explanation.status_code == 200
    assert explainer.explain_candidate.call_args.kwargs["disease_id"] == "ORPHA:793"
    assert explainer.explain_candidate.call_args.kwargs["disease_name"] == "SAPHO syndrome"
    assert explanation.json()["candidate_id"] == candidate["candidate_id"]

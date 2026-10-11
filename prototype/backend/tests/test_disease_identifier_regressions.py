"""Verified Orphanet identifiers must agree across fallback data and model queries."""

from __future__ import annotations

import runpy
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.v1 import candidates, diseases
from app.services import indication_service


@pytest.mark.parametrize(
    "orpha_id,name,cui",
    [
        ("ORPHA:646", "Niemann-Pick disease type C", "UMLS:C0220756"),
        ("ORPHA:586", "Cystic fibrosis", "UMLS:C0010674"),
        ("ORPHA:399", "Huntington disease", "UMLS:C0020179"),
        ("ORPHA:355", "Gaucher disease", "UMLS:C0017205"),
        ("ORPHA:805", "Tuberous sclerosis complex", "UMLS:C0041341"),
    ],
)
def test_model_mapping_uses_verified_identifiers(orpha_id, name, cui):
    assert candidates.ORPHA_TO_UMLS[orpha_id] == cui
    assert diseases.ORPHA_TO_UMLS[orpha_id] == cui
    fallback = next((d for d in diseases._FALLBACK_DISEASES if d["name"] == name), None)
    if fallback:
        assert fallback["id"] == orpha_id
        assert f"UMLS:{fallback['umls_cui']}" == cui


@pytest.mark.parametrize("orpha_id", ["ORPHA:635", "ORPHA:793"])
async def test_unrelated_diseases_do_not_receive_npc_or_cf_demo_candidates(
    orpha_id, monkeypatch, async_client
):
    service = Mock()
    service.is_ready.return_value = False
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": orpha_id})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "orpha_id,name,cui",
    [
        ("ORPHA:646", "Niemann-Pick disease type C", "UMLS:C0220756"),
        ("ORPHA:586", "Cystic fibrosis", "UMLS:C0010674"),
        ("ORPHA:399", "Huntington disease", "UMLS:C0020179"),
    ],
)
async def test_generation_and_disease_detail_agree(orpha_id, name, cui, monkeypatch, async_client):
    service = Mock()
    service.is_ready.return_value = True
    service.score_all_for_orpha.return_value = []
    monkeypatch.setattr(indication_service, "get_indication_service", lambda: service)
    monkeypatch.setattr(candidates, "_store_candidates", AsyncMock())
    response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": orpha_id})
    assert response.status_code == 200
    assert all(c["disease_id"] == orpha_id for c in response.json()["candidates"])
    service.score_all_for_orpha.assert_called_once_with(cui, top_k=20)
    detail = await async_client.get(f"/api/v1/diseases/{orpha_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == name


def test_generated_demo_disease_keys_are_unique_and_preserve_concepts():
    script = Path(__file__).resolve().parents[2] / "scripts/etl/generate_demo_data.py"
    data = runpy.run_path(str(script))
    records = data["DISEASES"]
    by_id = {row[0]: row for row in records}
    assert len(by_id) == len(records)
    assert by_id["ORPHA:586"][1] == "Cystic fibrosis"
    assert by_id["ORPHA:586"][7] == "C0010674"
    assert by_id["ORPHA:906"][1] == "Wiskott-Aldrich syndrome"
    assert by_id["ORPHA:906"][7] == "C0043194"
    assert ("1003", "ORPHA:586") in data["INDICATIONS"]
    assert ("1106", "ORPHA:906") in data["INDICATIONS"]

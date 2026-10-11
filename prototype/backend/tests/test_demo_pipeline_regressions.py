"""The command-line demo must run asynchronous services in both model modes."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pytest

from app.api.v1.diseases import _DISEASE_BY_ID, _FALLBACK_DISEASES
from app.core.config import settings
from app.services import (
    audit_service,
    dossier_service,
    explanation_service,
    indication_service,
    safety_service,
)


@pytest.mark.parametrize("model_ready", [False, True])
async def test_demo_awaits_services_and_runs_without_artifacts(
    model_ready, monkeypatch, tmp_path, capsys
):
    path = Path(__file__).resolve().parents[2] / "scripts" / "demo_npc.py"
    spec = importlib.util.spec_from_file_location("demo_npc", path)
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(demo, "backend_dir", tmp_path / "backend")
    processed_dir = tmp_path / "processed"
    drug_dir = processed_dir / "drugcentral"
    drug_dir.mkdir(parents=True)
    pd.DataFrame(
        [{"struct_id": "9001", "name": "Resolved drug name", "moa_classes": "Test"}]
    ).to_parquet(drug_dir / "drugcentral_fda_approved.parquet")
    monkeypatch.setattr(settings, "PROCESSED_DATA_DIR", str(processed_dir))
    monkeypatch.setitem(_DISEASE_BY_ID, "ORPHA:646", _FALLBACK_DISEASES[0])
    model = Mock(
        config={},
        drug_smiles={},
        disease_map={"UMLS:C0220756": 0},
        temperature=1.0,
        conformal_q=0.1,
    )
    model.is_ready.return_value = model_ready
    model.score_all_for_orpha.return_value = [
        {"drug_id": "drugcentral:9001", "probability": 0.8, "ci_lower": 0.7, "ci_upper": 0.9}
    ]
    safety = Mock()
    safety.assess_drug = AsyncMock(return_value={"overall": "caution"})
    explanation = Mock()
    explanation.explain_candidate.return_value = {}
    dossier = Mock()
    dossier.generate_dossier.return_value = {
        "pdf_base64": "",
        "audit_trail_id": "demo",
        "dossier_json": SimpleNamespace(sections={}),
    }
    audit = Mock()
    audit.add_entry = AsyncMock(return_value=SimpleNamespace(hash="test-hash"))
    audit.verify = AsyncMock(return_value={"valid": True, "entry_count": 2})
    for module, name, service in [
        (indication_service, "get_indication_service", model),
        (safety_service, "get_safety_service", safety),
        (explanation_service, "get_explanation_service", explanation),
        (dossier_service, "get_dossier_service", dossier),
        (audit_service, "get_audit_service", audit),
    ]:
        monkeypatch.setattr(module, name, lambda service=service: service)
    await demo.main()
    output = capsys.readouterr().out
    assert "ERROR" not in output
    assert "Demo Complete" in output
    safety.assess_drug.assert_awaited_once()
    assert audit.add_entry.await_count == 2
    exported_candidate = dossier.generate_dossier.call_args.kwargs["candidates"][0]
    expected_name = "Resolved drug name" if model_ready else "Miglustat"
    assert exported_candidate.drug_name == expected_name
    for call in audit.add_entry.await_args_list:
        assert call.kwargs["data"]["candidate_id"] == exported_candidate.candidate_id
    audit.verify.assert_awaited_once()
    if model_ready:
        model.score_all_for_orpha.assert_called_once_with("UMLS:C0220756", top_k=5)
    else:
        model.score_all_for_orpha.assert_not_called()
    assert not (tmp_path / "data" / "npc_dossier.pdf").exists()

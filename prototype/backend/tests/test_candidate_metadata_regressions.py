"""Candidate names must survive changes in the process working directory."""

from __future__ import annotations

import pandas as pd

from app.api.v1 import candidates
from app.core.config import settings


def test_metadata_loads_from_configured_processed_directory(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    drug_dir = processed_dir / "drugcentral"
    drug_dir.mkdir(parents=True)
    pd.DataFrame(
        [{"struct_id": "9001", "name": "Resolved drug", "moa_classes": "Test mechanism"}]
    ).to_parquet(drug_dir / "drugcentral_fda_approved.parquet")
    monkeypatch.setattr(settings, "PROCESSED_DATA_DIR", str(processed_dir))
    monkeypatch.chdir(tmp_path)
    meta = candidates._load_drug_meta()
    assert meta["drugcentral:9001"]["name"] == "Resolved drug"
    assert meta["drugcentral:9001"]["moa"] == "Test mechanism"


def test_candidate_preserves_resolved_name_when_metadata_is_missing(monkeypatch):
    monkeypatch.setattr(candidates, "_DRUG_META_LOADED", {})
    candidate = candidates._candidate_from_score(
        1,
        {
            "drug_id": "drugcentral:9001",
            "drug_name": "Resolved drug",
            "probability": 0.8,
            "ci_lower": 0.7,
            "ci_upper": 0.9,
        },
        "ORPHA:646",
    )
    assert candidate.drug_name == "Resolved drug"

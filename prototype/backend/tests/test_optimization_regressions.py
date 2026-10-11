"""Optimizations preserve model inputs and safety evidence while avoiding repeated work."""

from __future__ import annotations

import hashlib

import pytest
import torch

from app.ml.faers import merge_faers_reports
from app.ml.featurizer import ATOM_FEATURE_DIM, _hash_features
from app.services.safety_service import SafetyService


@pytest.mark.parametrize("smiles", ["", "CCO", "invalid-smiles", "未知"])
@pytest.mark.parametrize("max_atoms", [4, 16, 32])
def test_fallback_features_match_original_checkpoint_inputs(smiles, max_atoms):
    digest = hashlib.sha256(smiles.encode()).digest()
    n_atoms = 4 + (digest[0] % (max_atoms - 3))
    # Freeze the original scalar implementation to protect trained model inputs.
    expected = torch.zeros(n_atoms, ATOM_FEATURE_DIM)
    for i in range(n_atoms):
        for j in range(ATOM_FEATURE_DIM):
            expected[i, j] = digest[(i * ATOM_FEATURE_DIM + j) % len(digest)] / 255.0
    expected_edges = [[i, (i + 1) % n_atoms] for i in range(n_atoms)]
    expected_edges += [[i, (i + 2) % n_atoms] for i in range(0, n_atoms, 2)]

    features, edges = _hash_features(smiles, max_atoms)

    assert torch.equal(features, expected)
    assert torch.equal(edges, torch.tensor(expected_edges).t())
    assert features.dtype == expected.dtype


class CountingReports(list):
    """Count full report scans without relying on timing assertions."""

    scans = 0

    def __iter__(self):
        self.scans += 1
        return super().__iter__()


def test_safety_report_lookup_is_linear_and_preserves_first_matching_labels():
    service = SafetyService()
    reports = CountingReports(
        {"drug_id": drug, "event": f"event:{i}", "meddra_pt": f"{drug}:{repeat}:{i}"}
        for drug in ("other", "selected")
        for i in range(100)
        for repeat in range(3)
    )
    reports.extend({"drug_id": "selected", "event": "unlabelled"} for _ in range(3))
    reports.append({"drug_id": "selected", "event": "too-few", "meddra_pt": "skip"})
    reports.append({"drug_id": "selected"})
    tables = merge_faers_reports(reports)
    expected = [
        service.faers_analyzer.analyze(
            "selected",
            "Drug",
            event,
            "unlabelled" if event == "unlabelled" else f"selected:0:{event.split(':')[1]}",
            table,
        )
        for (drug, event), table in tables.items()
        if drug == "selected" and table.a >= service.faers_analyzer.min_reports
    ]
    expected.sort(key=lambda r: (r.level != "fail", r.level != "caution", -r.ror))
    reports.scans = 0

    actual = service._analyze_faers("selected", "Drug", reports=reports)

    assert actual == expected
    assert reports.scans <= 2

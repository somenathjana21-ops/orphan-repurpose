"""Performance changes preserve graph evidence and molecular/model outputs."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
import torch
from fastapi import HTTPException
from rdkit import Chem
from rdkit.Chem import MACCSkeys
from rdkit.Chem.rdMolDescriptors import GetMorganFingerprintAsBitVect

from app.api.v1 import kg
from app.ml.featurizer import ATOM_FEATURE_DIM, smiles_to_graph
from app.ml.indication_model import GraphSAGEDrugEncoder


def load_etl(name):
    path = Path(__file__).resolve().parents[2] / "scripts" / "etl" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("depth", [1, 3])
def test_subgraph_preserves_duplicate_symbols_and_first_edge_evidence(monkeypatch, depth):
    drug = {"id": "drug", "name": "Drug", "smiles": "CCO"}
    disease = {"id": "disease", "name": "Disease", "prevalence": 0.01}
    target = {"target_id": "target", "target_name": "Target", "gene": "GENE"}
    genes = [
        {"gene_id": "g1", "symbol": "GENE", "name": "First", "source": "curated"},
        {"gene_id": "g2", "symbol": "GENE", "name": "Second"},
        {"gene_id": "g3", "symbol": "OTHER", "name": "Unrelated"},
    ]
    execute = Mock(
        side_effect=[
            [drug],
            [disease],
            [{"evidence": "first", "confidence": 0.9}, {"evidence": "second"}],
            [target, {**target, "binding_value": 9}, {**target, "target_id": "empty", "gene": ""}],
            genes + [genes[0]],
            *([[]] if depth >= 3 else []),
        ]
    )
    monkeypatch.setattr(kg, "_get_kg_service", lambda: Mock(execute=execute))

    result = kg.get_subgraph("drug", "disease", max_depth=depth)

    assert execute.call_count == (6 if depth >= 3 else 5)
    nodes = {node["data"]["id"]: node["data"] for node in result["nodes"]}
    assert nodes["drug"]["smiles"] == "CCO"
    assert nodes["disease"]["prevalence"] == 0.01
    edges = [edge["data"] for edge in result["edges"]]
    assert len(edges) == 8
    assert edges[0]["evidence"] == "first"
    assert edges[0]["confidence"] == 0.9
    assert [(e["source"], e["target"]) for e in edges if e["label"] == "ASSOCIATED_WITH"] == [
        ("target", "g1"),
        ("target", "g2"),
    ]


@pytest.mark.parametrize("missing", ["drug", "disease"])
def test_subgraph_preserves_missing_entity_errors(monkeypatch, missing):
    execute = Mock(side_effect=[[]] if missing == "drug" else [[{"id": "drug"}], []])
    monkeypatch.setattr(kg, "_get_kg_service", lambda: Mock(execute=execute))
    with pytest.raises(HTTPException) as exc:
        kg.get_subgraph("drug", "disease", max_depth=1)
    assert exc.value.status_code == 404
    assert missing in exc.value.detail.lower()


@pytest.mark.parametrize("batch_size", [1, 3, 100])
def test_precomputation_matches_original_single_molecule_encoder(monkeypatch, batch_size):
    training = load_etl("train_indication_model_fast")
    drugs = dict(enumerate(["CCO", "C", "CCN", "CC", "invalid", "", "O"]))
    torch.manual_seed(42)
    encoder = GraphSAGEDrugEncoder(ATOM_FEATURE_DIM, hidden_dim=16, num_layers=2, dropout=0)
    encoder.eval()
    expected = {}
    with torch.no_grad():
        for did, smiles in drugs.items():
            features, edges = smiles_to_graph(smiles)
            expected[did] = encoder(features, edges).squeeze(0).numpy()

    sizes = []

    def create_encoder(**kwargs):
        model = GraphSAGEDrugEncoder(**kwargs)
        model.register_forward_pre_hook(lambda model, args: sizes.append(int(args[2].max()) + 1))
        return model

    monkeypatch.setattr(training, "GraphSAGEDrugEncoder", create_encoder)
    torch.manual_seed(42)
    actual = training.precompute_drug_embeddings(drugs, hidden_dim=16, batch_size=batch_size)

    assert list(actual) == list(expected)
    assert sizes == [min(batch_size, len(drugs) - i) for i in range(0, len(drugs), batch_size)]
    for did in drugs:
        np.testing.assert_allclose(actual[did], expected[did], rtol=1e-6, atol=1e-6)


@pytest.mark.parametrize("batch_size", [0, -1])
def test_precomputation_rejects_invalid_batch_size(batch_size):
    with pytest.raises(ValueError, match="positive"):
        load_etl("train_indication_model_fast").precompute_drug_embeddings(
            {}, batch_size=batch_size
        )


def test_empty_precomputation():
    assert load_etl("train_indication_model_fast").precompute_drug_embeddings({}) == {}


def test_molecular_pipeline_parses_once_and_preserves_features(monkeypatch):
    molecular = load_etl("compute_molecular_features")
    smiles_values = ["CCO", "c1ccccc1", "invalid", "", None, pd.NA, 42]
    frame = pd.DataFrame({"structure": smiles_values, "id": range(7)}, index=[8, 7, 6, 5, 4, 3, 2])
    expected_morgan, expected_maccs, expected_descriptors = [], [], []
    for smiles in smiles_values[:4]:
        mol = Chem.MolFromSmiles(smiles)
        morgan = np.zeros(1024, dtype=np.uint8)
        maccs = np.zeros(167, dtype=np.uint8)
        if mol is not None:
            morgan[list(GetMorganFingerprintAsBitVect(mol, 2, nBits=1024).GetOnBits())] = 1
            maccs[list(MACCSkeys.GenMACCSKeys(mol).GetOnBits())] = 1
        expected_morgan.append(morgan)
        expected_maccs.append(maccs)
        expected_descriptors.append(molecular.compute_rdkit_descriptors(smiles))
    parse = Mock(wraps=Chem.MolFromSmiles)
    monkeypatch.setattr(molecular.Chem, "MolFromSmiles", parse)

    result = molecular.compute_molecular_features(frame, smiles_col="structure", id_col="id")

    assert parse.call_count == 4
    assert result["valid_ids"] == [0, 1, 2, 3]
    assert result["valid_indices"] == [8, 7, 6, 5]
    np.testing.assert_array_equal(result["morgan"], np.stack(expected_morgan))
    np.testing.assert_array_equal(result["maccs"], np.stack(expected_maccs))
    assert result["morgan"].dtype == result["maccs"].dtype == np.uint8
    pd.testing.assert_frame_equal(result["descriptors"], pd.DataFrame(expected_descriptors))


def test_molecular_parse_failure_preserves_fallbacks(monkeypatch):
    molecular = load_etl("compute_molecular_features")
    parse = Mock(side_effect=RuntimeError("parse failed"))
    monkeypatch.setattr(molecular.Chem, "MolFromSmiles", parse)
    result = molecular.compute_molecular_features(
        pd.DataFrame({"smiles": ["CCO"], "struct_id": [9]})
    )
    parse.assert_called_once_with("CCO")
    assert result["valid_ids"] == [9]
    assert not result["morgan"].any()
    assert not result["maccs"].any()
    assert result["descriptors"].empty


def test_empty_molecular_input_preserves_empty_outputs():
    result = load_etl("compute_molecular_features").compute_molecular_features(pd.DataFrame())
    assert result["valid_ids"] == result["valid_indices"] == []
    assert result["morgan"].shape == result["maccs"].shape == (0,)
    assert result["descriptors"].empty


@pytest.mark.parametrize("radius,n_bits", [(1, 128), (3, 2048)])
def test_morgan_keeps_custom_parameters(radius, n_bits):
    molecular = load_etl("compute_molecular_features")
    molecule = Chem.MolFromSmiles("CCO")
    expected = np.zeros(n_bits, dtype=np.uint8)
    expected[list(GetMorganFingerprintAsBitVect(molecule, radius, nBits=n_bits).GetOnBits())] = 1
    np.testing.assert_array_equal(
        molecular.compute_morgan_fingerprint("CCO", radius, n_bits), expected
    )

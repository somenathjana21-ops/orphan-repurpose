"""Tests for the M2 indication model: encoders, fusion, losses, calibration."""

import torch
import pytest

from app.ml.indication_model import (
    GraphSAGEDrugEncoder,
    DiseaseEncoder,
    CrossAttentionFusion,
    IndicationModel,
    FocalLoss,
    TemperatureScaler,
    ConformalPredictor,
)
from app.ml.featurizer import smiles_to_graph, batch_graphs, ATOM_FEATURE_DIM


class TestFeaturizer:
    def test_smiles_to_graph_shapes(self):
        feats, edge_index = smiles_to_graph("CC(=O)Oc1ccccc1C(=O)O")  # aspirin
        assert feats.shape[1] == ATOM_FEATURE_DIM
        assert feats.shape[0] > 0
        assert edge_index.shape[0] == 2

    def test_invalid_smiles_falls_back(self):
        feats, edge_index = smiles_to_graph("this-is-not-a-smiles")
        assert feats.shape[1] == ATOM_FEATURE_DIM
        assert feats.shape[0] > 0

    def test_empty_smiles(self):
        feats, edge_index = smiles_to_graph("")
        assert feats.shape[1] == ATOM_FEATURE_DIM

    def test_batch_graphs(self):
        graphs = [smiles_to_graph("CCO"), smiles_to_graph("c1ccccc1")]
        feats, edges, batch = batch_graphs(graphs)
        assert batch.max().item() == 1
        assert feats.shape[0] == batch.shape[0]
        assert set(batch.tolist()) == {0, 1}


class TestEncoders:
    def test_graphsage_encoder_output(self):
        enc = GraphSAGEDrugEncoder(node_feature_dim=ATOM_FEATURE_DIM, hidden_dim=64, num_layers=2)
        feats, edge_index = smiles_to_graph("CCO")
        batch = torch.zeros(feats.size(0), dtype=torch.long)
        out = enc(feats, edge_index, batch)
        assert out.shape == (1, 64)

    def test_graphsage_encoder_empty_edges(self):
        enc = GraphSAGEDrugEncoder(node_feature_dim=ATOM_FEATURE_DIM, hidden_dim=32, num_layers=2)
        feats = torch.randn(3, ATOM_FEATURE_DIM)
        edge_index = torch.zeros(2, 0, dtype=torch.long)
        batch = torch.zeros(3, dtype=torch.long)
        out = enc(feats, edge_index, batch)
        assert out.shape == (1, 32)

    def test_disease_encoder_projection(self):
        enc = DiseaseEncoder(kg_dim=256, hidden_dim=64)
        out = enc(torch.randn(2, 256))
        assert out.shape == (2, 64)


class TestFusion:
    def test_cross_attention_output_dim(self):
        fusion = CrossAttentionFusion(embed_dim=64, num_heads=4)
        drug = torch.randn(5, 64)
        disease = torch.randn(5, 64)
        out = fusion(drug, disease)
        assert out.shape == (5, fusion.output_dim)
        assert fusion.output_dim == 64 * 3 + 1


class TestFullModel:
    def test_forward_shapes(self):
        model = IndicationModel(node_feature_dim=ATOM_FEATURE_DIM, kg_dim=128, hidden_dim=64, num_layers=2)
        graphs = [smiles_to_graph("CCO"), smiles_to_graph("c1ccccc1"), smiles_to_graph("CCN")]
        feats, edges, batch = batch_graphs(graphs)
        disease_emb = torch.randn(3, 128)
        logits = model(feats, edges, batch, disease_emb)
        assert logits.shape == (3,)

    def test_forward_is_deterministic_in_eval(self):
        model = IndicationModel(node_feature_dim=ATOM_FEATURE_DIM, kg_dim=64, hidden_dim=32, num_layers=2)
        model.eval()
        feats, edges, batch = batch_graphs([smiles_to_graph("CCO")])
        disease_emb = torch.randn(1, 64)
        with torch.no_grad():
            a = model(feats, edges, batch, disease_emb)
            b = model(feats, edges, batch, disease_emb)
        assert torch.allclose(a, b)


class TestLossesAndCalibration:
    def test_focal_loss_range(self):
        loss_fn = FocalLoss(gamma=2.0, alpha=0.25)
        logits = torch.tensor([2.0, -2.0, 0.5])
        targets = torch.tensor([1.0, 0.0, 1.0])
        loss = loss_fn(logits, targets)
        assert loss.item() >= 0

    def test_temperature_scaler_fit(self):
        torch.manual_seed(0)
        logits = torch.randn(200) * 2
        targets = (torch.rand(200) > 0.5).float()
        scaler = TemperatureScaler()
        temp = scaler.fit(logits, targets)
        assert temp > 0

    def test_conformal_intervals_cover(self):
        torch.manual_seed(0)
        probs = torch.rand(100)
        targets = (probs > 0.5).float()
        cp = ConformalPredictor(coverage=0.90)
        cp.calibrate(probs, targets)
        lower, upper = cp.predict_interval(probs)
        assert (lower <= probs).all()
        assert (upper >= probs).all()
        assert (upper <= 1.0).all() and (lower >= 0.0).all()

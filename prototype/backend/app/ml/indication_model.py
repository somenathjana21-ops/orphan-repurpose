"""
Indication Prediction Model — DualEncoderCrossAttention.

Architecture (per docs/06_data_and_models.md §3.1):
  Drug encoder:      GraphSAGE over the molecular graph (RDKit atom/bond features)
  Disease encoder:   KG embedding lookup (RGCN, 256-d)
  Fusion:            bidirectional multi-head cross-attention
  Head:              MLP(512 -> 256 -> 1) + Sigmoid
  Calibration:       Temperature scaling + split-conformal prediction

The model is intentionally small enough to train on CPU for the prototype while
keeping the same tensor shapes as the production spec.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Drug encoder — GraphSAGE over molecular graphs
# ---------------------------------------------------------------------------
class GraphSAGEConv(nn.Module):
    """Single GraphSAGE layer: h_v' = W1·h_v + W2·mean_{u in N(v)} h_u."""

    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.lin_self = nn.Linear(in_dim, out_dim)
        self.lin_neigh = nn.Linear(in_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """x: [N, in_dim]; edge_index: [2, E] (directed, both directions included)."""
        num_nodes = x.size(0)
        if edge_index.numel() == 0:
            neigh = torch.zeros_like(x)
        else:
            src, dst = edge_index[0], edge_index[1]
            # mean-aggregate neighbour features into dst
            agg = torch.zeros(num_nodes, x.size(1), dtype=x.dtype, device=x.device)
            ones = torch.ones(src.size(0), 1, dtype=x.dtype, device=x.device)
            agg.index_add_(0, dst, x[src])
            counts = torch.zeros(num_nodes, 1, dtype=x.dtype, device=x.device)
            counts.index_add_(0, dst, ones)
            counts = counts.clamp(min=1.0)
            neigh = agg / counts
        out = self.lin_self(x) + self.lin_neigh(neigh)
        out = self.norm(out)
        return F.relu(out)


class GraphSAGEDrugEncoder(nn.Module):
    """3-layer GraphSAGE + global mean pooling -> 256-d drug embedding."""

    def __init__(
        self,
        node_feature_dim: int = 78,
        hidden_dim: int = 256,
        num_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        dims = [node_feature_dim] + [hidden_dim] * num_layers
        self.convs = nn.ModuleList([GraphSAGEConv(dims[i], dims[i + 1]) for i in range(num_layers)])
        self.dropout = nn.Dropout(dropout)
        self.output_dim = hidden_dim

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        batch: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Returns [num_graphs, hidden_dim] pooled embeddings."""
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = self.dropout(x)

        # global mean pool
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
        num_graphs = int(batch.max().item()) + 1 if batch.numel() else 0
        pooled = torch.zeros(num_graphs, x.size(1), dtype=x.dtype, device=x.device)
        counts = torch.zeros(num_graphs, 1, dtype=x.dtype, device=x.device)
        pooled.index_add_(0, batch, x)
        counts.index_add_(0, batch, torch.ones(x.size(0), 1, dtype=x.dtype, device=x.device))
        pooled = pooled / counts.clamp(min=1.0)
        return pooled


# ---------------------------------------------------------------------------
# Disease encoder — KG embedding lookup with a projection
# ---------------------------------------------------------------------------
class DiseaseEncoder(nn.Module):
    """Projects pre-trained RGCN disease embeddings into the shared space."""

    def __init__(self, kg_dim: int = 256, hidden_dim: int = 256, dropout: float = 0.1):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(kg_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.output_dim = hidden_dim

    def forward(self, kg_embeddings: torch.Tensor) -> torch.Tensor:
        return self.proj(kg_embeddings)


# ---------------------------------------------------------------------------
# Bidirectional cross-attention fusion
# ---------------------------------------------------------------------------
class CrossAttentionFusion(nn.Module):
    """Drug<->disease bidirectional attention with explicit interaction features."""

    def __init__(self, embed_dim: int = 256, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.drug_to_disease = nn.MultiheadAttention(
            embed_dim, num_heads, dropout=dropout, batch_first=True
        )
        self.disease_to_drug = nn.MultiheadAttention(
            embed_dim, num_heads, dropout=dropout, batch_first=True
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.gate = nn.Linear(embed_dim * 2, embed_dim)
        # interaction features: elementwise product + |diff| + raw dot product
        self.output_dim = embed_dim * 3 + 1

    def forward(self, drug_emb: torch.Tensor, disease_emb: torch.Tensor) -> torch.Tensor:
        """drug_emb/disease_emb: [B, D] -> fused [B, 3D+1]."""
        d = drug_emb.unsqueeze(1)  # [B, 1, D]
        s = disease_emb.unsqueeze(1)  # [B, 1, D]

        # drug attends to disease
        d_att, _ = self.drug_to_disease(d, s, s)
        d_fused = self.norm1(d + d_att).squeeze(1)

        # disease attends to drug
        s_att, _ = self.disease_to_drug(s, d, d)
        s_fused = self.norm2(s + s_att).squeeze(1)

        gate = torch.sigmoid(self.gate(torch.cat([d_fused, s_fused], dim=-1)))
        merged = gate * d_fused + (1 - gate) * s_fused

        # explicit interaction terms — give the head direct similarity signals
        prod = d_fused * s_fused
        absdiff = torch.abs(d_fused - s_fused)
        dot = (d_fused * s_fused).sum(dim=-1, keepdim=True) / (self.embed_dim**0.5)

        return torch.cat([merged, prod, absdiff, dot], dim=-1)


# ---------------------------------------------------------------------------
# Full model
# ---------------------------------------------------------------------------
class IndicationModel(nn.Module):
    """DualEncoderCrossAttention indication predictor."""

    def __init__(
        self,
        node_feature_dim: int = 78,
        kg_dim: int = 256,
        hidden_dim: int = 256,
        num_layers: int = 3,
        num_heads: int = 4,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.drug_encoder = GraphSAGEDrugEncoder(node_feature_dim, hidden_dim, num_layers, dropout)
        self.disease_encoder = DiseaseEncoder(kg_dim, hidden_dim, dropout)
        self.fusion = CrossAttentionFusion(hidden_dim, num_heads, dropout)

        fused_dim = self.fusion.output_dim
        self.head = nn.Sequential(
            nn.Linear(fused_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 1),
        )

    def forward(
        self,
        atom_features: torch.Tensor,
        edge_index: torch.Tensor,
        batch: torch.Tensor,
        disease_kg_emb: torch.Tensor,
    ) -> torch.Tensor:
        """Returns logits [B]."""
        drug_emb = self.drug_encoder(atom_features, edge_index, batch)
        disease_emb = self.disease_encoder(disease_kg_emb)
        fused = self.fusion(drug_emb, disease_emb)
        return self.head(fused).squeeze(-1)


# ---------------------------------------------------------------------------
# Lightweight MLP model (for CPU-constrained training)
# ---------------------------------------------------------------------------
class MorganFingerprintEncoder(nn.Module):
    """Simple MLP encoder for Morgan fingerprints."""

    def __init__(self, input_dim: int = 1024, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.output_dim = hidden_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SimpleIndicationModel(nn.Module):
    """MLP-based indication model: drug_fp + disease_emb -> score."""

    def __init__(self, fp_dim: int = 1024, kg_dim: int = 256, hidden_dim: int = 128):
        super().__init__()
        self.drug_encoder = MorganFingerprintEncoder(fp_dim, hidden_dim)
        self.disease_proj = nn.Sequential(
            nn.Linear(kg_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
        )
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, drug_fp: torch.Tensor, disease_kg: torch.Tensor) -> torch.Tensor:
        d_emb = self.drug_encoder(drug_fp)
        s_emb = self.disease_proj(disease_kg)
        fused = torch.cat([d_emb, s_emb], dim=-1)
        return self.fusion(fused).squeeze(-1)


# ---------------------------------------------------------------------------
# Losses
# ---------------------------------------------------------------------------
class FocalLoss(nn.Module):
    """Binary focal loss (gamma=2, alpha=0.25 by default)."""

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        p = torch.sigmoid(logits)
        p_t = p * targets + (1 - p) * (1 - targets)
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        loss = alpha_t * (1 - p_t).pow(self.gamma) * bce
        return loss.mean()


# ---------------------------------------------------------------------------
# Calibration: temperature scaling
# ---------------------------------------------------------------------------
class TemperatureScaler(nn.Module):
    """Learns a single temperature on the validation set (Guo et al. 2017)."""

    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature.clamp(min=1e-3)

    def fit(self, logits: torch.Tensor, targets: torch.Tensor, max_iter: int = 100):
        """Optimise temperature by minimising NLL on held-out logits."""
        self.temperature.data.fill_(1.0)
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.1, max_iter=max_iter)

        def closure():
            optimizer.zero_grad()
            loss = F.binary_cross_entropy_with_logits(self(logits), targets)
            loss.backward()
            return loss

        optimizer.step(closure)
        return float(self.temperature.item())


# ---------------------------------------------------------------------------
# Conformal prediction (split conformal, binary classification)
# ---------------------------------------------------------------------------
class ConformalPredictor:
    """Split-conformal 90% prediction intervals for binary probabilities."""

    def __init__(self, coverage: float = 0.90):
        self.coverage = coverage
        self.q_hat: float | None = None

    def calibrate(self, probs: torch.Tensor, targets: torch.Tensor):
        """Compute the conformal quantile from calibration residuals."""
        n = probs.size(0)
        if n == 0:
            self.q_hat = 0.0
            return
        # nonconformity: 1 - p(true class)
        scores = torch.where(targets > 0.5, 1 - probs, probs)
        scores, _ = torch.sort(scores)
        level = min(1.0, math.ceil((n + 1) * self.coverage) / n)
        idx = min(int(math.ceil(level * n)) - 1, n - 1)
        self.q_hat = float(scores[idx].item())

    def predict_interval(self, probs: torch.Tensor):
        """Return (lower, upper) tensors for the given probabilities."""
        q = self.q_hat if self.q_hat is not None else 0.0
        lower = (probs - q).clamp(min=0.0)
        upper = (probs + q).clamp(max=1.0)
        return lower, upper

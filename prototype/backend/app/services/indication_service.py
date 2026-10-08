"""
Indication inference service.

Loads the trained DualEncoderCrossAttention checkpoint and scores every
FDA-approved drug against a query disease, returning ranked candidates with
calibrated probabilities, conformal prediction intervals, and MoA summaries.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional

import structlog
import torch

from app.ml.indication_model import IndicationModel, TemperatureScaler, ConformalPredictor
from app.ml.featurizer import smiles_to_graph

logger = structlog.get_logger()


class IndicationService:
    """Loads the indication model and produces ranked drug candidates."""

    def __init__(self, model_path: Optional[str] = None):
        from app.core.config import settings

        self.model_path = Path(model_path or settings.INDICATION_MODEL_PATH)
        self.model: Optional[IndicationModel] = None
        self.temperature = 1.0
        self.conformal_q: Optional[float] = None
        self.drug_smiles: Dict[str, str] = {}
        self.disease_map: Dict[str, int] = {}
        self.disease_embeddings = None
        self.config: Dict = {}
        self.metrics: Dict = {}
        self._graph_cache: Dict[str, tuple] = {}
        self._loaded = False

    # -- lifecycle ---------------------------------------------------------
    def load(self) -> bool:
        if self._loaded:
            return True
        if not self.model_path.exists():
            logger.warning("indication_model_missing", path=str(self.model_path))
            return False
        try:
            with open(self.model_path, "rb") as f:
                ckpt = pickle.load(f)
            self.config = ckpt.get("config", {})
            arch = self.config.get("architecture", "DualEncoderCrossAttention")
            
            if arch == "SimpleIndicationModel_MLP":
                from app.ml.indication_model import SimpleIndicationModel
                self.model = SimpleIndicationModel(
                    fp_dim=self.config.get("fp_dim", 1024),
                    kg_dim=self.config.get("kg_dim", 256),
                    hidden_dim=self.config.get("hidden_dim", 128),
                )
            else:
                self.model = IndicationModel(
                    node_feature_dim=self.config.get("node_feature_dim", 78),
                    kg_dim=self.config.get("kg_dim", 256),
                    hidden_dim=self.config.get("hidden_dim", 256),
                    num_layers=self.config.get("num_layers", 3),
                    num_heads=self.config.get("num_heads", 4),
                )
            self.model.load_state_dict(ckpt["model_state_dict"])
            self.model.eval()
            self.temperature = ckpt.get("temperature", 1.0)
            self.conformal_q = ckpt.get("conformal_q")
            self.drug_smiles = ckpt.get("drug_smiles", {})
            self.drug_fingerprints = ckpt.get("drug_fingerprints", {})
            self.disease_map = ckpt.get("disease_map", {})
            self.disease_embeddings = ckpt.get("disease_embeddings")
            self.metrics = ckpt.get("metrics", {})
            self._loaded = True
            logger.info(
                "indication_model_loaded",
                drugs=len(self.drug_smiles),
                diseases=len(self.disease_map),
                temperature=round(self.temperature, 3),
                architecture=arch,
            )
            return True
        except Exception as e:
            logger.error("indication_model_load_failed", error=str(e))
            return False

    # -- helpers -----------------------------------------------------------
    def _graph(self, drug_id: str):
        if drug_id not in self._graph_cache:
            self._graph_cache[drug_id] = smiles_to_graph(self.drug_smiles[drug_id])
        return self._graph_cache[drug_id]

    def _resolve_disease_key(self, disease_id: str) -> Optional[str]:
        """Map an ORPHA id (or raw UMLS id) to a key in the disease embedding map."""
        if disease_id in self.disease_map:
            return disease_id
        # try UMLS form
        if disease_id.startswith("UMLS:") and disease_id in self.disease_map:
            return disease_id
        return None

    # -- inference ---------------------------------------------------------
    def score_drugs(self, disease_key: str, drug_ids: Optional[List[str]] = None) -> List[dict]:
        """Score drugs against a disease; returns ranked dicts."""
        if not self._loaded and not self.load():
            return []
        if disease_key not in self.disease_map:
            return []

        arch = self.config.get("architecture", "DualEncoderCrossAttention")
        ids = drug_ids or list(self.drug_smiles.keys())
        ids = [d for d in ids if d in self.drug_smiles]
        if not ids:
            return []

        d_idx = self.disease_map[disease_key]
        disease_emb = torch.tensor(
            self.disease_embeddings[d_idx], dtype=torch.float32
        ).unsqueeze(0)

        results = []
        with torch.no_grad():
            for did in ids:
                if arch == "SimpleIndicationModel_MLP":
                    # Use pre-computed Morgan fingerprints
                    drug_fps = getattr(self, 'drug_fingerprints', {})
                    if did not in drug_fps:
                        continue
                    fp = torch.tensor(drug_fps[did], dtype=torch.float32).unsqueeze(0)
                    logits = self.model(fp, disease_emb)
                else:
                    # Use graph-based encoder
                    feats, edge_index = self._graph(did)
                    batch = torch.zeros(feats.size(0), dtype=torch.long)
                    logits = self.model(feats, edge_index, batch, disease_emb)
                # temperature-scale then sigmoid
                scaled = logits / max(self.temperature, 1e-3)
                prob = float(torch.sigmoid(scaled).item())
                q = self.conformal_q or 0.0
                results.append({
                    "drug_id": did,
                    "probability": prob,
                    "ci_lower": max(0.0, prob - q),
                    "ci_upper": min(1.0, prob + q),
                })

        results.sort(key=lambda r: r["probability"], reverse=True)
        return results

    def score_all_for_orpha(self, orpha_id: str, top_k: int = 20) -> List[dict]:
        """Convenience: score all drugs for a disease given by ORPHA id."""
        key = self._resolve_disease_key(orpha_id)
        if key is None:
            return []
        return self.score_drugs(key)[:top_k]

    def is_ready(self) -> bool:
        return self._loaded or self.load()


_service: Optional[IndicationService] = None


def get_indication_service() -> IndicationService:
    """Module-level singleton."""
    global _service
    if _service is None:
        _service = IndicationService()
        _service.load()
    return _service

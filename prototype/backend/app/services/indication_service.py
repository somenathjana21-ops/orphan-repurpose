"""
Indication inference service.

Loads the trained DualEncoderCrossAttention checkpoint and scores every
FDA-approved drug against a query disease, returning ranked candidates with
calibrated probabilities, conformal prediction intervals, and MoA summaries.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from threading import Lock, RLock

import structlog
import torch
from app.ml.featurizer import batch_graphs, smiles_to_graph
from app.ml.indication_model import IndicationModel

logger = structlog.get_logger()


class IndicationService:
    """Loads the indication model and produces ranked drug candidates."""

    def __init__(self, model_path: str | None = None, batch_size: int | None = None):
        from app.core.config import settings

        self.model_path = Path(model_path or settings.INDICATION_MODEL_PATH)
        self.batch_size = settings.INFERENCE_BATCH_SIZE if batch_size is None else batch_size
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")
        self._lock = RLock()
        self.model: IndicationModel | None = None
        self.temperature = 1.0
        self.conformal_q: float | None = None
        self.drug_smiles: dict[str, str] = {}
        self.drug_fingerprints: dict = {}
        self.disease_map: dict[str, int] = {}
        self.disease_embeddings = None
        self.config: dict = {}
        self.metrics: dict = {}
        self._graph_cache: dict[str, tuple] = {}
        self._loaded = False

    # -- lifecycle ---------------------------------------------------------
    def load(self) -> bool:
        """Load the checkpoint once, including when requests arrive concurrently."""
        with self._lock:
            return self._load()

    def _load(self) -> bool:
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

    def _resolve_disease_key(self, disease_id: str) -> str | None:
        """Map an ORPHA id (or raw UMLS id) to a key in the disease embedding map."""
        if disease_id in self.disease_map:
            return disease_id
        # try UMLS form
        if disease_id.startswith("UMLS:") and disease_id in self.disease_map:
            return disease_id
        return None

    # -- inference ---------------------------------------------------------
    def score_drugs(self, disease_key: str, drug_ids: list[str] | None = None) -> list[dict]:
        """Score bounded batches, serializing access to the shared model and features."""
        with self._lock:
            return self._score_drugs(disease_key, drug_ids)

    def _score_drugs(self, disease_key: str, drug_ids: list[str] | None) -> list[dict]:
        if not self._loaded and not self.load():
            return []
        if disease_key not in self.disease_map:
            return []

        arch = self.config.get("architecture", "DualEncoderCrossAttention")
        ids = list(self.drug_smiles) if drug_ids is None else drug_ids
        ids = [d for d in ids if d in self.drug_smiles]
        if arch == "SimpleIndicationModel_MLP":
            ids = [d for d in ids if d in self.drug_fingerprints]
        if not ids:
            return []
        assert self.model is not None

        d_idx = self.disease_map[disease_key]
        disease_emb = torch.as_tensor(
            self.disease_embeddings[d_idx], dtype=torch.float32
        ).unsqueeze(0)

        results = []
        with torch.inference_mode():
            for start in range(0, len(ids), self.batch_size):
                batch_ids = ids[start : start + self.batch_size]
                diseases = disease_emb.expand(len(batch_ids), -1)
                if arch == "SimpleIndicationModel_MLP":
                    fps = torch.stack(
                        [
                            torch.as_tensor(self.drug_fingerprints[did], dtype=torch.float32)
                            for did in batch_ids
                        ]
                    )
                    logits = self.model(fps, diseases)
                else:
                    feats, edge_index, batch = batch_graphs([self._graph(did) for did in batch_ids])
                    logits = self.model(feats, edge_index, batch, diseases)
                scaled = logits / max(self.temperature, 1e-3)
                probabilities = torch.sigmoid(scaled).tolist()
                q = self.conformal_q or 0.0
                for did, prob in zip(batch_ids, probabilities, strict=True):
                    results.append(
                        {
                            "drug_id": did,
                            "probability": prob,
                            "ci_lower": max(0.0, prob - q),
                            "ci_upper": min(1.0, prob + q),
                        }
                    )

        results.sort(key=lambda r: r["probability"], reverse=True)
        return results

    def score_all_for_orpha(self, orpha_id: str, top_k: int = 20) -> list[dict]:
        """Convenience: score all drugs for a disease given by ORPHA id."""
        if not self.is_ready():
            return []
        key = self._resolve_disease_key(orpha_id)
        if key is None:
            return []
        return self.score_drugs(key)[:top_k]

    def is_ready(self) -> bool:
        return self._loaded or self.load()


_service: IndicationService | None = None
_service_lock = Lock()


def get_indication_service() -> IndicationService:
    """Module-level singleton."""
    global _service
    with _service_lock:
        if _service is None:
            _service = IndicationService()
            _service.load()
    return _service

"""
Explanation service for OrphanRepurpose.

Caches and serves explanations for drug-disease pairs.
"""

from __future__ import annotations

from threading import Lock, RLock
from typing import Any

import structlog
from app.ml.explainer import Explainer

logger = structlog.get_logger()


class ExplanationService:
    """Caches and serves explanations for drug-disease pairs."""

    def __init__(self):
        self._lock = RLock()
        self._explainer = Explainer()
        self._cache: dict[tuple, dict[str, Any]] = {}
        self._cache_inputs: dict[tuple, tuple] = {}

    def explain_candidate(
        self,
        drug_id: str,
        disease_id: str,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
    ) -> dict[str, Any]:
        """Generate or retrieve cached explanation."""
        with self._lock:
            return self._explain_candidate(
                drug_id, disease_id, drug_name, disease_name, probability, moa_summary
            )

    def _explain_candidate(
        self,
        drug_id: str,
        disease_id: str,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
    ) -> dict[str, Any]:
        cache_key = (drug_id, disease_id)
        inputs = (drug_name, disease_name, probability, moa_summary)

        if cache_key in self._cache and self._cache_inputs.get(cache_key) == inputs:
            logger.debug("explanation_cache_hit", drug_id=drug_id, disease_id=disease_id)
            return self._cache[cache_key]

        try:
            explanation = self._explainer.explain(
                drug_id=drug_id,
                disease_id=disease_id,
                drug_name=drug_name,
                disease_name=disease_name,
                probability=probability,
                moa_summary=moa_summary,
            )
            self._cache[cache_key] = explanation
            self._cache_inputs[cache_key] = inputs
            logger.info(
                "explanation_generated",
                drug_id=drug_id,
                disease_id=disease_id,
                n_kg_paths=len(explanation.get("kg_paths", [])),
                n_shap=len(explanation.get("shap_values", {})),
                n_cf=len(explanation.get("counterfactuals", [])),
            )
            return explanation

        except Exception as e:
            self._cache.pop(cache_key, None)
            self._cache_inputs.pop(cache_key, None)
            logger.error("explanation_generation_failed", error=str(e))
            return self._fallback_explanation(
                drug_id, disease_id, drug_name, disease_name, probability, moa_summary
            )

    def get_cached(self, drug_id: str, disease_id: str) -> dict[str, Any] | None:
        """Get cached explanation if available."""
        with self._lock:
            return self._cache.get((drug_id, disease_id))

    def clear_cache(self):
        """Clear the explanation cache."""
        with self._lock:
            self._cache.clear()
            self._cache_inputs.clear()
        logger.info("explanation_cache_cleared")

    @staticmethod
    def _fallback_explanation(
        drug_id: str,
        disease_id: str,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
    ) -> dict[str, Any]:
        """Generate a fallback explanation when the full pipeline fails."""
        return {
            "candidate_id": f"{drug_id}_{disease_id}",
            "kg_paths": [],
            "shap_values": {},
            "counterfactuals": [],
            "llm_rationale": (
                f"{drug_name} shows {probability:.0%} predicted efficacy for {disease_name}. "
                f"{moa_summary}"
            ),
        }


_service: ExplanationService | None = None
_service_lock = Lock()


def get_explanation_service() -> ExplanationService:
    """Module-level singleton."""
    global _service
    with _service_lock:
        if _service is None:
            _service = ExplanationService()
    return _service

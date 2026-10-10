"""
Explanation service for OrphanRepurpose.

Caches and serves explanations for drug-disease pairs.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.ml.explainer import Explainer

logger = structlog.get_logger()


class ExplanationService:
    """Caches and serves explanations for drug-disease pairs."""

    def __init__(self):
        self._explainer = Explainer()
        self._cache: dict[tuple, dict[str, Any]] = {}

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
        cache_key = (drug_id, disease_id)

        if cache_key in self._cache:
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
            logger.error("explanation_generation_failed", error=str(e))
            return self._fallback_explanation(
                drug_id, disease_id, drug_name, disease_name, probability, moa_summary
            )

    def get_cached(self, drug_id: str, disease_id: str) -> dict[str, Any] | None:
        """Get cached explanation if available."""
        return self._cache.get((drug_id, disease_id))

    def clear_cache(self):
        """Clear the explanation cache."""
        self._cache.clear()
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


def get_explanation_service() -> ExplanationService:
    """Module-level singleton."""
    global _service
    if _service is None:
        _service = ExplanationService()
    return _service

"""
Safety service combining FAERS disproportionality and ADMET predictions.

Provides unified safety assessment for drug candidates.
"""
from __future__ import annotations

import structlog
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.ml.faers import FAERSAnalyzer, DisproportionalityResult, ContingencyTable
from app.ml.admet import ADMETPredictor, ADMET_ENDPOINTS

logger = structlog.get_logger()


class SafetyService:
    """Unified safety assessment service."""

    def __init__(self):
        self.faers_analyzer = FAERSAnalyzer()
        self.admet_predictor = ADMETPredictor()
        self._faers_cache: Dict[str, List[DisproportionalityResult]] = {}
        self._admet_cache: Dict[str, Dict[str, float]] = {}

    def assess_drug(
        self,
        drug_id: str,
        drug_name: str,
        smiles: str,
        faers_reports: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Full safety assessment for a drug."""
        # FAERS signals
        faers_signals = []
        if faers_reports:
            faers_signals = self._analyze_faers(drug_id, drug_name, faers_reports)

        # ADMET predictions
        admet_predictions = self._predict_admet(drug_id, smiles)

        # Overall safety
        admet_overall = self.admet_predictor.overall_safety(admet_predictions)
        faers_overall = self._faers_overall(faers_signals)

        # Combined
        if admet_overall == "fail" or faers_overall == "fail":
            overall = "fail"
        elif admet_overall == "caution" or faers_overall == "caution":
            overall = "caution"
        else:
            overall = "pass"

        return {
            "drug_id": drug_id,
            "drug_name": drug_name,
            "faers_signals": [
                {
                    "reaction": s.event,
                    "meddra_pt": s.meddra_pt,
                    "ror": s.ror,
                    "prr": s.prr,
                    "bcpnn": s.bcpnn_ic,
                    "n_reports": s.n_reports,
                    "level": s.level,
                }
                for s in faers_signals
            ],
            "admet_predictions": admet_predictions,
            "admet_classifications": self.admet_predictor.classify_safety(admet_predictions),
            "contraindications": self._extract_contraindications(faers_signals, admet_predictions),
            "overall": overall,
        }

    def _analyze_faers(
        self,
        drug_id: str,
        drug_name: str,
        reports: List[Dict[str, Any]],
    ) -> List[DisproportionalityResult]:
        """Analyze FAERS reports for a drug."""
        from app.ml.faers import merge_faers_reports

        tables = merge_faers_reports(reports)
        results = []

        for (did, event), table in tables.items():
            if did != drug_id:
                continue
            if table.a < self.faers_analyzer.min_reports:
                continue

            # Get meddra_pt from reports
            meddra_pt = event
            for r in reports:
                if r.get("drug_id") == drug_id and r.get("event") == event:
                    meddra_pt = r.get("meddra_pt", event)
                    break

            result = self.faers_analyzer.analyze(drug_id, drug_name, event, meddra_pt, table)
            results.append(result)

        # Sort by severity
        results.sort(key=lambda r: (r.level != "fail", r.level != "caution", -r.ror))
        return results

    def _predict_admet(self, drug_id: str, smiles: str) -> Dict[str, float]:
        """Predict ADMET properties for a drug."""
        if drug_id in self._admet_cache:
            return self._admet_cache[drug_id]

        predictions = self.admet_predictor.predict(smiles)
        self._admet_cache[drug_id] = predictions
        return predictions

    def _faers_overall(self, signals: List[DisproportionalityResult]) -> str:
        """Compute overall FAERS safety level."""
        if not signals:
            return "pass"

        n_fail = sum(1 for s in signals if s.level == "fail")
        n_caution = sum(1 for s in signals if s.level == "caution")

        if n_fail >= 2:
            return "fail"
        if n_fail >= 1 or n_caution >= 3:
            return "caution"
        return "pass"

    def _extract_contraindications(
        self,
        faers_signals: List[DisproportionalityResult],
        admet_predictions: Dict[str, float],
    ) -> List[str]:
        """Extract contraindications from safety data."""
        contraindications = []

        # From FAERS
        for signal in faers_signals:
            if signal.level == "fail":
                contraindications.append(f"Risk of {signal.meddra_pt} (ROR={signal.ror:.1f})")

        # From ADMET
        for endpoint, value in admet_predictions.items():
            info = ADMET_ENDPOINTS.get(endpoint, {})
            threshold = info.get("threshold", 0.5)
            direction = info.get("direction", "low")

            if direction == "low" and value > threshold * 2:
                contraindications.append(f"High {info.get('name', endpoint)} risk")
            elif direction == "high" and value < threshold * 0.5:
                contraindications.append(f"Poor {info.get('name', endpoint)}")

        return contraindications

    def get_faers_signals(self, drug_id: str) -> List[DisproportionalityResult]:
        """Get cached FAERS signals for a drug."""
        return self._faers_cache.get(drug_id, [])

    def get_admet_predictions(self, drug_id: str) -> Optional[Dict[str, float]]:
        """Get cached ADMET predictions for a drug."""
        return self._admet_cache.get(drug_id)

    def clear_cache(self):
        """Clear all caches."""
        self._faers_cache.clear()
        self._admet_cache.clear()
        logger.info("safety_cache_cleared")


_service: Optional[SafetyService] = None


def get_safety_service() -> SafetyService:
    """Module-level singleton."""
    global _service
    if _service is None:
        _service = SafetyService()
    return _service

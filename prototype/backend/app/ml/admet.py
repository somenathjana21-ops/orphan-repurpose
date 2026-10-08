"""
TDC ADMET prediction module.

Wraps Therapeutics Data Commons (TDC) ADMET models for pre-computed
safety property prediction. Falls back to RDKit-based descriptors
when TDC is unavailable.

ADMET endpoints (22 total from TDC ADMET_Group):
- Absorption: Caco2, HIA, Pgp, PAMPP
- Distribution: PPB, VDSS, BBB
- Metabolism: CYP1A2, CYP2C19, CYP2C9, CYP2D6, CYP3A4
- Excretion: CL, HalfLife, Clearance
- Toxicity: hERG, DILI, AMES, Carcinogenicity
- General: hERG, DILI, AMES, Carcinogenicity, Skin Reaction
"""
from __future__ import annotations

import structlog
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = structlog.get_logger()


# ADMET endpoint definitions with thresholds
ADMET_ENDPOINTS = {
    # Absorption
    "Caco2": {"name": "Caco-2 Permeability", "unit": "cm/s", "threshold": 0.5, "direction": "high"},
    "HIA": {"name": "Human Intestinal Absorption", "unit": "%", "threshold": 0.3, "direction": "high"},
    "Pgp": {"name": "P-glycoprotein Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "PAMPP": {"name": "PAMPA Permeability", "unit": "cm/s", "threshold": 0.5, "direction": "high"},
    # Distribution
    "PPB": {"name": "Plasma Protein Binding", "unit": "%", "threshold": 0.9, "direction": "low"},
    "VDSS": {"name": "Volume of Distribution", "unit": "L/kg", "threshold": 1.0, "direction": "low"},
    "BBB": {"name": "Blood-Brain Barrier", "unit": "binary", "threshold": 0.5, "direction": "high"},
    # Metabolism
    "CYP1A2": {"name": "CYP1A2 Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "CYP2C19": {"name": "CYP2C19 Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "CYP2C9": {"name": "CYP2C9 Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "CYP2D6": {"name": "CYP2D6 Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "CYP3A4": {"name": "CYP3A4 Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    # Excretion
    "CL": {"name": "Clearance", "unit": "mL/min/kg", "threshold": 5.0, "direction": "low"},
    "HalfLife": {"name": "Half-Life", "unit": "hours", "threshold": 12.0, "direction": "low"},
    "Clearance": {"name": "Hepatic Clearance", "unit": "mL/min/kg", "threshold": 5.0, "direction": "low"},
    # Toxicity
    "hERG": {"name": "hERG Inhibition", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "DILI": {"name": "Drug-Induced Liver Injury", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "AMES": {"name": "AMES Mutagenicity", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "Carcinogenicity": {"name": "Carcinogenicity", "unit": "binary", "threshold": 0.5, "direction": "low"},
    "SkinReaction": {"name": "Skin Sensitization", "unit": "binary", "threshold": 0.5, "direction": "low"},
}


class ADMETPredictor:
    """Predicts ADMET properties using TDC models or RDKit fallback."""

    def __init__(self):
        self._tdc_available = False
        self._models: Dict[str, Any] = {}
        self._check_tdc()

    def _check_tdc(self):
        """Check if TDC is available."""
        try:
            from tdc import BenchmarkGroup
            self._tdc_available = True
            logger.info("tdc_available")
        except ImportError:
            self._tdc_available = False
            logger.warning("tdc_not_available_using_rdkit_fallback")

    def predict(self, smiles: str) -> Dict[str, float]:
        """Predict all ADMET endpoints for a SMILES string."""
        if self._tdc_available:
            return self._predict_tdc(smiles)
        return self._predict_rdkit(smiles)

    def _predict_tdc(self, smiles: str) -> Dict[str, float]:
        """Predict using TDC models."""
        results = {}
        try:
            from tdc.single_pred import ADME

            for endpoint, info in ADMET_ENDPOINTS.items():
                try:
                    if endpoint not in self._models:
                        self._models[endpoint] = ADME(name=endpoint)
                    model = self._models[endpoint]
                    pred = model.predict([smiles])
                    if isinstance(pred, (list, np.ndarray)):
                        results[endpoint] = float(pred[0]) if len(pred) > 0 else 0.0
                    else:
                        results[endpoint] = float(pred)
                except Exception as e:
                    logger.debug(f"tdc_predict_failed_{endpoint}", error=str(e))
                    results[endpoint] = self._predict_rdkit_single(smiles, endpoint)

        except Exception as e:
            logger.warning("tdc_predict_failed_using_rdkit", error=str(e))
            return self._predict_rdkit(smiles)

        return results

    def _predict_rdkit(self, smiles: str) -> Dict[str, float]:
        """Predict using RDKit descriptors as fallback."""
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {k: 0.0 for k in ADMET_ENDPOINTS}

            mw = Descriptors.MolWt(mol)
            logp = Crippen.MolLogP(mol)
            hbd = rdMolDescriptors.CalcNumHBD(mol)
            hba = rdMolDescriptors.CalcNumHBA(mol)
            tpsa = rdMolDescriptors.CalcTPSA(mol)
            rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
            aromatic = rdMolDescriptors.CalcNumAromaticRings(mol)

            # Simple rule-based approximations
            results = {
                "Caco2": 1.0 if logp > 0 and logp < 5 else 0.0,
                "HIA": 1.0 if logp > 0 and logp < 5 and tpsa < 140 else 0.0,
                "Pgp": 1.0 if mw > 500 and hba > 8 else 0.0,
                "PAMPP": 1.0 if logp > 1 and logp < 5 else 0.0,
                "PPB": 1.0 if logp > 2 and mw > 300 else 0.0,
                "VDSS": 0.5 + 0.5 * logp,
                "BBB": 1.0 if logp > 1 and logp < 4 and tpsa < 90 and hbd < 3 else 0.0,
                "CYP1A2": 1.0 if aromatic > 0 else 0.0,
                "CYP2C19": 1.0 if hba > 2 else 0.0,
                "CYP2C9": 1.0 if hba > 1 else 0.0,
                "CYP2D6": 1.0 if hba > 1 and logp > 0 else 0.0,
                "CYP3A4": 1.0 if mw > 400 else 0.0,
                "CL": 5.0 - 0.5 * logp,
                "HalfLife": 4.0 + 0.5 * logp,
                "Clearance": 5.0 - 0.5 * logp,
                "hERG": 1.0 if logp > 3 and mw > 400 else 0.0,
                "DILI": 1.0 if logp > 4 else 0.0,
                "AMES": 1.0 if aromatic > 2 else 0.0,
                "Carcinogenicity": 1.0 if aromatic > 3 else 0.0,
                "SkinReaction": 1.0 if hbd > 2 else 0.0,
            }
            return results

        except Exception as e:
            logger.error("rdkit_predict_failed", error=str(e))
            return {k: 0.0 for k in ADMET_ENDPOINTS}

    def _predict_rdkit_single(self, smiles: str, endpoint: str) -> float:
        """Predict a single endpoint using RDKit."""
        results = self._predict_rdkit(smiles)
        return results.get(endpoint, 0.0)

    def classify_safety(self, predictions: Dict[str, float]) -> Dict[str, str]:
        """Classify each endpoint as 'pass', 'caution', or 'fail'."""
        classifications = {}
        for endpoint, value in predictions.items():
            info = ADMET_ENDPOINTS.get(endpoint, {})
            threshold = info.get("threshold", 0.5)
            direction = info.get("direction", "low")

            if direction == "high":
                # Higher is better
                if value < threshold * 0.5:
                    classifications[endpoint] = "fail"
                elif value < threshold:
                    classifications[endpoint] = "caution"
                else:
                    classifications[endpoint] = "pass"
            else:
                # Lower is better
                if value > threshold * 2:
                    classifications[endpoint] = "fail"
                elif value > threshold:
                    classifications[endpoint] = "caution"
                else:
                    classifications[endpoint] = "pass"

        return classifications

    def overall_safety(self, predictions: Dict[str, float]) -> str:
        """Compute overall safety classification."""
        classifications = self.classify_safety(predictions)
        n_fail = sum(1 for v in classifications.values() if v == "fail")
        n_caution = sum(1 for v in classifications.values() if v == "caution")

        if n_fail >= 3:
            return "fail"
        if n_fail >= 1 or n_caution >= 3:
            return "caution"
        return "pass"

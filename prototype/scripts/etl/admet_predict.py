#!/usr/bin/env python3
"""
Run ADMET predictions using RDKit fallback.
When TDC models are not available (no GPU), this script uses RDKit
to compute basic molecular descriptors as ADMET proxies.

For production use with GPU, use TDC ADMET models instead.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()

# ADMET proxy thresholds based on Lipinski's Rule of Five and other heuristics
ADMET_THRESHOLDS = {
    "molecular_weight": (0, 500),
    "logp": (-2, 5),
    "hbd": (0, 5),
    "hba": (0, 10),
    "tpsa": (0, 140),
    "rotatable_bonds": (0, 10),
}


def compute_rdkit_descriptors(smiles: str) -> dict:
    """Compute RDKit molecular descriptors as ADMET proxies."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}

        return {
            "molecular_weight": Descriptors.MolWt(mol),
            "logp": Descriptors.MolLogP(mol),
            "hbd": Lipinski.NumHDonors(mol),
            "hba": Lipinski.NumHAcceptors(mol),
            "tpsa": rdMolDescriptors.CalcTPSA(mol),
            "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
            "formal_charge": Chem.GetFormalCharge(mol),
            "num_atoms": mol.GetNumAtoms(),
            "num_heavy_atoms": mol.GetNumHeavyAtoms(),
            "num_rings": rdMolDescriptors.CalcNumRings(mol),
            "num_aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            "fraction_sp3": Lipinski.FractionCSP3(mol),
            "lipinski_violations": sum([
                Descriptors.MolWt(mol) > 500,
                Descriptors.MolLogP(mol) > 5,
                Lipinski.NumHDonors(mol) > 5,
                Lipinski.NumHAcceptors(mol) > 10,
            ]),
            "qed": Descriptors.qed(mol),
        }
    except ImportError:
        logger.warning("rdkit_not_installed")
        return {}
    except Exception as e:
        logger.warning("rdkit_error", error=str(e), smiles=smiles[:50])
        return {}


def predict_admet_risk(descriptors: dict) -> dict:
    """Predict ADMET risk based on molecular descriptors."""
    if not descriptors:
        return {"admet_risk": "unknown", "risk_score": 0.5, "violations": []}

    violations = []

    # Check Lipinski violations
    if descriptors.get("lipinski_violations", 0) > 1:
        violations.append(f"lipinski:{descriptors['lipinski_violations']}")

    # Check specific thresholds
    if descriptors.get("molecular_weight", 0) > 500:
        violations.append("mw>500")
    if descriptors.get("logp", 0) > 5:
        violations.append("logp>5")
    if descriptors.get("hbd", 0) > 5:
        violations.append("hbd>5")
    if descriptors.get("hba", 0) > 10:
        violations.append("hba>10")
    if descriptors.get("tpsa", 0) > 140:
        violations.append("tpsa>140")

    # Risk score: 0 (safe) to 1 (high risk)
    risk_score = min(1.0, len(violations) / 5.0)

    # Risk category
    if risk_score < 0.2:
        risk = "low"
    elif risk_score < 0.5:
        risk = "moderate"
    else:
        risk = "high"

    return {
        "admet_risk": risk,
        "risk_score": risk_score,
        "violations": violations,
    }


def predict_admet_for_drugs(processed_dir: Path, output_dir: Path) -> None:
    """Run ADMET predictions for all drugs in the dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load drug structures
    drug_path = processed_dir / "drugcentral" / "drugcentral_fda_approved.parquet"
    if not drug_path.exists():
        logger.warning("drug_file_missing", path=str(drug_path))
        return

    drugs = pd.read_parquet(drug_path)
    logger.info("admet_input", drugs=len(drugs))

    results = []
    for _, row in drugs.iterrows():
        smiles = row.get("smiles", "")
        name = row.get("name", "")
        struct_id = row.get("struct_id", "")

        if not smiles or pd.isna(smiles):
            continue

        # Compute RDKit descriptors
        descriptors = compute_rdkit_descriptors(smiles)

        # Predict ADMET risk
        admet = predict_admet_risk(descriptors)

        results.append({
            "struct_id": struct_id,
            "name": name,
            "smiles": smiles,
            **descriptors,
            **admet,
        })

    if not results:
        logger.warning("admet_no_results")
        return

    df = pd.DataFrame(results)
    df.to_parquet(output_dir / "admet_predictions.parquet", index=False)
    df.to_csv(output_dir / "admet_predictions.csv", index=False)

    # Summary statistics
    summary = {
        "total_drugs": len(df),
        "risk_distribution": df["admet_risk"].value_counts().to_dict(),
        "mean_risk_score": float(df["risk_score"].mean()),
        "high_risk_drugs": df[df["admet_risk"] == "high"]["name"].tolist(),
    }
    import json
    with open(output_dir / "admet_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("admet_complete", total_drugs=len(df), output_dir=str(output_dir))


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    processed_dir = data_dir / "processed"
    output_dir = data_dir / "safety" / "admet"

    print("🧪 Running ADMET predictions (RDKit fallback)...")
    print("  Note: For production use with GPU, use TDC ADMET models instead.")
    predict_admet_for_drugs(processed_dir, output_dir)
    print(f"\nADMET predictions complete. Output: {output_dir}")


if __name__ == "__main__":
    main()

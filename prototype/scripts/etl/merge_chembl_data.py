#!/usr/bin/env python3
"""
Merge real ChEMBL data with synthetic Orphanet data to create an expanded dataset.

Strategy:
  - Use ChEMBL as primary source for drugs, indications, mechanisms, targets
  - Keep synthetic Orphanet diseases (rare diseases) and map ChEMBL indications to them
  - Create unified parquet files for the KG and model training
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()

# Path to existing synthetic data
SYNTHETIC_SCRIPT = Path("/workspace/dev/orphan-repurpose/prototype/scripts/etl/generate_demo_data.py")
CHEMBL_DIR = Path("/root/chembl_data")
OUTPUT_DIR = Path("/workspace/dev/orphan-repurpose/prototype/data/processed")


def load_synthetic_drugs() -> list[dict]:
    """Parse drug tuples from generate_demo_data.py."""
    with open(SYNTHETIC_SCRIPT, "r") as f:
        content = f.read()
    
    drugs = []
    for m in re.finditer(r'\("(\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', content):
        drugs.append({
            "struct_id": m.group(1),
            "name": m.group(2),
            "smiles": m.group(3),
            "moa_class": m.group(4),
            "target_gene": m.group(5),
            "uniprot": m.group(6),
        })
    return drugs


def load_synthetic_diseases() -> list[dict]:
    """Parse disease tuples from generate_demo_data.py."""
    with open(SYNTHETIC_SCRIPT, "r") as f:
        content = f.read()
    
    diseases = []
    for m in re.finditer(
        r'\("(ORPHA:\d+)",\s*"([^"]+)",\s*([\d.]+),\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*\[([^\]]*)\],\s*"([^"]+)"\)',
        content
    ):
        genes = [g.strip().strip('"') for g in m.group(7).split(",") if g.strip()]
        diseases.append({
            "orpha_id": m.group(1),
            "name": m.group(2),
            "prevalence": float(m.group(3)),
            "prevalence_category": m.group(4),
            "inheritance": m.group(5),
            "age_of_onset": m.group(6),
            "genes": genes,
            "umls_cui": m.group(8),
        })
    return diseases


def load_synthetic_indications() -> list[tuple[str, str]]:
    """Parse indication pairs from generate_demo_data.py."""
    with open(SYNTHETIC_SCRIPT, "r") as f:
        content = f.read()
    
    indications = []
    for m in re.finditer(r'\("(\d+)",\s*"(ORPHA:\d+)"\)', content):
        indications.append((m.group(1), m.group(2)))
    return indications


def load_synthetic_targets() -> list[dict]:
    """Parse target tuples from generate_demo_data.py."""
    with open(SYNTHETIC_SCRIPT, "r") as f:
        content = f.read()
    
    targets = []
    for m in re.finditer(
        r'\("(T\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)',
        content
    ):
        targets.append({
            "target_id": m.group(1),
            "target_name": m.group(2),
            "gene": m.group(3),
            "uniprot": m.group(4),
            "target_class": m.group(5),
        })
    return targets


def merge_datasets():
    """Merge ChEMBL real data with synthetic Orphanet data."""
    
    # Load all sources
    synth_drugs = load_synthetic_drugs()
    synth_diseases = load_synthetic_diseases()
    synth_indications = load_synthetic_indications()
    synth_targets = load_synthetic_targets()
    
    chembl_mols = pd.read_csv(CHEMBL_DIR / "chembl_molecules.csv")
    chembl_inds = pd.read_csv(CHEMBL_DIR / "chembl_indications.csv")
    chembl_mechs = pd.read_csv(CHEMBL_DIR / "chembl_mechanisms.csv")
    chembl_tgts = pd.read_csv(CHEMBL_DIR / "chembl_targets.csv")
    
    logger.info(
        "data_loaded",
        synth_drugs=len(synth_drugs),
        synth_diseases=len(synth_diseases),
        synth_indications=len(synth_indications),
        chembl_drugs=len(chembl_mols),
        chembl_indications=len(chembl_inds),
        chembl_mechanisms=len(chembl_mechs),
        chembl_targets=len(chembl_tgts),
    )
    
    # --- Build unified drug table ---
    # Start with ChEMBL drugs (real SMILES)
    drug_rows = []
    drug_id_map = {}  # chembl_id -> unified struct_id
    
    for i, row in chembl_mols.iterrows():
        struct_id = f"chembl:{row['chembl_id']}"
        drug_id_map[row["chembl_id"]] = struct_id
        drug_rows.append({
            "struct_id": struct_id,
            "name": row["name"] if pd.notna(row["name"]) else row["chembl_id"],
            "smiles": row["smiles"],
            "inchi": "",
            "inchikey": "",
            "cas": "",
            "molecular_weight": 0.0,
            "xlogp": 0.0,
            "tpsa": 0.0,
            "rotatable_bonds": 0,
            "hba": 0,
            "hbd": 0,
            "charge": 0,
            "moa_classes": "",
            "target_name": "",
            "gene": "",
            "uniprot": "",
            "indication_umls": "",
            "indication_types": "ChEMBL",
            "first_approval_year": int(row["first_approval"]) if pd.notna(row.get("first_approval")) else 2000,
            "approval_status": "ChEMBL",
        })
    
    # Add synthetic drugs that aren't already in ChEMBL
    chembl_smiles = set(chembl_mols["smiles"].str.lower())
    for d in synth_drugs:
        if d["smiles"].lower() not in chembl_smiles:
            drug_rows.append({
                "struct_id": d["struct_id"],
                "name": d["name"],
                "smiles": d["smiles"],
                "inchi": "",
                "inchikey": "",
                "cas": "",
                "molecular_weight": 0.0,
                "xlogp": 0.0,
                "tpsa": 0.0,
                "rotatable_bonds": 0,
                "hba": 0,
                "hbd": 0,
                "charge": 0,
                "moa_classes": d["moa_class"],
                "target_name": d["target_gene"],
                "gene": d["target_gene"],
                "uniprot": d["uniprot"],
                "indication_umls": "",
                "indication_types": "DrugCentral",
                "first_approval_year": 1990,
                "approval_status": "FDA_approved",
            })
    
    df_drugs = pd.DataFrame(drug_rows)
    logger.info("unified_drugs", count=len(df_drugs))
    
    # --- Build unified disease table ---
    # Keep synthetic Orphanet diseases (rare diseases are the focus)
    disease_rows = []
    for d in synth_diseases:
        disease_rows.append({
            "id": d["orpha_id"],
            "name": d["name"],
            "prevalence": d["prevalence"],
            "prevalence_category": d["prevalence_category"],
            "inheritance": d["inheritance"],
            "age_of_onset": d["age_of_onset"],
            "genes": [{"symbol": g, "name": f"{g} gene"} for g in d["genes"]],
            "umls_cui": d["umls_cui"],
            "source": "Orphanet",
        })
    
    # Add ChEMBL diseases (from MeSH headings) — map to UMLS-like IDs
    chembl_diseases = chembl_inds[["mesh_id", "mesh_heading"]].drop_duplicates()
    for _, row in chembl_diseases.iterrows():
        disease_id = f"MESH:{row['mesh_id']}"
        disease_rows.append({
            "id": disease_id,
            "name": row["mesh_heading"],
            "prevalence": 0.0,
            "prevalence_category": "",
            "inheritance": "",
            "age_of_onset": "",
            "genes": [],
            "umls_cui": "",
            "source": "ChEMBL_MeSH",
        })
    
    df_diseases = pd.DataFrame(disease_rows)
    logger.info("unified_diseases", count=len(df_diseases))
    
    # --- Build unified indication table ---
    indication_rows = []
    
    # Synthetic indications (drug -> Orphanet disease)
    for sid, orpha in synth_indications:
        indication_rows.append({
            "struct_id": sid,
            "umls_cui": "",  # Will be filled from disease mapping
            "indication_type": "FDA",
            "max_phase_for_ind": 4,
            "approval_status": "FDA",
            "approval_year": 1995,
            "source": "DrugCentral",
            "disease_id": orpha,
        })
    
    # ChEMBL indications (drug -> MeSH disease)
    for _, row in chembl_inds.iterrows():
        chembl_id = row["drug_id"]
        if chembl_id in drug_id_map:
            indication_rows.append({
                "struct_id": drug_id_map[chembl_id],
                "umls_cui": "",
                "indication_type": "ChEMBL",
                "max_phase_for_ind": int(float(row["max_phase_for_ind"])) if pd.notna(row["max_phase_for_ind"]) else 0,
                "approval_status": "ChEMBL",
                "approval_year": 2000,
                "source": "ChEMBL",
                "disease_id": f"MESH:{row['mesh_id']}",
            })
    
    df_indications = pd.DataFrame(indication_rows)
    logger.info("unified_indications", count=len(df_indications))
    
    # --- Build unified target table ---
    target_rows = []
    
    # Synthetic targets
    for t in synth_targets:
        target_rows.append({
            "target_id": t["target_id"],
            "target_name": t["target_name"],
            "gene": t["gene"],
            "uniprot": t["uniprot"],
            "organism": "Homo sapiens",
            "target_class": t["target_class"],
            "source": "DrugCentral",
        })
    
    # ChEMBL targets
    for _, row in chembl_tgts.iterrows():
        target_rows.append({
            "target_id": f"chembl:{row['target_id']}",
            "target_name": row["target_name"] if pd.notna(row["target_name"]) else "",
            "gene": row["gene"] if pd.notna(row["gene"]) else "",
            "uniprot": row["uniprot"] if pd.notna(row["uniprot"]) else "",
            "organism": row["organism"] if pd.notna(row["organism"]) else "Homo sapiens",
            "target_class": row["target_type"] if pd.notna(row["target_type"]) else "",
            "source": "ChEMBL",
        })
    
    df_targets = pd.DataFrame(target_rows)
    logger.info("unified_targets", count=len(df_targets))
    
    # --- Build unified drug-target table ---
    dt_rows = []
    
    # Synthetic drug-target edges
    for d in synth_drugs:
        # Find matching target by gene
        for t in synth_targets:
            if t["gene"] == d["target_gene"]:
                dt_rows.append({
                    "struct_id": d["struct_id"],
                    "target_id": t["target_id"],
                    "action_type": "modulator",
                    "action_comment": d["moa_class"],
                    "binding_value": 100.0,
                    "binding_unit": "nM",
                    "binding_type": "Kd",
                    "source": "DrugCentral",
                })
                break
    
    # ChEMBL drug-target edges
    for _, row in chembl_mechs.iterrows():
        chembl_id = row["drug_id"]
        if chembl_id in drug_id_map:
            dt_rows.append({
                "struct_id": drug_id_map[chembl_id],
                "target_id": f"chembl:{row['target_id']}",
                "action_type": row["action_type"] if pd.notna(row["action_type"]) else "modulator",
                "action_comment": row["mechanism"] if pd.notna(row["mechanism"]) else "",
                "binding_value": 0.0,
                "binding_unit": "",
                "binding_type": "",
                "source": "ChEMBL",
            })
    
    df_drug_target = pd.DataFrame(dt_rows)
    logger.info("unified_drug_target", count=len(df_drug_target))
    
    # --- Save to parquet ---
    output_dir = OUTPUT_DIR / "drugcentral"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_drugs.to_parquet(output_dir / "drugcentral_fda_approved.parquet", index=False)
    df_indications.to_parquet(output_dir / "drugcentral_indications.parquet", index=False)
    df_targets.to_parquet(output_dir / "drugcentral_targets.parquet", index=False)
    df_drug_target.to_parquet(output_dir / "drugcentral_drug_target.parquet", index=False)
    
    # Save diseases
    orpha_dir = OUTPUT_DIR / "orpha"
    orpha_dir.mkdir(parents=True, exist_ok=True)
    df_diseases.to_parquet(orpha_dir / "orpha_diseases.parquet", index=False)
    
    # Save gene-disease relationships
    gene_disease_rows = []
    for d in synth_diseases:
        for g in d["genes"]:
            gene_disease_rows.append({
                "hgnc_id": f"HGNC:{8000 + hash(g) % 10000}",
                "symbol": g,
                "gene_name": f"{g} gene",
                "orpha_id": d["orpha_id"],
            })
    pd.DataFrame(gene_disease_rows).to_parquet(orpha_dir / "orpha_gene_disease.parquet", index=False)
    
    logger.info("merge_complete", output_dir=str(OUTPUT_DIR))
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"MERGED DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"Drugs: {len(df_drugs)} (ChEMBL: {len(chembl_mols)}, Synthetic: {len(synth_drugs)})")
    print(f"Diseases: {len(df_diseases)} (Orphanet: {len(synth_diseases)}, ChEMBL MeSH: {len(chembl_diseases)})")
    print(f"Indications: {len(df_indications)} (Synthetic: {len(synth_indications)}, ChEMBL: {len(chembl_inds)})")
    print(f"Targets: {len(df_targets)} (Synthetic: {len(synth_targets)}, ChEMBL: {len(chembl_tgts)})")
    print(f"Drug-Target edges: {len(df_drug_target)}")
    print(f"Possible pairs: {len(df_drugs) * len(df_diseases)}")
    print(f"Positive rate: {len(df_indications) / (len(df_drugs) * len(df_diseases)) * 100:.2f}%")
    print(f"{'='*60}")


if __name__ == "__main__":
    merge_datasets()

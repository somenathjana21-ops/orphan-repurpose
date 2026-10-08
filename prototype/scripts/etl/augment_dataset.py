#!/usr/bin/env python3
"""
Augment the synthetic dataset with real ChEMBL data.

Fetches:
  - Molecule structures (SMILES) for drugs with known indications
  - Drug-indication pairs (drug-disease mappings)
  - Drug-target mechanisms

Merges with existing synthetic data to create an expanded dataset
that better approximates real DrugCentral/Orphanet scale.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()

BASE = "https://www.ebi.ac.uk/chembl/api/data"
BATCH_SIZE = 50
MAX_INDICATIONS = 30000
MAX_MOLECULES = 5000


def fetch_chembl(endpoint: str, params: str = "", retries: int = 3) -> dict:
    """Fetch from ChEMBL API with retry logic."""
    url = f"{BASE}/{endpoint}.json?{params}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            logger.error("chembl_fetch_failed", endpoint=endpoint, error=str(e))
            return {}
        except Exception as e:
            logger.error("chembl_fetch_error", endpoint=endpoint, error=str(e))
            return {}
    return {}


def fetch_indications() -> pd.DataFrame:
    """Fetch drug-indication pairs from ChEMBL."""
    indications = []
    offset = 0
    limit = 1000
    
    while len(indications) < MAX_INDICATIONS:
        data = fetch_chembl("drug_indication", f"limit={limit}&offset={offset}")
        inds = data.get("drug_indications", [])
        if not inds:
            break
        
        for ind in inds:
            if ind.get("mesh_id") and ind.get("molecule_chembl_id"):
                indications.append({
                    "drug_id": ind["molecule_chembl_id"],
                    "mesh_id": ind["mesh_id"],
                    "mesh_heading": ind.get("mesh_heading", ""),
                    "efo_id": ind.get("efo_id", ""),
                    "efo_term": ind.get("efo_term", ""),
                    "max_phase_for_ind": ind.get("max_phase_for_ind", 0),
                })
        
        logger.info("indications_fetched", count=len(indications))
        offset += limit
        time.sleep(0.05)
    
    return pd.DataFrame(indications)


def fetch_molecules(drug_ids: list[str]) -> pd.DataFrame:
    """Fetch molecule structures for given ChEMBL drug IDs."""
    molecules = []
    
    for i in range(0, len(drug_ids), BATCH_SIZE):
        batch = drug_ids[i:i + BATCH_SIZE]
        ids_param = ",".join(batch)
        
        try:
            data = fetch_chembl("molecule", f"molecule_chembl_id__in={ids_param}&limit={BATCH_SIZE}")
            mols = data.get("molecules", [])
            
            for m in mols:
                if m.get("molecule_type") != "Small molecule":
                    continue
                structs = m.get("molecule_structures")
                if not structs or not structs.get("canonical_smiles"):
                    continue
                
                molecules.append({
                    "chembl_id": m.get("molecule_chembl_id"),
                    "name": m.get("pref_name", ""),
                    "smiles": structs["canonical_smiles"],
                    "max_phase": m.get("max_phase", 0),
                    "first_approval": m.get("first_approval"),
                    "molecule_type": m.get("molecule_type", "Small molecule"),
                })
            
            logger.info("molecules_fetched", count=len(molecules), batch=i // BATCH_SIZE)
            time.sleep(0.05)
            
            if len(molecules) >= MAX_MOLECULES:
                break
        except Exception as e:
            logger.warning("molecule_batch_failed", batch=i // BATCH_SIZE, error=str(e))
            continue
    
    return pd.DataFrame(molecules)


def fetch_mechanisms(drug_ids: list[str]) -> pd.DataFrame:
    """Fetch drug-target mechanisms from ChEMBL."""
    mechanisms = []
    
    for i in range(0, len(drug_ids), BATCH_SIZE):
        batch = drug_ids[i:i + BATCH_SIZE]
        ids_param = ",".join(batch)
        
        try:
            data = fetch_chembl("mechanism", f"molecule_chembl_id__in={ids_param}&limit={BATCH_SIZE}")
            mechs = data.get("mechanisms", [])
            
            for m in mechs:
                mechanisms.append({
                    "drug_id": m.get("molecule_chembl_id"),
                    "target_id": m.get("target_chembl_id"),
                    "mechanism": m.get("mechanism_of_action", ""),
                    "action_type": m.get("action_type", ""),
                })
            
            logger.info("mechanisms_fetched", count=len(mechanisms), batch=i // BATCH_SIZE)
            time.sleep(0.05)
        except Exception as e:
            logger.warning("mechanism_batch_failed", batch=i // BATCH_SIZE, error=str(e))
            continue
    
    return pd.DataFrame(mechanisms)


def fetch_target_details(target_ids: list[str]) -> pd.DataFrame:
    """Fetch target details (gene symbols, UniProt) from ChEMBL."""
    targets = []
    
    # Filter out non-string IDs (NaN floats)
    target_ids = [str(t) for t in target_ids if isinstance(t, str) or not pd.isna(t)]
    
    for i in range(0, len(target_ids), BATCH_SIZE):
        batch = target_ids[i:i + BATCH_SIZE]
        ids_param = ",".join(batch)
        
        try:
            data = fetch_chembl("target", f"target_chembl_id__in={ids_param}&limit={BATCH_SIZE}")
            tgt_list = data.get("targets", [])
            
            for t in tgt_list:
                components = t.get("target_components", [])
                gene = ""
                uniprot = ""
                if components:
                    gene = components[0].get("description", "")
                    uniprot = t.get("target_components", [{}])[0].get("accession", "")
                
                targets.append({
                    "target_id": t.get("target_chembl_id"),
                    "target_name": t.get("pref_name", ""),
                    "gene": gene,
                    "uniprot": uniprot,
                    "organism": t.get("organism", ""),
                    "target_type": t.get("target_type", ""),
                })
            
            logger.info("targets_fetched", count=len(targets), batch=i // BATCH_SIZE)
            time.sleep(0.05)
        except Exception as e:
            logger.warning("target_batch_failed", batch=i // BATCH_SIZE, error=str(e))
            continue
    
    return pd.DataFrame(targets)


def main():
    output_dir = Path("/root/chembl_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Fetch indications
    logger.info("step1_fetch_indications")
    df_ind = fetch_indications()
    df_ind.to_csv(output_dir / "chembl_indications.csv", index=False)
    logger.info("indications_saved", count=len(df_ind), path=str(output_dir / "chembl_indications.csv"))
    
    # Step 2: Fetch molecules for drugs with indications
    drug_ids = df_ind["drug_id"].unique().tolist()[:2000]  # Limit for speed
    logger.info("step2_fetch_molecules", drug_count=len(drug_ids))
    df_mol = fetch_molecules(drug_ids)
    df_mol.to_csv(output_dir / "chembl_molecules.csv", index=False)
    logger.info("molecules_saved", count=len(df_mol), path=str(output_dir / "chembl_molecules.csv"))
    
    # Step 3: Fetch mechanisms
    mech_drug_ids = df_mol["chembl_id"].unique().tolist()[:1000]
    logger.info("step3_fetch_mechanisms", drug_count=len(mech_drug_ids))
    df_mech = fetch_mechanisms(mech_drug_ids)
    df_mech.to_csv(output_dir / "chembl_mechanisms.csv", index=False)
    logger.info("mechanisms_saved", count=len(df_mech), path=str(output_dir / "chembl_mechanisms.csv"))
    
    # Step 4: Fetch target details
    if len(df_mech) > 0:
        target_ids = df_mech["target_id"].unique().tolist()[:500]
        logger.info("step4_fetch_targets", target_count=len(target_ids))
        df_tgt = fetch_target_details(target_ids)
        df_tgt.to_csv(output_dir / "chembl_targets.csv", index=False)
        logger.info("targets_saved", count=len(df_tgt), path=str(output_dir / "chembl_targets.csv"))
    
    logger.info("augment_dataset_complete", output_dir=str(output_dir))


if __name__ == "__main__":
    main()

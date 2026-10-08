#!/usr/bin/env python3
"""
Compute molecular fingerprints for drugs.
Generates Morgan fingerprints (1024-bit), MACCS keys, RDKit descriptors.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import structlog
from tqdm import tqdm
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys, Descriptors
from rdkit.Chem.rdMolDescriptors import GetMorganFingerprintAsBitVect
import pickle

logger = structlog.get_logger()


def compute_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 1024) -> np.ndarray:
    """Compute Morgan fingerprint (ECFP) for a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_bits, dtype=np.uint8)
        fp = GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros(n_bits, dtype=np.uint8)
        for idx in fp.GetOnBits():
            arr[idx] = 1
        return arr
    except Exception:
        return np.zeros(n_bits, dtype=np.uint8)


def compute_maccs_keys(smiles: str) -> np.ndarray:
    """Compute MACCS keys (166 bits) for a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(167, dtype=np.uint8)  # 166 keys + 1
        fp = MACCSkeys.GenMACCSKeys(mol)
        arr = np.zeros(167, dtype=np.uint8)
        for idx in fp.GetOnBits():
            arr[idx] = 1
        return arr
    except Exception:
        return np.zeros(167, dtype=np.uint8)


def compute_rdkit_descriptors(smiles: str) -> dict:
    """Compute RDKit molecular descriptors."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}
        
        descriptors = {}
        for name, func in Descriptors.descList:
            try:
                descriptors[name] = func(mol)
            except Exception:
                descriptors[name] = np.nan
        return descriptors
    except Exception:
        return {}


def compute_molecular_features(df: pd.DataFrame, smiles_col: str = 'smiles', id_col: str = 'struct_id') -> dict:
    """Compute all molecular features for a DataFrame of drugs."""
    logger.info("computing_molecular_features", n_drugs=len(df))
    
    morgan_fps = []
    maccs_fps = []
    descriptors_list = []
    valid_indices = []
    valid_ids = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Computing fingerprints"):
        smiles = row[smiles_col]
        drug_id = row[id_col]
        
        if pd.isna(smiles) or not isinstance(smiles, str):
            continue
        
        morgan = compute_morgan_fingerprint(smiles)
        maccs = compute_maccs_keys(smiles)
        desc = compute_rdkit_descriptors(smiles)
        
        morgan_fps.append(morgan)
        maccs_fps.append(maccs)
        descriptors_list.append(desc)
        valid_indices.append(idx)
        valid_ids.append(drug_id)
    
    # Stack arrays
    morgan_array = np.stack(morgan_fps) if morgan_fps else np.array([])
    maccs_array = np.stack(maccs_fps) if maccs_fps else np.array([])
    
    # Descriptors to DataFrame
    desc_df = pd.DataFrame(descriptors_list, index=valid_ids)
    
    logger.info("molecular_features_computed", 
                n_valid=len(valid_ids), 
                morgan_shape=morgan_array.shape,
                maccs_shape=maccs_array.shape,
                n_descriptors=len(desc_df.columns))
    
    return {
        'morgan': morgan_array,
        'maccs': maccs_array,
        'descriptors': desc_df,
        'valid_ids': valid_ids,
        'valid_indices': valid_indices,
    }


def save_molecular_features(features: dict, output_dir: Path):
    """Save molecular features to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save fingerprints as compressed numpy
    np.savez_compressed(output_dir / 'morgan_fingerprints.npz', 
                        fingerprints=features['morgan'],
                        ids=np.array(features['valid_ids']))
    
    np.savez_compressed(output_dir / 'maccs_fingerprints.npz',
                        fingerprints=features['maccs'],
                        ids=np.array(features['valid_ids']))
    
    # Save descriptors as parquet
    features['descriptors'].to_parquet(output_dir / 'rdkit_descriptors.parquet')
    
    # Save metadata
    metadata = {
        'n_drugs': len(features['valid_ids']),
        'morgan_bits': features['morgan'].shape[1] if len(features['morgan']) > 0 else 1024,
        'maccs_bits': features['maccs'].shape[1] if len(features['maccs']) > 0 else 167,
        'descriptor_names': list(features['descriptors'].columns),
        'valid_ids': features['valid_ids'],
    }
    
    with open(output_dir / 'molecular_features_metadata.json', 'w') as f:
        import json
        json.dump(metadata, f, indent=2)
    
    logger.info("molecular_features_saved", output_dir=str(output_dir))


def load_molecular_features(input_dir: Path) -> dict:
    """Load molecular features from disk."""
    morgan_data = np.load(input_dir / 'morgan_fingerprints.npz')
    maccs_data = np.load(input_dir / 'maccs_fingerprints.npz')
    descriptors = pd.read_parquet(input_dir / 'rdkit_descriptors.parquet')
    
    return {
        'morgan': morgan_data['fingerprints'],
        'maccs': maccs_data['fingerprints'],
        'descriptors': descriptors,
        'valid_ids': list(morgan_data['ids']),
    }


def main(processed_dir: Path, output_dir: Path):
    """Main function to compute molecular features for FDA-approved drugs."""
    # Load FDA-approved drugs
    fda_path = processed_dir / "drugcentral" / "drugcentral_fda_approved.parquet"
    if not fda_path.exists():
        logger.error("fda_approved_not_found", path=str(fda_path))
        return
    
    df = pd.read_parquet(fda_path)
    logger.info("loaded_fda_drugs", count=len(df))
    
    # Compute features
    features = compute_molecular_features(df)
    
    # Save
    save_molecular_features(features, output_dir)
    
    logger.info("molecular_features_pipeline_complete")


if __name__ == "__main__":
    import sys
    processed_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data/processed")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/molecular")
    main(processed_dir, output_dir)
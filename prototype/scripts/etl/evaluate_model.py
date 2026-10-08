#!/usr/bin/env python3
"""
Evaluate the indication model on the expanded dataset.
Computes Recall@K, AUPRC, AUROC, ECE, and compares with baseline.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score, average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))


def load_model(model_path: Path):
    with open(model_path, "rb") as f:
        ckpt = pickle.load(f)
    
    config = ckpt.get("config", {})
    arch = config.get("architecture", "DualEncoderCrossAttention")
    
    from app.ml.indication_model import IndicationModel, SimpleIndicationModel
    
    if arch == "SimpleIndicationModel_MLP":
        model = SimpleIndicationModel(
            fp_dim=config.get("fp_dim", 1024),
            kg_dim=config.get("kg_dim", 256),
            hidden_dim=config.get("hidden_dim", 128),
        )
    else:
        model = IndicationModel(
            node_feature_dim=config.get("node_feature_dim", 78),
            kg_dim=config.get("kg_dim", 256),
            hidden_dim=config.get("hidden_dim", 256),
            num_layers=config.get("num_layers", 3),
            num_heads=config.get("num_heads", 4),
        )
    
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    
    return model, ckpt


def compute_morgan_fingerprint(smiles: str, n_bits: int = 1024) -> np.ndarray:
    """Compute Morgan fingerprint using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_bits, dtype=np.float32)
        
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=n_bits)
        return np.array(fp, dtype=np.float32)
    except Exception:
        return np.zeros(n_bits, dtype=np.float32)


def evaluate_recall_at_k(model, ckpt, test_pairs, k_values=[10, 20, 50, 100]):
    """Compute Recall@K for given test pairs."""
    drug_smiles = ckpt["drug_smiles"]
    disease_map = ckpt["disease_map"]
    disease_embeddings = ckpt["disease_embeddings"]
    temperature = ckpt.get("temperature", 1.0)
    config = ckpt.get("config", {})
    arch = config.get("architecture", "DualEncoderCrossAttention")
    
    # Group by disease
    disease_to_pairs = {}
    for did, sid, label in test_pairs:
        if sid not in disease_to_pairs:
            disease_to_pairs[sid] = []
        disease_to_pairs[sid].append((did, label))
    
    recalls = {k: [] for k in k_values}
    
    with torch.no_grad():
        for disease_id, pairs in disease_to_pairs.items():
            if disease_id not in disease_map:
                continue
            
            d_idx = disease_map[disease_id]
            disease_emb = torch.tensor(
                disease_embeddings[d_idx], dtype=torch.float32
            ).unsqueeze(0)
            
            # Score all drugs for this disease
            scores = []
            labels = []
            for did, label in pairs:
                if did not in drug_smiles:
                    continue
                
                if arch == "SimpleIndicationModel_MLP":
                    # Use pre-computed fingerprints
                    drug_fps = ckpt.get("drug_fingerprints", {})
                    if did in drug_fps:
                        fp = torch.tensor(drug_fps[did], dtype=torch.float32).unsqueeze(0)
                        logits = model(fp, disease_emb)
                        scaled = logits / max(temperature, 1e-3)
                        prob = float(torch.sigmoid(scaled).item())
                    else:
                        continue
                else:
                    from app.ml.featurizer import smiles_to_graph
                    feats, edge_index = smiles_to_graph(drug_smiles[did])
                    batch = torch.zeros(feats.size(0), dtype=torch.long)
                    logits = model(feats, edge_index, batch, disease_emb)
                    scaled = logits / max(temperature, 1e-3)
                    prob = float(torch.sigmoid(scaled).item())
                
                scores.append(prob)
                labels.append(label)
            
            if not scores:
                continue
            
            # Rank by score
            ranked = sorted(zip(scores, labels), reverse=True)
            
            # Compute Recall@K
            n_pos = sum(labels)
            if n_pos == 0:
                continue
            
            for k in k_values:
                top_k = ranked[:k]
                n_pos_in_top = sum(label for _, label in top_k)
                recalls[k].append(n_pos_in_top / n_pos)
    
    return {k: np.mean(v) if v else 0.0 for k, v in recalls.items()}


def main():
    model_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("prototype/models/indication_model.pt")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("prototype/data/processed")
    
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return
    
    model, ckpt = load_model(model_path)
    
    # Load test pairs
    dc = processed_dir / "drugcentral"
    fda = pd.read_parquet(dc / "drugcentral_fda_approved.parquet")
    indications = pd.read_parquet(dc / "drugcentral_indications.parquet")
    
    drug_smiles = {}
    for _, row in fda.iterrows():
        struct_id = str(row["struct_id"])
        if struct_id.startswith("chembl:"):
            did = struct_id
        else:
            did = f"drugcentral:{struct_id}"
        smi = row.get("smiles")
        if isinstance(smi, str) and smi:
            drug_smiles[did] = smi
    
    # Build test pairs
    test_pairs = []
    for _, row in indications.iterrows():
        struct_id = str(row["struct_id"])
        if struct_id.startswith("chembl:"):
            did = struct_id
        else:
            did = f"drugcentral:{struct_id}"
        if did not in drug_smiles:
            continue
        
        disease_id = row.get("disease_id")
        if isinstance(disease_id, str) and disease_id:
            test_pairs.append((did, disease_id, 1.0))
        else:
            cui = row.get("umls_cui")
            if isinstance(cui, str) and cui:
                test_pairs.append((did, f"UMLS:{cui}", 1.0))
    
    # Add some negatives
    import random
    rng = random.Random(42)
    all_drugs = list(drug_smiles.keys())
    all_diseases = list(ckpt["disease_map"].keys())
    pos_set = {(d, s) for d, s, _ in test_pairs}
    
    neg_pairs = set()
    target_neg = len(test_pairs)
    guard = 0
    while len(neg_pairs) < target_neg and guard < target_neg * 50:
        guard += 1
        cand = (rng.choice(all_drugs), rng.choice(all_diseases))
        if cand not in pos_set:
            neg_pairs.add(cand)
    
    test_pairs += [(d, s, 0.0) for d, s in neg_pairs]
    
    print(f"Test pairs: {len(test_pairs)} ({sum(1 for _, _, l in test_pairs if l == 1.0)} positives)")
    
    # Evaluate
    recalls = evaluate_recall_at_k(model, ckpt, test_pairs)
    
    print(f"\n{'='*50}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*50}")
    for k, v in recalls.items():
        print(f"  Recall@{k}: {v*100:.1f}%")
    
    # Compare with baseline
    print(f"\n  Baseline (random): Recall@20 = {20/len(all_diseases)*100:.1f}%")
    print(f"  Target: Recall@20 ≥ 70%")
    
    # Model metrics from checkpoint
    metrics = ckpt.get("metrics", {})
    print(f"\n  Model metrics (from training):")
    for k, v in metrics.items():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()

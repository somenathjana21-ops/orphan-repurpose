#!/usr/bin/env python3
"""
Ultra-fast indication model training — no GNN, pure MLP on Morgan fingerprints.

This is a lightweight alternative to the full DualEncoderCrossAttention model
for CPU-constrained environments. Uses pre-computed Morgan fingerprints
instead of graph convolutions.
"""
from __future__ import annotations

import pickle
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import structlog

logger = structlog.get_logger()
SEED = 42


class MorganFingerprintEncoder(nn.Module):
    """Simple MLP encoder for Morgan fingerprints."""
    
    def __init__(self, input_dim: int = 1024, hidden_dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.output_dim = hidden_dim
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SimpleIndicationModel(nn.Module):
    """MLP-based indication model: drug_fp + disease_emb -> score."""
    
    def __init__(self, fp_dim: int = 1024, kg_dim: int = 256, hidden_dim: int = 128):
        super().__init__()
        self.drug_encoder = MorganFingerprintEncoder(fp_dim, hidden_dim)
        self.disease_proj = nn.Sequential(
            nn.Linear(kg_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
        )
        # Fusion: concat + MLP
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
    
    def forward(self, drug_fp: torch.Tensor, disease_kg: torch.Tensor) -> torch.Tensor:
        d_emb = self.drug_encoder(drug_fp)
        s_emb = self.disease_proj(disease_kg)
        fused = torch.cat([d_emb, s_emb], dim=-1)
        return self.fusion(fused).squeeze(-1)


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


def train_ultra_fast(
    processed_dir: Path,
    kg_embeddings_path: Path,
    output_path: Path,
    epochs: int = 5,
    batch_size: int = 512,
    lr: float = 1e-3,
    hidden_dim: int = 128,
    max_train_pairs: int = 5000,
    max_val_pairs: int = 1000,
):
    """Train ultra-fast indication model."""
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("training_start", device=str(device))
    
    # Load KG embeddings
    with open(kg_embeddings_path, "rb") as f:
        kg = pickle.load(f)
    
    disease_embs = kg["embeddings"]["Disease"]
    disease_map = kg["node_id_maps"]["Disease"]
    
    # Load data
    dc = processed_dir / "drugcentral"
    fda = pd.read_parquet(dc / "drugcentral_fda_approved.parquet")
    indications = pd.read_parquet(dc / "drugcentral_indications.parquet")
    
    # Build drug smiles map
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
    
    # Build positive pairs
    pos_pairs = set()
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
            if disease_id in disease_map:
                pos_pairs.add((did, disease_id))
        else:
            cui = row.get("umls_cui")
            if isinstance(cui, str) and cui:
                d_id = f"UMLS:{cui}"
                if d_id in disease_map:
                    pos_pairs.add((did, d_id))
    
    logger.info("positive_pairs", count=len(pos_pairs))
    
    # Build negative pairs
    all_drugs = list(drug_smiles.keys())
    all_diseases = list(disease_map.keys())
    neg_pairs = set()
    rng = random.Random(SEED)
    target_neg = len(pos_pairs)
    guard = 0
    while len(neg_pairs) < target_neg and guard < target_neg * 50:
        guard += 1
        cand = (rng.choice(all_drugs), rng.choice(all_diseases))
        if cand not in pos_pairs:
            neg_pairs.add(cand)
    
    pairs = [(d, s, 1.0) for d, s in pos_pairs] + [(d, s, 0.0) for d, s in neg_pairs]
    rng.shuffle(pairs)
    
    # Split
    pos_list = [p for p in pairs if p[2] == 1.0]
    neg_list = [p for p in pairs if p[2] == 0.0]
    
    def split(lst):
        k = len(lst)
        a = int(0.7 * k)
        b = int(0.85 * k)
        return lst[:a], lst[a:b], lst[b:]
    
    ptr, pva, pcal = split(pos_list)
    ntr, nva, ncal = split(neg_list)
    train_pairs = ptr + ntr
    val_pairs = pva + nva
    cal_pairs = pcal + ncal
    
    # Downsample
    if len(train_pairs) > max_train_pairs:
        rng2 = random.Random(SEED)
        rng2.shuffle(train_pairs)
        train_pairs = train_pairs[:max_train_pairs]
    if len(val_pairs) > max_val_pairs:
        rng2 = random.Random(SEED + 1)
        rng2.shuffle(val_pairs)
        val_pairs = val_pairs[:max_val_pairs]
    
    logger.info("splits", train=len(train_pairs), val=len(val_pairs), cal=len(cal_pairs))
    
    # Pre-compute Morgan fingerprints
    logger.info("computing_morgan_fingerprints", count=len(drug_smiles))
    drug_fps = {}
    for did, smi in drug_smiles.items():
        drug_fps[did] = compute_morgan_fingerprint(smi)
    
    # Pre-compute disease tensors
    disease_tensors = {}
    for did in all_diseases:
        idx = disease_map[did]
        disease_tensors[did] = torch.tensor(disease_embs[idx], dtype=torch.float32)
    
    # Create model
    model = SimpleIndicationModel(fp_dim=1024, kg_dim=256, hidden_dim=hidden_dim).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=3)
    criterion = nn.BCEWithLogitsLoss()
    
    def run_batch(batch):
        fps = []
        diseases = []
        labels = []
        for did, sid, y in batch:
            if did in drug_fps and sid in disease_tensors:
                fps.append(torch.tensor(drug_fps[did]))
                diseases.append(disease_tensors[sid])
                labels.append(y)
        
        if not fps:
            return None, None
        
        fp_tensor = torch.stack(fps).to(device)
        disease_tensor = torch.stack(diseases).to(device)
        target = torch.tensor(labels, dtype=torch.float32, device=device)
        
        logits = model(fp_tensor, disease_tensor)
        return logits, target
    
    def evaluate(pair_list):
        model.eval()
        all_logits, all_targets = [], []
        with torch.no_grad():
            for i in range(0, len(pair_list), batch_size):
                batch = pair_list[i:i + batch_size]
                logits, target = run_batch(batch)
                if logits is not None:
                    all_logits.append(logits.cpu())
                    all_targets.append(target.cpu())
        if not all_logits:
            return torch.zeros(0), torch.zeros(0)
        return torch.cat(all_logits), torch.cat(all_targets)
    
    # Training loop
    best_auprc = -1.0
    best_state = None
    patience = 0
    
    for epoch in range(epochs):
        model.train()
        rng = random.Random(SEED + epoch)
        shuffled = train_pairs[:]
        rng.shuffle(shuffled)
        
        total_loss = 0.0
        n_batches = 0
        
        for i in range(0, len(shuffled), batch_size):
            batch = shuffled[i:i + batch_size]
            optimizer.zero_grad()
            logits, target = run_batch(batch)
            if logits is None:
                continue
            loss = criterion(logits, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        
        scheduler.step()
        
        val_logits, val_targets = evaluate(val_pairs)
        probs = torch.sigmoid(val_logits)
        
        auroc = auprc = float("nan")
        try:
            from sklearn.metrics import roc_auc_score, average_precision_score
            y = val_targets.detach().cpu().numpy()
            p = probs.detach().cpu().numpy()
            if len(set(y.tolist())) > 1:
                auroc = float(roc_auc_score(y, p))
                auprc = float(average_precision_score(y, p))
        except Exception:
            pass
        
        avg_loss = total_loss / max(n_batches, 1)
        logger.info(
            "epoch", epoch=epoch, loss=round(avg_loss, 4),
            val_auroc=round(auroc, 4) if auroc == auroc else None,
            val_auprc=round(auprc, 4) if auprc == auprc else None,
        )
        
        if auprc == auprc and auprc > best_auprc:
            best_auprc = auprc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if patience >= 3:
            logger.info("early_stopping", epoch=epoch)
            break
    
    # Load best
    if best_state is not None:
        model.load_state_dict(best_state)
    
    # Calibration
    model.eval()
    cal_logits, cal_targets = evaluate(cal_pairs)
    
    # Temperature scaling
    from app.ml.indication_model import TemperatureScaler, ConformalPredictor
    scaler = TemperatureScaler()
    temp = scaler.fit(cal_logits, cal_targets) if len(cal_logits) else 1.0
    cal_probs = torch.sigmoid(scaler(cal_logits)) if len(cal_logits) else torch.zeros(0)
    conformal = ConformalPredictor(coverage=0.90)
    conformal.calibrate(cal_probs, cal_targets)
    
    test_logits, test_targets = evaluate(cal_pairs)
    test_probs = torch.sigmoid(scaler(test_logits)) if len(test_logits) else torch.zeros(0)
    
    test_metrics = {"auroc": float("nan"), "auprc": float("nan"), "ece": 0.0}
    try:
        from sklearn.metrics import roc_auc_score, average_precision_score
        y = test_targets.detach().cpu().numpy()
        p = test_probs.detach().cpu().numpy()
        if len(set(y.tolist())) > 1:
            test_metrics["auroc"] = float(roc_auc_score(y, p))
            test_metrics["auprc"] = float(average_precision_score(y, p))
    except Exception:
        pass
    
    # ECE
    if len(test_probs):
        bins = torch.linspace(0, 1, 11)
        for b in range(10):
            lo, hi = bins[b], bins[b + 1]
            mask = (test_probs >= lo) & (test_probs < hi if b < 9 else test_probs <= hi)
            if mask.sum() > 0:
                conf = test_probs[mask].mean().item()
                acc = test_targets[mask].mean().item()
                test_metrics["ece"] += (mask.sum().item() / len(test_probs)) * abs(conf - acc)
    
    logger.info(
        "final_metrics",
        temperature=round(temp, 4),
        conformal_q=round(conformal.q_hat or 0.0, 4),
        auprc=round(test_metrics["auprc"], 4) if test_metrics["auprc"] == test_metrics["auprc"] else None,
        auroc=round(test_metrics["auroc"], 4) if test_metrics["auroc"] == test_metrics["auroc"] else None,
        ece=round(test_metrics["ece"], 4),
    )
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(
            {
                "model_state_dict": model.state_dict(),
                "hidden_dim": hidden_dim,
                "temperature": temp,
                "conformal_q": conformal.q_hat,
                "drug_smiles": drug_smiles,
                "drug_fingerprints": drug_fps,
                "disease_map": disease_map,
                "disease_embeddings": disease_embs,
                "config": {
                    "architecture": "SimpleIndicationModel_MLP",
                    "fp_dim": 1024,
                    "kg_dim": 256,
                    "hidden_dim": hidden_dim,
                    "coverage": 0.90,
                },
                "metrics": test_metrics,
            },
            f,
        )
    logger.info("model_saved", path=str(output_path))


if __name__ == "__main__":
    processed = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../../data/processed")
    kg_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("../../models/kg_embeddings.pkl")
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("../../models/indication_model.pt")
    train_ultra_fast(processed, kg_path, out)

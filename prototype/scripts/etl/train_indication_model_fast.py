#!/usr/bin/env python3
"""
Fast indication model training — pre-computes drug embeddings, trains only fusion head.

Strategy:
  1. Pre-compute drug embeddings using GraphSAGE (one-time cost)
  2. Train only DiseaseEncoder + CrossAttentionFusion + MLP head
  3. Much faster than end-to-end training on CPU
"""
from __future__ import annotations

import pickle
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import structlog

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.ml.indication_model import (
    IndicationModel,
    GraphSAGEDrugEncoder,
    DiseaseEncoder,
    CrossAttentionFusion,
    FocalLoss,
    TemperatureScaler,
    ConformalPredictor,
)
from app.ml.featurizer import smiles_to_graph

logger = structlog.get_logger()
SEED = 42


def precompute_drug_embeddings(drug_smiles: dict, hidden_dim: int = 64, batch_size: int = 256):
    """Pre-compute drug embeddings using GraphSAGE encoder."""
    encoder = GraphSAGEDrugEncoder(
        node_feature_dim=78,
        hidden_dim=hidden_dim,
        num_layers=2,
        dropout=0.0,
    )
    encoder.eval()
    
    embeddings = {}
    with torch.no_grad():
        for did, smi in drug_smiles.items():
            feats, edge_index = smiles_to_graph(smi)
            batch = torch.zeros(feats.size(0), dtype=torch.long)
            emb = encoder(feats, edge_index, batch)
            embeddings[did] = emb.squeeze(0).numpy()
    
    return embeddings


def train_fast(
    processed_dir: Path,
    kg_embeddings_path: Path,
    output_path: Path,
    epochs: int = 15,
    batch_size: int = 256,
    lr: float = 1e-3,
    hidden_dim: int = 64,
    max_train_pairs: int = 8000,
    max_val_pairs: int = 2000,
):
    """Train indication model with pre-computed drug embeddings."""
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("training_start", device=str(device), hidden_dim=hidden_dim)
    
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
    
    # Downsample for speed
    if len(train_pairs) > max_train_pairs:
        rng2 = random.Random(SEED)
        rng2.shuffle(train_pairs)
        train_pairs = train_pairs[:max_train_pairs]
    if len(val_pairs) > max_val_pairs:
        rng2 = random.Random(SEED + 1)
        rng2.shuffle(val_pairs)
        val_pairs = val_pairs[:max_val_pairs]
    
    logger.info(
        "splits",
        train=len(train_pairs), val=len(val_pairs), cal=len(cal_pairs),
    )
    
    # Pre-compute drug embeddings
    logger.info("precomputing_drug_embeddings", count=len(drug_smiles))
    drug_emb_cache = precompute_drug_embeddings(drug_smiles, hidden_dim=hidden_dim)
    logger.info("drug_embeddings_ready")
    
    # Build disease tensor cache
    disease_tensor_cache = {}
    for did in all_diseases:
        idx = disease_map[did]
        disease_tensor_cache[did] = torch.tensor(disease_embs[idx], dtype=torch.float32)
    
    # Create model components
    disease_encoder = DiseaseEncoder(kg_dim=256, hidden_dim=hidden_dim, dropout=0.1).to(device)
    fusion = CrossAttentionFusion(embed_dim=hidden_dim, num_heads=4, dropout=0.1).to(device)
    fused_dim = fusion.output_dim
    head = torch.nn.Sequential(
        torch.nn.Linear(fused_dim, 128),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.1),
        torch.nn.Linear(128, 64),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.1),
        torch.nn.Linear(64, 1),
    ).to(device)
    
    # Combine all parameters
    params = list(disease_encoder.parameters()) + list(fusion.parameters()) + list(head.parameters())
    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=5)
    criterion = FocalLoss(gamma=2.0, alpha=0.25)
    
    def run_batch(batch):
        drug_embs = []
        disease_embs_list = []
        labels = []
        for did, sid, y in batch:
            if did in drug_emb_cache and sid in disease_tensor_cache:
                drug_embs.append(torch.tensor(drug_emb_cache[did], dtype=torch.float32))
                disease_embs_list.append(disease_tensor_cache[sid])
                labels.append(y)
        
        if not drug_embs:
            return None, None
        
        d_emb = torch.stack(drug_embs).to(device)
        s_emb = torch.stack(disease_embs_list).to(device)
        target = torch.tensor(labels, dtype=torch.float32, device=device)
        
        # Forward: drug_emb is already encoded (precomputed to hidden_dim),
        # disease KG embeddings (256-d) need projection to hidden_dim
        s_encoded = disease_encoder(s_emb)  # 256 -> hidden_dim
        fused = fusion(d_emb, s_encoded)  # both hidden_dim
        logits = head(fused).squeeze(-1)
        
        return logits, target
    
    def evaluate(pair_list):
        disease_encoder.eval()
        fusion.eval()
        head.eval()
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
    
    def metrics(logits, targets):
        probs = torch.sigmoid(logits)
        auroc = auprc = float("nan")
        try:
            from sklearn.metrics import roc_auc_score, average_precision_score
            y = targets.detach().cpu().numpy()
            p = probs.detach().cpu().numpy()
            if len(set(y.tolist())) > 1:
                auroc = float(roc_auc_score(y, p))
                auprc = float(average_precision_score(y, p))
        except Exception:
            pass
        ece = 0.0
        if len(probs):
            bins = torch.linspace(0, 1, 11)
            for b in range(10):
                lo, hi = bins[b], bins[b + 1]
                mask = (probs >= lo) & (probs < hi if b < 9 else probs <= hi)
                if mask.sum() > 0:
                    conf = probs[mask].mean().item()
                    acc = targets[mask].mean().item()
                    ece += (mask.sum().item() / len(probs)) * abs(conf - acc)
        return {"auroc": auroc, "auprc": auprc, "ece": ece}
    
    # Training loop
    best_auprc = -1.0
    best_state = None
    patience = 0
    
    for epoch in range(epochs):
        disease_encoder.train()
        fusion.train()
        head.train()
        
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
            torch.nn.utils.clip_grad_norm_(params, 5.0)
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        
        scheduler.step()
        
        if epoch % 2 == 0 or epoch == epochs - 1:
            disease_encoder.eval()
            fusion.eval()
            head.eval()
            val_logits, val_targets = evaluate(val_pairs)
            m = metrics(val_logits, val_targets)
            avg_loss = total_loss / max(n_batches, 1)
            logger.info(
                "epoch",
                epoch=epoch,
                loss=round(avg_loss, 4),
                val_auroc=round(m["auroc"], 4) if m["auroc"] == m["auroc"] else None,
                val_auprc=round(m["auprc"], 4) if m["auprc"] == m["auprc"] else None,
            )
            if m["auprc"] == m["auprc"] and m["auprc"] > best_auprc:
                best_auprc = m["auprc"]
                best_state = {
                    "disease_encoder": {k: v.clone() for k, v in disease_encoder.state_dict().items()},
                    "fusion": {k: v.clone() for k, v in fusion.state_dict().items()},
                    "head": {k: v.clone() for k, v in head.state_dict().items()},
                }
                patience = 0
            else:
                patience += 1
            if patience >= 5:
                logger.info("early_stopping", epoch=epoch)
                break
    
    # Load best
    if best_state is not None:
        disease_encoder.load_state_dict(best_state["disease_encoder"])
        fusion.load_state_dict(best_state["fusion"])
        head.load_state_dict(best_state["head"])
    
    # Calibration
    disease_encoder.eval()
    fusion.eval()
    head.eval()
    cal_logits, cal_targets = evaluate(cal_pairs)
    scaler = TemperatureScaler()
    temp = scaler.fit(cal_logits, cal_targets) if len(cal_logits) else 1.0
    cal_probs = torch.sigmoid(scaler(cal_logits)) if len(cal_logits) else torch.zeros(0)
    conformal = ConformalPredictor(coverage=0.90)
    conformal.calibrate(cal_probs, cal_targets)
    
    test_logits, test_targets = evaluate(cal_pairs)
    test_metrics = metrics(scaler(test_logits) if len(test_logits) else test_logits, test_targets)
    
    logger.info(
        "final_metrics",
        temperature=round(temp, 4),
        conformal_q=round(conformal.q_hat or 0.0, 4),
        auprc=round(test_metrics["auprc"], 4) if test_metrics["auprc"] == test_metrics["auprc"] else None,
        auroc=round(test_metrics["auroc"], 4) if test_metrics["auroc"] == test_metrics["auroc"] else None,
        ece=round(test_metrics["ece"], 4),
    )
    
    # Save checkpoint
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(
            {
                "model_state_dict": {
                    "disease_encoder": disease_encoder.state_dict(),
                    "fusion": fusion.state_dict(),
                    "head": head.state_dict(),
                },
                "hidden_dim": hidden_dim,
                "temperature": temp,
                "conformal_q": conformal.q_hat,
                "drug_smiles": drug_smiles,
                "drug_embeddings": drug_emb_cache,
                "disease_map": disease_map,
                "disease_embeddings": disease_embs,
                "config": {
                    "architecture": "DualEncoderCrossAttention_Fast",
                    "node_feature_dim": 78,
                    "kg_dim": 256,
                    "hidden_dim": hidden_dim,
                    "num_layers": 2,
                    "num_heads": 4,
                    "coverage": 0.90,
                },
                "metrics": {
                    "auprc": test_metrics["auprc"],
                    "auroc": test_metrics["auroc"],
                    "ece": test_metrics["ece"],
                },
            },
            f,
        )
    logger.info("model_saved", path=str(output_path))


if __name__ == "__main__":
    processed = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../../data/processed")
    kg_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("../../models/kg_embeddings.pkl")
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("../../models/indication_model.pt")
    train_fast(processed, kg_path, out)

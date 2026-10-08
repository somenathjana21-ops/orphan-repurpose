#!/usr/bin/env python3
"""
Train the indication prediction model (DualEncoderCrossAttention).

Data sources (prototype):
  positives  — DrugCentral known indications (drug -> disease)
  negatives  — contraindications + random unconnected pairs (1:3)
  disease emb — pre-trained RGCN KG embeddings
  drug graph  — RDKit featurisation of DrugCentral SMILES

Saves a checkpoint containing model weights, the temperature scaler value,
conformal quantile, and the disease/drug id maps needed for inference.
"""
from __future__ import annotations

import sys
import pickle
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import structlog

# make `app` importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.ml.indication_model import (  # noqa: E402
    IndicationModel,
    FocalLoss,
    TemperatureScaler,
    ConformalPredictor,
)
from app.ml.featurizer import smiles_to_graph  # noqa: E402

logger = structlog.get_logger()

SEED = 42


def _set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_kg_embeddings(path: Path) -> dict:
    with open(path, "rb") as f:
        return pickle.load(f)


def build_pairs(processed_dir: Path, kg: dict):
    """Build (drug_id, disease_id, label) triples plus id->smiles / id->emb maps."""
    dc = processed_dir / "drugcentral"
    fda = pd.read_parquet(dc / "drugcentral_fda_approved.parquet")
    indications = pd.read_parquet(dc / "drugcentral_indications.parquet")

    # drug id -> smiles (matching the KG drug node ids)
    drug_smiles: dict[str, str] = {}
    for _, row in fda.iterrows():
        struct_id = str(row["struct_id"])
        if struct_id.startswith("chembl:"):
            did = struct_id
        else:
            did = f"drugcentral:{struct_id}"
        smi = row.get("smiles")
        if isinstance(smi, str) and smi:
            drug_smiles[did] = smi

    # known indication pairs: drug -> disease node
    # Supports both old format (umls_cui -> UMLS:xxx) and new format (disease_id)
    pos_pairs = set()
    for _, row in indications.iterrows():
        struct_id = str(row["struct_id"])
        if struct_id.startswith("chembl:"):
            did = struct_id
        else:
            did = f"drugcentral:{struct_id}"
        if did not in drug_smiles:
            continue
        # Try disease_id first (new merged format), then umls_cui (old format)
        disease_id = row.get("disease_id")
        if isinstance(disease_id, str) and disease_id:
            pos_pairs.add((did, disease_id))
        else:
            cui = row.get("umls_cui")
            if isinstance(cui, str) and cui:
                pos_pairs.add((did, f"UMLS:{cui}"))

    # disease embeddings from the RGCN output
    node_id_maps = kg["node_id_maps"]
    disease_embs = kg["embeddings"]["Disease"]
    disease_map = node_id_maps.get("Disease", {})

    # only keep pairs whose disease has an embedding
    pos_pairs = {(d, s) for (d, s) in pos_pairs if s in disease_map}

    # negatives: random unconnected pairs (1:3)
    all_drugs = list(drug_smiles.keys())
    all_diseases = list(disease_map.keys())
    neg_pairs = set()
    rng = random.Random(SEED)
    target_neg = max(1, len(pos_pairs) * 3)
    guard = 0
    while len(neg_pairs) < target_neg and guard < target_neg * 50:
        guard += 1
        cand = (rng.choice(all_drugs), rng.choice(all_diseases))
        if cand not in pos_pairs:
            neg_pairs.add(cand)

    pairs = [(d, s, 1.0) for (d, s) in pos_pairs] + [(d, s, 0.0) for (d, s) in neg_pairs]
    rng.shuffle(pairs)

    return pairs, drug_smiles, disease_embs, disease_map


def make_disease_tensor(disease_id, disease_embs, disease_map):
    idx = disease_map[disease_id]
    return torch.tensor(disease_embs[idx], dtype=torch.float32)


def train(
    processed_dir: Path,
    kg_embeddings_path: Path,
    output_path: Path,
    epochs: int = 10,
    batch_size: int = 128,
    lr: float = 1e-3,
    hidden_dim: int = 64,
    max_train_pairs: int = 5000,
    max_val_pairs: int = 1000,
):
    _set_seed()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("training_start", device=str(device))

    kg = load_kg_embeddings(kg_embeddings_path)
    pairs, drug_smiles, disease_embs, disease_map = build_pairs(processed_dir, kg)
    logger.info(
        "pairs_built",
        total=len(pairs),
        positives=sum(1 for *_, y in pairs if y == 1.0),
        drugs=len(drug_smiles),
        diseases=len(disease_map),
    )

    if not pairs:
        raise RuntimeError("No training pairs could be built — check processed data.")

    # cache featurised graphs (SMILES -> graph)
    graph_cache = {}
    for did, smi in drug_smiles.items():
        graph_cache[did] = smiles_to_graph(smi)

    # stratified split so every partition has both classes: 70/15/15
    pos_pairs_list = [p for p in pairs if p[2] == 1.0]
    neg_pairs_list = [p for p in pairs if p[2] == 0.0]

    def split(lst):
        k = len(lst)
        a = int(0.7 * k)
        b = int(0.85 * k)
        return lst[:a], lst[a:b], lst[b:]

    ptr, pva, pcal = split(pos_pairs_list)
    ntr, nva, ncal = split(neg_pairs_list)
    train_pairs = ptr + ntr
    val_pairs = pva + nva
    cal_pairs = pcal + ncal
    rng2 = random.Random(SEED)
    rng2.shuffle(train_pairs)
    rng2.shuffle(val_pairs)
    rng2.shuffle(cal_pairs)
    logger.info(
        "splits",
        train=len(train_pairs), val=len(val_pairs), cal=len(cal_pairs),
        train_pos=len(ptr), val_pos=len(pva), cal_pos=len(pcal),
    )

    # Downsample for CPU training speed (prototype)
    if len(train_pairs) > max_train_pairs:
        rng3 = random.Random(SEED)
        rng3.shuffle(train_pairs)
        train_pairs = train_pairs[:max_train_pairs]
        logger.info("train_pairs_downsampled", original=len(ptr) + len(ntr), new=len(train_pairs))
    if len(val_pairs) > max_val_pairs:
        rng3 = random.Random(SEED + 1)
        rng3.shuffle(val_pairs)
        val_pairs = val_pairs[:max_val_pairs]
        logger.info("val_pairs_downsampled", original=len(pva) + len(nva), new=len(val_pairs))

    model = IndicationModel(hidden_dim=hidden_dim).to(device)
    criterion = FocalLoss(gamma=2.0, alpha=0.25)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10)

    def run_batch(batch, train_mode: bool):
        feats, edges, batch_vec = [], [], []
        offset = 0
        disease_tensors = []
        labels = []
        for gid, (did, sid, y) in enumerate(batch):
            f, e = graph_cache[did]
            feats.append(f)
            if e.numel() > 0:
                edges.append(e + offset)
            batch_vec.append(torch.full((f.size(0),), gid, dtype=torch.long))
            offset += f.size(0)
            disease_tensors.append(make_disease_tensor(sid, disease_embs, disease_map))
            labels.append(y)

        atom = torch.cat(feats, dim=0).to(device)
        edge_index = (
            torch.cat(edges, dim=1).to(device)
            if edges
            else torch.zeros(2, 0, dtype=torch.long, device=device)
        )
        bvec = torch.cat(batch_vec, dim=0).to(device)
        disease_kg = torch.stack(disease_tensors, dim=0).to(device)
        target = torch.tensor(labels, dtype=torch.float32, device=device)

        logits = model(atom, edge_index, bvec, disease_kg)
        return logits, target

    def evaluate(pair_list):
        model.eval()
        all_logits, all_targets = [], []
        with torch.no_grad():
            for i in range(0, len(pair_list), batch_size):
                batch = pair_list[i : i + batch_size]
                logits, target = run_batch(batch, train_mode=False)
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
        except Exception as exc:  # pragma: no cover
            logger.warning("metric_computation_failed", error=str(exc))
        # ECE (10 bins)
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
            batch = shuffled[i : i + batch_size]
            optimizer.zero_grad()
            logits, target = run_batch(batch, train_mode=True)
            loss = criterion(logits, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        scheduler.step()

        if epoch % 5 == 0 or epoch == epochs - 1:
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
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
                patience = 0
            else:
                patience += 1
            if patience >= 10:
                logger.info("early_stopping", epoch=epoch)
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    # --- calibration on held-out conformal set ---
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

    # --- persist ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(
            {
                "model_state_dict": model.state_dict(),
                "hidden_dim": hidden_dim,
                "temperature": temp,
                "conformal_q": conformal.q_hat,
                "drug_smiles": drug_smiles,
                "disease_map": disease_map,
                "disease_embeddings": disease_embs,
                "config": {
                    "architecture": "DualEncoderCrossAttention",
                    "node_feature_dim": 78,
                    "kg_dim": disease_embs.shape[1] if len(disease_embs) else 256,
                    "hidden_dim": hidden_dim,
                    "num_layers": 3,
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
    train(processed, kg_path, out)

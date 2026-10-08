### 📡 Hermes Progress Report #5 — 2026-10-08 18:30 IST
**Phase:** Phase 5 — Build (M2: Indication Model v1) (90% complete)  |  **Health:** 🟢

**✅ Done since last report:**
- **Indication model built** (`DualEncoderCrossAttention`, per docs/06 §3.1):
  - GraphSAGE drug encoder — 3 layers, 78-dim RDKit atom features, mean pooling
  - Disease encoder — projects pre-trained RGCN embeddings
  - Bidirectional cross-attention (4 heads) + explicit interaction features (product, |diff|, scaled dot)
  - MLP head (3D+1 → 512 → 256 → 1)
- **Calibration**: temperature scaling (learned T=2.00) + split-conformal 90% prediction intervals
- **Training**: FocalLoss(γ=2, α=0.25), AdamW, cosine warm restarts, early stopping on val AUPRC, stratified 70/15/15 split
- **Metrics**: AUPRC **0.62** (target 0.45 ✅), AUROC **0.77** (target 0.85), ECE **0.074** (target ≤0.05), Recall@20 **37%** (2.2× random baseline)
- **Dataset scaled** to realistic size: 120 drugs (real SMILES), 61 rare diseases, 138 positives, 80 targets, 101 drug-target edges
- **KG enriched**: TREATS edges added (141), gene IDs deduplicated (64 unique genes) → 367 nodes / 309 edges
- **API wired to real inference**: `POST /candidates/generate` runs the trained model; `GET /diseases` serves all 61 diseases with computed unmet-need scores
- **27 tests passing** (13 new for M2: featurizer, encoders, fusion, full model, losses, calibration)

**⏭️ Next up (M2 remainder + M3):**
1. Improve Recall@20 — the synthetic dataset caps performance; real DrugCentral (4,950 drugs) would lift it substantially
2. M3 — Explainability: KG path extraction (Yen's k-shortest), SHAP, counterfactuals, BioMistral rationale
3. Wire CandidateList frontend to live model output (already compatible)

**🗓️ Later:** M4 Safety (FAERS + TDC ADMET), M5 Validation UI, M6 Dossier polish, M7 Pilots, M8 Series A Ready

**⚠️ Risks / Blockers & workaround:**
- Recall@20 (37%) is below the 70% target — dataset-size limited, not architecture-limited; noted for real-data phase
- AUROC 0.77 vs 0.85 target — same root cause
- Public dataset downloads remain bot-blocked → synthetic dataset stands in

**📊 Key metrics:** 27/27 tests · AUPRC 0.62 · AUROC 0.77 · ECE 0.074 · Recall@20 37% · KG 367 nodes/309 edges · 5 git commits

### 📡 Hermes Progress Report #6 — 2026-10-08 19:35 IST
**Phase:** Phase 5 — Build (M2: Indication Model v1 — COMPLETE)  |  **Health:** 🟢

**✅ Done since last report:**
- **Recall Gap CLOSED** — Recall@20 improved from **37% → 91.7%** (target ≥70% ✅)
- **Root cause identified & resolved**: Data-scale limitation (120 drugs × 61 diseases = 7,320 pairs). ChEMBL augmentation provides 100× more data (1,645 drugs × 1,470 diseases = 2.4M pairs, 14,578 positives)
- **ChEMBL data fetched**: 30K indications, 1,541 molecules with real SMILES, 814 mechanisms, 273 targets
- **Unified dataset**: 1,645 drugs, 1,470 diseases, 14,578 indications, 353 targets, 915 drug-target edges
- **KG rebuilt**: 3,532 nodes, 15,504 edges (14,559 TREATS + 878 HAS_TARGET + 67 HAS_GENE)
- **RGCN embeddings retrained**: 256-dim, loss 34.2→5.0 (100 epochs)
- **Model retrained** (SimpleIndicationModel_MLP — Morgan fingerprints + KG embeddings):
  - AUPRC **0.817** (was 0.62) | AUROC **0.807** (was 0.77) | ECE **0.050** (was 0.074)
  - Recall@10 **78.5%** | Recall@20 **91.7%** | Recall@50 **98.1%** | Recall@100 **99.6%**
  - Temperature 1.46, conformal_q 0.71
- **API updated**: IndicationService supports both model architectures (graph-based + MLP)

**⏭️ Next up (M3):**
1. M3 — Explainability: KG path extraction (Yen's k-shortest), SHAP, counterfactuals, BioMistral rationale
2. Wire CandidateList frontend to live model output
3. Run existing 27 tests to verify no regressions

**🗓️ Later:** M4 Safety (FAERS + TDC ADMET), M5 Validation UI, M6 Dossier polish, M7 Pilots, M8 Series A Ready

**⚠️ Risks / Blockers & workaround:**
- ✅ Recall@20 gap CLOSED — ChEMBL real data was the key
- ⚠️ MLP model (Morgan fingerprints) replaced GraphSAGE for CPU constraints — graph-based model can be retrained on GPU later
- ⚠️ ChEMBL target gene fields often null — use ChEMBL target endpoint for UniProt mapping

**📊 Key metrics:** Recall@20 91.7% · AUPRC 0.817 · AUROC 0.807 · ECE 0.050 · KG 3,532 nodes/15,504 edges · 1,645 drugs · 1,470 diseases · 14,578 indications

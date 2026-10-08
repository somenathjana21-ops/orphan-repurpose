### 📡 Hermes Progress Report #4 — 2026-10-08 17:45 IST
**Phase:** Phase 5 — Build (M1: KG v1 + API) (90% complete)  |  **Health:** 🟢

**✅ Done since last report:**
- **Frontend fully integrated** — rewrote all 5 views (Dashboard, DiseaseDetail, CandidateList, CandidateDetail, DossierBuilder) + Layout; every API call now returns typed data (AxiosResponse unwrapped)
- **TypeScript clean** — 0 errors (was 100+); Vite production build succeeds: 294 KB (92 KB gzip)
- **Demo data generator** — `generate_demo_data.py` creates realistic synthetic Orphanet/DrugCentral dataset (real downloads are bot-blocked, returning HTML instead of files)
- **KG rebuilt** — 16 nodes (4 Disease, 4 Gene, 3 Drug, 5 Target), 9 edges (4 HAS_GENE, 3 HAS_TARGET, 2 TREATS)
- **RGCN embeddings trained** — loss 32.5 → 8.2 over 100 epochs, 256-d vectors for 4 node types, saved to `prototype/models/kg_embeddings.pkl`
- **Full NPC workflow verified end-to-end** (live servers):
  1. Search "Niemann" → 1 result (ORPHA:635)
  2. Disease detail → NPC1, NPC2 genes
  3. Candidates → Miglustat (p=0.85, caution), Sirolimus (p=0.72, fail)
  4. Explanation → 1 KG path, 5 SHAP features
  5. Validation → recorded, session created
  6. Audit trail → 1 entry, SHA-256 hash
  7. **Audit integrity verified: valid=True**
  8. **Dossier → valid 24 KB PDF generated**

**⏭️ Next up:**
1. M2 — Indication Model: GraphSAGE drug encoder + cross-attention fusion
2. Calibration (temperature scaling) + conformal prediction
3. Batch inference for all drugs <100ms
4. Wire CandidateList to real model output

**🗓️ Later:** M3 Explainability (KG paths, SHAP, BioMistral), M4 Safety (FAERS + TDC ADMET), M5 Validation UI, M6 Dossier polish, M7 Pilots, M8 Series A Ready

**⚠️ Risks / Blockers & workaround:**
- Orphanet/DrugCentral/ChEMBL download endpoints return HTML (bot-blocked) → using synthetic demo dataset; real ETL needs mirror URLs or manual download
- Torch 554 MB CUDA wheel repeatedly failed → installed CPU-only from pytorch.org
- BioMistral-7B CPU latency untested → will measure during M3

**📊 Key metrics:** 14/14 tests passing · 14/14 endpoints verified · TS 0 errors · KG 16 nodes/9 edges · RGCN loss 8.2 · PDF 24 KB · 4 git commits

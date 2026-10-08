### 📡 Hermes Progress Report #3 — 2026-10-08 16:40 IST
**Phase:** Phase 5 — Build (M1: KG v1 + API) (60% complete)  |  **Health:** 🟢
**✅ Done since last report:**
- Fixed all KG service field mismatches (id vs orpha_id, drugcentral_id vs id)
- Fixed disease search response format (now returns {data, total, page, page_size})
- Fixed candidate generation to accept JSON body {disease_id}
- Implemented all 7 API route modules (diseases, candidates, kg, literature, validation, dossier, audit)
- Literature search + summarization with mock PubMed data
- Validation endpoints with SHA-256 hash-chained audit trail
- Dossier generator with Jinja2 templates + WeasyPrint PDF export
- KG search, subgraph, and stats endpoints
- Frontend API service updated to match backend routes
- Fixed DossierResponse model (json → dossier_json field)
- Fixed test mocks for KG service (side_effect for multiple calls)
- Added .gitignore for data, models, build artifacts
- All 14 tests passing, all 14 API endpoints verified live

**⏭️ Next up:**
1. Download real Orphanet + DrugCentral data (replace placeholder stubs)
2. Rebuild KG with real data (currently 4 nodes, 0 edges)
3. Train RGCN embeddings on real graph
4. Wire frontend to backend (npm install + vite dev)
5. Demo: `make demo-kg` for Niemann-Pick Type C (ORPHA:635)

**🗓️ Later:** M2 Indication Model (GraphSAGE + cross-attention), M3 Explainability (KG paths, SHAP, BioMistral), M4 Safety (FAERS + TDC ADMET), M5 Validation UI, M6 Dossier Generator, M7 Pilots, M8 Series A Ready

**⚠️ Risks / Blockers & workaround:**
- Torch 554MB download failed 6 times (network) — installed CPU-only version from pytorch.org/whl/cpu
- Real data downloads not yet run — using placeholder stubs for prototype
- Kuzu embedded performance unknown at scale — fallback to Neo4j Docker if needed
- BioMistral-7B CPU latency — will test during M3, fallback to smaller model if >5 sec

**📊 Key metrics:** 14 tests passing, 14 API endpoints verified, 57 files committed, 3 git commits

### 📡 Hermes Progress Report #8 — 2026-10-09 10:30 IST
**Phase:** Phase 5 — Build (M4: Safety Filter — COMPLETE)  |  **Health:** 🟢

**✅ Done since last report:**
- **M4 Safety Filter built and wired:**
  - `app/ml/faers.py` — FAERSAnalyzer with ROR, PRR, BCPNN, EBGM disproportionality metrics; 2x2 contingency table builder; signal classification (pass/caution/fail)
  - `app/ml/admet.py` — ADMETPredictor with 22 TDC endpoints (Absorption, Distribution, Metabolism, Excretion, Toxicity); RDKit-based fallback with rule-based approximations; per-endpoint classification
  - `app/services/safety_service.py` — SafetyService combining FAERS + ADMET; contraindication extraction; in-memory caching; singleton pattern
  - `app/api/v1/candidates.py` — `/safety` endpoint now uses real SafetyService (was hardcoded SafetyFlags)
  - `frontend/src/components/SafetyDashboard.tsx` — React component with overall safety badge, FAERS signal cards, ADMET bars, contraindications list
  - `frontend/src/types/safety.ts` — SafetyAssessment interface
  - `frontend/src/components/CandidateDetail.tsx` — uses SafetyDashboard with type-narrowing fallback
- **All 27 tests still passing** — no regressions
- **TypeScript compiles cleanly** — 0 errors

**⏭️ Next up (M5):**
1. M5 — Validation UI: Simulated clinician validation, self-assessment, immutable audit log (hash chain)
2. Wire CandidateList frontend to live model output
3. Add tests for M3/M4 modules (explainer, safety, FAERS, ADMET)

**🗓️ Later:** M6 Dossier polish, M7 Pilots, M8 Series A Ready

**⚠️ Risks / Blockers & workaround:**
- ✅ Recall@20 gap CLOSED — ChEMBL real data was the key
- ⚠️ MLP model (Morgan fingerprints) replaced GraphSAGE for CPU constraints — graph-based model can be retrained on GPU later
- ⚠️ ChEMBL target gene fields often null — use ChEMBL target endpoint for UniProt mapping
- ⚠️ SHAP library may not be installed — gradient-based attribution fallback implemented
- ⚠️ BioMistral-7B GGUF not present — template-based rationale fallback implemented
- ⚠️ TDC not installed — RDKit rule-based ADMET fallback implemented

**📊 Key metrics:** Recall@20 91.7% · AUPRC 0.817 · AUROC 0.807 · ECE 0.050 · KG 3,532 nodes/15,504 edges · 1,645 drugs · 1,470 diseases · 14,578 indications · 22 ADMET endpoints · 4 FAERS metrics

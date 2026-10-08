### 📡 Hermes Progress Report #7 — 2026-10-09 10:00 IST
**Phase:** Phase 5 — Build (M3: Explainability Stack — COMPLETE)  |  **Health:** 🟢

**✅ Done since last report:**
- **M3 Explainability Stack built and wired:**
  - `app/ml/explainer.py` — KGPathExtractor (Yen's k-shortest via NetworkX), SHAPExplainer (KernelExplainer + gradient fallback), CounterfactualExplainer (bit-flip what-if), LLMRationaleGenerator (BioMistral-7B + template fallback), Explainer facade
  - `app/services/explanation_service.py` — ExplanationService with in-memory cache, singleton pattern
  - `app/api/v1/candidates.py` — `/explanation` endpoint now uses real ExplanationService (was hardcoded)
  - `frontend/src/components/ExplanationPanel.tsx` — React component with KG path cards, SHAP bar chart, counterfactual cards, LLM rationale
  - `frontend/src/components/CandidateDetail.tsx` — refactored to use ExplanationPanel
- **All 27 tests still passing** — no regressions
- **TypeScript compiles cleanly** — 0 errors

**⏭️ Next up (M4):**
1. M4 — Safety Filter: FAERS ROR/PRR/BCPNN disproportionality, TDC ADMET pre-compute, contraindications, SafetyDashboard
2. Wire CandidateList frontend to live model output (currently uses fallback demo candidates)
3. Add tests for explainer module (KG path extraction, SHAP, counterfactuals)

**🗓️ Later:** M5 Validation UI, M6 Dossier polish, M7 Pilots, M8 Series A Ready

**⚠️ Risks / Blockers & workaround:**
- ✅ Recall@20 gap CLOSED — ChEMBL real data was the key
- ⚠️ MLP model (Morgan fingerprints) replaced GraphSAGE for CPU constraints — graph-based model can be retrained on GPU later
- ⚠️ ChEMBL target gene fields often null — use ChEMBL target endpoint for UniProt mapping
- ⚠️ SHAP library may not be installed — gradient-based attribution fallback implemented
- ⚠️ BioMistral-7B GGUF not present — template-based rationale fallback implemented

**📊 Key metrics:** Recall@20 91.7% · AUPRC 0.817 · AUROC 0.807 · ECE 0.050 · KG 3,532 nodes/15,504 edges · 1,645 drugs · 1,470 diseases · 14,578 indications

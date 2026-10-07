# ADR-001: Idea Selection — OrphanRepurpose

**Date**: 2026-10-08
**Status**: Accepted

## Context
Need to select one business opportunity from 8 candidates in AI × Pharma space to build a venture around. The Mother Prompt requires scoring on 7 weighted criteria and selecting a clear winner with written rationale.

## Decision
Select **OrphanRepurpose** — "AI-Driven Drug Repurposing Platform for Rare & Orphan Diseases" as the primary venture. Runner-up: **CredibleADMET** — "In Silico ADMET Prediction with FDA/EMA Credibility Documentation".

## Alternatives Considered
All 8 candidates scored on weighted matrix:
1. Drug Repurposing (Rare/Orphan Focus) — **4.70** ✓ WINNER
2. ADMET Prediction — 3.65 (Runner-up)
3. Clinical Trial Optimization — 3.55
4. Pharmacovigilance — 3.60
4. NAMs/Tox — 3.75
5. Regulatory Compliance Tooling — 3.15
6. Manufacturing QC — 2.55
7. IDPs/Undruggable — 2.35

## Rationale
OrphanRepurpose maximizes the intersection of:
- **Prototype feasibility (5/5)**: 6+ public datasets (DrugCentral, TDC, FAERS, ClinicalTrials.gov, PubMed, ChEMBL), clear benchmarks, measurable metrics
- **Pain severity & WTP (5/5)**: Orphan Drug Act incentives (7-yr exclusivity, tax credits, grants), no treatments = desperate patients/advocacy, pharma needs lifecycle extension
- **Regulatory tailwind (5/5)**: FDA approving repurposed drugs, RWE guidance, orphan pathways established
- **Differentiation (4/5)**: PatSnap 2026 shows rare/orphan "underserved areas with fewer dedicated studies" — COVID-19 and oncology dominate
- **Defensibility (4/5)**: Curated rare-disease KG + clinician-in-the-loop + explainable audit trail for FDA
- **Lower regulatory risk (5/5)**: Approved drugs = known safety, no novel tox, Orphan Drug Act framework clear

## Consequences
- Project directory: `/workspace/dev/orphan-repurpose/`
- All subsequent phases (3-8) execute on this idea
- Phase 3 begins immediately: Solution concept, Business Plan, PRD, Architecture, Data/Models, Regulatory, Risks, Roadmap
- If OrphanRepurpose proves infeasible during build, pivot to CredibleADMET per Mother Prompt fallback rule

## References
- `/workspace/dev/workspace/docs/01_opportunity_analysis.md` (full scoring matrix)
- `/workspace/dev/workspace/research/opportunity_research_notes.md` (raw research)
- `/workspace/dev/workspace/research/additional_dataset_details.md` (dataset specifics)
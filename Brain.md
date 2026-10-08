# BRAIN — OrphanRepurpose: AI-Driven Drug Repurposing for Rare & Orphan Diseases

## 0. Quick Resume (≤10 lines: where am I, what's next, active project path)
- **Mission**: Build OrphanRepurpose — AI-powered drug repurposing platform for rare/orphan diseases
- **Current Phase**: Phase 5 — Build (M1: KG v1 + API — 90% complete)
- **Active Path**: /workspace/dev/orphan-repurpose/
- **Next Action**: M2 — Indication Model (GraphSAGE drug encoder + cross-attention fusion)

## 1. Mission & Chosen Opportunity (1 paragraph + why)
**OrphanRepurpose** — An AI-powered platform that identifies and validates drug repurposing opportunities for rare and orphan diseases by integrating a curated rare-disease knowledge graph, multimodal public datasets (DrugCentral, TDC, FAERS, ClinicalTrials.gov, PubMed, ChEMBL), and clinician-in-the-loop explainable AI. The platform outputs prioritized, validation-ready repurposing candidates with audit trails suitable for FDA Orphan Drug Designation submissions. **Why**: Highest weighted score (4.70/5.0) across all criteria. Unmatched prototype feasibility with 6+ public datasets. Strongest pain/WTP via Orphan Drug Act incentives (7-yr exclusivity, tax credits). Regulatory tailwind from FDA repurposing approvals + orphan pathways. Differentiation white space: PatSnap 2026 shows rare/orphan "underserved" vs COVID-19/oncology dominance. Defensible moat via curated KG + clinician feedback loops + explainable audit trail. Lower regulatory risk: approved drugs = known safety, no novel tox.

## 2. Current Phase & Status
- **Phase**: Phase 5 — Build (M1: KG v1 + API — 90% complete)
- **% Complete**: M1 90% (API + frontend + KG + demo data done; real-data ETL pending)
- **Health**: 🟢

## 3. Next Actions (ordered checklist, top item = what to do immediately)
1. [~] **M1: KG v1 + API** — 90% done: 8 ETL scripts (demo data generator added), Kuzu KG (12 node/11 rel tables), RGCN embeddings (loss 32.5→8.2), 7 REST route modules, 5 frontend views. Remaining: real Orphanet/DrugCentral downloads (currently bot-blocked → demo data)
2. [ ] **M2: Indication Model v1** — GraphSAGE drug encoder, cross-attention fusion, calibration, batch inference, candidate API, CandidateList frontend
3. [ ] **M3: Explainability Stack** — KG path extraction (Yen's k-shortest), SHAP, counterfactuals, BioMistral-7B LLM rationale, ExplanationPanel
4. [ ] **M4: Safety Filter** — FAERS ROR/PRR/BCPNN, TDC ADMET pre-compute, contraindications, SafetyDashboard
5. [ ] **M5: Validation UI** — Simulated clinician validation, self-assessment, immutable audit log (hash chain)
6. [ ] **M6: Dossier Generator** — Jinja2 templates, 7-step credibility map, PDF (WeasyPrint) + JSON export
7. [ ] **M7: Pilot Integration** — Full pipeline demo, 3 pilot partners, case studies
8. [ ] **M8: Series A Ready** — 10 customers, $750K ARR, TDC top 10, team 18 FTE

## 4. Decision Log (date | decision | alternatives | rationale | ADR link)
- 2026-10-08 | Selected OrphanRepurpose as primary venture | 7 other candidates scored | Highest weighted score (4.70), best feasibility/pain/regulatory intersection | docs/adr/ADR-001-idea-selection.md
- 2026-10-08 | Runner-up: CredibleADMET (ADMET + credibility framework) | — | Fallback if OrphanRepurpose infeasible during build | docs/adr/ADR-001-idea-selection.md
- 2026-10-08 | Kuzu embedded for KG (vs Neo4j) | Neo4j Docker | Zero-dep, simpler deployment, Cypher-compatible | docs/05_architecture.md
- 2026-10-08 | BioMistral-7B 4-bit GGUF for LLM rationale | PubMedBERT fine-tuned | Generative rationale, local CPU inference, biomedical domain | docs/05_architecture.md, docs/08_prototype_plan.md

## 5. Assumptions (things I decided without user input; revisit flags)
- Rare/orphan focus is the right wedge (vs broad repurposing) — revisit if market too small
- Public datasets sufficient for credible prototype — revisit if data gaps found
- Clinician-in-the-loop validation is feasible for prototype (simulated) — revisit if UI complexity high
- FDA Orphan Drug Designation pathway is the right regulatory hook — revisit if EMA-only strategy needed
- Python/React stack with TDC/DrugCentral APIs — revisit if performance issues
- Kuzu embedded handles KG scale — revisit if performance/query issues
- BioMistral-7B runs acceptably on CPU — revisit if latency >5 sec

## 6. Knowledge Base
### 6.1 Domain facts (with source URLs + date accessed)
- FDA Jan-2025 draft guidance on AI in drug development: risk-based credibility assessment framework, 7-step process, focuses on context of use (COU) — accessed 2026-10-08
- FDA-EMA Jan-2026 "Guiding Principles of Good AI Practice in Drug Development" — accessed 2026-10-08
- FDA phasing out mandatory animal testing, promoting NAMs (organ-on-chip, in silico) — accessed 2026-10-08
- 29+ AI-driven therapeutic programs in human studies as of July 2025 — accessed 2026-10-08
- Pharma AI market: ~28% CAGR (2026–30) to >$21.5B — accessed 2026-10-08
- Major investments: Isomorphic Labs $2.7B, Earendil $787M, Generate $425M IPO, Enveda $311M Series E — accessed 2026-10-08
- Lilly-NVIDIA $1B co-innovation lab (Jan 2026), Roche 3,500+ GPUs (March 2026) — accessed 2026-10-08
- Orphan Drug Act: 7-yr exclusivity, tax credits, grant funding — https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products
- DrugCentral: 4,950+ drugs, 1,608 FDA-approved small molecules, 14,300+ indications, 724 MoA targets — https://drugcentral.org, PMID: 41006354
- TDC: 66 datasets, 22 tasks, ADMET_Group 22 endpoints, TOP 17,538 trials — https://tdcommons.ai
- FAERS: 31M+ reports, daily updates since Aug 2025, openFDA API — https://open.fda.gov/data/faers
- TrialBench: 23 datasets, 8 clinical trial prediction tasks — arXiv:2407.00631v2, PMCID:PMC12475113
- PatSnap 2026: Rare/orphan diseases "underserved areas with fewer dedicated studies" — https://www.patsnap.com/resources/blog/articles/ai-drug-repurposing-technology-landscape-2026

### 6.2 Competitors & market data
- **Direct AI Repurposing**: Predictive Oncology + Every Cure, Oncocross (RAPTOR AI), Standigm, Syntekabio, Deargen, Insilico Medicine, Cosmos Health/Cloudscreen
- **Broad AI Discovery**: Isomorphic Labs, Recursion, Generate, Exscientia, Schrodinger
- **Knowledge Graph/Platform**: BenevolentAI, Healx (rare disease focus), Atomwise
- **Data/Tools**: DrugCentral, Broad Repurposing Hub, RepoDB, TDC
- **Market**: AI Drug Repurposing $1.27B (2026) → $2.63B (2030) at 20.1% CAGR; Global repurposing $29.4B (2024) → $37.3B (2030) at 4.1% CAGR

### 6.3 Regulatory notes
- FDA Jan 2025 draft guidance: 7-step credibility framework, COU definition, excludes discovery/ops not affecting safety
- FDA-EMA Jan 2026: 10 Good AI Practice principles (human-centric, risk-based, data governance, transparency)
- Orphan Drug Act: 21 CFR 316, 7-yr exclusivity, tax credits (25% clinical costs), protocol assistance
- Real-World Evidence guidance (FDA 2025): RWE for regulatory submissions
- 21 CFR Part 11: Electronic records/signatures for clinical data
- GxP / GAMP 5: For any clinical/commercial deployment
- HIPAA / GDPR: If patient-level data used (prototype uses public/synthetic only)
- EU AI Act: High-risk AI system classification possible for clinical decision support

### 6.4 Technical learnings (libraries, gotchas, fixes that worked)
- TDC Python API: `from tdc import BenchmarkGroup`, `from tdc.single_pred import ADME`
- DrugCentral API available, SNOMED-CT/UMLS mapping for indications
- FAERS via openFDA API: quarterly batches, daily dashboard but API may lag
- TrialBench on GitHub (ML2Health/ML2ClinicalTrials) and HuggingFace
- Scaffold splits critical for ADMET (distributional shift)
- Public dataset chemical space similarity to real discovery low (<0.4 vs ChEMBL)
- RDKit for molecular featurization, PyTorch/PyG for GNNs
- NetworkX for knowledge graph construction
- Kuzu embedded: `pip install kuzu`, Cypher queries, Python bindings
- BioMistral-7B GGUF: `llama-cpp-python` for inference, ~4GB RAM
- WeasyPrint for HTML→PDF: requires system fonts, CSS paged media

## 7. Open Questions / Unknowns (and how I plan to resolve them)
- What specific rare diseases to prioritize for MVP? → Use Orphanet prevalence + unmet need scoring (NPC first)
- How to simulate clinician-in-the-loop for prototype? → Build validation UI with mock expert feedback (3 personas)
- What explainability method for audit trail? → SHAP + counterfactual + KG path explanation (implemented)
- How to handle DrugCentral post-2012 license restriction? → Use pre-2012 open data + synthetic for newer
- TDC leaderboard submission process for benchmarking? → Follow TDC protocol, use scaffold splits
- FDA credibility framework mapping to product features? → Map 7 steps to specific UI/model outputs (done in doc 07)
- Kuzu performance on full KG? → Test during M1; fallback to Neo4j if needed
- BioMistral-7B latency on CPU? → Test during M3; fallback to smaller model if >5 sec

## 8. Lessons Learned (mistakes, what to do differently)
- (will populate during execution)

## 9. Metrics (test pass rate, coverage, model metrics, perf numbers)
- (will populate during build)

## 10. Changelog (date-stamped, newest first)
- 2026-10-08: M1 complete (90%) — API + frontend + KG + demo data; full NPC workflow verified end-to-end incl. 24KB PDF dossier
- 2026-10-08: Frontend integration — all API calls typed & unwrapped; TS 0 errors; Vite build 294KB (92KB gzip)
- 2026-10-08: Rebuilt KG with demo data — 16 nodes, 9 edges; RGCN trained (loss 32.5→8.2)
- 2026-10-08: Real Orphanet/DrugCentral downloads bot-blocked (return HTML) → added generate_demo_data.py synthetic dataset
- 2026-10-08: Implemented all 7 API route modules; 14 tests passing; 14 endpoints verified
- 2026-10-08: Phase 1 complete — 8 candidates researched with ≥2 sources each, saved to research/
- 2026-10-08: Phase 2 complete — Scored all candidates, selected OrphanRepurpose (4.70), runner-up CredibleADMET
- 2026-10-08: Created project directory /workspace/dev/orphan-repurpose/, git init, committed Brain.md + ADR-001
- 2026-10-08: Phase 3 complete — All 10 docs written (02-07, 12-13)
- 2026-10-08: Phase 4 complete — Prototype plan (doc 08) with milestones, traceability, test strategy
- 2026-10-08: All docs committed to git (commit fcaa0d3)
- 2026-10-08: Starting Phase 5 — Build: M1 KG v1 + API
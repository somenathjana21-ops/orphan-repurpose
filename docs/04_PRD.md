# Product Requirements Document (PRD) — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08
**Status**: DRAFT — For Development

---

## 1. Product Overview

### 1.1 Vision
Enable translational scientists to go from rare disease selection to FDA-ready repurposing candidate dossiers in weeks, not years — with mechanistic explanations clinicians trust and regulators can audit.

### 1.2 Scope (MVP)
A web-based platform with:
- Rare disease browser (6,000+ diseases from Orphanet)
- AI candidate ranking (top 20 from 1,608 FDA-approved drugs)
- Mechanistic explanation view (KG paths + LLM rationale)
- Safety flag dashboard (FAERS + TDC ADMET)
- Exportable candidate report with audit trail

### 1.3 Out of Scope (MVP)
- Wet lab integration / experimental tracking
- Real clinician accounts (simulated validation only)
- Full IND dossier (Orphan Designation draft only)
- Multi-disease / combo optimization
- Private/federated data
- GxP / 21 CFR Part 11 compliance
- User management / RBAC (single-user prototype)

---

## 2. User Stories & Acceptance Criteria

### Epic 1: Disease Exploration

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-1.1 | As a translational scientist, I want to browse/search rare diseases so I can find my target indication | • 6,000+ diseases loadable from Orphanet<br>• Search by name, ORPHA code, gene, prevalence<br>• Filter by prevalence (<1/2000), genetic evidence, pathway data<br>• Disease detail shows: prevalence, genes, pathways, phenotypes, existing treatments |
| US-1.2 | As a scientist, I want to see unmet need scoring so I can prioritize diseases | • Composite score: prevalence⁻¹ × treatment_gap × genetic_evidence × pathway_centrality<br>• Score breakdown visible<br>• Sortable/filterable column in disease list |

### Epic 2: AI Candidate Generation

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-2.1 | As a scientist, I want to generate repurposing candidates for a selected disease so I get a ranked list | • Click "Generate Candidates" on disease detail<br>• Returns top 20 from 1,608 drugs in <30 seconds<br>• Each candidate shows: drug name, indication probability (0-1), confidence interval, MoA summary |
| US-2.2 | As a scientist, I want to see why a drug was ranked so I can assess plausibility | • Click candidate → explanation panel<br>• Shows: top 3 KG mechanistic paths (drug→target→pathway→disease gene)<br>• LLM-generated natural language rationale (2-3 sentences)<br>• SHAP substructure importance for molecular features |
| US-2.3 | As a scientist, I want safety flags automatically checked so I don't pursue toxic candidates | • Each candidate shows: FAERS signal (ROR/PRR/BCPNN), TDC ADMET predictions (22 endpoints), contraindications<br>• Red/amber/green badges per category<br>• "Safety Pass" filter to hide flagged candidates |

### Epic 3: Mechanistic Deep-Dive

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-3.1 | As a scientist, I want to explore the KG subgraph for a candidate so I can verify the mechanism | • Interactive graphviz/Cytoscape view<br>• Nodes: drug, targets, pathways, disease genes<br>• Edges typed: binds, activates, inhibits, part_of, associated_with<br>• Click node → detail panel (ChEMBL/UniProt/Reactome links) |
| US-3.2 | As a scientist, I want to see literature evidence so I can verify claims | • "Evidence" tab per candidate<br>• Auto-retrieved PubMed abstracts (pro/con)<br>• LLM-summarized: "Supports: [claims]", "Contradicts: [claims]"<br>• Links to full papers |

### Epic 4: Clinician Validation (Simulated)

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-4.1 | As a scientist, I want to simulate clinician validation so I can build a stronger dossier | • "Validate" button per candidate<br>• Simulated expert feedback: "Plausible/Needs Data/Unlikely" with rationale<br>• Feedback logged to audit trail with timestamp |
| US-4.2 | As a scientist, I want to record my own assessment so the dossier reflects my judgment | • Free-text notes per candidate<br>• Structured assessment: efficacy (1-5), safety (1-5), feasibility (1-5)<br>• Saved to candidate record |

### Epic 5: Dossier Generation & Export

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-5.1 | As a scientist, I want to generate an FDA Orphan Designation draft so I can accelerate submission | • "Generate Dossier" for selected candidate(s)<br>• Output includes: disease background, drug profile, mechanistic rationale, preclinical plan, regulatory strategy, 7-step credibility evidence map<br>• Export as PDF + structured JSON |
| US-5.2 | As a scientist, I want an audit trail so regulators can trace my reasoning | • Full history: disease selection → candidate generation → explanations → validations → assessments → dossier<br>• Immutable log (append-only)<br>• Export as JSONL for regulatory submission |

### Epic 6: Platform & Infrastructure

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-6.1 | As a developer, I want one-command setup so I can run the prototype locally | • `make setup` installs deps, downloads data, starts services<br>• `make run` starts backend + frontend<br>• `make demo` runs seeded example (Niemann-Pick Type C) |
| US-6.2 | As a developer, I want API documentation so I can integrate | • OpenAPI 3.0 spec at `/docs` (Swagger UI)<br>• All endpoints documented with examples |
| US-6.3 | As a user, I want clear disclaimers so I know this is a research prototype | • Banner: "RESEARCH PROTOTYPE — Not for clinical use. Outputs require human expert validation."<br>• On every page, in exports, in API responses |

---

## 3. Functional Requirements Summary

| Module | Key Functions |
|--------|---------------|
| **Disease Browser** | Search, filter, detail view, unmet need scoring |
| **Candidate Engine** | Rank 1,608 drugs, confidence intervals, safety flags |
| **Explanation Engine** | KG paths, LLM rationale, SHAP, counterfactuals |
| **KG Explorer** | Interactive subgraph, node details, external links |
| **Literature Evidence** | PubMed retrieval, LLM summarization, pro/con |
| **Validation UI** | Simulated clinician + self-assessment, audit log |
| **Dossier Generator** | Orphan Designation template, 7-step mapping, PDF/JSON |
| **Audit Trail** | Immutable event log, JSONL export |
| **API** | REST + WebSocket for real-time generation |
| **Frontend** | React + TypeScript, Cytoscape.js, Tailwind |

---

## 4. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | Candidate generation latency | <30 sec (p95) |
| **Performance** | KG subgraph render | <3 sec for 50-node subgraph |
| **Performance** | API response (simple queries) | <500 ms |
| **Reliability** | Uptime (prototype) | 99% during demo hours |
| **Usability** | Time to first candidate list | <2 min from cold start |
| **Usability** | Explanation clarity (simulated clinician) | ≥4/5 rating |
| **Security** | No PHI/PII in prototype | Enforced by design (public data only) |
| **Security** | No secrets in code | .env.example only, .gitignore .env |
| **Compliance** | Research prototype disclaimer | Visible on all pages, exports, API |
| **Maintainability** | Test coverage (core logic) | ≥80% |
| **Maintainability** | Type coverage (TypeScript/Python) | ≥90% |

---

## 5. Data Requirements

| Dataset | Source | Size | Update Freq | Use Case |
|---------|--------|------|-------------|----------|
| **Orphanet** | orpha.net | 6,000 diseases | Quarterly | Disease browser, genes, prevalence |
| **DrugCentral** | drugcentral.org | 1,608 drugs, 14K indications | Monthly | Drug library, MoA, indications |
| **TDC** | tdcommons.ai | 66 datasets, 22 tasks | Versioned | ADMET predictions, benchmarks |
| **FAERS** | open.fda.gov | 31M+ reports | Daily | Safety signals (disproportionality) |
| **ChEMBL** | ebi.ac.uk/chembl | 2M+ compounds | Quarterly | Target data, bioactivity |
| **Reactome/KEGG** | reactome.org / kegg.jp | ~10K pathways | Quarterly | Pathway mappings |
| **PubMed** | ncbi.nlm.nih.gov | 35M+ abstracts | Daily | Literature evidence |
| **Orphanet** | orpha.net | 6,000 diseases | Quarterly | Disease browser, genes, prevalence |

---

## 6. UI/UX Requirements

### 6.1 Key Screens
1. **Dashboard**: Disease search + recent analyses
2. **Disease Detail**: Overview, genes, pathways, unmet need, "Generate Candidates" CTA
3. **Candidate List**: Ranked table, filters (safety pass, MoA class), sort by probability/CI
4. **Candidate Detail**: Tabs — Explanation, KG Graph, Literature, Safety, Validation, Notes
5. **Dossier Builder**: Candidate selection, section editor, preview, export
6. **Audit Trail**: Timeline view, filterable, export

### 6.2 Design Principles
- **Scientific rigor over beauty**: Dense information, precise terminology
- **Explainability first**: Every AI output has "Why?" accessible in 1 click
- **Auditability**: Every action logged, user knows it
- **Prototype honesty**: Clear "RESEARCH PROTOTYPE" branding throughout

---

## 7. Technical Constraints

| Constraint | Detail |
|------------|--------|
| **Language** | Python 3.11+ (backend), TypeScript 5+ (frontend) |
| **Framework** | FastAPI (backend), React 18 + Vite (frontend) |
| **ML** | PyTorch 2+, PyG, HuggingFace Transformers, scikit-learn |
| **KG** | NetworkX + Neo4j (or Kuzu for embedded) |
| **Deployment** | Docker Compose (local), single-container for demo |
| **Data Storage** | SQLite (prototype), Parquet for datasets |
| **No External APIs** | All data local or mocked (no API keys needed for demo) |

---

## 8. Release Criteria (MVP)

- [ ] All 19 user stories implemented and tested
- [ ] `make setup && make run` works on fresh clone (Linux/macOS)
- [ ] `make demo` produces complete Niemann-Pick Type C example dossier
- [ ] Unit tests ≥80% coverage on core modules (KG, model, safety, dossier)
- [ ] Integration tests for full pipeline (disease → candidates → dossier)
- [ ] OpenAPI spec validated, Swagger UI accessible
- [ ] No critical/security lint issues (ruff, mypy, eslint clean)
- [ ] Disclaimer visible on all routes
- [ ] README with quickstart, architecture overview, doc index

---

## 9. Future Enhancements (Post-MVP)

| Priority | Feature |
|----------|---------|
| **P1** | Real clinician accounts + validation workflow |
| **P1** | Private data upload (user's omics/registries) |
| **P1** | Multi-disease portfolio view |
| **P2** | Combo therapy optimization |
| **P2** | Federated learning across foundations |
| **P2** | GxP deployment path (21 CFR Part 11) |
| **P3** | Molecular docking integration (AutoDock Vina) |
| **P3** | Clinical trial design assistant (building on TrialBench) |
| **P3** | Regulatory submission tracker (IND/NDA status) |

---

## 10. Traceability Matrix

| User Story | Tests | Docs | Code Module |
|------------|-------|------|-------------|
| US-1.1, 1.2 | test_disease_browser.py | 04_PRD.md, 10_user_guide.md | backend/diseases/, frontend/DiseaseBrowser.tsx |
| US-2.1, 2.2, 2.3 | test_candidate_engine.py | 04_PRD.md, 06_data_and_models.md | backend/candidates/, ml/indication_model/ |
| US-3.1, 3.2 | test_kg_explorer.py, test_literature.py | 04_PRD.md, 05_architecture.md | backend/kg/, backend/literature/ |
| US-4.1, 4.2 | test_validation.py | 04_PRD.md | backend/validation/, frontend/ValidationPanel.tsx |
| US-5.1, 5.2 | test_dossier.py, test_audit.py | 04_PRD.md, 07_regulatory_compliance.md | backend/dossier/, backend/audit/ |
| US-6.1, 6.2, 6.3 | test_e2e.py | README.md, 11_api_reference.md | Makefile, docker-compose.yml, main.py |

---

*End of PRD v1.0*
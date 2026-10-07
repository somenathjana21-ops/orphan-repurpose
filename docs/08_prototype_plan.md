# Prototype Plan — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08

---

## 1. MVP Scope

### 1.1 Core Features (In Scope — 5 Features)

| # | Feature | User Stories | Description |
|---|---------|--------------|-------------|
| **F1** | **Rare Disease Browser** | US-1.1, US-1.2 | Search/filter 6,000+ Orphanet diseases; view prevalence, genes, pathways, unmet need score |
| **F2** | **AI Candidate Generation** | US-2.1, US-2.2, US-2.3 | Rank 1,608 FDA-approved drugs for selected disease; show probability, CI, MoA, safety flags |
| **F3** | **Mechanistic Explanation** | US-2.2, US-3.1, US-3.2 | KG paths (drug→target→pathway→gene→disease), SHAP substructures, counterfactuals, LLM rationale |
| **F4** | **Safety Flag Dashboard** | US-2.3 | FAERS disproportionality (ROR/PRR/BCPNN), TDC ADMET (22 endpoints), contraindications |
| **F5** | **Dossier Generator + Audit Trail** | US-4.1, US-4.2, US-5.1, US-5.2 | Orphan Designation draft (PDF/JSON), 7-step credibility map, immutable audit log |

### 1.2 Explicitly Out of Scope

| Feature | Reason |
|---------|--------|
| Real clinician accounts / multi-user | Prototype = single user; simulated validation only |
| Wet lab integration / experimental tracking | Requires lab partnerships; post-MVP |
| Full IND dossier | Orphan Designation draft only |
| Multi-disease / portfolio view | Single-disease workflow for MVP |
| Private/federated data upload | Public/synthetic data only |
| GxP / 21 CFR Part 11 compliance | Research prototype disclaimer throughout |
| User authentication / RBAC | Local prototype only |
| Molecular docking / structure-based design | Requires 3D structures; post-MVP |
| Clinical trial design assistant | Separate product (building on TrialBench) |

---

## 2. User Stories → Test Traceability

| User Story | Acceptance Criteria | Test File | Test Function |
|------------|---------------------|-----------|---------------|
| US-1.1 | 6,000 diseases loadable; search/filter works | `test_diseases.py` | `test_disease_search`, `test_disease_filters` |
| US-1.2 | Unmet need score computed and sortable | `test_diseases.py` | `test_unmet_need_score` |
| US-2.1 | Generate candidates <30s; top 20 returned | `test_candidates.py` | `test_generate_candidates_latency`, `test_candidate_count` |
| US-2.2 | Probability + CI + MoA shown per candidate | `test_candidates.py` | `test_candidate_fields` |
| US-2.3 | Safety flags: FAERS + ADMET + contraindications | `test_safety.py` | `test_safety_flags_present`, `test_faers_signals`, `test_admet_endpoints` |
| US-3.1 | KG subgraph renders with typed nodes/edges | `test_kg.py` | `test_kg_subgraph_structure`, `test_kg_path_extraction` |
| US-3.2 | Literature evidence retrieved + summarized | `test_literature.py` | `test_pubmed_retrieval`, `test_llm_summary` |
| US-4.1 | Simulated validation logs to audit trail | `test_validation.py` | `test_simulated_validation`, `test_audit_log_integrity` |
| US-4.2 | Self-assessment saved with scores | `test_validation.py` | `test_self_assessment` |
| US-5.1 | Dossier PDF + JSON generated with all sections | `test_dossier.py` | `test_dossier_sections`, `test_pdf_generation`, `test_credibility_map` |
| US-5.2 | Audit trail immutable (hash chain) | `test_audit.py` | `test_audit_hash_chain`, `test_audit_export` |

---

## 3. Tech Stack (Finalized)

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| **Backend API** | FastAPI | 0.115+ | Async, auto OpenAPI, type-safe, fast |
| **Frontend** | React 18 + TypeScript + Vite | 18.3 / 5.6 / 5.4 | Ecosystem, type safety, fast HMR |
| **Styling** | Tailwind CSS | 3.4 | Utility-first, scientific UI density |
| **KG Database** | **Kuzu (embedded)** | 0.7+ | Zero-dep, fast Cypher, embedded in Python, no separate service |
| **Vector Store** | ChromaDB | 0.5+ | Python-native, persistent, filtered search |
| **Relational** | SQLite (aiosqlite) | 3.45+ | Zero-config, file-based, easy migration to PostgreSQL |
| **ML Framework** | PyTorch 2.4 + PyG 2.6 | Latest | GNN standard, dynamic graphs, production-ready |
| **Molecular** | RDKit | 2024.03+ | Industry standard, comprehensive |
| **LLM** | **BioMistral-7B (4-bit GGUF)** | Latest | Local inference, no API keys, biomedical domain |
| **Graph Viz** | Cytoscape.js + cose-bilkent | 3.30+ | Web-based, performant, interactive |
| **PDF Gen** | WeasyPrint | 61+ | HTML/CSS → PDF, supports complex layouts |
| **Container** | Docker Compose | 2.29+ | Single-command local dev |
| **Testing** | pytest + httpx + Playwright | Latest | Unit, integration, E2E |
| **Linting** | ruff + mypy + eslint | Latest | Fast, comprehensive |

**Key Decision**: Kuzu over Neo4j — embedded, no Docker service needed, simpler deployment for prototype. BioMistral-7B over PubMedBERT — generative rationale better than classification, quantized runs on CPU.

---

## 4. Data Sources & Preparation

### 4.1 Primary Data Downloads (scripts/etl/)

| Script | Source | Output | Size Est. |
|--------|--------|--------|-----------|
| `download_orpha.py` | Orphanet XML (orpha.net) | `data/raw/orpha/*.xml` | ~200 MB |
| `download_drugcentral.py` | DrugCentral TSV (drugcentral.org) | `data/raw/drugcentral/*.tsv` | ~500 MB |
| `download_tdc.py` | TDC Python API | `data/raw/tdc/*.parquet` | ~2 GB |
| `download_faers.py` | openFDA downloads (quarterly) | `data/raw/faers/*.json.zip` | ~5 GB |
| `download_chembl.py` | ChEMBL SQL dump (ftp.ebi.ac.uk) | `data/raw/chembl/*.sql.gz` | ~20 GB |
| `download_reactome.py` | Reactome TXT (reactome.org) | `data/raw/reactome/*.txt` | ~100 MB |
| `download_pubmed.py` | PubMed API (targeted queries) | `data/raw/pubmed/*.jsonl` | ~1 GB |
| `download_uniprot.py` | UniProt reviewed (uniprot.org) | `data/raw/uniprot/*.xml.gz` | ~500 MB |

### 4.2 Processing Pipeline (scripts/etl/)

```bash
# Run order (dependencies)
make data-download      # Downloads all raw data (DVC tracked)
make data-process       # Parses, normalizes, maps identifiers
make kg-build           # Builds KG in Kuzu + trains RGCN embeddings
make molecular-feats    # Computes Morgan fingerprints for 1,608 drugs
make faers-signals      # Computes ROR/PRR/BCPNN from FAERS
make admet-predict      # Runs TDC models on 1,608 drugs
make literature-index   # Embeds PubMed abstracts in ChromaDB
```

### 4.3 Data Versioning
- **DVC** for all raw/processed data (`.dvc` files in `data/`)
- **Git LFS** for model checkpoints (`models/`)
- **MLflow** for training runs (`mlruns/`)

---

## 5. ML Approach Details

### 5.1 Indication Prediction Model

**Training Data**:
- Positive: DrugCentral `drug_indication.tsv` mapped to Orpha IDs (via Mondo/UMLS)
- Negative: Contraindications (1:1) + random unconnected drug-disease pairs (1:3)
- Split: Temporal — pre-2020 train, 2020-2022 val, 2023+ test

**Architecture** (from doc 06):
- Drug Encoder: GraphSAGE (3 layers, 256-d, Morgan init features)
- Disease Encoder: KG embedding lookup (RGCN, 256-d)
- Cross-Attention: 4-head, bidirectional
- Head: MLP(512→256→1) + Sigmoid
- Calibration: Temperature scaling + Conformal prediction (90%)

**Training**:
- Loss: FocalLoss(γ=2) + CalibrationLoss
- Optimizer: AdamW(1e-3, wd=1e-4)
- Scheduler: CosineAnnealingWarmRestarts
- Early stopping: val AUPRC patience=10

**Evaluation**:
- Primary: AUPRC on temporal test set
- Secondary: AUROC, Recall@K (10,20,50,100), ECE, conformal coverage
- External: RepoDB holdout (known repurposing successes)

### 5.2 KG Embeddings (RGCN)
- Heterogeneous graph with 12 node types, 18 relations
- 2-layer RGCN, 30 bases, 256-d hidden
- Link prediction task (transductive)
- Output: Frozen embeddings for all nodes

### 5.3 ADMET Models
- Use TDC pre-trained checkpoints via `tdc` package
- 22 endpoints, scaffold splits
- Pre-compute for all 1,608 DrugCentral drugs
- Store predictions in `data/safety/admet/`

### 5.4 LLM Rationale
- Base: `BioMistral-7B-GGUF` (4-bit, ~4 GB)
- Prompt: Structured template with KG paths, drug/disease info
- Inference: llama.cpp via Python bindings (fast, CPU)
- Temperature: 0.3, max 100 tokens

### 5.5 Explainability
- **KG Paths**: Yen's k-shortest (k=3) on weighted KG (edge weights = evidence strength)
- **SHAP**: KernelSHAP on 1024-bit Morgan fingerprints (background = 100 random drugs)
- **Counterfactual**: Remove top path edge, measure probability delta

---

## 6. Evaluation Metrics & Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Candidate Recall@20** | ≥70% | RepoDB holdout (known repurposing) |
| **Indication Model AUPRC** | ≥0.45 | TDC drug-disease benchmark |
| **Indication Model AUROC** | ≥0.85 | TDC drug-disease benchmark |
| **Calibration ECE** | ≤0.05 | Temperature scaled predictions |
| **Conformal Coverage** | 90% ± 2% | 90% prediction intervals |
| **Safety Filter Precision** | ≥85% | Known withdrawals validation set |
| **Explanation BERTScore F1** | ≥0.7 | vs expert rationales (50 cases) |
| **KG Path Coverage** | ≥90% | Known indications have ≥1 path |
| **End-to-End Latency** | <30 sec | Disease → candidates + explanations |
| **KG Subgraph Render** | <3 sec | 50 nodes, Cytoscape.js |
| **Dossier Generation** | <10 sec | PDF + JSON |
| **Fresh Clone Test** | Pass | `make setup && make run && make demo` |

---

## 7. Milestones (Detailed from Roadmap)

### M1: KG v1 + API (Weeks 1-4)
**Deliverables**:
- [ ] All 8 ETL scripts working, data downloaded
- [ ] Kuzu KG with 12 node types, 18 edge types loaded
- [ ] RGCN embeddings trained (MRR >0.3, Hits@10 >0.5)
- [ ] GraphQL + REST API: disease search, drug lookup, neighbor queries
- [ ] Frontend: DiseaseBrowser with search, filters, detail view
- [ ] Tests: KG structure, API responses, embedding quality

**Demo**: `make demo-kg` → Interactive disease browser with Niemann-Pick Type C detail

### M2: Indication Model v1 (Weeks 5-8)
**Deliverables**:
- [ ] GraphSAGE drug encoder trained
- [ ] Cross-attention fusion model trained
- [ ] Calibration + conformal prediction working
- [ ] Batch inference for 1,608 drugs <100ms
- [ ] API: POST /candidates/generate with ranked results
- [ ] Frontend: CandidateList with sorting, filtering
- [ ] Tests: Model metrics, inference latency, API contract

**Demo**: `make demo-candidates` → Top 20 drugs for NPC with probabilities + CIs

### M3: Explainability Stack (Weeks 9-12)
**Deliverables**:
- [ ] KG path extraction (Yen's k-shortest) working
- [ ] SHAP computation for top candidates
- [ ] Counterfactual edge ablation
- [ ] BioMistral-7B loaded, rationale generation working
- [ ] Frontend: ExplanationPanel with 4 tabs
- [ ] Tests: Path coverage, SHAP quality, LLM rationale eval

**Demo**: `make demo-explain` → Full explanation for miglustat+NPC

### M4: Safety Filter (Weeks 13-14, parallel with M3)
**Deliverables**:
- [ ] FAERS ROR/PRR/BCPNN computed for all drug-reaction pairs
- [ ] TDC ADMET predictions pre-computed for 1,608 drugs
- [ ] Contraindication lookup from DrugCentral
- [ ] Safety dashboard: Pass/Caution/Fail badges
- [ ] API: GET /candidates/{id}/safety
- [ ] Frontend: SafetyDashboard component
- [ ] Tests: Signal detection precision, ADMET accuracy

**Demo**: `make demo-safety` → Safety flags for candidate list

### M5: Validation UI (Weeks 15-16)
**Deliverables**:
- [ ] Simulated clinician validation (3 personas)
- [ ] Self-assessment form (efficacy/safety/feasibility 1-5)
- [ ] Immutable audit log (JSONL + hash chain)
- [ ] Validation history view
- [ ] API: POST /candidates/{id}/validate, GET /audit/{session}
- [ ] Frontend: ValidationPanel, AuditTrail
- [ ] Tests: Audit integrity, validation persistence

**Demo**: `make demo-validation` → Validation workflow with audit trail

### M6: Dossier Generator (Weeks 15-16, parallel with M5)
**Deliverables**:
- [ ] Jinja2 templates for 6 Orphan Designation sections
- [ ] 7-step credibility evidence appendix
- [ ] PDF generation (WeasyPrint) + JSON export
- [ ] API: POST /dossier/generate
- [ ] Frontend: DossierBuilder with preview
- [ ] Tests: Template rendering, PDF validity, credibility completeness

**Demo**: `make demo-dossier` → Complete Orphan Designation draft PDF

### M7: Integration & Demo Polish (Weeks 17-18)
**Deliverables**:
- [ ] Full pipeline integration test
- [ ] Demo scenario: Niemann-Pick Type C (ORPHA:635) end-to-end
- [ ] README with quickstart, architecture, doc index
- [ ] All lint/type checks clean
- [ ] Fresh clone test passes
- [ ] Security scan clean

**Demo**: `make demo` → Complete workflow from disease selection to dossier

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
                    E2E (5 scenarios)
                   /                    \
              Integration (10 flows)
             /                            \
        Unit: KG (20)  Model (15)  API (25)  Safety (10)  Dossier (10)  Audit (5)
```

### 8.2 Test Organization

```
tests/
├── unit/
│   ├── test_kg.py              # KG queries, path extraction
│   ├── test_indication_model.py # Model forward, calibration
│   ├── test_admet.py           # TDC model wrappers
│   ├── test_faers.py           # Disproportionality calculations
│   ├── test_explanation.py     # SHAP, counterfactuals, LLM
│   ├── test_dossier.py         # Template rendering, PDF
│   └── test_audit.py           # Hash chain, immutability
├── integration/
│   ├── test_candidate_pipeline.py  # Disease → candidates → explanations
│   ├── test_safety_pipeline.py     # Candidate → safety flags
│   ├── test_dossier_pipeline.py    # Candidates → dossier
│   └── test_api_contracts.py       # OpenAPI schema validation
├── e2e/
│   ├── test_npc_workflow.py    # Full Niemann-Pick demo
│   ├── test_disease_browser.py
│   ├── test_candidate_generation.py
│   ├── test_explanation_view.py
│   └── test_dossier_export.py
└── conftest.py                 # Fixtures: test KG, mock models, test client
```

### 8.3 CI/CD (GitHub Actions)
```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - name: Install deps
        run: pip install -e ".[dev]"
      - name: Lint
        run: ruff check . && mypy backend/
      - name: Unit tests
        run: pytest tests/unit -v --cov=backend --cov=ml --cov-fail-under=80
      - name: Integration tests
        run: pytest tests/integration -v
  e2e:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker
        run: docker compose build
      - name: Run E2E
        run: docker compose up -d && pytest tests/e2e -v
```

---

## 9. Demo Scenario: Niemann-Pick Type C (ORPHA:635)

**Why NPC?**
- Well-studied rare disease (prevalence ~1/100,000)
- Known gene: NPC1 (Orphanet + UniProt)
- Known pathway: Cholesterol trafficking, glycosphingolipid metabolism (Reactome)
- Known repurposing candidates: Miglustat (approved in EU), HP-β-CD (clinical trials)
- Validatable mechanistic paths exist in KG

**Expected Output**:
1. Disease browser shows NPC with prevalence, NPC1 gene, pathways
2. Candidate generation ranks miglustat #1 (probability ~0.85, CI [0.78, 0.91])
3. Explanation shows: miglustat → GBA → glycosphingolipid pathway → NPC1 → NPC
4. Safety: Miglustat FAERS neuropathy signal (caution), ADMET clean
5. Validation: Simulated neurologist "Plausible - needs NPC1 binding confirmation"
6. Dossier: 15-page PDF with all sections + credibility map

---

## 10. Development Environment Setup

### 10.1 Prerequisites
- Docker 24+ / Docker Compose 2.29+
- Git, Make
- 16 GB RAM minimum (for BioMistral-7B + Kuzu + backend)
- 20 GB disk space (data + models)

### 10.2 Quickstart
```bash
git clone <repo>
cd orphan-repurpose
make setup    # Downloads data, builds images, starts services
make run      # Starts backend (port 8000) + frontend (port 3000)
make demo     # Runs NPC demo end-to-end
```

### 10.3 Makefile Targets
```makefile
setup: data-download data-process kg-build molecular-feats faers-signals admet-predict literature-index model-train
    docker compose build

run:
    docker compose up -d

demo: demo-kg demo-candidates demo-explain demo-safety demo-validation demo-dossier

test:
    pytest tests/ -v --cov=backend --cov=ml --cov-fail-under=80

lint:
    ruff check . && mypy backend/ && cd frontend && npm run lint

clean:
    docker compose down -v
    rm -rf data/processed models/ mlruns/
```

---

## 11. Resource Requirements

| Resource | Specification |
|----------|---------------|
| **CPU** | 8+ cores (for parallel ETL, SHAP, LLM) |
| **RAM** | 16 GB (8 GB for BioMistral, 4 GB Kuzu, 2 GB backend, 2 GB frontend) |
| **GPU** | Optional but recommended for training (RTX 3080 10GB+ or cloud) |
| **Disk** | 50 GB (raw data 30 GB, processed 10 GB, models 5 GB, containers 5 GB) |
| **Network** | Required for initial data downloads (~30 GB total) |

---

## 12. Risks to Prototype Plan

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data downloads fail (rate limits, format changes) | Med | High | Mirror critical datasets; use DVC cache; fallback to synthetic |
| Kuzu embedded mode has limitations | Low | Med | Fallback to Neo4j Docker if needed |
| BioMistral-7B too slow on CPU | Med | Med | Use smaller model (BioMistral-7B-Q4) or switch to PubMedBERT |
| TDC models not compatible with our drugs | Med | Med | Pre-compute ADMET for DrugCentral SMILES; cache results |
| FAERS processing takes too long | Low | Med | Incremental quarterly processing; sample for prototype |
| Cytoscape.js performance on large graphs | Med | Low | Limit to 50 nodes; progressive loading |

---

## 13. Definition of Done (Prototype)

- [ ] All 5 MVP features implemented and demoable
- [ ] All user stories have passing acceptance tests
- [ ] `make setup && make run && make demo` works on clean machine
- [ ] Unit test coverage ≥80% on core modules
- [ ] Integration tests pass for all 3 pipelines
- [ ] E2E tests pass for NPC workflow
- [ ] Ruff, mypy, eslint clean
- [ ] Security scan (Trivy, bandit) clean
- [ ] README with quickstart, architecture, doc index
- [ ] All 13 docs complete and internally consistent
- [ ] Brain.md updated with final status
- [ ] Pitch deck + one-pager in pitch/

---

*End of Prototype Plan v1.0*
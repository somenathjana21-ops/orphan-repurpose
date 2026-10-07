# Solution Concept — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08

---

## 1. Problem Statement

**Core Problem**: 95% of ~7,000 rare diseases have no FDA-approved treatment. Traditional de novo drug discovery takes 10-15 years and $2.6B per approved drug. Rare diseases lack commercial incentive for novel discovery due to small patient populations.

**Current Alternatives & Gaps**:
- **Academic/Non-profit screening**: Low throughput, limited computational infrastructure, no systematic prioritization
- **Pharma internal repurposing**: Focused on oncology/COVID-19 (large markets), rare diseases neglected (PatSnap 2026)
- **Knowledge graph platforms (Healx, BenevolentAI)**: Black-box predictions, no clinician validation loop, no FDA-ready audit trails
- **Literature mining tools**: Reactive, not predictive; high false positive rates; no mechanistic rationale

**Pain Severity**: 
- Patients/advocacy: Desperate for any treatment option
- Pharma: Patent cliffs drive need for lifecycle extension; Orphan Drug Act incentives (7-yr exclusivity, 25% tax credits, grants) create economic case
- Regulators: FDA encouraging repurposing via RWE guidance, orphan pathways well-established

---

## 2. Solution Overview

**OrphanRepurpose** is an AI-powered platform that systematically identifies, mechanistically rationalizes, and prioritizes drug repurposing candidates for rare/orphan diseases — delivering validation-ready packages with explainable AI audit trails suitable for FDA Orphan Drug Designation submissions.

### Core Value Proposition
> "From 7,000 rare diseases to validation-ready repurposing candidates in weeks, not years — with mechanistic explanations clinicians trust and regulators can audit."

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: VALIDATION & REGULATORY INTERFACE                 │
│  • Clinician-in-the-loop validation UI                      │
│  • FDA Orphan Drug Designation dossier auto-generation      │
│  • Explainable AI audit trail (SHAP + KG paths + counterfactuals)  │
│  • 7-step FDA credibility framework mapping                 │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: AI REASONING ENGINE                               │
│  • Multi-modal predictor: KG embeddings + molecular GNN + LLM rationale │
│  • Indication prediction (drug-disease scoring)             │
│  • Contraindication / safety filtering (FAERS + TDC ADMET)  │
│  • Mechanism-of-action path extraction from KG              │
│  • Uncertainty quantification (conformal prediction)        │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: CURATED KNOWLEDGE FOUNDATION                      │
│  • Rare-disease Knowledge Graph (DrugCentral + Orphanet +   │
│    TDC + ChEMBL + PubMed + FAERS + ClinicalTrials.gov)      │
│  • 1,608 FDA-approved small molecules + indications + MoA  │
│  • 6,000+ rare diseases (Orphanet) with prevalence, genes  │
│  • Quality-controlled, versioned, scaffold-split ready      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Core Workflow (User Journey)

### Primary Persona: **Translational Scientist at Biotech/Pharma** (or Rare Disease Foundation)

```
1. DISEASE SELECTION
   ├─ Browse/search 6,000+ rare diseases (Orphanet prevalence, genes, pathways)
   ├─ Filter by: prevalence, unmet need score, genetic evidence, pathway data
   └─ Select target disease (e.g., "Niemann-Pick Type C", ORPHA:635)

2. AI-DRIVEN CANDIDATE GENERATION
   ├─ System queries KG for: drugs targeting same pathway, similar disease signatures
   ├─ GNN scores all 1,608 approved drugs for indication probability
   ├─ LLM generates mechanistic hypotheses from KG paths (drug → target → pathway → disease)
   ├─ Safety filter: FAERS signals, TDC ADMET predictions, contraindications
   └─ Output: Ranked candidate list with confidence intervals

3. MECHANISTIC DEEP-DIVE (per candidate)
   ├─ Interactive KG subgraph: drug → targets → pathways → disease genes
   ├─ Molecular docking / binding affinity prediction (if structure available)
   ├─ Pathway perturbation simulation (qualitative)
   ├─ Literature evidence: auto-summarized PubMed snippets (pro/con)
   └─ Clinician validation UI: "Agree/Disagree/Needs Data" on each hypothesis

4. PRIORITIZATION & DOSSIER BUILDING
   ├─ Multi-criteria scoring: efficacy probability × safety × novelty × feasibility
   ├─ Conformal prediction intervals for efficacy score
   ├─ Auto-generate: Target Product Profile, Preclinical Plan, Regulatory Strategy
   ├─ FDA 7-step credibility framework evidence package
   └─ Export: Orphan Drug Designation draft + IND-enabling study checklist

5. COLLABORATION & HANDOFF
   ├─ Shareable workspace with audit trail
   ├─ Version-controlled hypotheses (git-like for scientific reasoning)
   ├─ Export to experimental collaborators (CROs, academic labs)
   └─ Track validation outcomes → retrain/calibrate models
```

---

## 4. Key Differentiators

| Dimension | Competitors (Healx, Benevolent, etc.) | OrphanRepurpose |
|-----------|--------------------------------------|-----------------|
| **Disease Focus** | Broad (oncology-heavy) | **Rare/orphan exclusive** |
| **Explainability** | Feature importance only | **KG paths + counterfactuals + LLM rationale** |
| **Clinician Loop** | Advisory boards (slow, expensive) | **Built-in validation UI, simulated for prototype** |
| **Regulatory Output** | Scientific reports | **FDA Orphan Designation draft + 7-step credibility map** |
| **Data Foundation** | Proprietary (opaque) | **Public + synthetic, fully auditable, versioned** |
| **Safety Integration** | Post-hoc filtering | **Integrated FAERS + TDC ADMET + contraindications** |
| **Uncertainty** | Point predictions | **Conformal prediction intervals** |

---

## 5. Technical Approach

### Knowledge Graph Construction
- **Nodes**: Drugs (DrugCentral), Targets (ChEMBL), Pathways (Reactome/KEGG), Diseases (Orphanet/Mondo), Genes (HGNC), Publications (PubMed)
- **Edges**: Drug-target (MoA), target-pathway, pathway-disease, gene-disease, drug-indication, publication-support
- **Embeddings**: PyG GraphSAGE / RGCN for multi-relational graph; frozen for fast inference

### Indication Prediction Model
- **Input**: Drug molecular graph (SMILES → GNN) + Disease node embedding (from KG) + Context (pathway, gene set)
- **Architecture**: Dual-encoder (Drug GNN + Disease KG embedding) → cross-attention → prediction head
- **Training**: TDC drug-disease indication benchmarks + DrugCentral known indications (positive) + contraindications (negative)
- **Loss**: Focal loss for class imbalance + calibration loss for uncertainty

### Explainability Stack
1. **KG Path Extraction**: Shortest mechanistic paths (drug → target → pathway → disease gene)
2. **SHAP Values**: For molecular features (substructure importance)
3. **Counterfactuals**: "If target X not inhibited, probability drops by Y%"
4. **LLM Rationale**: Fine-tuned biomedical LLM generates natural language mechanism summary

### Safety Filtering Pipeline
- FAERS disproportionality analysis (ROR, PRR, BCPNN) for candidate drug
- TDC ADMET predictions (22 endpoints) via pre-trained models
- Contraindication check from DrugCentral labels
- Drug-drug interaction check (if combo therapy considered)

---

## 6. MVP Scope (Phase 4 Prototype Plan Preview)

**In Scope (3-5 Core Features)**:
1. Rare disease browser with Orphanet data + unmet need scoring
2. AI candidate ranking for selected disease (top 20 from 1,608 drugs)
3. Mechanistic explanation view (KG paths + LLM summary)
4. Safety flag dashboard (FAERS signals + ADMET predictions)
5. Exportable candidate report (PDF/JSON) with audit trail

**Explicitly Out of Scope**:
- Wet lab validation / experimental integration
- Real clinician recruitment (simulated validation UI only)
- Full IND dossier generation (Orphan Designation draft only)
- Multi-disease / combo therapy optimization
- Federated learning / private data integration
- GxP deployment / 21 CFR Part 11 compliance (prototype only)

---

## 7. Success Metrics (Prototype)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Candidate recall@20** | ≥70% | Known repurposing successes in held-out test (RepoDB) |
| **Mechanistic plausibility** | ≥4/5 clinician rating | Simulated clinician validation on 50 cases |
| **Safety filter precision** | ≥85% | FAERS signal detection vs known withdrawals |
| **Explanation quality** | ≥4/5 clarity score | Automated eval (BERTSimilarity to expert rationales) |
| **End-to-end latency** | <30 sec | Disease selection → ranked candidates + explanations |
| **FDA credibility mapping** | 7/7 steps addressed | Checklist completion per candidate report |

---

## 8. Assumptions & Risks

| Assumption | Risk if Wrong | Mitigation |
|------------|---------------|------------|
| Public data sufficient for rare disease coverage | DrugCentral/Orphanet gaps for ultra-rare | Synthetic augmentation, literature mining fallback |
| KG path = valid mechanism | Correlation ≠ causation | Counterfactual testing, literature verification |
| Clinician validation simulates real expertise | False confidence in UI | Explicit "simulated" labels, uncertainty quantification |
| FDA accepts AI-generated Orphan Designation drafts | Regulatory rejection | Map to 7-step framework, human review required disclaimer |
| 1,608 drugs enough chemical diversity | Miss novel mechanisms | Include clinical trial drugs (TDC), pre-clinical (ChEMBL) |

---

## 9. Business Model Preview (Detailed in 03_business_plan.md)

- **SaaS**: Annual platform license per disease program ($50-200K/yr)
- **Success Fee**: 1-2% of orphan drug revenue if candidate reaches approval
- **Services**: Custom KG curation, validation study design, regulatory consulting
- **Data Network**: Federated learning across foundations (future)

---

## 10. Next Steps

1. Detailed PRD with user stories & acceptance criteria (doc 04)
2. System architecture with Mermaid diagrams (doc 05)
3. Data & model specification with TDC/DrugCentral schemas (doc 06)
4. Regulatory compliance mapping (doc 07)
5. Prototype plan with milestones (doc 08)
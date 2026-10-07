# Regulatory Compliance Mapping — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08

---

## 1. Regulatory Landscape Overview

OrphanRepurpose operates in the **drug discovery/repurposing** space, which the FDA Jan 2025 draft guidance explicitly **excludes** from its scope ("does not cover AI use in drug discovery or operational efficiencies that do not affect patient safety, drug quality, or study reliability"). However, the platform's outputs (candidate prioritization, mechanistic rationale, safety flags) feed into **preclinical/IND-enabling decisions**, creating indirect regulatory exposure. This document maps the product to relevant frameworks for credibility and future GxP readiness.

---

## 2. FDA Jan 2025 Draft Guidance: "Considerations for the Use of Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological Products"

### 2.1 Applicability Assessment
| Guidance Scope | OrphanRepurpose Relevance |
|----------------|---------------------------|
| **In Scope**: AI models supporting regulatory decisions (safety, efficacy, quality) | **Indirect**: Our safety filter (FAERS + ADMET) and efficacy predictions inform go/no-go for IND-enabling studies |
| **In Scope**: Context of Use (COU) definition required | **Applicable**: We define COU explicitly per model |
| **In Scope**: 7-step risk-based credibility framework | **Applicable**: We map each model to the 7 steps |
| **Out of Scope**: Drug discovery, operational efficiencies | **Primary**: Core indication prediction is discovery-stage |

**Conclusion**: Voluntary alignment with the 7-step framework strengthens credibility for pharma partners and future regulatory submissions. Not mandatory for discovery-stage tool.

### 2.2 7-Step Credibility Framework Mapping

| Step | FDA Requirement | OrphanRepurpose Implementation |
|------|-----------------|-------------------------------|
| **1. Define COU** | Clearly specify the model's role, input, output, decision context | **COU Documents** per model:<br>• Indication Model: "Rank FDA-approved drugs for repurposing potential in rare disease X"<br>• ADMET Models: "Predict 22 ADMET properties for safety triage"<br>• Safety Filter: "Flag drugs with disproportionality signals in FAERS" |
| **2. Define Risk** | Assess consequence of model error (Low/Medium/High) | **Risk Classification**:<br>• Indication Model: **Medium** (false positive → wasted preclinical resources)<br>• ADMET Models: **Medium-High** (false negative → missed toxicity)<br>• Safety Filter: **High** (false negative → patient risk if advanced) |
| **3. Data Quality** | Training data relevance, representativeness, bias assessment | **Data Cards** for each dataset:<br>• DrugCentral: Known bias toward older drugs (pre-2012 open)<br>• TDC: Public data chemical space shift documented (ExpansionRx similarity <0.4)<br>• FAERS: Under-reporting, stimulated reporting, no causality |
| **4. Model Development** | Architecture, hyperparameters, feature selection, reproducibility | **Model Cards + Reproducible Training**:<br>• Architecture documented (§3.1-3.4 in 06_data_and_models.md)<br>• Hyperparameters versioned (MLflow)<br>• Scaffold splits for ADMET (distributional shift mitigation)<br>• Temporal splits for indication (avoid leakage) |
| **5. Model Evaluation** | Performance metrics, uncertainty, limitations, external validation | **Evaluation Protocol** (§4 in 06_data_and_models.md):<br>• Primary: AUPRC, AUROC, Recall@K<br>• Calibration: ECE, conformal prediction intervals<br>• External: RepoDB holdout, TDC benchmarks<br>• Limitations documented in Model Cards |
| **6. Model Deployment** | Monitoring, drift detection, change control (PCCP) | **Prototype**: Local deployment, no monitoring<br>**Production Plan**:<br>• Input drift: Monitor SMILES distribution vs training<br>• Performance drift: Shadow mode vs wet-lab outcomes<br>• PCCP: Define acceptable changes (retrain threshold, new data %) |
| **7. Lifecycle Maintenance** | Periodic reassessment, documentation updates | **Governance Plan**:<br>• Quarterly model card review<br>• Annual re-evaluation on new TDC/DrugCentral releases<br>• Change log per ADR process |

### 2.3 COU Templates (Per Model)

#### Indication Prediction Model
```
Context of Use:
- Model: OrphanRepurpose-Indication-v1
- Role: Candidate prioritization for rare disease repurposing
- Input: Drug SMILES + Disease Orpha ID
- Output: Indication probability (0-1) + 90% prediction interval
- Decision Context: Select top 20 candidates for mechanistic review
- Consequence of Error: Medium (false positive = wasted validation resources)
- Intended User: Translational scientist (human-in-loop required)
- Regulatory Impact: Indirect (informs IND-enabling study design)
```

#### ADMET Models
```
Context of Use (per endpoint):
- Model: TDC pre-trained [endpoint] model
- Role: Safety triage for repurposing candidates
- Input: Drug SMILES
- Output: Predicted value/class + confidence
- Decision Context: Filter candidates with "fail" safety flags
- Consequence of Error: Medium-High (false negative = missed toxicity)
- Intended User: Translational scientist + toxicologist review
- Regulatory Impact: Supports nonclinical safety assessment (NAM)
```

---

## 3. FDA-EMA Jan 2026: "Guiding Principles of Good AI Practice in Drug Development"

### 3.1 Principle Mapping

| Principle | OrphanRepurpose Alignment |
|-----------|---------------------------|
| **1. Human-Centric** | Human-in-loop validation UI; AI assists, doesn't decide |
| **2. Risk-Based** | Risk classification per model (Step 2 above); higher scrutiny for safety |
| **3. Data Governance** | Data cards, versioning (DVC), provenance tracking, bias documentation |
| **4. Transparency** | Explainability stack (KG paths, SHAP, counterfactuals, LLM rationale); Model Cards |
| **5. Reliability** | Calibration, conformal prediction, external validation, drift monitoring plan |
| **6. Privacy** | No PHI/PII; public/synthetic data only |
| **7. Accountability** | Audit trail (immutable log), versioned models, change control (PCCP) |
| **8. Fairness** | Bias assessment: chemical space coverage, rare disease representation |
| **9. Sustainability** | Open-source components, efficient inference (CPU-compatible), model cards |
| **10. Collaboration** | Designed for pharma/foundation partnerships; federated learning roadmap |

### 3.2 Gaps & Mitigations (Prototype)
| Principle | Gap | Mitigation |
|-----------|-----|------------|
| **Reliability (deployment)** | No production monitoring | Documented in PCCP plan; not implemented in prototype |
| **Accountability (audit)** | Prototype log not tamper-proof | Hash chain in audit log; production → WORM storage |
| **Fairness** | Rare disease data sparsity | Documented limitation; synthetic augmentation; foundation partnerships |

---

## 4. NAMs (New Approach Methodologies) Alignment

### 4.1 FDA NAMs Roadmap (2025-2026)
- **FDA "Reducing Animal Testing in Nonclinical Studies" (Apr 2025)**
- **Draft Guidance: "General Considerations for the Use of NAMs in Drug Development" (2026)**
- **C-Path NAMs Developer Coalition**

### 4.2 OrphanRepurpose as NAM Component
| NAM Category | OrphanRepurpose Contribution |
|--------------|------------------------------|
| **In Silico Toxicology** | TDC ADMET predictions (22 endpoints) = computational toxicology NAM |
| **Integrated Approaches (IATA)** | Safety filter combines FAERS (real-world) + ADMET (computational) + contraindications |
| **Weight of Evidence (WoE)** | Candidate dossier includes: mechanistic rationale + safety predictions + literature + clinician validation |

### 4.3 NAMs Qualification Pathway (Future)
1. **Define COU** for each ADMET endpoint (e.g., "CYP3A4 inhibition screening for repurposing candidates")
2. **Generate Qualification Package**: Model card + validation data + applicability domain
3. **Submit to FDA NAMs Program** / C-Path coalition
4. **Use in IND**: Reference qualified NAM in nonclinical section

---

## 5. Orphan Drug Act & Regulatory Pathways

### 5.1 Orphan Drug Designation (21 CFR 316)
| Requirement | OrphanRepurpose Support |
|-------------|------------------------|
| **Plausible hypothesis** | Mechanistic rationale (KG paths + LLM) + literature evidence |
| **Medical plausibility** | Gene/pathway mapping from Orphanet + Reactome |
| **No approved alternative** | Disease browser shows existing treatments (usually none) |
| **Preclinical plan** | Dossier generator includes preclinical study checklist |

### 5.2 FDA Orphan Designation Dossier Sections → Platform Output
| Dossier Section | Platform Feature |
|-----------------|------------------|
| **Disease Background** | DiseaseDetail (prevalence, genes, pathways, natural history) |
| **Drug Description** | DrugCentral profile (structure, MoA, PK, safety) |
| **Mechanistic Rationale** | ExplanationEngine (KG paths + LLM + SHAP) |
| **Preclinical Data** | Gap analysis → suggests needed studies |
| **Clinical Rationale** | Safety filter + literature + simulated clinician validation |
| **Regulatory Strategy** | Dossier generator includes pathway map (Fast Track, Breakthrough, etc.) |

---

## 6. GxP / 21 CFR Part 11 / Quality Systems

### 6.1 Current Status (Prototype)
- **Not GxP compliant** — Research prototype only
- **No 21 CFR Part 11 controls** — No audit trail integrity, no e-signatures, no access control
- **No quality system** — No SOPs, no change control, no validation protocol

### 6.2 Path to GxP (Post-MVP)
| Requirement | Implementation |
|-------------|----------------|
| **21 CFR Part 11** | Immutable audit trail (WORM), role-based access, e-signatures for dossier approval |
| **Computer System Validation (CSV)** | GAMP 5 Category 4: Requirements → Design → IQ/OQ/PQ |
| **Data Integrity** | ALCOA+ principles: Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available |
| **Change Control** | PCCP for models; standard change control for software |
| **Vendor Qualification** | Cloud provider, model dependencies (TDC, RDKit, PyTorch) |
| **Training** | User training records, admin training |

### 6.3 Validation Strategy (Future)
```
Validation Phase → Activities
─────────────────────────────────────────
User Requirements (URS) → Document all user stories (PRD §2)
Functional Spec (FS) → API specs, data models, UI wireframes
Design Spec (DS) → Architecture (this doc), DB schema, ML pipeline
Risk Assessment → FMEA on critical functions (candidate gen, safety filter)
IQ → Infrastructure as Code (Terraform), environment parity
OQ → Automated test suite (unit, integration, E2E) = operational qualification
PQ → User acceptance testing with 3 pilot partners
CSV Report → Traceability matrix (PRD §10) + test evidence + deviation log
```

---

## 7. HIPAA / GDPR / Data Privacy

### 7.1 Current Status
- **No PHI/PII processed** — All data: public databases, synthetic, or de-identified
- **No patient-level data** — FAERS is aggregated; ClinicalTrials.gov is public registry
- **No user accounts** — Prototype is single-user local

### 7.2 Future Considerations
| Regulation | Trigger | Preparation |
|------------|---------|-------------|
| **HIPAA** | If user uploads patient registry data | BAA with cloud provider; encryption at rest/transit; access logging |
| **GDPR** | If EU users / EU patient data | DPIA; lawful basis (legitimate interest/consent); DPO; data subject rights |
| **State Laws (CCPA, etc.)** | If US users with personal data | Privacy policy; opt-out; data minimization |

---

## 8. EU AI Act Classification

### 8.1 Risk Assessment
| Criterion | Assessment |
|-----------|------------|
| **Medical Device (MDR)** | No — not intended for diagnosis/treatment; decision support for research |
| **High-Risk AI (Annex III)** | Possibly: "AI systems intended to be used for evaluating the eligibility of natural persons for... clinical trials" — but we don't evaluate patients |
| **Transparency Obligations (Art. 50)** | Yes — AI-generated content (rationales, dossiers) must be labeled |

### 8.2 Likely Classification: **Limited Risk (Transparency Obligations)**
- Disclose AI-generated content
- Provide model information (Model Cards)
- Human oversight (built-in validation UI)

### 8.3 If Classified High-Risk (Conservative Prep)
- Quality management system (ISO 13485 / QMSR)
- Technical documentation (Annex IV)
- Conformity assessment (self or notified body)
- Post-market surveillance plan
- Incident reporting

---

## 9. Intellectual Property & Data Licensing

### 9.1 Data Licenses (Compliance)
| Dataset | License | Commercial Use | Attribution | Our Use |
|---------|---------|----------------|-------------|---------|
| Orphanet | Open (citation) | Yes | Required | ✓ |
| DrugCentral (pre-2012) | Open | Yes | Required | ✓ |
| DrugCentral (post-2012) | Custom (OHDSI) | Requires license | Required | ⚠️ Synthetic proxy |
| TDC | Non-commercial | No (research only) | Required | ✓ (prototype) |
| FAERS | Public domain | Yes | None | ✓ |
| ChEMBL | CC BY-SA 4.0 | Yes (share-alike) | Required | ✓ |
| Reactome | CC BY 4.0 | Yes | Required | ✓ |
| PubMed | Public domain | Yes | None | ✓ |

### 9.2 IP Strategy
- **Trade Secrets**: KG construction pipeline, explanation synthesis method, dossier templates
- **Patents**: 3 provisional filings planned (Indication model architecture, Explainability method, Credibility mapping)
- **Copyright**: Code, documentation, dossier templates
- **Trademark**: "OrphanRepurpose" (filed)

---

## 10. Compliance Checklist (Prototype → Production)

| Area | Prototype | Production Target |
|------|-----------|-------------------|
| **FDA 7-Step Credibility** | Mapped & documented | Implemented + monitored |
| **FDA-EMA 10 Principles** | Designed in | Audited + certified |
| **NAMs Qualification** | ADMET models documented | Submitted for qualification |
| **Orphan Designation Support** | Dossier generator | Validated with FDA feedback |
| **21 CFR Part 11** | N/A | Full compliance |
| **GAMP 5 CSV** | N/A | Category 4 validated |
| **HIPAA/GDPR** | N/A (no PHI) | Ready for PHI if needed |
| **EU AI Act** | Transparency labels | Conformity assessment if high-risk |
| **Data Licenses** | Compliant (public/synthetic) | Licensed for commercial use |
| **Model Cards** | All models | Living documents, versioned |
| **Audit Trail** | Hash-chained JSONL | WORM storage, e-signatures |
| **Change Control** | ADR process | PCCP + standard CCB |

---

## 11. Key References

1. FDA Draft Guidance: "Considerations for the Use of AI To Support Regulatory Decision-Making for Drug and Biological Products" (Jan 2025)
2. FDA-EMA: "Guiding Principles of Good AI Practice in Drug Development" (Jan 2026)
3. FDA: "Reducing Animal Testing in Nonclinical Studies: Year One Progress" (Apr 2025)
4. FDA: "General Considerations for the Use of NAMs in Drug Development" (Draft, 2026)
5. 21 CFR Part 11: Electronic Records; Electronic Signatures
6. 21 CFR 316: Orphan Drugs
7. ICH E6(R3): Good Clinical Practice
8. ICH M4: Common Technical Document
9. EU AI Act (Regulation 2024/1689)
10. GAMP 5: A Risk-Based Approach to Compliant GxP Computerized Systems
11. TDC: "Therapeutics Data Commons" (Huang et al., NeurIPS 2021)
12. DrugCentral: "DrugCentral 2021 supports drug discovery and repositioning" (NAR 2021)

---

*End of Regulatory Compliance Mapping v1.0*
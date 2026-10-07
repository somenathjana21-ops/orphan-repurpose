# Risks & Mitigations — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08

---

## 1. Risk Assessment Framework

| Risk Level | Probability × Impact | Response |
|------------|---------------------|----------|
| **Critical** | High × High | Avoid / Major Mitigation |
| **High** | High × Med / Med × High | Mitigate + Contingency |
| **Medium** | Med × Med / Low × High | Mitigate |
| **Low** | Low × Low | Accept / Monitor |

---

## 2. Technical Risks

| ID | Risk | Prob | Impact | Level | Mitigation | Contingency |
|----|------|------|--------|-------|------------|-------------|
| **T-01** | Public data chemical space shift: TDC/DrugCentral compounds don't cover novel chemical space for rare diseases | High | High | **Critical** | • Document applicability domain per model<br>• Conformal prediction intervals flag OOD<br>• Synthetic augmentation for rare disease relevant space<br>• Partner with foundations for private data | Pivot to "hypothesis generation only" mode; emphasize human review |
| **T-02** | Indication model fails to beat strong baselines (KG path count, similarity) | Med | High | **High** | • Dual-encoder + cross-attention architecture<br>• KG embeddings provide structural prior<br>• Focal loss for class imbalance<br>• Temporal splits prevent leakage<br>• Benchmark against TDC leaderboard | Fallback to ensemble: KG paths + similarity + model voting |
| **T-03** | KG construction fails: identifier mapping errors, incomplete coverage | Med | High | **High** | • Automated QA: connectivity checks, orphan node detection<br>• Manual curation of high-value subgraphs (top 50 rare diseases)<br>• Multiple identifier mapping sources (UniProt, HGNC, Orpha, Mondo)<br>• Versioned KG with rollback | Ship with reduced KG (DrugCentral + Orphanet only); add sources incrementally |
| **T-04** | LLM rationale hallucinates mechanisms | High | Med | **High** | • Constrained prompting with KG paths as required evidence<br>• Fine-tune on verified rationales (not pure generation)<br>• Counterfactual check: "If path removed, rationale changes"<br>• Human validation UI flags implausible claims | Disable LLM rationale; show only KG paths + SHAP |
| **T-05** | FAERS disproportionality analysis produces false signals (stimulated reporting, confounding) | High | Med | **High** | • Multiple methods: ROR, PRR, BCPNN (consensus)<br>• Time-window analysis (exclude post-approval spike periods)<br>• Confounder adjustment (age, sex, indication)<br>• Clear "signal ≠ causality" UI warnings | Safety filter = advisory only; never auto-reject |
| **T-06** | Model inference too slow for interactive use (>30 sec) | Low | Med | **Medium** | • Batch inference for 1,608 drugs (single forward pass)<br>• ONNX export for CPU deployment<br>• Cache embeddings<br>• Async generation with WebSocket progress | Pre-compute for common diseases; background job for rare |
| **T-07** | Cytoscape.js KG graph crashes browser on large subgraphs | Med | Low | **Medium** | • Limit subgraph to 50 nodes / 100 edges<br>• Progressive loading (expand on click)<br>• Canvas renderer, not SVG<br>• Virtualized node rendering | Fallback to static SVG + table view |
| **T-08** | TDC model licenses prevent commercial use | High | High | **Critical** | • Prototype: non-commercial use only (compliant)<br>• Production: train own models on public data (ChEMBL, PubChem)<br>• Negotiate TDC commercial license<br>• Build proprietary ADMET models as differentiator | Replace TDC models with self-trained before commercial launch |

---

## 3. Data Risks

| ID | Risk | Prob | Impact | Level | Mitigation | Contingency |
|----|------|------|--------|-------|------------|-------------|
| **D-01** | DrugCentral post-2012 data license restricts commercial use | High | High | **Critical** | • Use pre-2012 open subset (1,608 drugs includes many post-2012)<br>• Synthetic proxy: ChEMBL bioactivity + literature mining for newer drugs<br>• Negotiate license with UNM/IDG<br>• Focus on older drugs with expired patents (repurposing sweet spot) | Limit to pre-2012 drugs; document coverage gap |
| **D-02** | Orphanet/OrphaNet API changes or access restricted | Low | High | **Medium** | • Download full dataset (XML) and version locally<br>• Map to Mondo Disease Ontology as backup<br>• Monitor Orphanet announcements | Use Mondo + manual curation |
| **D-03** | FAERS API rate limits / format changes break pipeline | Med | Med | **Medium** | • Local quarterly extracts (DVC tracked) via openFDA downloads<br>• neksa/openfda-faers GitHub as reference implementation<br>• Graceful degradation: cached signals if API down | Use local extracts exclusively |
| **D-04** | Rare disease data too sparse for meaningful KG paths | High | Med | **High** | • Pathway-level reasoning (not gene-level only)<br>• Orthology transfer from model organisms<br>• Literature mining for gene-disease links (PubMed NLP)<br>• Synthetic path generation with confidence scores | Show "insufficient evidence" instead of false paths |
| **D-05** | TDC benchmark data leakage (test set contamination) | Med | High | **High** | • Strict scaffold splits (TDC default)<br>• Temporal splits for indication model<br>• Reproduce TDC leaderboard results as sanity check<br>• Document all splits in Model Cards | Report metrics with caveats; emphasize external validation |

---

## 4. Regulatory & Compliance Risks

| ID | Risk | Prob | Impact | Level | Mitigation | Contingency |
|----|------|------|--------|-------|------------|-------------|
| **R-01** | FDA rejects AI-generated Orphan Designation drafts | Low | High | **Medium** | • Explicit "human review required" disclaimers<br>• 7-step credibility mapping per model<br>• Dossier = decision support, not submission-ready<br>• Engage FDA early (Q-submission) | Position as "internal decision support" not regulatory tool |
| **R-02** | Platform classified as Medical Device (SaMD) requiring clearance | Low | High | **Medium** | • Clear intended use: "research hypothesis generation"<br>• No patient-specific recommendations<br>• No diagnostic/therapeutic claims<br>• Disclaimer on every output | Regulatory consultation; limit claims |
| **R-03** | EU AI Act classifies as High-Risk AI | Low | High | **Medium** | • Transparency labeling (Art. 50) implemented<br>• Human oversight built-in (validation UI)<br>• Model Cards = technical documentation<br>• Prepare QMS documentation | Engage EU regulatory consultant |
| **R-04** | Pharma partners require GxP compliance we can't provide | Med | High | **High** | • Prototype explicitly non-GxP<br>• Pilot agreements: "evaluation only"<br>• Roadmap to GAMP 5 Category 4 (doc 07 §6)<br>• Partner with validated platform vendor (Veeva, etc.) | SaaS on validated infrastructure (AWS GovCloud + partner) |
| **R-05** | Data licensing lawsuits (DrugCentral, TDC, ChEMBL) | Low | High | **Medium** | • Legal review of all licenses<br>• Maintain license compliance matrix (doc 07 §9)<br>• Synthetic alternatives for restricted data<br>• Open-source only components for core IP | Pivot to fully synthetic/proprietary data stack |

---

## 5. Market & Business Risks

| ID | Risk | Prob | Impact | Level | Mitigation | Contingency |
|----|------|------|--------|-------|------------|-------------|
| **M-01** | Healx or BenevolentAI pivots to rare-exclusive + explainable | Med | High | **High** | • Speed to market (MVP in 12 months)<br>• Regulatory-ready differentiation (7-step, Orphan dossier)<br>• Patent provisional on explainability method<br>• Deep rare disease KG (Orphanet + Reactome + literature) | Partner instead of compete; white-label our explainability |
| **M-02** | Pharma prefers internal tools over external SaaS | Med | High | **High** | • Pilot-to-license motion (low commitment)<br>• Success-fee alignment (we win when they win)<br>• White-label / on-prem deployment option<br>• API-first for integration into their workflows | Services-heavy model (custom KG + validation studies) |
| **M-03** | Patient foundations lack budget for SaaS | Med | Med | **Medium** | • Grant-funded pilots (ODP, NIH, foundation grants)<br>• Deferred payment (success fee only)<br>• Consortium pricing (multiple foundations)<br>• Free tier for qualified non-profits | Philanthropic funding; grant writing as service |
| **M-04** | Orphan Drug Act incentives reduced / repealed | Low | High | **Medium** | • Diversify: also target EU orphan regulation, Japan SAKIGAKE<br>• Repurposing value exists without incentives (lower cost/risk)<br>• Monitor policy; engage advocacy (NORD, Global Genes) | Emphasize cost/speed advantage regardless of incentives |
| **M-05** | Key talent unavailable (ML + rare disease pharma) | High | High | **Critical** | • Remote-first, global hiring<br>• Advisor-heavy (KOLs, FDA alumni, Pharma BD)<br>• Acqui-hire option (small AI-bio teams)<br>• Upskill: ML engineers learn pharma, pharma scientists learn ML | Fractional experts + strong advisors; outsource non-core |

---

## 6. Operational Risks

| ID | Risk | Prob | Impact | Level | Mitigation | Contingency |
|----|------|------|--------|-------|------------|-------------|
| **O-01** | Founder/key person dependency | High | High | **Critical** | • Document everything (this Brain.md + docs)<br>• Pair programming / knowledge sharing<br>• Advisory board with operational authority<br>• Key person insurance | Succession plan documented |
| **O-02** | Compute costs exceed budget (GPU for training) | Med | Med | **Medium** | • CPU-compatible models (quantized, distilled)<br>• Cloud spot instances for training<br>• TDC pre-trained models (no training needed)<br>• Local inference for prototype | Reduce model size; fewer endpoints |
| **O-03** | Dependency on external APIs (PubMed, ChEMBL) fails | Low | Med | **Low** | • Local mirrors of critical datasets<br>• Graceful degradation (cached data)<br>• Multiple source redundancy | Ship with snapshot datasets |
| **O-04** | Security vulnerability in dependencies | Med | High | **High** | • Dependabot + weekly updates<br>• Minimal dependencies<br>• Container scanning (Trivy)<br>• No external API keys in prototype | Rapid patch deployment |

---

## 7. Risk Register Summary (Top 10)

| Rank | ID | Risk | Level | Owner | Status |
|------|-----|------|-------|-------|--------|
| 1 | T-01 | Chemical space shift | Critical | ML Lead | Mitigating |
| 2 | T-08 | TDC license commercial | Critical | Legal/CEO | Planning |
| 3 | D-01 | DrugCentral license | Critical | Legal/CEO | Mitigating |
| 4 | M-01 | Competitor pivot | High | CEO | Monitoring |
| 5 | M-02 | Pharma SaaS reluctance | High | CEO/BD | Mitigating |
| 6 | M-05 | Talent shortage | Critical | CEO/HR | Active |
| 7 | O-01 | Key person risk | Critical | CEO | Documenting |
| 8 | T-02 | Model performance | High | ML Lead | Building |
| 9 | T-03 | KG construction | High | Data Lead | Building |
| 10 | R-04 | GxP gap | High | Regulatory | Planning |

---

## 8. Risk Monitoring Cadence

| Cadence | Activity | Participants |
|---------|----------|--------------|
| **Weekly** | Technical risk review (T-01 to T-08) | ML Lead, Data Lead, CTO |
| **Bi-weekly** | Business/regulatory risk review (M, R) | CEO, Advisors |
| **Monthly** | Full risk register update | All leads |
| **Quarterly** | Board/advisor risk deep-dive | CEO, Board, Advisors |

---

## 9. Risk-Adjusted Milestones (from Roadmap)

| Milestone | Original Target | Risk-Adjusted | Key Risks Addressed |
|-----------|-----------------|---------------|---------------------|
| M1: KG v1 | Month 3 | Month 4 | T-03, D-02, D-04 |
| M2: Indication Model v1 | Month 6 | Month 7 | T-01, T-02, D-05 |
| M3: Explainability Stack | Month 9 | Month 10 | T-04, R-01 |
| M4: Safety Filter | Month 9 | Month 10 | T-05, D-03 |
| M5: Validation UI | Month 12 | Month 13 | R-01, R-02 |
| M6: Dossier Generator | Month 12 | Month 13 | R-01, R-03 |
| M7: Pilot Customers | Month 15 | Month 16 | M-01, M-02, M-03 |
| M8: Series A Ready | Month 18 | Month 20 | All |

---

*End of Risks & Mitigations v1.0*
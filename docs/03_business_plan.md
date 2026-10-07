# Business Plan — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08
**Status**: DRAFT — For Internal Planning

---

## 1. Executive Summary

**OrphanRepurpose** is an AI-powered platform that systematically identifies and validates drug repurposing opportunities for rare and orphan diseases. By integrating a curated rare-disease knowledge graph (6,000+ diseases, 1,608 FDA-approved drugs), multimodal public datasets, and clinician-in-the-loop explainable AI, the platform delivers prioritized, validation-ready repurposing candidates with audit trails suitable for FDA Orphan Drug Designation submissions.

**The Opportunity**: 95% of ~7,000 rare diseases lack approved treatments. The Orphan Drug Act provides 7-year exclusivity, 25% tax credits, and grant funding — creating a compelling economic case for repurposing. Yet current AI repurposing efforts focus on oncology/COVID-19 (PatSnap 2026). Rare diseases are "underserved areas with fewer dedicated studies."

**Our Wedge**: Exclusive focus on rare/orphan diseases + FDA-ready explainable AI + clinician validation loop = defensible niche with high willingness-to-pay from biotech, pharma, and patient foundations.

**Business Model**: SaaS platform license ($50-200K/yr per disease program) + success fees (1-2% of orphan drug revenue) + services.

**Funding Ask**: $2M Seed (18 months) → Series A $10M (Year 2) → Profitability Year 4.

---

## 2. Problem & Market Context

### 2.1 The Rare Disease Crisis
- **7,000+ rare diseases** affect 300M+ people globally (25-30M in US, 30M in EU)
- **95% have no FDA-approved treatment**
- **Average diagnosis**: 5-7 years; **mortality**: 30% of children die before age 5
- **Traditional discovery**: 10-15 years, $2.6B/approved drug — economically unviable for small populations

### 2.2 Why Repurposing is the Answer
- **Approved drugs**: Known safety, PK/PD, manufacturing — de-risked
- **Orphan Drug Act (1983)**: 7-yr market exclusivity, 25% clinical tax credits, FDA protocol assistance, grant programs (ODP)
- **Repurposing timeline**: 3-5 years, $10-50M vs 10-15 years, $2.6B
- **FDA approving repurposed orphans**: 2023-2025 saw multiple approvals (e.g., nitisinone for AKU, trientine for Wilson's)

### 2.3 Current Market Failures
| Approach | Limitation |
|----------|------------|
| Academic screening | Low throughput, no systematic prioritization, grant-dependent |
| Pharma internal | Portfolio prioritization favors large markets (oncology = 40% of AI repurposing per PatSnap) |
| AI platforms (Healx, Benevolent) | Black-box, no clinician loop, no regulatory audit trail, broad focus |
| Patient foundations | Limited computational expertise, fragmented efforts |

---

## 3. Solution & Value Proposition

### 3.1 Product
**OrphanRepurpose Platform** — Three layers:
1. **Curated Knowledge Foundation**: Rare-disease KG (DrugCentral, Orphanet, TDC, ChEMBL, FAERS, ClinicalTrials.gov, PubMed)
2. **AI Reasoning Engine**: Multi-modal predictor (KG embeddings + molecular GNN + LLM rationale) with safety filtering
3. **Validation & Regulatory Interface**: Clinician validation UI, FDA Orphan Designation dossier generator, 7-step credibility mapping

### 3.2 Value Proposition
> **"From 7,000 rare diseases to validation-ready repurposing candidates in weeks — with mechanistic explanations clinicians trust and regulators can audit."**

### 3.3 Key Differentiators
- **Rare/orphan exclusive focus** (vs broad platforms)
- **Explainable AI**: KG mechanistic paths + counterfactuals + LLM rationale (vs feature importance only)
- **Clinician-in-the-loop**: Built-in validation UI with simulated expert feedback
- **Regulatory-ready output**: FDA Orphan Designation draft + 7-step credibility evidence package
- **Public + synthetic data**: Fully auditable, versioned, no proprietary data dependency
- **Integrated safety**: FAERS disproportionality + TDC ADMET + contraindications (not post-hoc)

---

## 4. Target Customers & ICP

### 4.1 Ideal Customer Profile (ICP)
| Segment | Profile | Pain Point | Budget | Decision Maker |
|---------|---------|------------|--------|----------------|
| **Biotech (Series A-C)** | 10-100 employees, 1-3 orphan programs | Need pipeline expansion, limited computational team | $100-500K/yr | CSO / Head of Discovery |
| **Mid-size Pharma** | $1-10B revenue, orphan franchise | Patent cliffs, lifecycle extension, regulatory pressure | $500K-2M/yr | VP Translational Research |
| **Patient Foundations** | Well-funded (e.g., CF Foundation, MDA) | Desperate for treatments, have patient data/registries | $50-200K/yr + grants | Scientific Director |
| **Academic TTOs** | University tech transfer offices | Need to de-risk IP for licensing | $25-100K/yr | Director of Licensing |

### 4.2 User Personas
1. **Translational Scientist** (Primary): Runs disease queries, evaluates candidates, builds dossiers
2. **Clinical Advisor** (Secondary): Validates mechanisms, assesses clinical feasibility
3. **Regulatory Affairs** (Tertiary): Reviews credibility packages, prepares submissions
4. **Foundation Scientific Director** (Tertiary): Explores portfolio, funds validation studies

---

## 5. Market Sizing

### 5.1 Methodology
- **TAM**: All spending on rare disease drug discovery + AI platforms
- **SAM**: Addressable with SaaS + services model (biotech, mid-pharma, foundations)
- **SOM**: Realistic capture in 3 years (conservative penetration)

### 5.2 Market Size Calculations

**TAM (Global Rare Disease Drug Discovery + AI)**
- Global rare disease market: $300B+ (2025) growing 12% CAGR
- Orphan drug sales: $250B (2025) → $450B (2030)
- R&D spend on rare diseases: ~$50B/yr (est. 15% of pharma R&D)
- AI in drug discovery market: $1.9B (2025) → $19B (2035) at 25.6% CAGR
- **TAM = $50B (R&D) + $19B (AI) ≈ $69B**

**SAM (Platform + Services Addressable)**
- Biotech companies with orphan programs: ~500 globally (Series A+)
- Mid-pharma with orphan franchises: ~50
- Well-funded patient foundations: ~100
- Academic TTOs with rare disease IP: ~200
- Average contract: $150K/yr (blended)
- **SAM = 850 accounts × $150K = $127.5M/yr**

**SOM (3-Year Capture)**
- Year 1: 10 pilots (5 paid) = $750K ARR
- Year 2: 30 customers = $4.5M ARR
- Year 3: 75 customers = $11.25M ARR
- **3-Year SOM = ~$16.5M cumulative revenue**

### 5.3 Market Growth Drivers
- FDA orphan designations: 500+ per year (record 2023: 573)
- Orphan drug approvals: 50-60/year
- AI adoption in pharma: 73% deploying agentic AI by 2026
- Patent cliff: $200B+ exposure 2025-2030
- Patient advocacy funding: $2B+ annually to research

---

## 6. Competitive Landscape & Positioning

### 6.1 Competitive Map

```
                    HIGH EXPLAINABILITY
                          ↑
                          |
    Healx                 |                 OrphanRepurpose
    (rare focus,          |                 (rare exclusive,
     black-box)           |                  explainable, regulatory-ready)
                          |
                          |
    BenevolentAI          |                 Recursion
    (broad,               |                 (phenotypic,
     platform)             |                  not repurposing)
                          |
                          |
         LOW EXPLAINABILITY → HIGH REGULATORY READINESS
```

### 6.2 Competitor Analysis

| Competitor | Focus | Strength | Weakness | Our Edge |
|------------|-------|----------|----------|----------|
| **Healx** | Rare disease repurposing | Disease focus, Healnet platform | Black-box, no clinician loop, no FDA audit trail | Explainability + regulatory output |
| **BenevolentAI** | Broad AI discovery | KG scale, partnerships | Not rare-exclusive, clinical failures | Rare focus + mechanistic rationale |
| **Recursion** | Phenotypic screening | Wet lab + AI loop | Not repurposing, capital intensive | Lower cost, faster, repurposing-specific |
| **Insilico Medicine** | End-to-end discovery | Phase 2 assets, chemistry | Broad, not rare-focused | Rare specialization |
| **Oncocross/Standigm** | Oncology repurposing | Pharma partnerships | Oncology-only | Rare disease white space |
| **Academic tools** (RepoDB, DrugCentral) | Data resources | Free, open | No AI, no UI, no regulatory support | Productized, integrated, actionable |

### 6.3 Positioning Statement
> **For translational scientists at biotech/pharma and rare disease foundations, OrphanRepurpose is the only AI repurposing platform exclusively focused on rare/orphan diseases that delivers mechanistically explained, safety-filtered, regulator-ready candidates — because we combine a curated rare-disease knowledge graph, explainable multi-modal AI, and built-in clinician validation with FDA Orphan Designation dossier generation.**

---

## 7. Business Model & Pricing

### 7.1 Revenue Streams

| Stream | Model | Price | Target |
|--------|-------|-------|--------|
| **Platform SaaS** | Annual license per disease program | $50K (foundation) - $200K (pharma) | All segments |
| **Success Fee** | % of net sales if candidate approved | 1-2% (capped at 10× license) | Biotech/Pharma |
| **Professional Services** | Custom KG curation, validation design, regulatory consulting | $200-500K/project | Pharma, Foundations |
| **Data Network (Future)** | Federated learning across partners | Revenue share | Year 3+ |

### 7.2 Pricing Math
- **Biotech (Series B, 2 programs)**: 2 × $150K = $300K/yr + 1.5% success fee
- **Mid-pharma (5 programs)**: 5 × $200K = $1M/yr + success fees
- **Foundation (3 diseases)**: 3 × $75K = $225K/yr (grant-funded)
- **Blended Year 3 ARR target**: $11.25M at 75 customers × $150K avg

### 7.3 Unit Economics (Year 3 Steady State)
- **CAC**: $50K (content marketing, conferences, referrals)
- **LTV**: 3 years × $150K = $450K (conservative, no expansion)
- **LTV:CAC = 9:1**
- **Gross Margin**: 85% (SaaS), 60% (services)
- **Payback Period**: 4 months

---

## 8. Go-to-Market Strategy

### 8.1 First 10 Customers (Year 1)
| # | Target | Approach | Champion |
|---|--------|----------|----------|
| 1 | Rare disease foundation (e.g., Every Cure partner) | Warm intro via advisor network | Scientific Director |
| 2 | Biotech with 1 orphan asset (Series A) | Conference (BIO, JP Morgan) + demo | CSO |
| 3 | Academic center with rare disease center | Grant collaboration (ODP) | PI + TTO |
| 4 | Mid-pharma orphan franchise | VP Translational intro via advisor | VP Translational |
| 5 | Patient foundation (well-funded) | Advocacy conference (NORD) | Scientific Director |
| 6-10 | Referrals from 1-5 + inbound | Product-led growth | — |

### 8.2 Channels
1. **Direct Sales** (70%): Founder-led → hire 2 AEs Year 2
2. **Partnerships** (20%): CROs (Charles River, Crown), TTOs, foundation networks
3. **Content/Inbound** (10%): Benchmark publications, regulatory guides, webinars

### 8.3 Pharma Partnership Strategy
- **Year 1**: Pilot programs (3-6 months, $50-100K) → case studies
- **Year 2**: Multi-program licenses, co-development agreements
- **Year 3**: Strategic partnerships (joint ventures, equity investments)
- **Key Insight**: Pharma buys *de-risked candidates*, not software — position as "candidate generation engine"

---

## 9. Financial Projections (3-Year)

### 9.1 Assumptions Table

| Parameter | Year 1 | Year 2 | Year 3 |
|-----------|--------|--------|--------|
| Customers (EoY) | 10 | 30 | 75 |
| Avg Contract Value | $75K | $125K | $150K |
| Services Revenue | $200K | $800K | $1.5M |
| Success Fees | $0 | $0 | $500K (prob. weighted) |
| Headcount (EoY) | 8 | 18 | 35 |
| Avg Fully Loaded Cost | $180K | $190K | $200K |
| Cloud/Infra % Revenue | 5% | 4% | 3% |
| Sales & Marketing % Rev | 30% | 25% | 20% |

### 9.2 P&L Projection

| ($000s) | Year 1 | Year 2 | Year 3 |
|---------|--------|--------|--------|
| **SaaS Revenue** | 750 | 3,750 | 11,250 |
| **Services Revenue** | 200 | 800 | 1,500 |
| **Success Fees** | 0 | 0 | 500 |
| **Total Revenue** | **950** | **4,550** | **13,250** |
| **COGS (Cloud + Services Delivery)** | 150 | 500 | 1,200 |
| **Gross Profit** | **800** | **4,050** | **12,050** |
| **Gross Margin** | 84% | 89% | 91% |
| **R&D** | 1,200 | 2,200 | 3,500 |
| **Sales & Marketing** | 285 | 1,138 | 2,650 |
| **G&A** | 400 | 600 | 900 |
| **Total OpEx** | **1,885** | **3,938** | **7,050** |
| **Operating Income** | **(1,085)** | **112** | **5,000** |
| **Op Margin** | -114% | 2% | 38% |

### 9.3 Cash Flow & Burn
- **Year 1 Net Burn**: $1.1M
- **Year 2 Net Burn**: -$0.1M (near breakeven)
- **Year 3 Net Cash Gen**: $4.5M
- **Cumulative Cash Need (pre-revenue to breakeven)**: ~$1.2M

### 9.4 Headcount Plan

| Role | Year 1 | Year 2 | Year 3 |
|------|--------|--------|--------|
| **Founders (2)** | 2 | 2 | 2 |
| **ML/Backend Engineers** | 2 | 5 | 10 |
| **Frontend/UX** | 1 | 2 | 4 |
| **Data/Knowledge Graph** | 1 | 2 | 4 |
| **Regulatory/Clinical** | 0 | 1 | 2 |
| **Sales (AE)** | 0 | 2 | 5 |
| **Customer Success** | 0 | 1 | 3 |
| **Operations/Finance** | 1 | 2 | 3 |
| **Advisors (part-time)** | 3 | 3 | 3 |
| **Total FTE** | **8** | **18** | **35** |

---

## 10. Funding Ask & Use of Funds

### 10.1 Seed Round: $2M (18-month runway)
| Use of Funds | Amount | % |
|--------------|--------|---|
| **Team (7 hires)** | $1.1M | 55% |
| **Cloud/Compute (GPU, data)** | $200K | 10% |
| **Data Licensing/Access** | $100K | 5% |
| **Legal/IP/Regulatory** | $150K | 7.5% |
| **Sales/Marketing (conferences, content)** | $150K | 7.5% |
| **Operations/Buffer** | $300K | 15% |
| **Total** | **$2.0M** | 100% |

### 10.2 Milestones for Series A (Month 18)
- 10 paying customers ($750K ARR)
- 3 published case studies (validated repurposing candidates)
- FDA Orphan Designation draft used in ≥1 real submission
- TDC benchmark: Top 10 on drug-disease indication task
- Team: 18 FTE, repeatable sales motion

### 10.3 Series A: $10M (Year 2-3)
- Scale sales (5 AEs), customer success (3)
- Expand ML team (foundation models, LLM fine-tuning)
- Build federated data network with foundations
- International expansion (EU, Japan orphan pathways)
- Target: $11M ARR, profitability by Year 4

---

## 11. Team Plan

### 11.1 Founding Team (Assumed)
- **CEO/CSO**: Pharma/ML background, rare disease experience
- **CTO**: ML systems, KG, production deployment
- **Advisors**: KOL in rare disease, FDA regulatory expert, Pharma BD leader

### 11.2 Key Hires (Year 1)
1. **Senior ML Engineer** (KG + GNN + LLM) — Core IP
2. **Backend Engineer** (API, data pipelines, TDC integration)
3. **Frontend Engineer** (React, scientific viz, validation UI)
4. **Data Curator/KN Engineer** (KG construction, DrugCentral/Orphanet)
5. **Regulatory/Clinical Scientist** (FDA pathway, credibility framework)
6. **Founding AE** (technical sales, pharma network)
7. **Operations/Finance** (grants, compliance, HR)

### 11.3 Advisory Board (Target)
- Rare disease KOL (e.g., NIH NCATS, Orphanet leader)
- FDA former reviewer (Orphan Drug Division)
- Pharma BD VP (orphan franchise experience)
- AI in Drug Discovery pioneer (academic/industry)

---

## 12. Milestones & KPIs

### 12.1 Product Milestones
| Milestone | Target | Success Criteria |
|-----------|--------|------------------|
| **M1: KG v1 + API** | Month 3 | 6,000 diseases, 1,608 drugs, queryable via GraphQL |
| **M2: Indication Model v1** | Month 6 | Top-20 recall ≥70% on RepoDB holdout |
| **M3: Explainability Stack** | Month 9 | KG paths + LLM rationale + SHAP for 100% candidates |
| **M4: Safety Filter** | Month 9 | FAERS + TDC ADMET integrated, precision ≥85% |
| **M5: Validation UI** | Month 12 | Clinician sim: ≥4/5 plausibility on 50 cases |
| **M6: Orphan Dossier Generator** | Month 12 | 7-step credibility map complete, PDF export |
| **M7: Pilot with 3 Customers** | Month 15 | Paid pilots, case studies drafted |
| **M8: Series A Ready** | Month 18 | 10 customers, $750K ARR, 3 case studies |

### 12.2 Business KPIs
| KPI | Year 1 | Year 2 | Year 3 |
|-----|--------|--------|--------|
| ARR | $750K | $4.5M | $11.25M |
| Net Revenue Retention | N/A | 120% | 130% |
| CAC Payback | 4 mo | 3 mo | 3 mo |
| Candidates Delivered | 50 | 300 | 1,000 |
| Validated in Wet Lab | 5 | 30 | 100 |
| Orphan Designations Filed | 1 | 5 | 15 |

---

## 13. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Public data insufficient for ultra-rare diseases** | Medium | High | Synthetic data generation, literature mining, foundation partnerships for private data |
| **Inductive Bio / big tech dominate ADMET/indication benchmarks** | High | Medium | Differentiate on rare-disease specificity + explainability + regulatory output, not raw accuracy |
| **Pharma prefers internal tools over SaaS** | Medium | High | Pilot-to-license motion, success-fee alignment, white-label option |
| **FDA rejects AI-generated Orphan Designation drafts** | Low | High | Human-in-loop required, 7-step mapping explicit, disclaimer prominent |
| **Key hires not available (ML + pharma rare combo)** | Medium | High | Remote-first, advisor-heavy, acqui-hire option |
| **Patient foundations lack budget** | Medium | Medium | Grant-funded pilots, ODP grant collaboration, deferred payment |
| **Competitor pivots to rare focus (Healx)** | Medium | Medium | Speed to market, regulatory-ready differentiation, patent on explainability method |

---

## 14. Exit & Strategic Options

### 14.1 Primary: Strategic Acquisition (Year 4-6)
- **Acquirers**: Veeva (Vault Safety + Discovery), IQVIA, Medidata, Recursion, BenevolentAI, Schrödinger, Large Pharma (Novartis, Roche, Pfizer orphan units)
- **Rationale**: Regulatory-ready AI + rare disease expertise + pharma relationships = strategic asset
- **Comparable**: Healx valuation ~$500M (2023), Cyclica acquired by Recursion ($40M), Genentech acquired Prescient Design

### 14.2 Secondary: IPO (Year 6-8)
- If ARR >$50M, >30% growth, profitable
- Comps: Schrödinger, Certara, Veeva (vertical SaaS + science)

### 14.3 Tertiary: Pharma Spin-in / Joint Venture
- Co-develop 2-3 assets, pharma funds validation, equity + royalties
- De-risks both sides, aligns incentives

---

## 15. Intellectual Property Strategy

| IP Asset | Type | Timeline |
|----------|------|----------|
| **KG Construction Pipeline** | Trade Secret + Patent (method) | Year 1 provisional |
| **Multi-modal Indication Model Architecture** | Patent | Year 1 provisional |
| **Explainability Method (KG paths + counterfactuals + LLM)** | Patent | Year 1 provisional |
| **FDA Credibility Framework Mapping** | Trade Secret | Continuous |
| **Orphan Dossier Auto-generation** | Copyright + Patent | Year 2 |
| **Brand: OrphanRepurpose** | Trademark | Month 1 |

---

## 16. Appendix: Key References

1. FDA Orphan Drug Act: 21 CFR 316 — https://www.fda.gov/industry/designating-orphan-product
2. PatSnap 2026: AI Drug Repurposing Landscape — https://www.patsnap.com/resources/blog/articles/ai-drug-repurposing-technology-landscape-2026
3. TDC: https://tdcommons.ai (ADMET_Group, TOP trial outcome)
4. DrugCentral: https://drugcentral.org (1,608 FDA small molecules)
5. FAERS/openFDA: https://open.fda.gov/data/faers (31M+ reports)
6. TrialBench: arXiv:2407.00631v2, PMCID:PMC12475113
7. Orphanet: https://www.orpha.net (6,000+ rare diseases)
8. FDA Jan 2025 Draft Guidance: AI for Regulatory Decision-Making
9. FDA-EMA Jan 2026: Guiding Principles of Good AI Practice
10. Fortune Business Insights: AI in Drug Repurposing Market 2034
11. ResearchAndMarkets: AI in Drug Repurposing 2026 Report
12. Global Genes: Rare Disease Impact Report (300M patients)

---

*End of Business Plan v1.0 — All figures conservative estimates for planning. Update with real data as pilots progress.*
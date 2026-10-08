# OrphanRepurpose: AI-Driven Drug Repurposing for Rare & Orphan Diseases

An AI-powered platform that identifies and validates drug repurposing opportunities for rare and orphan diseases by integrating a curated rare-disease knowledge graph, multimodal public datasets, and clinician-in-the-loop explainable AI.

## Overview

OrphanRepurpose addresses the critical unmet need in rare disease therapeutics by leveraging AI to repurpose existing approved drugs for new indications. The platform combines:
- Curated knowledge graph of rare diseases and drug mechanisms
- Multimodal public datasets (DrugCentral, TDC, FAERS, ClinicalTrials.gov, PubMed, ChEMBL)
- Explainable AI with clinician validation workflows
- Audit trails suitable for FDA Orphan Drug Designation submissions

## Key Features

- **Knowledge Graph Construction**: Integrated rare disease knowledge graph using Kuzu embedded database
- **Drug-Disease Prediction**: Graph neural network models (DualEncoderCrossAttention, SimpleIndicationModel_MLP) for indication prediction
- **Explainability Suite**: SHAP values, counterfactual explanations, knowledge graph path extraction, and BioMistral-7B generated rationales
- **Safety Filtering**: FAERS-based adverse event analysis and TDC ADMET predictions
- **Validation Interface**: Clinician-in-the-loop validation with audit logging
- **Dossier Generation**: Automated FDA-ready submission documents with credibility mapping

## Technical Stack

- **Backend**: Python, PyTorch/PyG, Kuzu (embedded graph database)
- **ML Models**: GraphSAGE, RGCN, DualEncoderCrossAttention, MLP with Morgan fingerprints
- **Explainability**: SHAP, BioMistral-7B (LLM rationale), knowledge graph traversal
- **API**: RESTful endpoints for model inference and knowledge graph queries
- **Frontend**: React/Vite interface (in prototype directory)
- **Data Sources**: DrugCentral, TDC, FAERS, ChEMBL, ClinicalTrials.gov, PubMed

## Current Status & Metrics

### Phase 5 - Build (M2: Indication Model) - 90% Complete

**Model Performance (ChEMBL-augmented dataset):**
- AUPRC: 0.817
- AUROC: 0.807
- ECE: 0.050
- Recall@10: 78.5%
- Recall@20: 91.7% ✅ (Target: ≥70%)
- Recall@50: 98.1%
- Recall@100: 99.6%

**Dataset Statistics:**
- Drugs: 1,645
- Diseases: 1,470
- Known indications: 14,578
- Drug-target edges: 915
- Knowledge graph: 3,532 nodes, 15,504 edges

## Project Structure

```
orphan-repurpose/
├── Brain.md                    # Project vision, roadmap, and technical documentation
├── Makefile                   # Build and deployment commands
├── docker-compose.yml         # Container orchestration
├── PROGRESS.md                # Ongoing progress tracking
├── data/                      # Data storage and processing
├── docs/                      # Detailed technical documentation
├── pitch/                     # Pitch materials and presentations
├── prototype/                 # Working prototype implementation
│   ├── scripts/etl/           # Data extraction, transformation, loading
│   ├── models/                # Trained ML models
│   └── api/                   # REST API endpoints
└── .gitignore                 # Git exclusion patterns
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/somenathjana21-ops/orphan-repurpose.git
   cd orphan-repurpose
   ```

2. Install dependencies:
   ```bash
   # Assuming you have Python 3.9+ and pip
   pip install -r requirements.txt  # If available
   # Or install key packages:
   pip install torch torch-geometric kuzu tdc rdkit pandas numpy scikit-learn
   ```

3. Run the prototype:
   ```bash
   # See Makefile for available commands
   make help
   ```

## Development Roadmap

See `Brain.md` for detailed phase breakdown:

- **M1**: Knowledge Graph v1 + API (90% complete)
- **M2**: Indication Model v1 (90% complete - Recall@20 target achieved)
- **M3**: Explainability Stack
- **M4**: Safety Filter
- **M5**: Validation UI
- **M6**: Dossier Generator
- **M7**: Pilot Integration
- **M8**: Series A Ready

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Somenath Jana - somenathjana21@gmail.com

Built with ❤️ for rare disease patients everywhere.
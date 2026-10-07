# Data & Models Specification — OrphanRepurpose

**Project**: OrphanRepurpose — AI-Driven Drug Repurposing for Rare & Orphan Diseases
**Version**: 1.0
**Date**: 2026-10-08

---

## 1. Data Sources & Schemas

### 1.1 Primary Datasets

| Dataset | Source | Format | Size | Key Fields | License |
|---------|--------|--------|------|------------|---------|
| **Orphanet** | orpha.net | XML/JSON | 6,000 diseases | ORPHAcode, name, prevalence, genes (HGNC), phenotypes (HPO), age of onset, inheritance | Open (citation required) |
| **DrugCentral** | drugcentral.org | TSV/SQL dump | 4,950 drugs (1,608 FDA small mol) | struct_id, smiles, inchi, inchikey, moa, targets (UniProt), indications (SNOMED/UMLS), approval_year | Open (pre-2012) / License (post-2012) |
| **TDC** | tdcommons.ai | Python API / CSV | 66 datasets, 22 tasks | ADMET_Group (22 endpoints), TOP (17,538 trials), drug-target, etc. | Non-commercial |
| **FAERS** | open.fda.gov | JSON (quarterly) / API | 31M+ reports | safetyreportid, patient, drug, reaction (MedDRA), outcomes | Public domain |
| **ChEMBL** | ebi.ac.uk/chembl | SQL/Parquet | 2.4M compounds, 15M activities | molecule_chembl_id, target_chembl_id, standard_value, standard_type, assay_type | CC BY-SA 4.0 |
| **Reactome** | reactome.org | TXT/SBML/JSON | ~10K pathways, 12K reactions | pathway_id, name, species, genes (UniProt), reactions | CC BY 4.0 |
| **PubMed** | ncbi.nlm.nih.gov | XML/API | 35M+ abstracts | pmid, title, abstract, mesh, chemicals, publication_date | Public domain |
| **UniProt** | uniprot.org | XML/TSV | 200K+ reviewed | accession, gene_name, function, pathway, disease | CC BY 4.0 |

### 1.2 Derived/Processed Data

| Artifact | Format | Location | Description |
|----------|--------|----------|-------------|
| **KG Nodes** | Parquet | `data/kg/nodes/` | Node ID, type, properties (name, synonyms, identifiers) |
| **KG Edges** | Parquet | `data/kg/edges/` | Source, target, relation_type, evidence, weight |
| **KG Embeddings** | .pt / .npy | `models/kg_embeddings/` | 256-d RGCN embeddings per node |
| **Drug Fingerprints** | .npz | `data/molecular/` | Morgan (1024-bit), MACCS, RDKit descriptors for 1,608 drugs |
| **FAERS Signals** | Parquet | `data/safety/faers_signals/` | ROR, PRR, BCPNN per drug-reaction pair (quarterly) |
| **ADMET Predictions** | Parquet | `data/safety/admet/` | 22 endpoints × 1,608 drugs (pre-computed) |
| **Literature Index** | ChromaDB | `data/literature/chroma/` | Embedded abstracts for semantic search |

---

## 2. Knowledge Graph Construction

### 2.1 Node Types (12)
| Type | Source | Count (est.) | Key Properties |
|------|--------|--------------|----------------|
| `Disease` | Orphanet | 6,000 | orpha_id, name, prevalence, inheritance, age_onset |
| `Gene` | Orphanet + UniProt | 4,000 | hgnc_id, symbol, name, uniprot_id |
| `Pathway` | Reactome/KEGG | 10,000 | reactome_id, name, species |
| `Drug` | DrugCentral | 1,608 | drugcentral_id, smiles, inchikey, approval_year |
| `Target` | ChEMBL/DrugCentral | 8,000 | uniprot_id, gene_symbol, target_class |
| `MolecularStructure` | DrugCentral | 1,608 | smiles, inchi, molecular_weight, logp |
| `Indication` | DrugCentral | 14,000 | drug_id, disease_id (SNOMED→Orpha mapping), source |
| `Contraindication` | DrugCentral | 2,000 | drug_id, disease_id, source |
| `Publication` | PubMed | 500K (targeted) | pmid, title, year, mesh_terms |
| `Evidence` | Derived | 1M+ | publication_id, subject_type, subject_id, predicate, confidence |
| `AdverseEvent` | FAERS | 500K (signals) | drug_id, meddra_pt, ror, prr, bcpnn, n_reports |
| `ADMETProperty` | TDC | 35K (1,608 × 22) | drug_id, endpoint, value, unit, model_version |

### 2.2 Edge Types (18)
| Relation | Source→Target | Evidence Source | Weight |
|----------|---------------|-----------------|--------|
| `treats` | Drug→Disease | DrugCentral indications | 1.0 |
| `contraindicates` | Drug→Disease | DrugCentral contraindications | 1.0 |
| `has_target` | Drug→Target | DrugCentral MoA + ChEMBL | pChEMBL / 10 |
| `participates_in` | Target→Pathway | Reactome | 1.0 |
| `implicated_in` | Pathway→Disease | Literature mining + GWAS | Text-mining score |
| `has_gene` | Disease→Gene | Orphanet | 1.0 |
| `in_pathway` | Gene→Pathway | Reactome | 1.0 |
| `has_structure` | Drug→MolecularStructure | DrugCentral | 1.0 |
| `supports` | Publication→(Drug/Disease/Target) | PubMed + NLP | NLP confidence |
| `causes_ae` | Drug→AdverseEvent | FAERS disproportionality | log(ROR) |
| `has_admet` | Drug→ADMETProperty | TDC predictions | 1.0 |

### 2.3 KG Building Pipeline
```python
# scripts/etl/build_kg.py
1. Download all source files (Orphanet XML, DrugCentral TSV, etc.)
2. Parse & normalize identifiers (map SNOMED/UMLS → Orpha, UniProt → HGNC)
3. Create nodes with stable IDs: <type>:<source>:<id> (e.g., "disease:orpha:635")
4. Create edges with evidence references
5. Quality checks: connectivity, orphan nodes, duplicate edges
6. Export to Parquet + import to Kuzu/Neo4j
7. Train RGCN embeddings (see §3.2)
8. Version & tag (Git LFS for Parquet, DVC for large files)
```

---

## 3. Model Specifications

### 3.1 Indication Prediction Model

#### 3.1.1 Architecture Details
```yaml
model_name: "OrphanRepurpose-Indication-v1"
architecture: "DualEncoderCrossAttention"
drug_encoder:
  type: "GraphSAGE"
  input: "Molecular graph (RDKit: atoms=nodes, bonds=edges)"
  node_features: 78  # atom type, degree, hybridization, aromatic, etc.
  edge_features: 6   # bond type, conjugation, ring, stereo
  hidden_dim: 256
  num_layers: 3
  dropout: 0.1
  readout: "global_mean_pool"
  output_dim: 256
disease_encoder:
  type: "EmbeddingLookup"
  input: "Disease node ID"
  source: "Pre-trained KG embeddings (RGCN, 256-d)"
  output_dim: 256
cross_attention:
  type: "MultiheadAttention"
  num_heads: 4
  embed_dim: 256
  dropout: 0.1
  bidirectional: true  # drug→disease and disease→drug
prediction_head:
  type: "MLP"
  layers: [512, 256, 1]
  activation: "ReLU"
  output_activation: "Sigmoid"
calibration:
  method: "TemperatureScaling + ConformalPrediction"
  coverage: 0.90  # 90% prediction intervals
```

#### 3.1.2 Training Configuration
```yaml
training:
  positive_source: "DrugCentral known indications (drug-disease)"
  negative_strategy: "Contraindications (1:1) + random unconnected (1:3)"
  train_val_test_split: "Temporal (pre-2020 train, 2020-2022 val, 2023+ test)"
  loss:
    primary: "FocalLoss(gamma=2.0, alpha=0.25)"
    auxiliary: "CalibrationLoss(ECE)"
  optimizer: "AdamW(lr=1e-3, weight_decay=1e-4)"
  scheduler: "CosineAnnealingWarmRestarts(T_0=10)"
  epochs: 50
  early_stopping: "val_auprc patience=10"
  batch_size: 256 (drug-disease pairs)
  device: "cuda if available else cpu"
```

#### 3.1.3 Evaluation Metrics
| Metric | Target | Benchmark |
|--------|--------|-----------|
| **AUPRC** (primary) | ≥0.45 | TDC drug-disease leaderboard |
| **AUROC** | ≥0.85 | TDC drug-disease leaderboard |
| **Recall@20** | ≥70% | Known repurposing successes (RepoDB holdout) |
| **Recall@50** | ≥85% | — |
| **ECE (calibration)** | ≤0.05 | Temperature scaling |
| **Prediction Interval Coverage** | 90% ± 2% | Conformal prediction |
| **Inference Latency** | <100ms/batch(1608) | GPU: <10ms, CPU: <100ms |

### 3.2 KG Embeddings (RGCN)

```yaml
model_name: "OrphanRepurpose-KGE-v1"
architecture: "RGCN"
num_layers: 2
hidden_dim: 256
num_bases: 30  # for relation parameterization
dropout: 0.2
training:
  task: "LinkPrediction"
  negative_sampling: "Uniform (1:10)"
  loss: "MarginRankingLoss(margin=1.0)"
  optimizer: "Adam(lr=1e-2)"
  epochs: 100
  eval_metric: "MRR, Hits@1, Hits@10"
output: "Entity embeddings (256-d) for all node types"
```

### 3.3 ADMET Models (TDC Pre-trained)

| Endpoint | TDC Dataset | Task | Metric | Model Source |
|----------|-------------|------|--------|--------------|
| Caco2 Permeability | caco2_wang | Regression | Spearman | TDC leaderboard best |
| HIA | hia_hou | Binary | AUPRC | TDC leaderboard best |
| CYP2C9 Inhibition | cyp2c9_veith | Binary | AUPRC | TDC leaderboard best |
| CYP2D6 Inhibition | cyp2d6_veith | Binary | AUPRC | TDC leaderboard best |
| CYP3A4 Inhibition | cyp3a4_veith | Binary | AUPRC | TDC leaderboard best |
| CYP2C9 Substrate | cyp2c9_substrate | Binary | AUPRC | TDC leaderboard best |
| CYP2D6 Substrate | cyp2d6_substrate | Binary | AUPRC | TDC leaderboard best |
| CYP3A4 Substrate | cyp3a4_substrate | Binary | AUROC | TDC leaderboard best |
| Half Life | half_life_obach | Regression | Spearman | TDC leaderboard best |
| Clearance Hepatocyte | cl_hepatocyte | Regression | Spearman | TDC leaderboard best |
| Clearance Microsome | cl_microsome | Regression | Spearman | TDC leaderboard best |
| DILI | dili | Binary | AUPRC | TDC leaderboard best |
| ... | ... | ... | ... | ... |

**Note**: For prototype, use TDC's pre-trained model checkpoints via `tdc` Python package. Fine-tune on DrugCentral chemical space if time permits.

### 3.4 LLM Rationale Generator

```yaml
model_name: "OrphanRepurpose-LLM-Rationale-v1"
base_model: "BioMistral-7B" (4-bit quantized) OR "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract" (fine-tuned)
approach: "Few-shot prompting with structured template" (if BioMistral) OR "Fine-tuning" (if PubMedBERT)
prompt_template: |
  You are a pharmacology expert. Given a drug, a rare disease, and mechanistic paths from a knowledge graph,
  write a 2-3 sentence mechanistic rationale for why this drug might treat this disease.
  
  Drug: {drug_name} (MoA: {moa})
  Disease: {disease_name} (Genes: {genes}, Pathways: {pathways})
  Mechanistic Paths:
  {kg_paths_formatted}
  
  Rationale:
fine_tuning_data: "Synthetic rationales generated from KG paths + expert review (target: 1,000 examples)"
inference: "Temperature=0.3, max_new_tokens=100, stop at newline"
```

### 3.5 Explainability Components

| Component | Method | Output |
|-----------|--------|--------|
| **KG Paths** | Yen's k-shortest paths (k=3) on weighted KG | List of paths: Drug→Target→Pathway→Gene→Disease |
| **SHAP** | KernelSHAP on Morgan fingerprints (1024-bit) | Substructure importance dict {bit_idx: shap_value} |
| **Counterfactual** | Edge ablation on KG paths | "Removing {edge} changes probability by {delta}" |
| **LLM Rationale** | See §3.4 | Natural language summary |

---

## 4. Evaluation Framework

### 4.1 Benchmark Datasets

| Benchmark | Source | Use Case |
|-----------|--------|----------|
| **RepoDB** | DrugCentral-derived | Drug-disease indication holdout (known repurposing) |
| **TDC Drug-Disease** | TDC | Standardized benchmark with leaderboard |
| **Orphanet Gold Standard** | Curated | Rare disease specific: drugs with orphan designation |
| **FAERS Validation** | Known withdrawals | Safety filter precision/recall |
| **Literature Verification** | Manual curation | Explanation plausibility (50 cases) |

### 4.2 Evaluation Protocol

```python
# evaluation/protocol.py
def evaluate_indication_model(model, test_pairs):
    """Evaluate on temporal holdout (post-2022 indications)"""
    y_true, y_pred = [], []
    for drug_id, disease_id in test_pairs:
        prob = model.predict(drug_id, disease_id)
        y_pred.append(prob)
        y_true.append(1 if (drug_id, disease_id) in known_indications else 0)
    
    return {
        "auprc": average_precision_score(y_true, y_pred),
        "auroc": roc_auc_score(y_true, y_pred),
        "recall_at_k": {k: recall_at_k(y_true, y_pred, k) for k in [10, 20, 50, 100]},
        "ece": expected_calibration_error(y_true, y_pred),
        "coverage": conformal_coverage(model, test_pairs, alpha=0.10)
    }

def evaluate_explanations(model, test_cases, clinicians=3):
    """Simulated clinician evaluation of mechanistic plausibility"""
    scores = []
    for case in test_cases:
        explanation = model.explain(case.drug, case.disease)
        # Simulated: compare to expert-written rationale
        similarity = bert_score(explanation.llm_rationale, case.expert_rationale)
        scores.append(similarity.f1)
    return {"mean_bertscore_f1": np.mean(scores), "distribution": scores}
```

### 4.3 Baseline Models (for comparison)

| Baseline | Description | Expected AUPRC |
|----------|-------------|----------------|
| **Random** | Random ranking | ~0.01 (prevalence) |
| **Frequency** | Rank by drug approval count | ~0.05 |
| **Similarity** | Chemical similarity to known treatments | ~0.15 |
| **KG Path Count** | Number of paths drug→disease | ~0.25 |
| **TDC Best** | TDC leaderboard top model | ~0.40 |
| **Our Model (target)** | Dual-encoder + KG + calibration | **≥0.45** |

---

## 5. Data Versioning & Reproducibility

| Artifact | Versioning | Storage |
|----------|------------|---------|
| Raw downloads | DVC (SHA256) | `data/raw/` (gitignored, DVC tracked) |
| Processed Parquet | DVC + Git LFS | `data/processed/` |
| KG database | DVC (dump files) | `data/kg/dump/` |
| Model checkpoints | DVC + Git LFS | `models/` |
| Training logs | MLflow (local) | `mlruns/` |
| Evaluation results | JSON + Git | `evaluation/results/` |

**Reproducibility Commands**:
```bash
# Full pipeline
make data          # Download + process all data (DVC pull)
make kg            # Build KG + train embeddings
make train         # Train indication model
make eval          # Run full evaluation suite
make demo          # Generate demo dossier
```

---

## 6. Synthetic Data Strategy (for gaps)

| Gap | Synthetic Approach |
|-----|-------------------|
| Ultra-rare diseases (<10 patients) with no gene/pathway data | Generate synthetic gene-pathway associations from model organism orthologs |
| Missing DrugCentral post-2012 indications | Use ChEMBL bioactivity + literature mining as proxy |
| FAERS under-reporting for rare diseases | Simulate reporting rates using capture-recapture models |
| LLM rationale training data | Generate from KG paths using template + expert review (1000 examples) |
| Negative indication pairs | Systematic: all unconnected drug-disease pairs minus contraindications |

---

## 7. Model Cards (Prototype)

Each model includes a `MODEL_CARD.md`:
- **Intended Use**: Rare disease repurposing candidate ranking
- **Training Data**: Sources, sizes, splits, biases
- **Limitations**: Public data chemical space shift, rare disease data sparsity, no wet-lab validation
- **Ethical Considerations**: Not for clinical use, requires expert review, orphan drug incentives may distort priorities
- **Performance**: Metrics from §3.1.3, §4.2
- **Version**: Semantic versioning (v1.0.0, v1.1.0, etc.)

---

*End of Data & Models Spec v1.0*
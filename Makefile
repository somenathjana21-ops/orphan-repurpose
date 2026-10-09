# OrphanRepurpose Makefile
# Usage: make <target>
# Key targets: setup, run, demo, test, lint, clean, verify

.PHONY: help setup data-download data-process kg-build kg-embeddings molecular-feats faers-signals admet-predict literature-index model-train run demo test lint clean verify install-shap install-tdc

# Default target
help:
	@echo "OrphanRepurpose - AI-Driven Drug Repurposing for Rare & Orphan Diseases"
	@echo ""
	@echo "Key targets:"
	@echo "  make setup           - Full setup: download data, process, build KG, train models"
	@echo "  make run             - Start backend + frontend (docker-compose)"
	@echo "  make demo            - Run full NPC demo pipeline"
	@echo "  make test            - Run all tests"
	@echo "  make lint            - Run linters (ruff, mypy, eslint)"
	@echo "  make clean           - Clean build artifacts"
	@echo "  make verify          - Run tests + check all endpoints"
	@echo ""
	@echo "Individual pipeline steps:"
	@echo "  make data-download   - Download all raw datasets"
	@echo "  make data-process    - Process raw data to Parquet"
	@echo "  make kg-build        - Build Kuzu KG + train RGCN embeddings"
	@echo "  make molecular-feats - Compute molecular fingerprints"
	@echo "  make faers-signals   - Compute FAERS disproportionality"
	@echo "  make admet-predict   - Run ADMET predictions (RDKit fallback)"
	@echo "  make literature-index - Index PubMed abstracts in ChromaDB"
	@echo "  make model-train     - Train indication prediction model"
	@echo ""
	@echo "Installation helpers:"
	@echo "  make install-shap    - Install SHAP for model explainability"
	@echo "  make install-tdc     - Install TDC (requires GPU for deep learning)"

# Configuration
DATA_DIR := ./prototype/data
RAW_DIR := $(DATA_DIR)/raw
PROCESSED_DIR := $(DATA_DIR)/processed
MODELS_DIR := ./prototype/models
BACKEND_DIR := ./prototype/backend
FRONTEND_DIR := ./prototype/frontend

# Python environment resolution (supports local venv or system python)
ifeq ($(OS),Windows_NT)
    VENV_PY := $(wildcard .venv/Scripts/python.exe)
    PYTHON ?= $(if $(VENV_PY),$(abspath $(VENV_PY)),python)
else
    VENV_PY := $(wildcard .venv/bin/python)
    PYTHON ?= $(if $(VENV_PY),$(abspath $(VENV_PY)),python3)
endif

# =============================================================================
# DATA DOWNLOAD
# =============================================================================
data-download: download-orpha download-drugcentral download-tdc download-faers download-chembl download-reactome download-pubmed download-uniprot generate-demo-data

download-orpha:
	@echo "📥 Downloading Orphanet data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_orpha.py $(DATA_DIR)

download-drugcentral:
	@echo "📥 Downloading DrugCentral data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_drugcentral.py $(DATA_DIR)

download-tdc:
	@echo "📥 Downloading TDC data..."
	@echo "  Note: TDC requires GPU for deep learning models."
	@echo "  Install with: pip install tdc"
	cd $(BACKEND_DIR) && python ../scripts/download/download_tdc.py $(DATA_DIR)

download-faers:
	@echo "📥 Downloading FAERS data via openFDA API..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_faers.py $(DATA_DIR)

download-chembl:
	@echo "📥 Copying ChEMBL data from /root/..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_chembl.py $(DATA_DIR)

download-reactome:
	@echo "📥 Creating curated Reactome pathway data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_reactome.py $(DATA_DIR)

download-pubmed:
	@echo "📥 Creating curated PubMed publication data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_pubmed.py $(DATA_DIR)

download-uniprot:
	@echo "📥 Creating curated UniProt mapping data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_uniprot.py $(DATA_DIR)

# =============================================================================
# DATA PROCESSING
# =============================================================================
data-process: process-orpha process-drugcentral process-tdc process-faers process-chembl process-reactome process-pubmed

process-orpha:
	@echo "⚙️  Processing Orphanet data..."
	python ./prototype/scripts/etl/process_orpha.py $(RAW_DIR)/orpha $(PROCESSED_DIR)/orpha

process-drugcentral:
	@echo "⚙️  Processing DrugCentral data..."
	python ./prototype/scripts/etl/process_drugcentral.py $(RAW_DIR)/drugcentral $(PROCESSED_DIR)/drugcentral

process-tdc:
	@echo "⚙️  Processing TDC data..."
	@echo "  Note: TDC requires GPU for deep learning models."
	python ./prototype/scripts/etl/process_tdc.py $(RAW_DIR)/tdc $(PROCESSED_DIR)/tdc

process-faers:
	@echo "⚙️  Processing FAERS data..."
	python ./prototype/scripts/etl/process_faers.py $(RAW_DIR)/faers $(PROCESSED_DIR)/faers

process-chembl:
	@echo "⚙️  Processing ChEMBL data..."
	python ./prototype/scripts/etl/merge_chembl_data.py

process-reactome:
	@echo "⚙️  Processing Reactome data..."
	python ./prototype/scripts/etl/process_reactome.py $(RAW_DIR)/reactome $(PROCESSED_DIR)/reactome

process-pubmed:
	@echo "⚙️  Processing PubMed data..."
	python ./prototype/scripts/etl/process_pubmed.py $(RAW_DIR)/pubmed $(PROCESSED_DIR)/pubmed

# =============================================================================
# KG BUILD
# =============================================================================
kg-build:
	@echo "🏗️  Building Knowledge Graph..."
	python ./prototype/scripts/etl/build_kg.py $(PROCESSED_DIR) $(DATA_DIR)/kuzu_db

# =============================================================================
# KG EMBEDDINGS
# =============================================================================
kg-embeddings:
	@echo "🧠 Training KG embeddings (RGCN)..."
	cd $(BACKEND_DIR) && python ../scripts/etl/train_kg_embeddings.py $(DATA_DIR)/kuzu_db $(MODELS_DIR)/kg_embeddings.pkl

# =============================================================================
# MOLECULAR FEATURES
# =============================================================================
molecular-feats:
	@echo "🧬 Computing molecular fingerprints..."
	cd $(BACKEND_DIR) && python ../scripts/etl/compute_molecular_features.py $(PROCESSED_DIR) $(DATA_DIR)/molecular

# =============================================================================
# FAERS SIGNALS
# =============================================================================
faers-signals:
	@echo "⚠️  Computing FAERS disproportionality signals..."
	python ./prototype/scripts/etl/faers_disproportionality.py $(DATA_DIR)

# =============================================================================
# ADMET PREDICTIONS
# =============================================================================
admet-predict:
	@echo "🧪 Running ADMET predictions (RDKit fallback)..."
	@echo "  Note: For production use with GPU, use TDC ADMET models instead."
	python ./prototype/scripts/etl/admet_predict.py $(DATA_DIR)

# =============================================================================
# LITERATURE INDEX
# =============================================================================
literature-index:
	@echo "📚 Indexing literature in ChromaDB..."
	python ./prototype/scripts/etl/literature_index.py $(DATA_DIR)

# =============================================================================
# MODEL TRAINING
# =============================================================================
model-train: kg-embeddings train-indication-model

train-indication-model:
	@echo "🧠 Training indication prediction model (DualEncoderCrossAttention)..."
	python ./prototype/scripts/etl/train_indication_model.py $(PROCESSED_DIR) $(MODELS_DIR)/kg_embeddings.pkl $(MODELS_DIR)/indication_model.pt

# =============================================================================
# FULL SETUP
# =============================================================================
setup: data-download data-process kg-build kg-embeddings molecular-feats faers-signals admet-predict literature-index model-train docker-build
	@echo "✅ Setup complete! Run 'make run' to start the platform."

# =============================================================================
# DOCKER
# =============================================================================
docker-build:
	@echo "🐳 Building Docker images..."
	docker compose -f docker-compose.yml build

docker-up:
	@echo "🐳 Starting services..."
	docker compose -f docker-compose.yml up -d

docker-down:
	@echo "🐳 Stopping services..."
	docker compose -f docker-compose.yml down

run: docker-up
	@echo "🚀 Services started!"
	@echo "   Backend:  http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   API Docs: http://localhost:8000/docs"

# =============================================================================
# DEMO
# =============================================================================
demo: demo-kg demo-candidates demo-explain demo-safety demo-validation demo-dossier

demo-kg:
	@echo "🎬 Demo: KG Disease Browser (Niemann-Pick Type C)"
	@echo "   Query: ORPHA:635"
	@echo "   Expected: Disease detail with genes, pathways, unmet need score"

demo-candidates:
	@echo "🎬 Demo: Candidate Generation"
	@echo "   Input: ORPHA:635"
	@echo "   Expected: Top 20 drugs with probabilities + CIs"

demo-explain:
	@echo "🎬 Demo: Explanation (Miglustat for NPC)"
	@echo "   Expected: KG paths, SHAP, counterfactual, LLM rationale"

demo-safety:
	@echo "🎬 Demo: Safety Dashboard"
	@echo "   Expected: FAERS signals + ADMET + contraindications"

demo-validation:
	@echo "🎬 Demo: Validation UI"
	@echo "   Expected: Simulated clinician + self-assessment + audit log"

demo-dossier:
	@echo "🎬 Demo: Dossier Generator"
	@echo "   Expected: Orphan Designation draft PDF + JSON"

# =============================================================================
# TESTING
# =============================================================================
test:
	@echo "🧪 Running tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --cov=app --cov-fail-under=80

test-unit:
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -m "not integration" -v

test-integration:
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -m "integration" -v

test-e2e:
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v

# =============================================================================
# LINTING
# =============================================================================
lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Linting backend..."
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check app/ && $(PYTHON) -m mypy --explicit-package-bases app/

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd $(FRONTEND_DIR) && npm run lint

# =============================================================================
# CLEAN
# =============================================================================
clean:
	@echo "🧹 Cleaning..."
	docker compose -f docker-compose.yml down -v 2>/dev/null || true
	rm -rf $(PROCESSED_DIR)
	rm -rf $(DATA_DIR)/kuzu_db
	rm -rf $(DATA_DIR)/chroma_db
	rm -rf $(DATA_DIR)/molecular
	rm -rf $(DATA_DIR)/safety
	rm -rf $(MODELS_DIR)
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf $(BACKEND_DIR)/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete"

# =============================================================================
# DEVELOPMENT HELPERS
# =============================================================================
dev-backend:
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

install-backend:
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -e ".[dev]"

install-frontend:
	cd $(FRONTEND_DIR) && npm install

install: install-backend install-frontend

# =============================================================================
# ADDITIONAL INSTALLATION TARGETS
# =============================================================================
install-shap:
	@echo "📦 Installing SHAP for model explainability..."
	pip install shap

install-tdc:
	@echo "📦 Installing TDC (Therapeutics Data Commons)..."
	@echo "  Note: TDC requires GPU for deep learning models."
	@echo "  For CPU-only usage, TDC data loading still works but model training will be slow."
	pip install tdc

# =============================================================================
# VERIFY
# =============================================================================
verify: test verify-endpoints
	@echo "✅ Verification complete!"

verify-endpoints:
	@echo "🔍 Checking all API endpoints..."
	@echo ""
	@echo "Checking backend health..."
	@curl -s -o /dev/null -w "  GET /health: %{http_code}\n" http://localhost:8000/health || echo "  ⚠️  Backend not running. Start with: make run"
	@echo ""
	@echo "Checking API endpoints..."
	@curl -s -o /dev/null -w "  GET /api/v1/diseases: %{http_code}\n" http://localhost:8000/api/v1/diseases || true
	@curl -s -o /dev/null -w "  GET /api/v1/diseases/ORPHA:635: %{http_code}\n" http://localhost:8000/api/v1/diseases/ORPHA:635 || true
	@curl -s -o /dev/null -w "  GET /api/v1/candidates?disease_id=ORPHA:635: %{http_code}\n" "http://localhost:8000/api/v1/candidates?disease_id=ORPHA:635" || true
	@curl -s -o /dev/null -w "  GET /api/v1/kg/disease/ORPHA:635: %{http_code}\n" http://localhost:8000/api/v1/kg/disease/ORPHA:635 || true
	@curl -s -o /dev/null -w "  GET /api/v1/literature?disease_id=ORPHA:635: %{http_code}\n" "http://localhost:8000/api/v1/literature?disease_id=ORPHA:635" || true
	@curl -s -o /dev/null -w "  GET /api/v1/validation: %{http_code}\n" http://localhost:8000/api/v1/validation || true
	@curl -s -o /dev/null -w "  GET /api/v1/audit: %{http_code}\n" http://localhost:8000/api/v1/audit || true
	@echo ""
	@echo "Checking frontend..."
	@curl -s -o /dev/null -w "  GET /: %{http_code}\n" http://localhost:3000/ || echo "  ⚠️  Frontend not running. Start with: make run"
	@echo ""
	@echo "Checking data files..."
	@test -f $(PROCESSED_DIR)/drugcentral/drugcentral_fda_approved.parquet && echo "  ✓ DrugCentral data present" || echo "  ⚠️  DrugCentral data missing. Run: make data-process"
	@test -f $(PROCESSED_DIR)/orpha/orpha_diseases.parquet && echo "  ✓ Orphanet data present" || echo "  ⚠️  Orphanet data missing. Run: make data-process"
	@test -f $(DATA_DIR)/kuzu_db/.kuzu && echo "  ✓ Knowledge Graph present" || echo "  ⚠️  Knowledge Graph missing. Run: make kg-build"
	@test -f $(MODELS_DIR)/kg_embeddings.pkl && echo "  ✓ KG embeddings present" || echo "  ⚠️  KG embeddings missing. Run: make kg-embeddings"
	@test -f $(MODELS_DIR)/indication_model.pt && echo "  ✓ Indication model present" || echo "  ⚠️  Indication model missing. Run: make model-train"
	@echo ""
	@echo "Checking safety data..."
	@test -f $(DATA_DIR)/safety/faers_signals/faers_signals.parquet && echo "  ✓ FAERS signals present" || echo "  ⚠️  FAERS signals missing. Run: make faers-signals"
	@test -f $(DATA_DIR)/safety/admet/admet_predictions.parquet && echo "  ✓ ADMET predictions present" || echo "  ⚠️  ADMET predictions missing. Run: make admet-predict"
	@echo ""
	@echo "Checking literature index..."
	@test -d $(DATA_DIR)/chroma_db && echo "  ✓ ChromaDB index present" || echo "  ⚠️  ChromaDB index missing. Run: make literature-index"
	@echo ""
	@echo "Verification complete!"

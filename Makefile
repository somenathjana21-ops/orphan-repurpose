# OrphanRepurpose Makefile
# Usage: make <target>
# Key targets: setup, run, demo, test, lint, clean

.PHONY: help setup data-download data-process kg-build molecular-feats faers-signals admet-predict literature-index model-train run demo test lint clean

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
	@echo ""
	@echo "Individual pipeline steps:"
	@echo "  make data-download   - Download all raw datasets"
	@echo "  make data-process    - Process raw data to Parquet"
	@echo "  make kg-build        - Build Kuzu KG + train RGCN embeddings"
	@echo "  make molecular-feats - Compute molecular fingerprints"
	@echo "  make faers-signals   - Compute FAERS disproportionality"
	@echo "  make admet-predict   - Run TDC ADMET models"
	@echo "  make literature-index - Index PubMed abstracts in ChromaDB"
	@echo "  make model-train     - Train indication prediction model"

# Configuration
DATA_DIR := ./prototype/data
RAW_DIR := $(DATA_DIR)/raw
PROCESSED_DIR := $(DATA_DIR)/processed
MODELS_DIR := ./prototype/models
BACKEND_DIR := ./prototype/backend
FRONTEND_DIR := ./prototype/frontend

# =============================================================================
# DATA DOWNLOAD
# =============================================================================
data-download: download-orpha download-drugcentral download-tdc download-faers download-chembl download-reactome download-pubmed download-uniprot

download-orpha:
	@echo "📥 Downloading Orphanet data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_orpha.py $(DATA_DIR)

download-drugcentral:
	@echo "📥 Downloading DrugCentral data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_drugcentral.py $(DATA_DIR)

download-tdc:
	@echo "📥 Downloading TDC data..."
	cd $(BACKEND_DIR) && python ../scripts/download/download_tdc.py $(DATA_DIR)

download-faers:
	@echo "📥 Downloading FAERS data (placeholder)..."
	@mkdir -p $(RAW_DIR)/faers
	@touch $(RAW_DIR)/faers/faers_2024q1.json.zip
	@touch $(RAW_DIR)/faers/faers_2024q2.json.zip
	@touch $(RAW_DIR)/faers/faers_2024q3.json.zip
	@touch $(RAW_DIR)/faers/faers_2024q4.json.zip
	@touch $(RAW_DIR)/faers/faers_2025q1.json.zip
	@touch $(RAW_DIR)/faers/faers_2025q2.json.zip

download-chembl:
	@echo "📥 Downloading ChEMBL data (placeholder)..."
	@mkdir -p $(RAW_DIR)/chembl
	@touch $(RAW_DIR)/chembl/chembl_33.sql.gz

download-reactome:
	@echo "📥 Downloading Reactome data (placeholder)..."
	@mkdir -p $(RAW_DIR)/reactome
	@touch $(RAW_DIR)/reactome/reactome_pathways.txt

download-pubmed:
	@echo "📥 Downloading PubMed data (placeholder)..."
	@mkdir -p $(RAW_DIR)/pubmed
	@touch $(RAW_DIR)/pubmed/pubmed_npc.jsonl

download-uniprot:
	@echo "📥 Downloading UniProt data (placeholder)..."
	@mkdir -p $(RAW_DIR)/uniprot
	@touch $(RAW_DIR)/uniprot/uniprot_reviewed.xml.gz

# =============================================================================
# DATA PROCESSING
# =============================================================================
data-process: process-orpha process-drugcentral process-tdc process-faers process-chembl process-reactome process-pubmed

process-orpha:
	@echo "⚙️  Processing Orphanet data..."
	@mkdir -p $(PROCESSED_DIR)/orpha
	# TODO: Implement Orphanet XML parsing

process-drugcentral:
	@echo "⚙️  Processing DrugCentral data..."
	@mkdir -p $(PROCESSED_DIR)/drugcentral
	# TODO: Implement DrugCentral TSV parsing

process-tdc:
	@echo "⚙️  Processing TDC data..."
	@mkdir -p $(PROCESSED_DIR)/tdc
	# TODO: Implement TDC dataset processing

process-faers:
	@echo "⚙️  Processing FAERS data..."
	@mkdir -p $(PROCESSED_DIR)/faers
	# TODO: Implement FAERS disproportionality calculation

process-chembl:
	@echo "⚙️  Processing ChEMBL data..."
	@mkdir -p $(PROCESSED_DIR)/chembl
	# TODO: Implement ChEMBL processing

process-reactome:
	@echo "⚙️  Processing Reactome data..."
	@mkdir -p $(PROCESSED_DIR)/reactome
	# TODO: Implement Reactome processing

process-pubmed:
	@echo "⚙️  Processing PubMed data..."
	@mkdir -p $(PROCESSED_DIR)/pubmed
	# TODO: Implement PubMed processing

# =============================================================================
# KG BUILD
# =============================================================================
kg-build:
	@echo "🏗️  Building Knowledge Graph..."
	@mkdir -p $(DATA_DIR)/kuzu_db
	@mkdir -p $(MODELS_DIR)
	# TODO: Implement KG construction from processed data
	# TODO: Train RGCN embeddings
	@echo "KG build complete (placeholder)"

# =============================================================================
# MOLECULAR FEATURES
# =============================================================================
molecular-feats:
	@echo "🧬 Computing molecular fingerprints..."
	@mkdir -p $(DATA_DIR)/molecular
	# TODO: Compute Morgan fingerprints for 1,608 DrugCentral drugs
	@echo "Molecular features complete (placeholder)"

# =============================================================================
# FAERS SIGNALS
# =============================================================================
faers-signals:
	@echo "⚠️  Computing FAERS disproportionality signals..."
	@mkdir -p $(DATA_DIR)/safety/faers_signals
	# TODO: Compute ROR, PRR, BCPNN
	@echo "FAERS signals complete (placeholder)"

# =============================================================================
# ADMET PREDICTIONS
# =============================================================================
admet-predict:
	@echo "🧪 Running TDC ADMET predictions..."
	@mkdir -p $(DATA_DIR)/safety/admet
	# TODO: Run TDC models on 1,608 drugs
	@echo "ADMET predictions complete (placeholder)"

# =============================================================================
# LITERATURE INDEX
# =============================================================================
literature-index:
	@echo "📚 Indexing literature in ChromaDB..."
	@mkdir -p $(DATA_DIR)/chroma_db
	# TODO: Embed PubMed abstracts
	@echo "Literature index complete (placeholder)"

# =============================================================================
# MODEL TRAINING
# =============================================================================
model-train: train-kg-embeddings train-indication-model

train-kg-embeddings:
	@echo "🧠 Training KG embeddings (RGCN)..."
	# TODO: Train RGCN on KG
	@echo "KG embeddings training complete (placeholder)"

train-indication-model:
	@echo "🧠 Training indication prediction model..."
	# TODO: Train dual-encoder cross-attention model
	@echo "Indication model training complete (placeholder)"

# =============================================================================
# FULL SETUP
# =============================================================================
setup: data-download data-process kg-build molecular-feats faers-signals admet-predict literature-index model-train docker-build
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
	cd $(BACKEND_DIR) && python -m pytest tests/ -v --cov=app --cov=ml --cov-fail-under=80

test-unit:
	cd $(BACKEND_DIR) && python -m pytest tests/unit -v

test-integration:
	cd $(BACKEND_DIR) && python -m pytest tests/integration -v

test-e2e:
	cd $(BACKEND_DIR) && python -m pytest tests/e2e -v

# =============================================================================
# LINTING
# =============================================================================
lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Linting backend..."
	cd $(BACKEND_DIR) && ruff check . && mypy app/

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
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

install-backend:
	cd $(BACKEND_DIR) && pip install -e ".[dev]"

install-frontend:
	cd $(FRONTEND_DIR) && npm install

install: install-backend install-frontend
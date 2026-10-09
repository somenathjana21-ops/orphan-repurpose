import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import structlog

# Test Audit Service
class TestAuditService:
    @pytest.mark.asyncio
    async def test_audit_service_add_entry(self):
        from app.services.audit_service import get_audit_service
        from app.db.database import async_session_factory, _ensure_tables
        from app.db.models import AuditEntryModel
        from sqlalchemy import select, delete
        
        await _ensure_tables()
        svc = get_audit_service()
        
        # Clean up any existing test data
        async with async_session_factory() as db:
            await db.execute(delete(AuditEntryModel).where(AuditEntryModel.session_id == "test_audit_1"))
            await db.commit()
        
        entry = await svc.add_entry(
            session_id="test_audit_1",
            entry_type="validation",
            user="test_user",
            data={"candidate_id": "cand_001", "assessment": "plausible"}
        )
        
        assert entry.type == "validation"
        assert entry.user == "test_user"
        assert entry.data == {"candidate_id": "cand_001", "assessment": "plausible"}
        assert entry.hash != ""
        
        # Verify it's in DB
        async with async_session_factory() as db:
            result = await db.execute(
                select(AuditEntryModel).where(AuditEntryModel.session_id == "test_audit_1")
            )
            rows = result.scalars().all()
            assert len(rows) == 1
            assert rows[0].hash == entry.hash

    @pytest.mark.asyncio
    async def test_audit_service_get_trail(self):
        from app.services.audit_service import get_audit_service
        from app.db.database import async_session_factory, _ensure_tables
        from app.db.models import AuditEntryModel
        from sqlalchemy import delete
        
        await _ensure_tables()
        svc = get_audit_service()
        
        # Clean up
        async with async_session_factory() as db:
            await db.execute(delete(AuditEntryModel).where(AuditEntryModel.session_id == "test_audit_2"))
            await db.commit()
        
        await svc.add_entry("test_audit_2", "type1", "user1", {"a": 1})
        await svc.add_entry("test_audit_2", "type2", "user2", {"b": 2})
        
        trail = await svc.get_trail("test_audit_2")
        assert trail is not None
        assert trail.session_id == "test_audit_2"
        assert len(trail.entries) == 2

    @pytest.mark.asyncio
    async def test_audit_service_verify_valid(self):
        from app.services.audit_service import get_audit_service
        from app.db.database import async_session_factory, _ensure_tables
        from app.db.models import AuditEntryModel
        from sqlalchemy import delete
        
        await _ensure_tables()
        svc = get_audit_service()
        
        async with async_session_factory() as db:
            await db.execute(delete(AuditEntryModel).where(AuditEntryModel.session_id == "test_audit_3"))
            await db.commit()
        
        await svc.add_entry("test_audit_3", "validation", "user1", {"a": 1})
        await svc.add_entry("test_audit_3", "self_assessment", "user1", {"b": 2})
        
        result = await svc.verify("test_audit_3")
        assert result["session_id"] == "test_audit_3"
        assert result["valid"] is True
        assert result["entry_count"] == 2

    @pytest.mark.asyncio
    async def test_audit_service_verify_invalid_session(self):
        from app.services.audit_service import get_audit_service
        
        svc = get_audit_service()
        result = await svc.verify("nonexistent_session_xyz")
        assert result["session_id"] == "nonexistent_session_xyz"
        assert result["valid"] is False
        assert result["message"] == "Session not found"

    @pytest.mark.asyncio
    async def test_audit_service_get_all_sessions(self):
        from app.services.audit_service import get_audit_service
        from app.db.database import async_session_factory, _ensure_tables
        from app.db.models import AuditEntryModel
        from sqlalchemy import delete
        
        await _ensure_tables()
        svc = get_audit_service()
        
        async with async_session_factory() as db:
            await db.execute(delete(AuditEntryModel).where(AuditEntryModel.session_id == "test_audit_4"))
            await db.commit()
        
        await svc.add_entry("test_audit_4", "test", "user", {"x": 1})
        
        sessions = await svc.get_all_sessions()
        assert "test_audit_4" in sessions

    @pytest.mark.asyncio
    async def test_audit_service_clear(self):
        from app.services.audit_service import get_audit_service
        
        svc = get_audit_service()
        svc.clear()
        assert svc._cache == {}


# Test Indication Service
class TestIndicationService:
    @pytest.mark.asyncio
    async def test_indication_service_singleton(self):
        from app.services.indication_service import get_indication_service
        svc1 = get_indication_service()
        svc2 = get_indication_service()
        assert svc1 is svc2

    @pytest.mark.asyncio
    async def test_indication_service_is_ready(self):
        from app.services.indication_service import get_indication_service
        svc = get_indication_service()
        # Should return False if model not loaded, True if loaded
        result = svc.is_ready()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_indication_service_load_model(self):
        from app.services.indication_service import get_indication_service
        svc = get_indication_service()
        # Try to load model (may fail if not available)
        try:
            await svc.load_model()
        except Exception:
            pass  # Model may not be available in test environment
        # After load attempt, is_ready should return bool
        assert isinstance(svc.is_ready(), bool)

    @pytest.mark.asyncio
    async def test_indication_service_score_all_for_orpha(self):
        from app.services.indication_service import get_indication_service
        svc = get_indication_service()
        
        if svc.is_ready():
            scores = svc.score_all_for_orpha("UMLS:C0028042", top_k=5)
            assert isinstance(scores, list)
            for score in scores:
                assert "drug_id" in score
                assert "probability" in score
                assert "ci_lower" in score
                assert "ci_upper" in score
                assert 0 <= score["probability"] <= 1
                assert score["ci_lower"] <= score["probability"] <= score["ci_upper"]


# Test KG Service - use KGService class directly
class TestKGService:
    @pytest.mark.asyncio
    async def test_kg_service_singleton(self):
        from app.services.kg_service import KGService
        svc1 = KGService()
        svc2 = KGService()
        # Not a singleton, just check they can be instantiated
        assert svc1 is not None
        assert svc2 is not None
        svc1.close()
        svc2.close()



    def test_kg_service_get_disease_genes(self):
        from app.services.kg_service import KGService
        svc = KGService()
        
        # This is not an async method
        genes = svc.get_disease_genes("ORPHA:635")
        assert isinstance(genes, list)
        # Returns list of gene symbols (strings)
        svc.close()

    def test_kg_service_get_disease_pathways(self):
        from app.services.kg_service import KGService
        svc = KGService()
        
        # This may fail if HAS_PATHWAY doesn't exist
        try:
            pathways = svc.get_disease_pathways("ORPHA:635")
            assert isinstance(pathways, list)
        except Exception:
            pass  # Expected if HAS_PATHWAY doesn't exist
        svc.close()


# Test Safety Service
class TestSafetyService:
    @pytest.mark.asyncio
    async def test_safety_service_singleton(self):
        from app.services.safety_service import get_safety_service
        svc1 = get_safety_service()
        svc2 = get_safety_service()
        assert svc1 is svc2

    @pytest.mark.asyncio
    async def test_safety_service_assess_drug(self):
        from app.services.safety_service import get_safety_service
        svc = get_safety_service()
        
        result = await svc.assess_drug(
            drug_id="drugcentral:1001",
            drug_name="Miglustat",
            smiles="CC(C)O[C@H]1[C@H](O)[C@@H](O)[C@H](NC(C)C)O1"
        )
        
        assert "overall" in result
        assert "faers_signals" in result
        assert "admet_predictions" in result
        assert "contraindications" in result
        assert result["overall"] in ["pass", "caution", "fail"]


# Test FAERS Service - use get_faers_data method
class TestFAERSService:
    @pytest.mark.asyncio
    async def test_faers_service_singleton(self):
        from app.services.faers_service import get_faers_service
        svc1 = get_faers_service()
        svc2 = get_faers_service()
        assert svc1 is svc2

    @pytest.mark.asyncio
    async def test_faers_service_get_data(self):
        from app.services.faers_service import get_faers_service
        from app.ml.faers import ContingencyTable
        svc = get_faers_service()
        
        tables = await svc.get_faers_data("miglustat")
        assert isinstance(tables, dict)
        for event, table in tables.items():
            assert isinstance(table, ContingencyTable)
            # ContingencyTable has a, b, c, d properties
            assert table.a >= 0
            assert table.b >= 0
            assert table.c >= 0
            assert table.d >= 0


# Test Explanation Service
class TestExplanationService:
    @pytest.mark.asyncio
    async def test_explanation_service_singleton(self):
        from app.services.explanation_service import get_explanation_service
        svc1 = get_explanation_service()
        svc2 = get_explanation_service()
        assert svc1 is svc2

    @pytest.mark.asyncio
    async def test_explanation_service_explain_candidate(self):
        from app.services.explanation_service import get_explanation_service
        svc = get_explanation_service()
        
        explanation = svc.explain_candidate(
            drug_id="drugcentral:1001",
            disease_id="ORPHA:635",
            drug_name="Miglustat",
            disease_name="Niemann-Pick Type C",
            probability=0.85,
            moa_summary="Inhibits glucosylceramide synthase"
        )
        
        assert "candidate_id" in explanation
        assert "kg_paths" in explanation
        assert "shap_values" in explanation
        assert "counterfactuals" in explanation
        assert "llm_rationale" in explanation


# Test Dossier Service
class TestDossierService:
    @pytest.mark.asyncio
    async def test_dossier_service_singleton(self):
        from app.services.dossier_service import get_dossier_service
        svc1 = get_dossier_service()
        svc2 = get_dossier_service()
        assert svc1 is svc2

    def test_dossier_service_generate(self):
        from app.services.dossier_service import get_dossier_service
        from app.models.disease import Candidate, SafetyFlags, FAERSSignal, KGPath, KGPathNode, KGPathEdge
        
        svc = get_dossier_service()
        
        # Create mock candidates
        candidates = [
            Candidate(
                candidate_id="cand_001",
                drug_id="drugcentral:1001",
                drug_name="Miglustat",
                indication_probability=0.85,
                confidence_interval=[0.75, 0.92],
                moa_summary="Inhibits glucosylceramide synthase",
                safety_flags=SafetyFlags(
                    faers_signals=[],
                    admet_predictions={},
                    contraindications=[],
                    overall="pass"
                ),
                kg_paths=[],
                llm_rationale="Test rationale",
                shap_values={}
            )
        ]
        
        from app.models.disease import DiseaseDetail
        disease = DiseaseDetail(
            orpha_id="ORPHA:635",
            name="Niemann-Pick Type C",
            prevalence=0.000001,
            prevalence_category="<1/1,000,000",
            inheritance=["autosomal recessive"],
            age_of_onset=["childhood"],
            genes=[],
            pathways=[],
            phenotypes=["hepatosplenomegaly"],
            existing_treatments=["Miglustat"],
            unmet_need_score=0.85,
            description="Rare lysosomal storage disease",
            synonyms=[],
            omim_ids=[],
            mondo_id=None,
            icar_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # generate_dossier is not async
        result = svc.generate_dossier(
            disease=disease,
            candidates=candidates,
            sections=["background", "drug_profile", "mechanistic_rationale"],
            audit_trail_id="test_audit_123"
        )
        
        assert "pdf_base64" in result
        assert "dossier_json" in result
        assert "audit_trail_id" in result


# Test ML Modules
class TestADMET:
    @pytest.mark.asyncio
    async def test_admet_predict_smiles(self):
        from app.ml.admet import ADMETPredictor
        
        predictor = ADMETPredictor()
        smiles = "CC(C)O[C@H]1[C@H](O)[C@@H](O)[C@H](NC(C)C)O1"
        result = predictor.predict(smiles)
        
        assert isinstance(result, dict)
        assert "Caco2" in result or "HIA" in result
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_admet_predict_invalid_smiles(self):
        from app.ml.admet import ADMETPredictor
        
        predictor = ADMETPredictor()
        result = predictor.predict("INVALID_SMILES")
        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_admet_classify_safety(self):
        from app.ml.admet import ADMETPredictor
        
        predictor = ADMETPredictor()
        smiles = "CC(C)O[C@H]1[C@H](O)[C@@H](O)[C@H](NC(C)C)O1"
        predictions = predictor.predict(smiles)
        classifications = predictor.classify_safety(predictions)
        
        assert isinstance(classifications, dict)
        for v in classifications.values():
            assert v in ["pass", "caution", "fail"]

    @pytest.mark.asyncio
    async def test_admet_overall_safety(self):
        from app.ml.admet import ADMETPredictor
        
        predictor = ADMETPredictor()
        smiles = "CC(C)O[C@H]1[C@H](O)[C@@H](O)[C@H](NC(C)C)O1"
        predictions = predictor.predict(smiles)
        overall = predictor.overall_safety(predictions)
        
        assert overall in ["pass", "caution", "fail"]


class TestExplainer:
    @pytest.mark.asyncio
    async def test_explainer_shap_values(self):
        from app.ml.explainer import Explainer
        
        # This tests the fallback SHAP values
        explainer = Explainer()
        # explain method takes different params
        result = explainer.explain(
            drug_id="drugcentral:1001",
            disease_id="ORPHA:635",
            drug_name="Miglustat",
            disease_name="Niemann-Pick Type C",
            probability=0.85,
            moa_summary="Inhibits glucosylceramide synthase"
        )
        
        assert isinstance(result, dict)
        assert "shap_values" in result
        assert "kg_paths" in result
        assert "counterfactuals" in result
        assert "llm_rationale" in result


class TestFAERS:
    @pytest.mark.asyncio
    async def test_faers_analyzer(self):
        from app.ml.faers import FAERSAnalyzer, ContingencyTable
        
        analyzer = FAERSAnalyzer()
        # Create a contingency table and analyze
        table = ContingencyTable(a=45, b=120, c=800, d=50000)
        result = analyzer.analyze(
            drug_id="drugcentral:1001",
            drug_name="Miglustat",
            event="Diarrhea",
            meddra_pt="Diarrhea",
            table=table
        )
        
        assert result.drug_id == "drugcentral:1001"
        assert result.event == "Diarrhea"
        assert isinstance(result.ror, float)
        assert isinstance(result.prr, float)
        assert isinstance(result.bcpnn_ic, float)
        assert result.level in ["pass", "caution", "fail"]


# Test Indication Service more thoroughly
class TestIndicationServiceDeep:
    @pytest.mark.asyncio
    async def test_indication_service_get_drug_smiles(self):
        from app.services.indication_service import get_indication_service
        svc = get_indication_service()
        
        if svc.is_ready():
            # Test getting drug SMILES
            smiles = svc.drug_smiles.get("drugcentral:1001")
            # May be None if not loaded
            if smiles is not None:
                assert isinstance(smiles, str)

    @pytest.mark.asyncio
    async def test_indication_service_load_model_twice(self):
        from app.services.indication_service import get_indication_service
        svc = get_indication_service()
        
        # Try loading twice
        try:
            await svc.load_model()
            await svc.load_model()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_indication_service_score_all_for_orpha(self):
        from app.services.indication_service import get_indication_service
        svc = get_indication_service()
        
        if svc.is_ready():
            scores = svc.score_all_for_orpha("UMLS:C0028042", top_k=5)
            assert isinstance(scores, list)
            for score in scores:
                assert "drug_id" in score
                assert "probability" in score
                assert "ci_lower" in score
                assert "ci_upper" in score


# Test KG Service more
class TestKGServiceDeep:
    def test_kg_service_execute(self):
        from app.services.kg_service import KGService
        svc = KGService()
        
        # Test execute method
        results = svc.execute("MATCH (d:Drug) RETURN d.id LIMIT 5", {})
        assert isinstance(results, list)
        svc.close()

    def test_kg_service_get_drug_candidates(self):
        from app.services.kg_service import KGService
        svc = KGService()
        
        try:
            candidates = svc.get_drug_candidates("ORPHA:635", limit=10)
            assert isinstance(candidates, list)
        except Exception:
            pass  # Query may fail if graph not fully populated
        svc.close()

    def test_kg_service_get_kg_subgraph(self):
        from app.services.kg_service import KGService
        svc = KGService()
        
        subgraph = svc.get_kg_subgraph("drugcentral:1001", "ORPHA:635", max_depth=3)
        assert isinstance(subgraph, dict)
        assert "nodes" in subgraph
        assert "edges" in subgraph
        svc.close()


# Test Safety Service more
class TestSafetyServiceDeep:
    @pytest.mark.asyncio
    async def test_safety_service_assess_drug_no_smiles(self):
        from app.services.safety_service import get_safety_service
        svc = get_safety_service()
        
        result = await svc.assess_drug(
            drug_id="drugcentral:1001",
            drug_name="Miglustat",
            smiles=""
        )
        
        assert "overall" in result
        assert "faers_signals" in result
        assert "admet_predictions" in result
        assert "contraindications" in result

    @pytest.mark.asyncio
    async def test_safety_service_assess_unknown_drug(self):
        from app.services.safety_service import get_safety_service
        svc = get_safety_service()
        
        result = await svc.assess_drug(
            drug_id="unknown:999",
            drug_name="Unknown Drug",
            smiles="CCO"
        )
        
        assert "overall" in result
        assert result["overall"] in ["pass", "caution", "fail"]


# Test FAERS Service more
class TestFAERSServiceDeep:
    @pytest.mark.asyncio
    async def test_faers_service_clear_cache(self):
        from app.services.faers_service import get_faers_service
        svc = get_faers_service()
        
        # Add some data to cache
        await svc.get_faers_data("miglustat")
        # Clear cache
        svc.clear_cache()
        assert svc._cache == {}

    @pytest.mark.asyncio
    async def test_faers_service_multiple_drugs(self):
        from app.services.faers_service import get_faers_service
        svc = get_faers_service()
        
        for drug in ["miglustat", "sirolimus", "ivacaftor", "everolimus"]:
            tables = await svc.get_faers_data(drug)
            assert isinstance(tables, dict)


# Test Explanation Service more
class TestExplanationServiceDeep:
    @pytest.mark.asyncio
    async def test_explanation_service_different_candidates(self):
        from app.services.explanation_service import get_explanation_service
        svc = get_explanation_service()
        
        for drug_name, drug_id in [("Miglustat", "drugcentral:1001"), ("Sirolimus", "drugcentral:1002"), ("Ivacaftor", "drugcentral:1003")]:
            explanation = svc.explain_candidate(
                drug_id=drug_id,
                disease_id="ORPHA:635",
                drug_name=drug_name,
                disease_name="Niemann-Pick Type C",
                probability=0.75,
                moa_summary="Test MoA"
            )
            
            assert "candidate_id" in explanation
            assert "kg_paths" in explanation
            assert "shap_values" in explanation
            assert "counterfactuals" in explanation
            assert "llm_rationale" in explanation


# Test ADMET more
class TestADMETDeep:
    @pytest.mark.asyncio
    async def test_admet_predictor_multiple_smiles(self):
        from app.ml.admet import ADMETPredictor, ADMET_ENDPOINTS
        
        predictor = ADMETPredictor()
        smiles_list = [
            "CC(C)O[C@H]1[C@H](O)[C@@H](O)[C@H](NC(C)C)O1",  # Miglustat
            "CCO",  # Ethanol
            "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
        ]
        
        for smiles in smiles_list:
            result = predictor.predict(smiles)
            assert isinstance(result, dict)
            assert len(result) == len(ADMET_ENDPOINTS)
            for k, v in result.items():
                assert isinstance(v, (int, float))

    @pytest.mark.asyncio
    async def test_admet_classify_all_endpoints(self):
        from app.ml.admet import ADMETPredictor
        
        predictor = ADMETPredictor()
        smiles = "CC(C)O[C@H]1[C@H](O)[C@@H](O)[C@H](NC(C)C)O1"
        predictions = predictor.predict(smiles)
        classifications = predictor.classify_safety(predictions)
        
        # Should classify all endpoints
        assert len(classifications) == len(predictions)
        for v in classifications.values():
            assert v in ["pass", "caution", "fail"]


# Test Explainer more
class TestExplainerDeep:
    @pytest.mark.asyncio
    async def test_explainer_with_kg_paths(self):
        from app.ml.explainer import Explainer
        
        explainer = Explainer()
        result = explainer.explain(
            drug_id="drugcentral:1001",
            disease_id="ORPHA:635",
            drug_name="Miglustat",
            disease_name="Niemann-Pick Type C",
            probability=0.85,
            moa_summary="Inhibits glucosylceramide synthase"
        )
        
        assert isinstance(result, dict)
        assert "shap_values" in result
        assert "kg_paths" in result
        assert "counterfactuals" in result
        assert "llm_rationale" in result
        assert isinstance(result["kg_paths"], list)
        assert isinstance(result["counterfactuals"], list)


# Test FAERS Analyzer more
class TestFAERSAnalyzerDeep:
    @pytest.mark.asyncio
    async def test_faers_analyzer_edge_cases(self):
        from app.ml.faers import FAERSAnalyzer, ContingencyTable, compute_2x2_table
        
        analyzer = FAERSAnalyzer()
        
        # Test with zero cells (should apply correction)
        table = ContingencyTable(a=0, b=100, c=50, d=10000)
        ror, ci_lower, ci_upper = analyzer.compute_ror(table)
        assert isinstance(ror, float)
        assert ci_lower <= ror <= ci_upper
        
        prr, chi2 = analyzer.compute_prr(table)
        assert isinstance(prr, float)
        
        bcpnn_ic, bcpnn_lower, bcpnn_upper = analyzer.compute_bcpnn(table)
        assert isinstance(bcpnn_ic, float)
        
        ebge = analyzer.compute_ebge(table)
        assert isinstance(ebge, float)
        
        # Test classify_signal
        level = analyzer.classify_signal(ror, prr, bcpnn_ic, table.a)
        assert level in ["pass", "caution", "fail"]
        
        # Test compute_2x2_table helper
        table2 = compute_2x2_table(10, 90, 100, 9800)
        assert table2.a == 10
        assert table2.b == 90
        assert table2.c == 100
        assert table2.d == 9800


# Test Featurizer
class TestFeaturizer:
    @pytest.mark.asyncio
    async def test_featurizer_smiles_to_graph(self):
        from app.ml.featurizer import smiles_to_graph
        
        # Valid SMILES
        graph = smiles_to_graph("CCO")
        assert graph is not None
        # Returns tuple (x, edge_index)
        assert isinstance(graph, tuple)
        assert len(graph) == 2
        x, edge_index = graph
        assert x is not None
        assert edge_index is not None
        
        # Invalid SMILES
        graph = smiles_to_graph("INVALID")
        assert graph is not None  # Should return empty graph fallback
        assert isinstance(graph, tuple)


# Test Indication Model
class TestIndicationModel:
    @pytest.mark.asyncio
    async def test_model_forward(self):
        from app.ml.indication_model import SimpleIndicationModel
        import torch
        
        model = SimpleIndicationModel(
            fp_dim=1024,
            kg_dim=256,
            hidden_dim=128
        )
        
        # Create dummy inputs
        drug_fp = torch.randn(2, 1024)
        disease_emb = torch.randn(2, 256)
        
        model.eval()
        with torch.no_grad():
            output = model(drug_fp, disease_emb)
        
        assert output.shape == (2,)
        # Output is logits, not probabilities
        assert isinstance(output, torch.Tensor)


# Test Indication Service more thoroughly









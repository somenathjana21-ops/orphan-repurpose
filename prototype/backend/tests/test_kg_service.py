import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.kg_service import KGService
from app.models.disease import DiseaseDetail, DiseaseSearchResult


class TestKGService:
    @pytest.fixture
    def mock_kg_service(self):
        with patch('app.services.kg_service.kuzu') as mock_kuzu:
            mock_db = Mock()
            mock_conn = Mock()
            mock_kuzu.Database.return_value = mock_db
            mock_kuzu.Connection.return_value = mock_conn
            
            service = KGService()
            service.db = mock_db
            service.conn = mock_conn
            yield service
    
    def test_search_diseases_no_filters(self, mock_kg_service):
        mock_kg_service.execute.return_value = [
            {"total": 1}
        ]
        mock_kg_service.execute.return_value = [
            {
                "d": {
                    "orpha_id": "ORPHA:635",
                    "name": "Niemann-Pick disease type C",
                    "prevalence": 0.09,
                    "prevalence_category": "<1/1,000,000",
                    "inheritance": ["Autosomal recessive"],
                    "age_of_onset": ["Infancy"],
                    "genes": [{"hgnc_id": "HGNC:7852", "symbol": "NPC1", "name": "NPC1"}],
                    "pathways": [{"reactome_id": "R-HSA-123", "name": "Cholesterol metabolism"}],
                    "phenotypes": ["Hepatosplenomegaly"],
                    "existing_treatments": ["Miglustat"],
                    "unmet_need_score": 0.92,
                }
            }
        ]
        
        diseases, total = mock_kg_service.search_diseases()
        
        assert total == 1
        assert len(diseases) == 1
        assert diseases[0].orpha_id == "ORPHA:635"
        assert diseases[0].name == "Niemann-Pick disease type C"
    
    def test_get_disease_found(self, mock_kg_service):
        mock_kg_service.execute.return_value = [{
            "d": {
                "orpha_id": "ORPHA:635",
                "name": "Niemann-Pick disease type C",
                "prevalence": 0.09,
                "prevalence_category": "<1/1,000,000",
                "inheritance": ["Autosomal recessive"],
                "age_of_onset": ["Infancy"],
                "phenotypes": ["Hepatosplenomegaly"],
                "existing_treatments": ["Miglustat"],
                "unmet_need_score": 0.92,
                "description": "A rare genetic disorder...",
                "synonyms": ["NPC"],
                "omim_ids": ["257220"],
                "mondo_id": "MONDO:0009593",
                "icar_id": "ICAR:0000001",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            "genes": [{"hgnc_id": "HGNC:7852", "symbol": "NPC1", "name": "NPC1"}],
            "pathways": [{"reactome_id": "R-HSA-123", "name": "Cholesterol metabolism"}],
        }]
        
        disease = mock_kg_service.get_disease("ORPHA:635")
        
        assert disease is not None
        assert disease.orpha_id == "ORPHA:635"
        assert disease.description == "A rare genetic disorder..."
    
    def test_get_disease_not_found(self, mock_kg_service):
        mock_kg_service.execute.return_value = []
        
        disease = mock_kg_service.get_disease("ORPHA:999999")
        
        assert disease is None
    
    def test_get_disease_genes(self, mock_kg_service):
        mock_kg_service.execute.return_value = [
            {"symbol": "NPC1"},
            {"symbol": "NPC2"},
        ]
        
        genes = mock_kg_service.get_disease_genes("ORPHA:635")
        
        assert genes == ["NPC1", "NPC2"]
    
    def test_get_disease_pathways(self, mock_kg_service):
        mock_kg_service.execute.return_value = [
            {"name": "Cholesterol metabolism"},
            {"name": "Lysosomal transport"},
        ]
        
        pathways = mock_kg_service.get_disease_pathways("ORPHA:635")
        
        assert pathways == ["Cholesterol metabolism", "Lysosomal transport"]


class TestKGServiceIntegration:
    """Integration tests that would run against a real Kuzu instance."""
    
    @pytest.mark.integration
    def test_real_kuzu_connection(self):
        """Test that would run against actual Kuzu DB."""
        pass  # Implement when Kuzu is set up
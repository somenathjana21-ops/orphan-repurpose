import pytest
from app.models.disease import DiseaseSearchResult, DiseaseDetail, Gene, Pathway


class TestDiseaseModels:
    def test_gene_model(self):
        gene = Gene(hgnc_id="HGNC:7852", symbol="NPC1", name="NPC intracellular cholesterol transporter 1")
        assert gene.symbol == "NPC1"
        assert gene.hgnc_id == "HGNC:7852"
    
    def test_pathway_model(self):
        pathway = Pathway(reactome_id="R-HSA-12345", name="Cholesterol metabolism", species="Homo sapiens")
        assert pathway.name == "Cholesterol metabolism"
        assert pathway.species == "Homo sapiens"
    
    def test_disease_search_result(self):
        disease = DiseaseSearchResult(
            orpha_id="ORPHA:635",
            name="Niemann-Pick disease type C",
            prevalence=0.09,
            prevalence_category="<1/1,000,000",
            genes=[Gene(hgnc_id="HGNC:7852", symbol="NPC1", name="NPC1")],
            pathways=[Pathway(reactome_id="R-HSA-12345", name="Cholesterol metabolism")],
            phenotypes=["Hepatosplenomegaly", "Neurological deterioration"],
            existing_treatments=["Miglustat (EU)"],
            unmet_need_score=0.92,
        )
        assert disease.orpha_id == "ORPHA:635"
        assert len(disease.genes) == 1
        assert disease.unmet_need_score == 0.92
    
    def test_disease_detail_extends_search_result(self):
        detail = DiseaseDetail(
            orpha_id="ORPHA:635",
            name="Niemann-Pick disease type C",
            description="A rare genetic disorder...",
            synonyms=["NPC", "Niemann-Pick type C"],
            omim_ids=["257220", "607625"],
            mondo_id="MONDO:0009593",
            icar_id="ICAR:0000001",
            genes=[],
            pathways=[],
            phenotypes=[],
            existing_treatments=[],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert detail.description == "A rare genetic disorder..."
        assert "NPC" in detail.synonyms
        assert detail.mondo_id == "MONDO:0009593"
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import structlog
from app.models.disease import DiseaseSearchResult, DiseaseDetail, DiseaseSearchParams, DiseaseSearchResponse, Gene, Pathway

logger = structlog.get_logger()
router = APIRouter()

# Mock data for diseases
MOCK_DISEASES = [
    DiseaseSearchResult(
        orpha_id="ORPHA:635",
        name="Niemann-Pick disease type C",
        prevalence=0.5,
        prevalence_category="1/200,000 - 1/2,000",  # 1-5 per 100,000 = 1/20,000 to 5/100,000, which falls in 1/200,000 - 1/2,000 range
        inheritance=["Autosomal recessive"],
        age_of_onset=["Infantile", "Juvenile", "Adult"],
        genes=[
            Gene(hgnc_id="HGNC:7694", symbol="NPC1", name="NPC intracellular cholesterol transporter 1"),
            Gene(hgnc_id="HGNC:14133", symbol="NPC2", name="NPC intracellular cholesterol transporter 2")
        ],
        pathways=[
            Pathway(reactome_id="R-HSA-1430728", name="Cholesterol biosynthesis"),
            Pathway(reactome_id="R-HSA-1430729", name="Cholesterol transport")
        ],
        phenotypes=["Vertical supranuclear gaze palsy", "Ataxia", "Dysphagia"],
        existing_treatments=["Miglustat"],
        unmet_need_score=0.85
    ),
    DiseaseSearchResult(
        orpha_id="ORPHA:793",
        name="Cystic fibrosis",
        prevalence=3.5,
        prevalence_category="1/200,000 - 1/2,000",  # 3.5 per 100,000
        inheritance=["Autosomal recessive"],
        age_of_onset=["Neonatal", "Infantile", "Childhood"],
        genes=[
            Gene(hgnc_id="HGNC:2649", symbol="CFTR", name="Cystic fibrosis transmembrane conductance regulator")
        ],
        pathways=[
            Pathway(reactome_id="R-HSA-388794", name="CFTR-dependent regulation of electrolyte transport"),
            Pathway(reactome_id="R-HSA-388795", name="CFTR-dependent regulation of fluid transport")
        ],
        phenotypes=["Chronic cough", "Recurrent pulmonary infections", "Pancreatic insufficiency"],
        existing_treatments=["Ivacaftor", "Lumacaftor/ivacaftor"],
        unmet_need_score=0.6
    ),
    DiseaseSearchResult(
        orpha_id="ORPHA:98065",
        name="Huntington disease",
        prevalence=5.0,
        prevalence_category="1/200,000 - 1/2,000",  # 5 per 100,000
        inheritance=["Autosomal dominant"],
        age_of_onset=["Adult"],
        genes=[
            Gene(hgnc_id="HGNC:4848", symbol="HTT", name="Huntingtin")
        ],
        pathways=[
            Pathway(reactome_id="R-HSA-422475", name="Huntington disease protein interactions"),
            Pathway(reactome_id="R-HSA-422476", name="Neurotrophic factor-mediated signaling")
        ],
        phenotypes=["Chorea", "Cognitive decline", "Psychiatric disturbances"],
        existing_treatments=["Tetrabenazine", "Deutetrabenazine"],
        unmet_need_score=0.75
    )
]

def get_mock_disease_by_id(orpha_id: str) -> Optional[DiseaseSearchResult]:
    for disease in MOCK_DISEASES:
        if disease.orpha_id == orpha_id:
            return disease
    return None

@router.get("", response_model=DiseaseSearchResponse)
async def search_diseases(
    q: Optional[str] = Query(None, description="Search query (name, ORPHA code, gene, pathway)"),
    prevalence_max: Optional[float] = Query(None, description="Maximum prevalence (per 100,000)"),
    gene: Optional[str] = Query(None, description="Gene symbol filter"),
    pathway: Optional[str] = Query(None, description="Pathway name filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("unmet_need_score"),
    sort_order: str = Query("desc"),
):
    """Search and filter rare diseases from Orphanet."""
    try:
        # Filter mock data
        filtered = MOCK_DISEASES
        if q:
            q_lower = q.lower()
            filtered = [
                d for d in filtered
                if q_lower in d.name.lower() or q_lower in d.orpha_id.lower() or
                any(q_lower in g.symbol.lower() for g in d.genes) or
                any(q_lower in p.name.lower() for p in d.pathways)
            ]
        if prevalence_max is not None:
            filtered = [d for d in filtered if d.prevalence is None or d.prevalence <= prevalence_max]
        if gene:
            filtered = [d for d in filtered if any(g.symbol.upper() == gene.upper() for g in d.genes)]
        if pathway:
            filtered = [d for d in filtered if any(pathway.lower() in p.name.lower() for p in d.pathways)]
        
        # Sort
        reverse = sort_order == "desc"
        if sort_by == "name":
            filtered.sort(key=lambda d: d.name, reverse=reverse)
        elif sort_by == "orpha_id":
            filtered.sort(key=lambda d: d.orpha_id, reverse=reverse)
        elif sort_by == "prevalence":
            filtered.sort(key=lambda d: d.prevalence if d.prevalence is not None else 0, reverse=reverse)
        elif sort_by == "unmet_need_score":
            filtered.sort(key=lambda d: d.unmet_need_score if d.unmet_need_score is not None else 0, reverse=reverse)
        
        # Paginate
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]
        
        return DiseaseSearchResponse(
            data=paginated,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error("disease_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Disease search failed")

@router.get("/{orpha_id}", response_model=DiseaseDetail)
async def get_disease(orpha_id: str):
    """Get detailed disease information."""
    try:
        disease = get_mock_disease_by_id(orpha_id)
        if not disease:
            raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
        
        # Convert to DiseaseDetail (add extra fields)
        return DiseaseDetail(
            orpha_id=disease.orpha_id,
            name=disease.name,
            prevalence=disease.prevalence,
            prevalence_category=disease.prevalence_category,
            inheritance=disease.inheritance,
            age_of_onset=disease.age_of_onset,
            genes=disease.genes,
            pathways=disease.pathways,
            phenotypes=disease.phenotypes,
            existing_treatments=disease.existing_treatments,
            unmet_need_score=disease.unmet_need_score,
            description=f"{disease.name} is a rare genetic disorder characterized by ...",
            synonyms=[disease.name, "NPC" if disease.orpha_id == "ORPHA:635" else "CF" if disease.orpha_id == "ORPHA:793" else "HD"],
            omim_ids=["#607623"] if disease.orpha_id == "ORPHA:635" else ["#602421"] if disease.orpha_id == "ORPHA:793" else ["#143100"],
            mondo_id="MONDO:0005256" if disease.orpha_id == "ORPHA:635" else "MONDO:0005144" if disease.orpha_id == "ORPHA:793" else "MONDO:0008034",
            icar_id="ICAR:12345",
            created_at="2026-10-01T00:00:00Z",
            updated_at="2026-10-08T00:00:00Z"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("disease_get_failed", orpha_id=orpha_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve disease")

@router.get("/{orpha_id}/genes", response_model=List[str])
async def get_disease_genes(orpha_id: str):
    """Get genes associated with a disease."""
    try:
        disease = get_mock_disease_by_id(orpha_id)
        if not disease:
            raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
        return [g.symbol for g in disease.genes]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("disease_genes_failed", orpha_id=orpha_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve disease genes")

@router.get("/{orpha_id}/pathways", response_model=List[str])
async def get_disease_pathways(orpha_id: str):
    """Get pathways associated with a disease."""
    try:
        disease = get_mock_disease_by_id(orpha_id)
        if not disease:
            raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
        return [p.name for p in disease.pathways]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("disease_pathways_failed", orpha_id=orpha_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve disease pathways")
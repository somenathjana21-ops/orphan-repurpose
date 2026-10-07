from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.disease import DiseaseSearchResult, DiseaseDetail, DiseaseSearchParams
from app.services.kg_service import KGService
from app.core.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter()


# Dependency
def get_kg_service() -> KGService:
    return KGService()


@router.get("", response_model=List[DiseaseSearchResult])
async def search_diseases(
    q: Optional[str] = Query(None, description="Search query (name, ORPHA code, gene, pathway)"),
    prevalence_max: Optional[float] = Query(None, description="Maximum prevalence (per 100,000)"),
    gene: Optional[str] = Query(None, description="Gene symbol filter"),
    pathway: Optional[str] = Query(None, description="Pathway name filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("unmet_need_score"),
    sort_order: str = Query("desc"),
    kg: KGService = Depends(get_kg_service),
):
    """Search and filter rare diseases from Orphanet."""
    try:
        results, total = kg.search_diseases(
            query=q,
            prevalence_max=prevalence_max,
            gene=gene,
            pathway=pathway,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return results
    except Exception as e:
        logger.error("disease_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Disease search failed")


@router.get("/{orpha_id}", response_model=DiseaseDetail)
async def get_disease(
    orpha_id: str,
    kg: KGService = Depends(get_kg_service),
):
    """Get detailed disease information."""
    try:
        disease = kg.get_disease(orpha_id)
        if not disease:
            raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
        return disease
    except HTTPException:
        raise
    except Exception as e:
        logger.error("disease_get_failed", orpha_id=orpha_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve disease")


@router.get("/{orpha_id}/genes", response_model=List[str])
async def get_disease_genes(
    orpha_id: str,
    kg: KGService = Depends(get_kg_service),
):
    """Get genes associated with a disease."""
    try:
        genes = kg.get_disease_genes(orpha_id)
        return genes
    except Exception as e:
        logger.error("disease_genes_failed", orpha_id=orpha_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve disease genes")


@router.get("/{orpha_id}/pathways", response_model=List[str])
async def get_disease_pathways(
    orpha_id: str,
    kg: KGService = Depends(get_kg_service),
):
    """Get pathways associated with a disease."""
    try:
        pathways = kg.get_disease_pathways(orpha_id)
        return pathways
    except Exception as e:
        logger.error("disease_pathways_failed", orpha_id=orpha_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve disease pathways")
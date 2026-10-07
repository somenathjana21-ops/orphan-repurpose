from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DiseasePrevalence(str, Enum):
    ULTRA_RARE = "<1/1,000,000"
    RARE = "1/1,000,000 - 1/200,000"
    LESS_RARE = "1/200,000 - 1/2,000"


class Gene(BaseModel):
    hgnc_id: str
    symbol: str
    name: str
    uniprot_id: Optional[str] = None
    ensembl_id: Optional[str] = None


class Pathway(BaseModel):
    reactome_id: str
    name: str
    species: str = "Homo sapiens"
    url: Optional[str] = None


class DiseaseBase(BaseModel):
    orpha_id: str = Field(..., description="Orpha code (e.g., ORPHA:635)")
    name: str
    prevalence: Optional[float] = None
    prevalence_category: Optional[DiseasePrevalence] = None
    inheritance: Optional[List[str]] = None
    age_of_onset: Optional[List[str]] = None
    genes: List[Gene] = []
    pathways: List[Pathway] = []
    phenotypes: List[str] = []
    existing_treatments: List[str] = []
    unmet_need_score: Optional[float] = None


class DiseaseSearchResult(DiseaseBase):
    pass


class DiseaseDetail(DiseaseBase):
    description: Optional[str] = None
    synonyms: List[str] = []
    omim_ids: List[str] = []
    mondo_id: Optional[str] = None
    icar_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DiseaseSearchParams(BaseModel):
    q: Optional[str] = None
    prevalence_max: Optional[float] = None
    gene: Optional[str] = None
    pathway: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "unmet_need_score"
    sort_order: str = "desc"
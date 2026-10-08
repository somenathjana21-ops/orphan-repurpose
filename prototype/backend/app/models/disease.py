from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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

# Models for candidates and safety
class FAERSSignal(BaseModel):
    reaction: str
    meddra_pt: str
    ror: float
    prr: float
    bcpnn: float
    n_reports: int
    level: str  # 'pass' | 'caution' | 'fail'

class SafetyFlags(BaseModel):
    faers_signals: List[FAERSSignal]
    admet_predictions: Dict[str, float]
    contraindications: List[str]
    overall: str  # 'pass' | 'caution' | 'fail'

class KGPathNode(BaseModel):
    id: str
    type: str
    name: str
    properties: Dict[str, Any] = {}

class KGPathEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float

class KGPath(BaseModel):
    nodes: List[KGPathNode]
    edges: List[KGPathEdge]
    score: float

class Candidate(BaseModel):
    candidate_id: str
    drug_id: str
    drug_name: str
    indication_probability: float
    confidence_interval: List[float]  # [lower, upper]
    moa_summary: str
    safety_flags: SafetyFlags
    kg_paths: List[KGPath]
    llm_rationale: str
    shap_values: Dict[str, float]

class CandidateGenerateRequest(BaseModel):
    disease_id: str

class CandidateGenerateResponse(BaseModel):
    candidates: List[Candidate]
    session_id: str

class Explanation(BaseModel):
    candidate_id: str
    kg_paths: List[KGPath]
    shap_values: Dict[str, float]
    counterfactuals: List[Dict[str, Any]]
    llm_rationale: str

class Counterfactual(BaseModel):
    removed_edge: str
    probability_delta: float
    description: str

class ValidationRequest(BaseModel):
    validator: str
    assessment: str  # 'plausible' | 'needs_data' | 'unlikely'
    rationale: str

class SelfAssessmentRequest(BaseModel):
    efficacy: float
    safety: float
    feasibility: float
    notes: str

class AuditEntry(BaseModel):
    timestamp: str
    type: str  # 'validation' | 'self_assessment' | 'note' | 'generation'
    user: str
    data: Dict[str, Any]
    hash: str

class AuditTrail(BaseModel):
    session_id: str
    entries: List[AuditEntry]

class DossierRequest(BaseModel):
    disease_id: str
    candidate_ids: List[str]
    include_sections: List[str]

class DossierJSON(BaseModel):
    disease: DiseaseDetail
    candidates: List[Candidate]
    sections: Dict[str, Any]

class DossierResponse(BaseModel):
    pdf_base64: str
    dossier_json: DossierJSON
    audit_trail_id: str

class CredibilityMap(BaseModel):
    step_1_cou: str
    step_2_risk: str
    step_3_data_quality: str
    step_4_model_development: str
    step_5_model_evaluation: str
    step_6_deployment: str
    step_7_lifecycle: str

# Disease search params
class DiseaseSearchParams(BaseModel):
    q: Optional[str] = None
    prevalence_max: Optional[float] = None
    gene: Optional[str] = None
    pathway: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "unmet_need_score"
    sort_order: str = "desc"

class DiseaseSearchResponse(BaseModel):
    data: List[DiseaseSearchResult]
    total: int
    page: int
    page_size: int
from fastapi import APIRouter, HTTPException
import structlog
from app.models.disease import Candidate, SafetyFlags, FAERSSignal, CandidateGenerateResponse, CandidateGenerateRequest

logger = structlog.get_logger()
router = APIRouter()

# Mock data for candidates
MOCK_CANDIDATES = [
    Candidate(
        candidate_id="cand_001",
        drug_id="CHEMBL1200",
        drug_name="Miglustat",
        indication_probability=0.85,
        confidence_interval=[0.75, 0.92],
        moa_summary="Inhibits glucosylceramide synthase, reducing glycosphingolipid accumulation",
        safety_flags=SafetyFlags(
            faers_signals=[
                FAERSSignal(
                    reaction="Diarrhea",
                    meddra_pt="Diarrhea",
                    ror=1.2,
                    prr=1.1,
                    bcpnn=0.8,
                    n_reports=45,
                    level="caution"
                )
            ],
            admet_predictions={
                "logP": 0.5,
                "logS": -2.1,
                "BBB": 0.8,
                "CYP2D6": 0.1,
                "CYP3A4": 0.3
            },
            contraindications=["Severe hepatic impairment"],
            overall="caution"
        ),
        kg_paths=[
            {
                "nodes": [
                    {"id": "CHEMBL1200", "type": "drug", "name": "Miglustat", "properties": {}},
                    {"id": "GO:0008603", "type": "biological_process", "name": "glucosylceramide metabolic process", "properties": {}},
                    {"id": "HP:0007325", "type": "phenotype", "name": "Hepatosplenomegaly", "properties": {}}
                ],
                "edges": [
                    {"source": "CHEMBL1200", "target": "GO:0008603", "type": "inhibits", "weight": 0.9},
                    {"source": "GO:0008603", "target": "HP:0007325", "type": "associated_with", "weight": 0.8}
                ],
                "score": 0.85
            }
        ],
        llm_rationale="Miglustat inhibits glucosylceramide synthase, which is upregulated in Niemann-Pick type C due to impaired cholesterol trafficking. This reduction in glycosphingolipid accumulation helps mitigate lysosomal storage.",
        shap_values={
            "drug_structure_similarity": 0.35,
            "target_expression_in_tissue": 0.25,
            "pathway_centrality": 0.20,
            "safety_profile": 0.10,
            "known_indications": 0.10
        }
    ),
    Candidate(
        candidate_id="cand_002",
        drug_id="CHEMBL345",
        drug_name="Sirolimus",
        indication_probability=0.72,
        confidence_interval=[0.60, 0.81],
        moa_summary="Inhibits mTOR pathway, reducing autophagy dysfunction and lipid accumulation",
        safety_flags=SafetyFlags(
            faers_signals=[
                FAERSSignal(
                    reaction="Hyperlipidemia",
                    meddra_pt="Hyperlipidemia",
                    ror=1.8,
                    prr=1.6,
                    bcpnn=1.4,
                    n_reports=120,
                    level="fail"
                ),
                FAERSSignal(
                    reaction="Thrombocytopenia",
                    meddra_pt="Thrombocytopenia",
                    ror=1.5,
                    prr=1.3,
                    bcpnn=1.1,
                    n_reports=85,
                    level="caution"
                )
            ],
            admet_predictions={
                "logP": 2.0,
                "logS": -3.2,
                "BBB": 0.6,
                "CYP2D6": 0.0,
                "CYP3A4": 0.9
            },
            contraindications=["Active infection", "Severe hepatic impairment"],
            overall="fail"
        ),
        kg_paths=[
            {
                "nodes": [
                    {"id": "CHEMBL345", "type": "drug", "name": "Sirolimus", "properties": {}},
                    {"id": "GO:0016236", "type": "biological_process", "name": "macroautophagy", "properties": {}},
                    {"id": "HP:0007325", "type": "phenotype", "name": "Hepatosplenomegaly", "properties": {}}
                ],
                "edges": [
                    {"source": "CHEMBL345", "target": "GO:0016236", "type": "inhibits", "weight": 0.8},
                    {"source": "GO:0016236", "target": "HP:0007325", "type": "associated_with", "weight": 0.7}
                ],
                "score": 0.72
            }
        ],
        llm_rationale="Sirolimus inhibits mTOR, which regulates autophagy. In Niemann-Pick type C, autophagy dysfunction contributes to lipid accumulation. Inhibiting mTOR may help restore autophagic flux and reduce storage.",
        shap_values={
            "drug_structure_similarity": 0.20,
            "target_expression_in_tissue": 0.30,
            "pathway_centrality": 0.25,
            "safety_profile": -0.15,  # Negative due to safety concerns
            "known_indications": 0.10
        }
    )
]

@router.post("/generate", response_model=CandidateGenerateResponse)
async def generate_candidates(request: CandidateGenerateRequest):
    """Generate repurposing candidates for a disease."""
    disease_id = request.disease_id
    # In a real implementation, this would use ML models and KG reasoning
    # For now, return mock data if disease exists
    valid_diseases = ["ORPHA:635", "ORPHA:793", "ORPHA:98065"]
    if disease_id not in valid_diseases:
        raise HTTPException(status_code=404, detail=f"Disease {disease_id} not found")
    
    # Return different candidates based on disease
    if disease_id == "ORPHA:635":  # Niemann-Pick type C
        return CandidateGenerateResponse(
            candidates=MOCK_CANDIDATES,
            session_id="sess_001"
        )
    elif disease_id == "ORPHA:793":  # Cystic fibrosis
        # Different candidates for CF
        cf_candidates = [
            Candidate(
                candidate_id="cand_003",
                drug_id="CHEMBL210",
                drug_name="Ivacaftor",
                indication_probability=0.90,
                confidence_interval=[0.82, 0.95],
                moa_summary="CFTR potentiator that increases channel open probability",
                safety_flags=SafetyFlags(
                    faers_signals=[
                        FAERSSignal(
                            reaction="Elevated liver enzymes",
                            meddra_pt="Hepatic enzyme increased",
                            ror=1.3,
                            prr=1.2,
                            bcpnn=0.9,
                            n_reports=60,
                            level="caution"
                        )
                    ],
                    admet_predictions={
                        "logP": 4.5,
                        "logS": -4.8,
                        "BBB": 0.1,
                        "CYP2D6": 0.7,
                        "CYP3A4": 0.8
                    },
                    contraindications=[],
                    overall="pass"
                ),
                kg_paths=[
                    {
                        "nodes": [
                            {"id": "CHEMBL210", "type": "drug", "name": "Ivacaftor", "properties": {}},
                            {"id": "GO:0035579", "type": "biological_process", "name": "cAMP-mediated signaling", "properties": {}},
                            {"id": "HP:0002722", "type": "phenotype", "name": "Pancreatic insufficiency", "properties": {}}
                        ],
                        "edges": [
                            {"source": "CHEMBL210", "target": "GO:0035579", "type": "activates", "weight": 0.9},
                            {"source": "GO:0035579", "target": "HP:0002722", "type": "associated_with", "weight": 0.8}
                        ],
                        "score": 0.90
                    }
                ],
                llm_rationale="Ivacaftor potentiates the CFTR channel, which is defective in cystic fibrosis due to mutations in the CFTR gene. This increases chloride transport and improves hydration of airway surfaces.",
                shap_values={
                    "drug_structure_similarity": 0.40,
                    "target_expression_in_tissue": 0.30,
                    "pathway_centrality": 0.15,
                    "safety_profile": 0.10,
                    "known_indications": 0.05
                }
            )
        ]
        return CandidateGenerateResponse(
            candidates=cf_candidates,
            session_id="sess_002"
        )
    else:  # Huntington disease or default
        return CandidateGenerateResponse(
            candidates=MOCK_CANDIDATES[:1],  # Just first candidate
            session_id="sess_003"
        )

@router.get("/{candidate_id}", response_model=Candidate)
async def get_candidate(candidate_id: str):
    """Get detailed candidate information."""
    # Find candidate in mock data
    for candidate in MOCK_CANDIDATES:
        if candidate.candidate_id == candidate_id:
            return candidate
    
    # Check if it's a CF candidate
    if candidate_id == "cand_003":
        # Return the CF candidate manually
        return Candidate(
            candidate_id="cand_003",
            drug_id="CHEMBL210",
            drug_name="Ivacaftor",
            indication_probability=0.90,
            confidence_interval=[0.82, 0.95],
            moa_summary="CFTR potentiator that increases channel open probability",
            safety_flags=SafetyFlags(
                faers_signals=[
                    FAERSSignal(
                        reaction="Elevated liver enzymes",
                        meddra_pt="Hepatic enzyme increased",
                        ror=1.3,
                        prr=1.2,
                        bcpnn=0.9,
                        n_reports=60,
                        level="caution"
                    )
                ],
                admet_predictions={
                    "logP": 4.5,
                    "logS": -4.8,
                    "BBB": 0.1,
                    "CYP2D6": 0.7,
                    "CYP3A4": 0.8
                },
                contraindications=[],
                overall="pass"
            ),
            kg_paths=[
                {
                    "nodes": [
                        {"id": "CHEMBL210", "type": "drug", "name": "Ivacaftor", "properties": {}},
                        {"id": "GO:0035579", "type": "biological_process", "name": "cAMP-mediated signaling", "properties": {}},
                        {"id": "HP:0002722", "type": "phenotype", "name": "Pancreatic insufficiency", "properties": {}}
                    ],
                    "edges": [
                        {"source": "CHEMBL210", "target": "GO:0035579", "type": "activates", "weight": 0.9},
                        {"source": "GO:0035579", "target": "HP:0002722", "type": "associated_with", "weight": 0.8}
                    ],
                    "score": 0.90
                }
            ],
            llm_rationale="Ivacaftor potentiates the CFTR channel, which is defective in cystic fibrosis due to mutations in the CFTR gene. This increases chloride transport and improves hydration of airway surfaces.",
            shap_values={
                "drug_structure_similarity": 0.40,
                "target_expression_in_tissue": 0.30,
                "pathway_centrality": 0.15,
                "safety_profile": 0.10,
                "known_indications": 0.05
            }
        )
    
    raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

@router.get("/{candidate_id}/explanation")
async def get_candidate_explanation(candidate_id: str):
    """Get explanation for a candidate."""
    candidate = await get_candidate(candidate_id)
    # Return explanation structure
    return {
        "candidate_id": candidate_id,
        "kg_paths": candidate.kg_paths,
        "shap_values": candidate.shap_values,
        "counterfactuals": [
            {
                "removed_edge": "CHEMBL1200 -> GO:0008603",
                "probability_delta": -0.35,
                "description": "If Miglustat did not inhibit glucosylceramide synthase, indication probability would decrease significantly"
            }
        ],
        "llm_rationale": candidate.llm_rationale
    }

@router.get("/{candidate_id}/safety")
async def get_candidate_safety(candidate_id: str):
    """Get safety assessment for a candidate."""
    candidate = await get_candidate(candidate_id)
    return candidate.safety_flags

@router.get("/{candidate_id}/kg-subgraph")
async def get_candidate_kg_subgraph(candidate_id: str):
    """Get KG subgraph for a candidate."""
    candidate = await get_candidate(candidate_id)
    return {
        "candidate_id": candidate_id,
        "subgraph": {
            "nodes": [],
            "edges": []
        }  # Simplified for now
    }

@router.get("/{candidate_id}/literature")
async def get_candidate_literature(candidate_id: str):
    """Get literature for a candidate."""
    return {
        "candidate_id": candidate_id,
        "literature": [
            {
                "pmid": "12345678",
                "title": "Drug repurposing for rare diseases: A systematic review",
                "journal": "Nature Reviews Drug Discovery",
                "year": 2023,
                "relevance_score": 0.85
            }
        ]
    }

@router.post("/{candidate_id}/validate")
async def validate_candidate(candidate_id: str, data: dict):
    """Validate a candidate with expert feedback."""
    # In a real implementation, this would store the validation
    return {
        "candidate_id": candidate_id,
        "validation": data,
        "timestamp": "2026-10-08T10:00:00Z",
        "message": "Validation recorded successfully"
    }

@router.post("/{candidate_id}/assess")
async def self_assess_candidate(candidate_id: str, data: dict):
    """Self-assessment of a candidate."""
    return {
        "candidate_id": candidate_id,
        "assessment": data,
        "timestamp": "2026-10-08T10:00:00Z",
        "message": "Self-assessment recorded successfully"
    }
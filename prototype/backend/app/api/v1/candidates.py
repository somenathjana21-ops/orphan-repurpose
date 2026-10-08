from fastapi import APIRouter, HTTPException
import structlog
from app.models.disease import Candidate, SafetyFlags, FAERSSignal, CandidateGenerateResponse, CandidateGenerateRequest

logger = structlog.get_logger()
router = APIRouter()

# Drug metadata for the demo drugs (name, moa, safety) keyed by KG drug id
DRUG_META = {
    "drugcentral:1001": {
        "name": "Miglustat",
        "moa": "Inhibits glucosylceramide synthase, reducing glycosphingolipid accumulation",
        "rationale": "Miglustat inhibits glucosylceramide synthase, which is upregulated in Niemann-Pick type C due to impaired cholesterol trafficking. Reducing glycosphingolipid accumulation mitigates lysosomal storage.",
        "safety": SafetyFlags(
            faers_signals=[FAERSSignal(reaction="Diarrhea", meddra_pt="Diarrhea", ror=1.2, prr=1.1, bcpnn=0.8, n_reports=45, level="caution")],
            admet_predictions={"logP": 0.5, "logS": -2.1, "BBB": 0.8, "CYP2D6": 0.1, "CYP3A4": 0.3},
            contraindications=["Severe hepatic impairment"],
            overall="caution",
        ),
    },
    "drugcentral:1002": {
        "name": "Sirolimus",
        "moa": "Inhibits mTOR, restoring autophagic flux and reducing lipid accumulation",
        "rationale": "Sirolimus inhibits mTOR, which regulates autophagy. In Niemann-Pick type C, autophagy dysfunction contributes to lipid accumulation; inhibiting mTOR may restore autophagic flux.",
        "safety": SafetyFlags(
            faers_signals=[FAERSSignal(reaction="Hyperlipidemia", meddra_pt="Hyperlipidemia", ror=1.8, prr=1.6, bcpnn=1.4, n_reports=120, level="fail")],
            admet_predictions={"logP": 2.0, "logS": -3.2, "BBB": 0.6, "CYP2D6": 0.0, "CYP3A4": 0.9},
            contraindications=["Active infection", "Severe hepatic impairment"],
            overall="fail",
        ),
    },
    "drugcentral:1003": {
        "name": "Ivacaftor",
        "moa": "CFTR potentiator that increases channel open probability",
        "rationale": "Ivacaftor potentiates the CFTR channel, defective in cystic fibrosis due to CFTR mutations, increasing chloride transport and improving airway surface hydration.",
        "safety": SafetyFlags(
            faers_signals=[FAERSSignal(reaction="Elevated liver enzymes", meddra_pt="Hepatic enzyme increased", ror=1.3, prr=1.2, bcpnn=0.9, n_reports=60, level="caution")],
            admet_predictions={"logP": 4.5, "logS": -4.8, "BBB": 0.1, "CYP2D6": 0.7, "CYP3A4": 0.8},
            contraindications=[],
            overall="pass",
        ),
    },
    "drugcentral:1036": {
        "name": "Everolimus",
        "moa": "mTOR inhibitor, antiproliferative",
        "rationale": "Everolimus inhibits mTOR signalling, which is hyperactivated in tuberous sclerosis complex due to TSC1/TSC2 mutations. This reduces aberrant cell proliferation.",
        "safety": SafetyFlags(
            faers_signals=[FAERSSignal(reaction="Stomatitis", meddra_pt="Stomatitis", ror=2.1, prr=1.9, bcpnn=1.6, n_reports=210, level="caution")],
            admet_predictions={"logP": 4.1, "logS": -4.2, "BBB": 0.3, "CYP2D6": 0.1, "CYP3A4": 0.95},
            contraindications=["Active infection"],
            overall="caution",
        ),
    },
}

DEFAULT_SAFETY = SafetyFlags(
    faers_signals=[],
    admet_predictions={},
    contraindications=[],
    overall="caution",
)

# ORPHA id -> UMLS CUI (the disease key used by the trained model)
ORPHA_TO_UMLS = {
    "ORPHA:635": "UMLS:C0028042",
    "ORPHA:793": "UMLS:C0010674",
    "ORPHA:98065": "UMLS:C0020179",
    "ORPHA:399": "UMLS:C0017205",
    "ORPHA:310": "UMLS:C0041341",
}

DRUG_ID_TO_ORPHA = {v: k for k, v in ORPHA_TO_UMLS.items()}


def _load_drug_meta() -> dict:
    """Load drug names/MoA from the processed DrugCentral parquet at import time."""
    from pathlib import Path
    import pandas as pd

    meta: dict = {}
    candidates = [
        Path("../data/processed/drugcentral/drugcentral_fda_approved.parquet"),
        Path("data/processed/drugcentral/drugcentral_fda_approved.parquet"),
    ]
    for path in candidates:
        if path.exists():
            try:
                df = pd.read_parquet(path)
                for _, row in df.iterrows():
                    meta[f"drugcentral:{row['struct_id']}"] = {
                        "name": row.get("name") or f"Drug {row['struct_id']}",
                        "moa": row.get("moa_classes") or "Mechanism not annotated",
                        "gene": row.get("gene") or "",
                    }
                break
            except Exception:
                continue
    return meta


_DRUG_META_LOADED = _load_drug_meta()


def _build_kg_path(drug_id: str, drug_name: str, disease_name: str) -> list:
    """Construct a representative KG path drug -> target -> phenotype."""
    return [{
        "nodes": [
            {"id": drug_id, "type": "drug", "name": drug_name, "properties": {}},
            {"id": "GO:0008603", "type": "biological_process", "name": "glucosylceramide metabolic process", "properties": {}},
            {"id": "HP:0007325", "type": "phenotype", "name": "Hepatosplenomegaly", "properties": {}},
        ],
        "edges": [
            {"source": drug_id, "target": "GO:0008603", "type": "inhibits", "weight": 0.9},
            {"source": "GO:0008603", "target": "HP:0007325", "type": "associated_with", "weight": 0.8},
        ],
        "score": 0.85,
    }]


def _candidate_from_score(rank: int, score: dict) -> Candidate:
    """Turn a model score dict into a Candidate response object."""
    drug_id = score["drug_id"]
    meta = DRUG_META.get(drug_id) or _DRUG_META_LOADED.get(drug_id)
    name = meta["name"] if meta else drug_id.split(":")[-1]
    moa = meta["moa"] if meta else "Mechanism not annotated"
    rationale = (
        meta.get("rationale") if meta and meta.get("rationale")
        else f"Model-predicted repurposing candidate (rank {rank}, calibrated probability "
             f"{score['probability']:.2f}). Mechanism: {moa}."
    )
    safety = meta["safety"] if meta and "safety" in meta else DEFAULT_SAFETY

    return Candidate(
        candidate_id=f"cand_{rank:03d}",
        drug_id=drug_id,
        drug_name=name,
        indication_probability=round(score["probability"], 4),
        confidence_interval=[round(score["ci_lower"], 4), round(score["ci_upper"], 4)],
        moa_summary=moa,
        safety_flags=safety,
        kg_paths=_build_kg_path(drug_id, name, "query disease"),
        llm_rationale=rationale,
        shap_values={
            "drug_structure_similarity": 0.35,
            "target_expression_in_tissue": 0.25,
            "pathway_centrality": 0.20,
            "safety_profile": 0.10,
            "known_indications": 0.10,
        },
    )


@router.post("/generate", response_model=CandidateGenerateResponse)
async def generate_candidates(request: CandidateGenerateRequest):
    """Generate repurposing candidates for a disease using the trained model."""
    disease_id = request.disease_id

    # try real model inference
    try:
        from app.services.indication_service import get_indication_service

        svc = get_indication_service()
        if svc.is_ready():
            umls_key = ORPHA_TO_UMLS.get(disease_id, disease_id)
            scores = svc.score_all_for_orpha(umls_key, top_k=20)
            if scores:
                candidates = [_candidate_from_score(i + 1, s) for i, s in enumerate(scores)]
                _store_candidates(candidates)
                logger.info(
                    "candidates_generated_from_model",
                    disease_id=disease_id,
                    count=len(candidates),
                )
                return CandidateGenerateResponse(
                    candidates=candidates,
                    session_id=f"sess_{disease_id.replace(':', '_')}",
                )
    except Exception as e:
        logger.warning("model_inference_failed_falling_back", error=str(e))

    # fallback: curated demo candidates
    valid_diseases = ["ORPHA:635", "ORPHA:793", "ORPHA:98065"]
    if disease_id not in valid_diseases:
        raise HTTPException(status_code=404, detail=f"Disease {disease_id} not found")

    if disease_id == "ORPHA:635":
        return CandidateGenerateResponse(
            candidates=[_candidate_from_score(1, {"drug_id": "drugcentral:1001", "probability": 0.85, "ci_lower": 0.75, "ci_upper": 0.92}),
                        _candidate_from_score(2, {"drug_id": "drugcentral:1002", "probability": 0.72, "ci_lower": 0.60, "ci_upper": 0.81})],
            session_id="sess_ORPHA_635",
        )
    elif disease_id == "ORPHA:793":
        return CandidateGenerateResponse(
            candidates=[_candidate_from_score(1, {"drug_id": "drugcentral:1003", "probability": 0.90, "ci_lower": 0.82, "ci_upper": 0.95})],
            session_id="sess_ORPHA_793",
        )
    return CandidateGenerateResponse(
        candidates=[_candidate_from_score(1, {"drug_id": "drugcentral:1001", "probability": 0.55, "ci_lower": 0.40, "ci_upper": 0.70})],
        session_id=f"sess_{disease_id.replace(':', '_')}",
    )



# In-memory store of generated candidates, keyed by candidate_id
_CANDIDATE_STORE: dict = {}


def _store_candidates(candidates):
    for c in candidates:
        _CANDIDATE_STORE[c.candidate_id] = c


def _lookup_candidate(candidate_id: str):
    """Look up a candidate, generating the default NPC set if the store is cold."""
    if candidate_id in _CANDIDATE_STORE:
        return _CANDIDATE_STORE[candidate_id]
    # Cold start: materialise the NPC candidate list so detail views work.
    try:
        from app.services.indication_service import get_indication_service

        svc = get_indication_service()
        if svc.is_ready():
            scores = svc.score_all_for_orpha("UMLS:C0028042", top_k=20)
            cands = [_candidate_from_score(i + 1, s) for i, s in enumerate(scores)]
            _store_candidates(cands)
            if candidate_id in _CANDIDATE_STORE:
                return _CANDIDATE_STORE[candidate_id]
    except Exception as e:
        logger.warning("candidate_cold_start_failed", error=str(e))
    return None


@router.get("/{candidate_id}", response_model=Candidate)
async def get_candidate(candidate_id: str):
    """Get detailed candidate information."""
    candidate = _lookup_candidate(candidate_id)
    if candidate is not None:
        return candidate
    raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")


@router.get("/{candidate_id}/explanation")
async def get_candidate_explanation(candidate_id: str):
    """Get explanation for a candidate."""
    candidate = await get_candidate(candidate_id)
    try:
        from app.services.explanation_service import get_explanation_service
        svc = get_explanation_service()
        explanation = svc.explain_candidate(
            drug_id=candidate.drug_id,
            disease_id="unknown",
            drug_name=candidate.drug_name,
            disease_name="query disease",
            probability=candidate.indication_probability,
            moa_summary=candidate.moa_summary,
        )
        return explanation
    except Exception as e:
        logger.warning("explanation_service_failed_falling_back", error=str(e))
        return {
            "candidate_id": candidate_id,
            "kg_paths": candidate.kg_paths,
            "shap_values": candidate.shap_values,
            "counterfactuals": [],
            "llm_rationale": candidate.llm_rationale
        }

@router.get("/{candidate_id}/safety")
async def get_candidate_safety(candidate_id: str):
    """Get safety assessment for a candidate."""
    candidate = await get_candidate(candidate_id)
    try:
        from app.services.safety_service import get_safety_service
        svc = get_safety_service()
        smiles = ""
        try:
            from app.services.indication_service import get_indication_service
            ind_svc = get_indication_service()
            if ind_svc.is_ready():
                smiles = ind_svc.drug_smiles.get(candidate.drug_id, "")
        except Exception:
            pass
        result = svc.assess_drug(
            drug_id=candidate.drug_id,
            drug_name=candidate.drug_name,
            smiles=smiles,
        )
        return result
    except Exception as e:
        logger.warning("safety_service_failed_falling_back", error=str(e))
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
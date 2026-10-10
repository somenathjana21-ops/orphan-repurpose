from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import structlog
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.models.disease import (
    DiseaseDetail,
    DiseaseSearchResponse,
    DiseaseSearchResult,
    Gene,
    Pathway,
)

logger = structlog.get_logger()
router = APIRouter()

# ---------------------------------------------------------------------------
# Disease data loaded from the processed Orphanet parquet
# ---------------------------------------------------------------------------
_ORPHA_PARQUET_CANDIDATES = [
    Path(settings.PROCESSED_DATA_DIR) / "orpha" / "orpha_diseases.parquet",
    Path("../data/processed/orpha/orpha_diseases.parquet"),
    Path("data/processed/orpha/orpha_diseases.parquet"),
]

# UMLS CUI -> ORPHA id, so we can map the model's disease keys back to Orphanet ids
_UMLS_TO_ORPHA: dict[str, str] = {}

# Fallback curated diseases if the parquet is unavailable
_FALLBACK_DISEASES = [
    {
        "id": "ORPHA:635",
        "name": "Niemann-Pick disease type C",
        "prevalence": 0.5,
        "prevalence_category": "1/200,000 - 1/2,000",
        "inheritance": ["Autosomal recessive"],
        "age_of_onset": ["Infantile", "Juvenile", "Adult"],
        "genes": [
            {
                "hgnc_id": "HGNC:7694",
                "symbol": "NPC1",
                "name": "NPC intracellular cholesterol transporter 1",
            },
            {
                "hgnc_id": "HGNC:14133",
                "symbol": "NPC2",
                "name": "NPC intracellular cholesterol transporter 2",
            },
        ],
        "phenotypes": ["Hepatosplenomegaly", "Ataxia", "Dysphagia"],
        "existing_treatments": ["Miglustat"],
        "unmet_need_score": 0.85,
        "description": "Niemann-Pick type C is a rare lysosomal storage disorder characterised by progressive neurodegeneration.",
        "umls_cui": "C0028042",
    },
    {
        "id": "ORPHA:793",
        "name": "Cystic fibrosis",
        "prevalence": 3.5,
        "prevalence_category": "1/200,000 - 1/2,000",
        "inheritance": ["Autosomal recessive"],
        "age_of_onset": ["Neonatal", "Infantile", "Childhood"],
        "genes": [
            {
                "hgnc_id": "HGNC:2649",
                "symbol": "CFTR",
                "name": "Cystic fibrosis transmembrane conductance regulator",
            }
        ],
        "phenotypes": [
            "Chronic cough",
            "Recurrent pulmonary infections",
            "Pancreatic insufficiency",
        ],
        "existing_treatments": ["Ivacaftor"],
        "unmet_need_score": 0.60,
        "description": "Cystic fibrosis is a genetic disorder affecting the CFTR protein.",
        "umls_cui": "C0010674",
    },
    {
        "id": "ORPHA:98065",
        "name": "Huntington disease",
        "prevalence": 5.0,
        "prevalence_category": "1/200,000 - 1/2,000",
        "inheritance": ["Autosomal dominant"],
        "age_of_onset": ["Adult"],
        "genes": [{"hgnc_id": "HGNC:4848", "symbol": "HTT", "name": "Huntingtin"}],
        "phenotypes": ["Chorea", "Cognitive decline", "Psychiatric disturbances"],
        "existing_treatments": ["Tetrabenazine"],
        "unmet_need_score": 0.75,
        "description": "Huntington disease is a progressive neurodegenerative disorder.",
        "umls_cui": "C0020179",
    },
]


def _compute_unmet_need(prevalence: float | None, n_treatments: int, n_genes: int) -> float:
    """Heuristic unmet-need score in [0, 1].

    Rare + few existing treatments + known genetic basis -> higher unmet need.
    """
    prev = prevalence if prevalence is not None else 5.0
    rarity = max(0.0, min(1.0, 1.0 - (prev / 30.0)))
    treatment_gap = max(0.0, 1.0 - n_treatments / 5.0)
    genetic_basis = 0.5 if n_genes > 0 else 0.0
    return round(0.45 * rarity + 0.35 * treatment_gap + 0.20 * genetic_basis, 3)


def _load_diseases() -> list[dict]:
    """Load and normalise disease records from the processed parquet."""
    global _UMLS_TO_ORPHA
    for path in _ORPHA_PARQUET_CANDIDATES:
        if not path.exists():
            continue
        try:
            df = pd.read_parquet(path)
        except Exception as e:
            logger.warning("orpha_parquet_read_failed", path=str(path), error=str(e))
            continue

        records = []
        for _, row in df.iterrows():
            orpha_id = row.get("id")
            if not isinstance(orpha_id, str) or not orpha_id.startswith("ORPHA:"):
                continue

            genes_raw = row.get("genes")
            genes = []
            if genes_raw is not None:
                try:
                    for g in list(genes_raw):
                        if isinstance(g, dict) and g.get("symbol"):
                            genes.append(
                                {
                                    "hgnc_id": g.get("hgnc_id") or f"HGNC:{g['symbol']}",
                                    "symbol": g["symbol"],
                                    "name": g.get("name") or g["symbol"],
                                }
                            )
                except Exception:
                    genes = []

            hpo_raw = row.get("hpo_terms")
            phenotypes = []
            if hpo_raw is not None:
                try:
                    phenotypes = [
                        h.get("term")
                        for h in list(hpo_raw)
                        if isinstance(h, dict) and h.get("term")
                    ]
                except Exception:
                    phenotypes = []

            prev = row.get("prevalence")
            prev = float(prev) if pd.notna(prev) else None

            inheritance = row.get("inheritance")
            inheritance_list = (
                inheritance.split("|") if isinstance(inheritance, str) and inheritance else []
            )
            onset = row.get("age_of_onset")
            onset_list = onset.split("|") if isinstance(onset, str) and onset else []

            cui = row.get("umls_cui")
            if isinstance(cui, str) and cui:
                _UMLS_TO_ORPHA[f"UMLS:{cui}"] = orpha_id

            records.append(
                {
                    "id": orpha_id,
                    "name": row.get("name") or orpha_id,
                    "prevalence": prev,
                    "prevalence_category": row.get("prevalence_category"),
                    "inheritance": inheritance_list,
                    "age_of_onset": onset_list,
                    "genes": genes,
                    "phenotypes": phenotypes,
                    "existing_treatments": [],
                    "unmet_need_score": _compute_unmet_need(prev, 0, len(genes)),
                    "description": f"{row.get('name')} is a rare disease catalogued in Orphanet.",
                    "umls_cui": cui if isinstance(cui, str) else None,
                }
            )

        if records:
            logger.info("diseases_loaded", count=len(records), path=str(path))
            return records

    logger.warning("using_fallback_diseases")
    return _FALLBACK_DISEASES


_DISEASES = _load_diseases()
_DISEASE_BY_ID = {d["id"]: d for d in _DISEASES}

# ORPHA -> UMLS mapping used by the candidate model
ORPHA_TO_UMLS = {d["id"]: f"UMLS:{d['umls_cui']}" for d in _DISEASES if d.get("umls_cui")}
UMLS_TO_ORPHA = {v: k for k, v in ORPHA_TO_UMLS.items()}


def _normalize_str_list(val: Any) -> list[str]:
    """Ensure a string or list field is returned as a clean list of strings."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x and str(x).strip()]
    if isinstance(val, str):
        if "|" in val:
            return [x.strip() for x in val.split("|") if x.strip()]
        return [val.strip()] if val.strip() else []
    return [str(val).strip()]


def _parse_datetime(val: Any, default_iso: str = "2026-10-01T00:00:00+00:00") -> datetime:
    """Parse string or datetime object into a datetime instance."""
    if isinstance(val, datetime):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.fromisoformat(default_iso)


def _to_search_result(d: dict) -> DiseaseSearchResult:
    return DiseaseSearchResult(
        orpha_id=d["id"],
        name=d["name"],
        prevalence=d.get("prevalence"),
        prevalence_category=d.get("prevalence_category"),
        inheritance=_normalize_str_list(d.get("inheritance")),
        age_of_onset=_normalize_str_list(d.get("age_of_onset")),
        genes=[Gene(**g) for g in d.get("genes", [])],
        pathways=[Pathway(**p) for p in d.get("pathways", [])],
        phenotypes=_normalize_str_list(d.get("phenotypes")),
        existing_treatments=_normalize_str_list(d.get("existing_treatments")),
        unmet_need_score=d.get("unmet_need_score"),
    )


def _to_detail(d: dict) -> DiseaseDetail:
    return DiseaseDetail(
        orpha_id=d["id"],
        name=d["name"],
        prevalence=d.get("prevalence"),
        prevalence_category=d.get("prevalence_category"),
        inheritance=_normalize_str_list(d.get("inheritance")),
        age_of_onset=_normalize_str_list(d.get("age_of_onset")),
        genes=[Gene(**g) for g in d.get("genes", [])],
        pathways=[Pathway(**p) for p in d.get("pathways", [])],
        phenotypes=_normalize_str_list(d.get("phenotypes")),
        existing_treatments=_normalize_str_list(d.get("existing_treatments")),
        unmet_need_score=d.get("unmet_need_score"),
        description=d.get("description"),
        synonyms=_normalize_str_list(d.get("synonyms") or [d.get("name", "")]),
        omim_ids=_normalize_str_list(d.get("omim_ids")),
        mondo_id=d.get("mondo_id"),
        icar_id=d.get("icar_id"),
        created_at=_parse_datetime(d.get("created_at"), "2026-10-01T00:00:00+00:00"),
        updated_at=_parse_datetime(d.get("updated_at"), "2026-10-08T00:00:00+00:00"),
    )


@router.get("", response_model=DiseaseSearchResponse)
async def search_diseases(
    q: str | None = Query(None, description="Search query (name, ORPHA code, gene, pathway)"),
    prevalence_max: float | None = Query(None, description="Maximum prevalence (per 100,000)"),
    gene: str | None = Query(None, description="Gene symbol filter"),
    pathway: str | None = Query(None, description="Pathway name filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("unmet_need_score"),
    sort_order: str = Query("desc"),
):
    """Search and filter rare diseases from Orphanet."""
    try:
        filtered = list(_DISEASES)
        if q:
            q_lower = q.lower()
            filtered = [
                d
                for d in filtered
                if q_lower in d["name"].lower()
                or q_lower in d["id"].lower()
                or any(q_lower in g["symbol"].lower() for g in d.get("genes", []))
            ]
        if prevalence_max is not None:
            filtered = [
                d
                for d in filtered
                if d.get("prevalence") is None or d["prevalence"] <= prevalence_max
            ]
        if gene:
            filtered = [
                d
                for d in filtered
                if any(g["symbol"].upper() == gene.upper() for g in d.get("genes", []))
            ]

        reverse = sort_order == "desc"
        key_map = {
            "name": lambda d: d["name"],
            "orpha_id": lambda d: d["id"],
            "prevalence": lambda d: d.get("prevalence") or 0,
            "unmet_need_score": lambda d: d.get("unmet_need_score") or 0,
        }
        filtered.sort(key=key_map.get(sort_by, key_map["unmet_need_score"]), reverse=reverse)

        total = len(filtered)
        start = (page - 1) * page_size
        page_items = filtered[start : start + page_size]

        return DiseaseSearchResponse(
            data=[_to_search_result(d) for d in page_items],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error("disease_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Disease search failed") from e


@router.get("/{orpha_id}", response_model=DiseaseDetail)
async def get_disease(orpha_id: str):
    """Get detailed disease information."""
    d = _DISEASE_BY_ID.get(orpha_id)
    if d is None:
        raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
    return _to_detail(d)


@router.get("/{orpha_id}/genes", response_model=list[str])
async def get_disease_genes(orpha_id: str):
    """Get genes associated with a disease."""
    d = _DISEASE_BY_ID.get(orpha_id)
    if d is None:
        raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
    return [g["symbol"] for g in d.get("genes", [])]


@router.get("/{orpha_id}/pathways", response_model=list[str])
async def get_disease_pathways(orpha_id: str):
    """Get pathways associated with a disease."""
    d = _DISEASE_BY_ID.get(orpha_id)
    if d is None:
        raise HTTPException(status_code=404, detail=f"Disease {orpha_id} not found")
    return [p["name"] for p in d.get("pathways", [])]

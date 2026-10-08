from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import structlog
from app.models.disease import DiseaseDetail

logger = structlog.get_logger()
router = APIRouter()

# Mock literature data
MOCK_PUBLICATIONS = [
    {
        "pmid": "33567210",
        "title": "Drug repurposing for rare diseases: A systematic review",
        "journal": "Nature Reviews Drug Discovery",
        "year": 2023,
        "abstract": "Systematic review of computational drug repurposing approaches for rare diseases...",
        "relevance_score": 0.92,
    },
    {
        "pmid": "28765320",
        "title": "Miglustat for Niemann-Pick disease type C: a randomized controlled trial",
        "journal": "The Lancet Neurology",
        "year": 2022,
        "abstract": "Randomized controlled trial of miglustat in NPC patients showing...",
        "relevance_score": 0.88,
    },
    {
        "pmid": "31006543",
        "title": "Knowledge graph-based drug repurposing for rare genetic disorders",
        "journal": "Bioinformatics",
        "year": 2021,
        "abstract": "We present a knowledge graph approach integrating multiple biomedical...",
        "relevance_score": 0.85,
    },
    {
        "pmid": "25677008",
        "title": "The Orphan Drug Act and its impact on rare disease drug development",
        "journal": "Orphanet Journal of Rare Diseases",
        "year": 2020,
        "abstract": "Analysis of the Orphan Drug Act incentives and their effect on...",
        "relevance_score": 0.78,
    },
    {
        "pmid": "36198754",
        "title": "AI-driven drug discovery for orphan diseases: challenges and opportunities",
        "journal": "Drug Discovery Today",
        "year": 2024,
        "abstract": "Review of AI approaches for orphan disease drug discovery including...",
        "relevance_score": 0.82,
    },
]


@router.get("/search")
async def search_literature(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search literature by query string."""
    try:
        q_lower = q.lower()
        results = [
            p for p in MOCK_PUBLICATIONS
            if q_lower in p["title"].lower()
            or q_lower in p["abstract"].lower()
            or q_lower in p["journal"].lower()
        ]
        # If no matches, return all (for demo purposes)
        if not results:
            results = MOCK_PUBLICATIONS
        return {"results": results[:limit], "total": len(results)}
    except Exception as e:
        logger.error("literature_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Literature search failed")


@router.post("/summarize")
async def summarize_literature(pmids: List[str]):
    """Summarize literature by PMIDs."""
    try:
        results = []
        for pmid in pmids:
            pub = next((p for p in MOCK_PUBLICATIONS if p["pmid"] == pmid), None)
            if pub:
                results.append({
                    "pmid": pmid,
                    "title": pub["title"],
                    "summary": f"This study from {pub['journal']} ({pub['year']}) investigates {pub['title'].lower()}. Key findings suggest potential therapeutic implications for rare disease treatment.",
                })
        return {"summaries": results}
    except Exception as e:
        logger.error("literature_summarize_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Literature summarization failed")

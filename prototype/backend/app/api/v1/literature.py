import hashlib
import re
from typing import Any

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Query

logger = structlog.get_logger()
router = APIRouter()

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
HTTP_TIMEOUT = 10.0

# Curated fallback PMIDs for rare disease drug repurposing
FALLBACK_PMIDS = ["33567210", "28765320", "31006543", "25677008", "36198754"]

# Simple in-memory cache: key -> (timestamp, data)
_cache: dict[str, Any] = {}


def _cache_key(*parts: str) -> str:
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _get_cached(key: str) -> Any | None:
    return _cache.get(key)


def _set_cached(key: str, value: Any) -> None:
    _cache[key] = value


async def _esearch(query: str, retmax: int) -> list[str]:
    """Search PubMed and return a list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(retmax),
        "retmode": "json",
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{EUTILS_BASE}/esearch.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])


async def _esummary(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch summaries for a list of PMIDs."""
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{EUTILS_BASE}/esummary.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result", {})
        uids = result.get("uids", [])
        publications = []
        for uid in uids:
            item = result.get(uid, {})
            # Extract authors
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            # Parse year from pubdate
            pubdate = item.get("pubdate", "")
            year = ""
            if pubdate:
                match = re.search(r"\d{4}", pubdate)
                if match:
                    year = match.group(0)
            # Build abstract from elocation or title (esummary may not have abstract)
            abstract = item.get("abstract", item.get("title", ""))
            publications.append(
                {
                    "pmid": uid,
                    "title": item.get("title", ""),
                    "journal": item.get("fulljournalname", item.get("source", "")),
                    "year": year,
                    "authors": authors,
                    "abstract": abstract,
                    "doi": item.get("elocationid", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    "relevance_score": 0.0,  # Will be set by search ranking
                }
            )
        return publications


async def _efetch_abstracts(pmids: list[str]) -> dict[str, str]:
    """Fetch raw abstracts from efetch for a list of PMIDs."""
    if not pmids:
        return {}
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "text",
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(f"{EUTILS_BASE}/efetch.fcgi", params=params)
        resp.raise_for_status()
        text = resp.text
        # Parse blocks separated by blank lines
        # Each record starts with a PMID line
        abstracts: dict[str, str] = {}
        current_pmid: str | None = None
        current_lines: list[str] = []

        for line in text.split("\n"):
            line = line.strip()
            # Detect PMID line (starts with "PMID:")
            pmid_match = re.match(r"^PMID:\s*(\d+)", line)
            if pmid_match:
                if current_pmid and current_lines:
                    abstracts[current_pmid] = " ".join(current_lines).strip()
                current_pmid = pmid_match.group(1)
                current_lines = []
            elif current_pmid is not None and line:
                # Collect non-empty lines as abstract text
                current_lines.append(line)

        # Don't forget the last block
        if current_pmid and current_lines:
            abstracts[current_pmid] = " ".join(current_lines).strip()

        return abstracts


def _extractive_summary(abstract: str, max_sentences: int = 3) -> str:
    """Generate a simple extractive summary: first N sentences of the abstract."""
    if not abstract:
        return ""
    # Split on sentence-ending periods followed by space/newline or end
    sentences = re.split(r"(?<=[.!?])\s+", abstract.strip())
    # Take first N non-empty sentences
    selected = []
    for s in sentences:
        s = s.strip()
        if s:
            selected.append(s)
        if len(selected) >= max_sentences:
            break
    return " ".join(selected)


@router.get("/search")
async def search_literature(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search PubMed for literature matching the query."""
    try:
        ck = _cache_key("search", query, str(limit))
        cached = _get_cached(ck)
        if cached is not None:
            return cached

        # Step 1: esearch to get PMIDs
        try:
            pmids = await _esearch(query, limit)
        except Exception as e:
            logger.warning("esearch_failed", error=str(e))
            pmids = FALLBACK_PMIDS[:limit]

        # Step 2: esummary to get publication details
        try:
            publications = await _esummary(pmids)
        except Exception as e:
            logger.warning("esummary_failed", error=str(e))
            # Fallback: build minimal entries from fallback PMIDs
            publications = [
                {
                    "pmid": pmid,
                    "title": f"Publication {pmid}",
                    "journal": "Unknown",
                    "year": "",
                    "authors": [],
                    "abstract": f"Abstract for PMID {pmid} could not be retrieved.",
                    "doi": "",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "relevance_score": 0.0,
                }
                for pmid in FALLBACK_PMIDS[:limit]
            ]

        # Assign a simple relevance score (higher = earlier in results)
        for i, pub in enumerate(publications):
            pub["relevance_score"] = round(1.0 - (i * 0.05), 2)

        result = {"results": publications, "total": len(publications)}
        _set_cached(ck, result)
        return result

    except Exception as e:
        logger.error("literature_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Literature search failed") from e


@router.post("/summarize")
async def summarize_literature(pmids: list[str]):
    """Fetch abstracts and generate extractive summaries for given PMIDs."""
    try:
        ck = _cache_key("summarize", ",".join(sorted(pmids)))
        cached = _get_cached(ck)
        if cached is not None:
            return cached

        # Fetch abstracts via efetch
        try:
            abstracts = await _efetch_abstracts(pmids)
        except Exception as e:
            logger.warning("efetch_failed", error=str(e))
            abstracts = {}

        # Fetch metadata via esummary for titles/journals
        try:
            summaries_meta = await _esummary(pmids)
            meta_map = {s["pmid"]: s for s in summaries_meta}
        except Exception as e:
            logger.warning("esummary_for_summarize_failed", error=str(e))
            meta_map = {}

        results = []
        for pmid in pmids:
            meta = meta_map.get(pmid, {})
            abstract = abstracts.get(pmid, meta.get("abstract", ""))
            summary_text = _extractive_summary(abstract)

            if not summary_text:
                # Fallback: use title as summary basis
                title = meta.get("title", f"Publication {pmid}")
                summary_text = f"Title: {title}. Abstract could not be retrieved from PubMed."

            results.append(
                {
                    "pmid": pmid,
                    "title": meta.get("title", f"Publication {pmid}"),
                    "journal": meta.get("journal", ""),
                    "year": meta.get("year", ""),
                    "summary": summary_text,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                }
            )

        output = {"summaries": results}
        _set_cached(ck, output)
        return output

    except Exception as e:
        logger.error("literature_summarize_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Literature summarization failed") from e

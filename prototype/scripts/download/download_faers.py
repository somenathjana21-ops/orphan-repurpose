#!/usr/bin/env python3
"""
Download FAERS data via openFDA API for drugs in our dataset.
Fetches drug event reports for the drugs we care about.
"""
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Any

import pandas as pd
import structlog

logger = structlog.get_logger()

OPENFDA_API_BASE = "https://api.fda.gov/drug/event.json"
API_KEY = os.environ.get("OPENFDA_API_KEY", "")  # Optional - rate limits without key
MAX_DRUGS_PER_QUERY = 5
MAX_RESULTS_PER_QUERY = 100
SLEEP_BETWEEN_QUERIES = 1.0  # seconds - be nice to the API


def load_drug_names() -> list[str]:
    """Load drug names from the demo data generator."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_demo_data",
        Path(__file__).parent.parent / "scripts" / "etl" / "generate_demo_data.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [d[1] for d in mod.DRUGS]


def fetch_faers_page(drug_names: list[str], skip: int = 0, limit: int = 100) -> dict[str, Any]:
    """Fetch one page of FAERS results for the given drugs."""
    # Build openFDA query: patient.drug.medicinalproduct matches any drug
    drug_filter = ",".join(f'"{d}"' for d in drug_names)
    query = f"patient.drug.medicinalproduct:({drug_filter})"

    params = {"search": query, "limit": min(limit, MAX_RESULTS_PER_QUERY)}
    if skip > 0:
        params["skip"] = str(skip)

    url = f"{OPENFDA_API_BASE}?{urllib.parse.urlencode(params)}"
    if API_KEY:
        url += f"&api_key={API_KEY}"

    logger.info("fetching_faers_page", drugs=drug_names, skip=skip, url=url[:200])

    req = urllib.request.Request(url, headers={"User-Agent": "OrphanRepurpose/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.info("faers_no_results", drugs=drug_names)
            return {"results": [], "meta": {"results": {"total": 0}}}
        if e.code == 429:
            logger.warning("faers_rate_limited", retry_after=10)
            time.sleep(10)
            return fetch_faers_page(drug_names, skip, limit)
        logger.warning("faers_http_error", code=e.code, drugs=drug_names)
        return {"results": [], "meta": {"results": {"total": 0}}}
    except Exception as e:
        logger.warning("faers_fetch_error", error=str(e), drugs=drug_names)
        return {"results": [], "meta": {"results": {"total": 0}}}


def fetch_faers_for_drugs(drug_names: list[str], output_dir: Path) -> None:
    """Fetch FAERS data for all drugs in batches."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []
    total_fetched = 0
    batch_num = 0

    for i in range(0, len(drug_names), MAX_DRUGS_PER_QUERY):
        batch = drug_names[i : i + MAX_DRUGS_PER_QUERY]
        batch_num += 1

        # First page
        data = fetch_faers_page(batch, skip=0, limit=100)
        results = data.get("results", [])
        all_results.extend(results)
        total_fetched += len(results)

        total_available = data.get("meta", {}).get("results", {}).get("total", 0)
        logger.info("faers_batch_fetched", batch=batch_num, drugs=batch,
                     fetched=len(results), total_available=total_available)

        # Paginate if needed
        skip = len(results)
        while skip < total_available and skip < MAX_RESULTS_PER_QUERY:
            time.sleep(SLEEP_BETWEEN_QUERIES)
            data = fetch_faers_page(batch, skip=skip, limit=100)
            results = data.get("results", [])
            if not results:
                break
            all_results.extend(results)
            total_fetched += len(results)
            skip += len(results)

        time.sleep(SLEEP_BETWEEN_QUERIES)

    # Save results
    output_file = output_dir / "faers_drug_events.json"
    with open(output_file, "w") as f:
        json.dump({"meta": {"total_fetched": total_fetched, "drugs_queried": len(drug_names)},
                    "results": all_results}, f, indent=2)

    # Also save as JSONL for easy streaming
    jsonl_file = output_dir / "faers_drug_events.jsonl"
    with open(jsonl_file, "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")

    logger.info("faers_download_complete", total_fetched=total_fetched,
                 output=str(output_file), jsonl=str(jsonl_file))


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    raw_dir = data_dir / "raw" / "faers"

    drug_names = load_drug_names()
    logger.info("faers_start", num_drugs=len(drug_names))

    fetch_faers_for_drugs(drug_names, raw_dir)

    print(f"\nFAERS data saved to {raw_dir}")
    print(f"Queried {len(drug_names)} drugs via openFDA API")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Process PubMed publication data into a unified literature table.
Parses JSONL publications and creates a structured DataFrame.
"""
import json
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()


def process_pubmed_data(raw_dir: Path, processed_dir: Path) -> None:
    """Process PubMed publication data."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load publications from JSONL
    jsonl_path = raw_dir / "pubmed_npc.jsonl"
    if not jsonl_path.exists():
        logger.warning("pubmed_file_missing", path=str(jsonl_path))
        return

    publications = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                publications.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not publications:
        logger.warning("pubmed_no_publications")
        return

    df = pd.DataFrame(publications)
    df.to_parquet(processed_dir / "pubmed_publications.parquet", index=False)
    df.to_csv(processed_dir / "pubmed_publications.csv", index=False)

    # Create drug-publication edges
    drug_pub_rows = []
    for pub in publications:
        for drug in pub.get("drug_names", []):
            drug_pub_rows.append({
                "drug_name": drug,
                "pmid": pub["pmid"],
                "title": pub["title"],
            })
    pd.DataFrame(drug_pub_rows).to_parquet(processed_dir / "pubmed_drug_publication.parquet", index=False)

    # Create disease-publication edges
    disease_pub_rows = []
    for pub in publications:
        for did in pub.get("disease_ids", []):
            disease_pub_rows.append({
                "disease_id": did,
                "pmid": pub["pmid"],
                "title": pub["title"],
            })
    pd.DataFrame(disease_pub_rows).to_parquet(processed_dir / "pubmed_disease_publication.parquet", index=False)

    logger.info("pubmed_processing_complete",
                 publications=len(publications),
                 drug_edges=len(drug_pub_rows),
                 disease_edges=len(disease_pub_rows))


def main() -> None:
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data/raw/pubmed")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./prototype/data/processed/pubmed")

    print("⚙️  Processing PubMed data...")
    process_pubmed_data(raw_dir, processed_dir)
    print(f"\nPubMed processing complete. Output: {processed_dir}")


if __name__ == "__main__":
    main()

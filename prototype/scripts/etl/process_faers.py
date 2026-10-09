#!/usr/bin/env python3
"""
Process FAERS data: parse JSON/JSONL drug event reports,
extract drug-event pairs, compute basic statistics.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()


def parse_faers_jsonl(jsonl_path: Path) -> list[dict]:
    """Parse FAERS JSONL file into a list of drug-event records."""
    records = []
    if not jsonl_path.exists():
        logger.warning("faers_file_missing", path=str(jsonl_path))
        return records

    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def parse_faers_json(json_path: Path) -> list[dict]:
    """Parse FAERS JSON file (from openFDA API response)."""
    records = []
    if not json_path.exists():
        logger.warning("faers_file_missing", path=str(json_path))
        return records

    with open(json_path) as f:
        data = json.load(f)

    for r in data.get("results", []):
        records.append(r)
    return records


def extract_drug_events(records: list[dict]) -> pd.DataFrame:
    """Extract drug-event pairs from FAERS records."""
    drug_events = []

    for rec in records:
        # Get patient info
        patient = rec.get("patient", {})
        age = patient.get("patientonsetage", None)
        sex = patient.get("patientsex", None)

        # Get drugs
        drugs = patient.get("drug", [])
        drug_names = set()
        for d in drugs:
            name = d.get("medicinalproduct", "")
            if name:
                drug_names.add(name)

        # Get adverse events
        reactions = patient.get("reaction", [])
        event_names = set()
        for rx in reactions:
            event = rx.get("reactionmeddrapt", "")
            if event:
                event_names.add(event)

        # Create drug-event pairs
        for drug in drug_names:
            for event in event_names:
                drug_events.append({
                    "drug_name": drug,
                    "event_name": event,
                    "patient_age": age,
                    "patient_sex": sex,
                    "report_id": rec.get("safetyreportid", ""),
                    "receipt_date": rec.get("receiptdate", ""),
                })

    return pd.DataFrame(drug_events)


def compute_faers_statistics(drug_events: pd.DataFrame) -> dict:
    """Compute basic FAERS statistics."""
    if drug_events.empty:
        return {"total_reports": 0, "unique_drugs": 0, "unique_events": 0}

    stats = {
        "total_reports": len(drug_events),
        "unique_drugs": drug_events["drug_name"].nunique(),
        "unique_events": drug_events["event_name"].nunique(),
        "top_drugs": drug_events["drug_name"].value_counts().head(20).to_dict(),
        "top_events": drug_events["event_name"].value_counts().head(20).to_dict(),
    }
    return stats


def process_faers_data(raw_dir: Path, processed_dir: Path) -> None:
    """Process FAERS data from raw to processed format."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Try JSONL first, then JSON
    jsonl_path = raw_dir / "faers_drug_events.jsonl"
    json_path = raw_dir / "faers_drug_events.json"

    if jsonl_path.exists():
        records = parse_faers_jsonl(jsonl_path)
        logger.info("faers_parsed_jsonl", records=len(records))
    elif json_path.exists():
        records = parse_faers_json(json_path)
        logger.info("faers_parsed_json", records=len(records))
    else:
        logger.warning("faers_no_data_found", raw_dir=str(raw_dir))
        # Create empty output
        pd.DataFrame().to_parquet(processed_dir / "faers_drug_events.parquet", index=False)
        return

    # Extract drug-event pairs
    drug_events = extract_drug_events(records)
    logger.info("faers_drug_events_extracted", count=len(drug_events))

    # Save processed data
    drug_events.to_parquet(processed_dir / "faers_drug_events.parquet", index=False)

    # Compute and save statistics
    stats = compute_faers_statistics(drug_events)
    stats["total_records"] = len(records)
    with open(processed_dir / "faers_statistics.json", "w") as f:
        json.dump(stats, f, indent=2)

    logger.info("faers_processing_complete",
                 total_records=len(records),
                 drug_events=len(drug_events),
                 output_dir=str(processed_dir))


def main() -> None:
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data/raw/faers")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./prototype/data/processed/faers")

    print("⚙️  Processing FAERS data...")
    process_faers_data(raw_dir, processed_dir)
    print(f"\nFAERS processing complete. Output: {processed_dir}")


if __name__ == "__main__":
    main()

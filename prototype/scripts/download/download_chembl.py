#!/usr/bin/env python3
"""
Copy ChEMBL data from the pre-downloaded /root/ directory to the raw data directory.
The ChEMBL data was pre-fetched as:
  - /root/chembl_indications.csv (50K lines)
  - /root/chembl_mechanisms.csv (7K lines)
"""
import shutil
from pathlib import Path

import structlog

logger = structlog.get_logger()

SOURCES = [
    "/root/chembl_indications.csv",
    "/root/chembl_mechanisms.csv",
]


def copy_chembl_data(raw_dir: Path) -> None:
    """Copy pre-downloaded ChEMBL CSVs to raw/chembl/."""
    raw_dir.mkdir(parents=True, exist_ok=True)

    for src_path in SOURCES:
        src = Path(src_path)
        if not src.exists():
            logger.warning("chembl_source_missing", path=src_path)
            print(f"⚠️  Source not found: {src_path}")
            continue

        dst = raw_dir / src.name
        shutil.copy2(src, dst)
        logger.info("chembl_copied", source=str(src), dest=str(dst))
        print(f"  ✓ {src.name} -> {dst}")

    # Also create a small molecules file from the indications CSV (unique drug_ids + names)
    import pandas as pd

    ind_path = raw_dir / "chembl_indications.csv"
    if ind_path.exists():
        df = pd.read_csv(ind_path)
        # Extract unique drug names
        if "drug_name" in df.columns and "drug_id" in df.columns:
            drugs = df[["drug_id", "drug_name"]].drop_duplicates()
            drugs.to_csv(raw_dir / "chembl_molecules.csv", index=False)
            logger.info("chembl_molecules_created", count=len(drugs))

        # Extract unique targets
        if "target_name" in df.columns and "target_id" in df.columns:
            targets = df[["target_id", "target_name"]].drop_duplicates()
            targets.to_csv(raw_dir / "chembl_targets.csv", index=False)
            logger.info("chembl_targets_created", count=len(targets))

    logger.info("chembl_download_complete", path=str(raw_dir))


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    raw_dir = data_dir / "raw" / "chembl"

    print("📥 Copying ChEMBL data...")
    copy_chembl_data(raw_dir)
    print(f"\nChEMBL data ready at {raw_dir}")


if __name__ == "__main__":
    main()

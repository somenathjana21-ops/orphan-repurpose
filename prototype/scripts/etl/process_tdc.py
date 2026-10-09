#!/usr/bin/env python3
"""
Process TDC (Therapeutics Data Commons) data.

TDC datasets require GPU for deep learning models. This script processes
the downloaded TDC CSV files into parquet format for easier access.

Note: TDC requires manual download or pip install tdc.
The TDC package is at https://github.com/mims-harvard/TDC
"""
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()

# TDC ADMET dataset files we expect
TDC_ADMET_FILES = [
    "caco2_wang",
    "hia_hou",
    "cyp2c9_veith",
    "cyp2d6_veith",
    "cyp3a4_veith",
    "cyp2c9_substrate",
    "cyp2d6_substrate",
    "cyp3a4_substrate",
    "half_life_obach",
    "cl_hepatocyte",
    "cl_microsome",
    "dili",
    "pgp_broccatelli",
    "bioavailability_ma",
    "lipophilicity_astrazeneca",
    "solubility_aqsoldb",
    "bbb_martins",
    "ppbr_az",
    "vdss_lombardo",
    "cyp1a2_veith",
    "cyp2b6_veith",
    "cyp2c19_veith",
]


def process_tdc_data(raw_dir: Path, processed_dir: Path) -> None:
    """Process TDC CSV files to parquet."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    found_files = []
    missing_files = []

    for dataset in TDC_ADMET_FILES:
        csv_path = raw_dir / f"{dataset}.csv"
        parquet_path = processed_dir / f"{dataset}.parquet"

        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                df.to_parquet(parquet_path, index=False)
                found_files.append({"dataset": dataset, "rows": len(df), "columns": list(df.columns)})
                logger.info("tdc_processed", dataset=dataset, rows=len(df))
            except Exception as e:
                logger.warning("tdc_process_error", dataset=dataset, error=str(e))
                missing_files.append({"dataset": dataset, "error": str(e)})
        else:
            missing_files.append({"dataset": dataset, "error": "file not found"})

    # Save processing summary
    import json
    summary = {
        "total_expected": len(TDC_ADMET_FILES),
        "processed": len(found_files),
        "missing": len(missing_files),
        "datasets": found_files,
        "missing_datasets": missing_files,
    }
    with open(processed_dir / "tdc_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("tdc_processing_complete",
                 processed=len(found_files),
                 missing=len(missing_files),
                 output_dir=str(processed_dir))


def main() -> None:
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data/raw/tdc")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./prototype/data/processed/tdc")

    print("⚙️  Processing TDC data...")
    print(f"  Note: TDC requires GPU for deep learning models.")
    print(f"  TDC package: pip install tdc")
    process_tdc_data(raw_dir, processed_dir)
    print(f"\nTDC processing complete. Output: {processed_dir}")


if __name__ == "__main__":
    main()

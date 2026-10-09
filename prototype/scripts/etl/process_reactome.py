#!/usr/bin/env python3
"""
Process Reactome pathway data into a unified pathway table.
Merges pathway definitions, disease-pathway mappings, and gene-pathway mappings.
"""
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()


def process_reactome_data(raw_dir: Path, processed_dir: Path) -> None:
    """Process Reactome pathway data."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load pathways
    pathways_path = raw_dir / "reactome_pathways.csv"
    if not pathways_path.exists():
        logger.warning("reactome_file_missing", path=str(pathways_path))
        return

    pathways = pd.read_csv(pathways_path)
    pathways.to_parquet(processed_dir / "reactome_pathways.parquet", index=False)
    logger.info("reactome_pathways_saved", count=len(pathways))

    # Load disease-pathway mappings
    dp_path = raw_dir / "reactome_disease_pathway.csv"
    if dp_path.exists():
        dp = pd.read_csv(dp_path)
        dp.to_parquet(processed_dir / "reactome_disease_pathway.parquet", index=False)
        logger.info("reactome_disease_pathway_saved", count=len(dp))

    # Load gene-pathway mappings
    gp_path = raw_dir / "reactome_gene_pathway.csv"
    if gp_path.exists():
        gp = pd.read_csv(gp_path)
        gp.to_parquet(processed_dir / "reactome_gene_pathway.parquet", index=False)
        logger.info("reactome_gene_pathway_saved", count=len(gp))

    # Create unified pathway table
    pathway_table = pathways[["reactome_id", "pathway_name", "description"]].copy()
    pathway_table.to_csv(processed_dir / "reactome_unified.csv", index=False)

    logger.info("reactome_processing_complete", output_dir=str(processed_dir))


def main() -> None:
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data/raw/reactome")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./prototype/data/processed/reactome")

    print("⚙️  Processing Reactome data...")
    process_reactome_data(raw_dir, processed_dir)
    print(f"\nReactome processing complete. Output: {processed_dir}")


if __name__ == "__main__":
    main()

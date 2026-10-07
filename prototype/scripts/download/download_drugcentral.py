#!/usr/bin/env python3
"""
Download DrugCentral data.
Source: https://drugcentral.org/download
"""
import os
import requests
import gzip
import shutil
from pathlib import Path
from tqdm import tqdm
import structlog

logger = structlog.get_logger()

DRUG_CENTRAL_URLS = {
    "structures": "https://drugcentral.org/download/structures.tsv.gz",
    "synonyms": "https://drugcentral.org/download/synonyms.tsv.gz",
    "indications": "https://drugcentral.org/download/indications.tsv.gz",
    "contraindications": "https://drugcentral.org/download/contraindications.tsv.gz",
    "pharmacologic_class": "https://drugcentral.org/download/pharmacologic_class.tsv.gz",
    "targets": "https://drugcentral.org/download/targets.tsv.gz",
    "drug_target": "https://drugcentral.org/download/drug_target.tsv.gz",
    "omop": "https://drugcentral.org/download/omop.tsv.gz",
}


def download_file(url: str, dest: Path, chunk_size: int = 8192):
    """Download file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    
    with open(dest, 'wb') as f, tqdm(
        desc=dest.name,
        total=total,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))


def download_drugcentral(data_dir: Path):
    """Download all DrugCentral datasets."""
    raw_dir = data_dir / "raw" / "drugcentral"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    for name, url in DRUG_CENTRAL_URLS.items():
        gz_path = raw_dir / f"{name}.tsv.gz"
        tsv_path = raw_dir / f"{name}.tsv"
        
        if tsv_path.exists():
            logger.info("file_exists_skipping", file=str(tsv_path))
            continue
        
        logger.info("downloading", name=name, url=url)
        try:
            download_file(url, gz_path)
            
            # Extract gzip
            logger.info("extracting", file=str(gz_path))
            with gzip.open(gz_path, 'rb') as f_in:
                with open(tsv_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove gz
            gz_path.unlink()
            
            logger.info("downloaded_and_extracted", name=name, path=str(tsv_path))
        except Exception as e:
            logger.error("download_failed", name=name, error=str(e))
            raise


if __name__ == "__main__":
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    download_drugcentral(data_dir)
#!/usr/bin/env python3
"""
Download Orphanet data.
Source: https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_rare_diseases.zip
"""
import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm
import structlog

logger = structlog.get_logger()

ORPHANET_URL = "https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_rare_diseases.zip"
ORPHANET_ENZYMES_URL = "https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_enzymes.zip"
ORPHANET_GENES_URL = "https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_genes.zip"
ORPHANET_HPO_URL = "https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_HPO.zip"
ORPHANET_LINEARIZATION_URL = "https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_linearization.zip"


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


def download_orpha_data(data_dir: Path):
    """Download all Orphanet datasets."""
    raw_dir = data_dir / "raw" / "orpha"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    urls = {
        "rare_diseases": ORPHANET_URL,
        "enzymes": ORPHANET_ENZYMES_URL,
        "genes": ORPHANET_GENES_URL,
        "hpo": ORPHANET_HPO_URL,
        "linearization": ORPHANET_LINEARIZATION_URL,
    }
    
    for name, url in urls.items():
        zip_path = raw_dir / f"{name}.zip"
        if zip_path.exists():
            logger.info("file_exists_skipping", file=str(zip_path))
            continue
        
        logger.info("downloading", name=name, url=url)
        try:
            download_file(url, zip_path)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(raw_dir / name)
            
            logger.info("downloaded_and_extracted", name=name, path=str(raw_dir / name))
        except Exception as e:
            logger.error("download_failed", name=name, error=str(e))
            raise


if __name__ == "__main__":
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    download_orpha_data(data_dir)
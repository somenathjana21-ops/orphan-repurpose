#!/usr/bin/env python3
"""
Download Orphanet data.
Source: https://www.orphadata.com/data/xml/
"""
import os
import requests
from pathlib import Path
import structlog
from tqdm import tqdm

logger = structlog.get_logger()

ORPHADATA_BASE = "https://www.orphadata.com/data/xml/"

ORPHANET_FILES = {
    "rare_diseases": "en_product4.xml",
    "genes": "en_product6.xml",
    "hpo": "en_product9_ages.xml",
    "linearization": "en_product10.xml",
    # enzymes file not found in orphadata; we'll skip for now
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

def download_orpha_data(data_dir: Path):
    """Download all Orphanet datasets."""
    raw_dir = data_dir / "raw" / "orpha"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for name, filename in ORPHANET_FILES.items():
        url = ORPHADATA_BASE + filename
        dest_path = raw_dir / filename
        if dest_path.exists():
            logger.info("file_exists_skipping", file=str(dest_path))
            continue
        logger.info("downloading", name=name, url=url)
        try:
            download_file(url, dest_path)
            logger.info("downloaded", name=name, path=str(dest_path))
        except Exception as e:
            logger.error("download_failed", name=name, error=str(e))
            raise

if __name__ == "__main__":
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    download_orpha_data(data_dir)

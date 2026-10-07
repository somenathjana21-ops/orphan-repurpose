#!/usr/bin/env python3
"""
Download TDC data using the TDC Python package.
"""
import os
from pathlib import Path
import structlog
from tqdm import tqdm

logger = structlog.get_logger()


def download_tdc_data(data_dir: Path):
    """Download TDC benchmark datasets using the TDC package."""
    raw_dir = data_dir / "raw" / "tdc"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from tdc import BenchmarkGroup
        from tdc.utils import retrieve_benchmark_names
        
        # Download ADMET benchmark group
        logger.info("downloading_tdc_admet_group")
        group = BenchmarkGroup(name='ADMET_Group', path=str(raw_dir))
        
        # This will download all 22 ADMET datasets
        dataset_names = group.dataset_names
        logger.info("tdc_datasets_available", count=len(dataset_names), datasets=dataset_names)
        
        # Also get the clinical trial outcome benchmark
        logger.info("downloading_tdc_trial_outcome")
        from tdc.multi_pred import TrialOutcome
        trial_outcome = TrialOutcome(name='TOP', path=str(raw_dir))
        
        logger.info("tdc_download_complete", path=str(raw_dir))
        
    except ImportError:
        logger.warning("tdc_not_installed", message="Run: pip install tdc")
        # Create placeholder files for development
        for dataset in ['caco2_wang', 'hia_hou', 'cyp2c9_veith', 'cyp2d6_veith', 'cyp3a4_veith',
                        'cyp2c9_substrate', 'cyp2d6_substrate', 'cyp3a4_substrate',
                        'half_life_obach', 'cl_hepatocyte', 'cl_microsome', 'dili',
                        'pgp_broccatelli', 'bioavailability_ma', 'lipophilicity_astrazeneca',
                        'solubility_aqsoldb', 'bbb_martins', 'ppbr_az', 'vdss_lombardo',
                        'cyp1a2_veith', 'cyp2b6_veith', 'cyp2c19_veith']:
            (raw_dir / f"{dataset}.csv").touch()
        logger.info("created_placeholder_tdc_files")
    except Exception as e:
        logger.error("tdc_download_failed", error=str(e))
        raise


if __name__ == "__main__":
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    download_tdc_data(data_dir)
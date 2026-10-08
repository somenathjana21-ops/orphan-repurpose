#!/usr/bin/env python3
"""
Process DrugCentral TSV data to Parquet.
Parses: structures, synonyms, indications, contraindications, pharmacologic_class, targets, drug_target, omop
"""
import pandas as pd
from pathlib import Path
import structlog
from tqdm import tqdm

logger = structlog.get_logger()


def parse_drugcentral_structures(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral structures (SMILES, InChI, etc.)."""
    logger.info("parsing_drugcentral_structures", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    
    # Keep relevant columns
    cols = ['struct_id', 'smiles', 'inchi', 'inchikey', 'cas', 'molecular_weight', 
            'xlogp', 'tpsa', 'rotatable_bonds', 'hba', 'hbd', 'charge']
    available_cols = [c for c in cols if c in df.columns]
    df = df[available_cols].copy()
    
    # Filter to FDA-approved small molecules
    # This will be done later after merging with approval data
    
    logger.info("parsed_structures", count=len(df), columns=list(df.columns))
    return df


def parse_drugcentral_indications(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral indications."""
    logger.info("parsing_drugcentral_indications", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    
    # Columns: struct_id, umls_cui, sme_id, indication_type, max_phase_for_ind, 
    # approval_status, approval_year, source
    logger.info("parsed_indications", count=len(df), columns=list(df.columns))
    return df


def parse_drugcentral_contraindications(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral contraindications."""
    logger.info("parsing_drugcentral_contraindications", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    logger.info("parsed_contraindications", count=len(df))
    return df


def parse_drugcentral_pharmacologic_class(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral pharmacologic class (MoA)."""
    logger.info("parsing_drugcentral_moa", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    # Columns: struct_id, class_code, class_name, source
    logger.info("parsed_moa", count=len(df))
    return df


def parse_drugcentral_targets(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral targets."""
    logger.info("parsing_drugcentral_targets", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    # Columns: target_id, target_name, gene, uniprot, organism, target_class
    logger.info("parsed_targets", count=len(df))
    return df


def parse_drugcentral_drug_target(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral drug-target interactions."""
    logger.info("parsing_drugcentral_drug_target", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    # Columns: struct_id, target_id, action_type, action_comment, selectivity_comment,
    # binding_db_id, binding_value, binding_unit, binding_type, ph, temp, source
    logger.info("parsed_drug_target", count=len(df))
    return df


def parse_drugcentral_omop(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral OMOP mappings."""
    logger.info("parsing_drugcentral_omop", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    # Columns: struct_id, concept_id, concept_name, domain_id, vocabulary_id, concept_class_id, standard_concept
    logger.info("parsed_omop", count=len(df))
    return df


def parse_drugcentral_synonyms(tsv_path: Path) -> pd.DataFrame:
    """Parse DrugCentral synonyms."""
    logger.info("parsing_drugcentral_synonyms", path=str(tsv_path))
    
    df = pd.read_csv(tsv_path, sep='\t', low_memory=False)
    # Columns: struct_id, synonym, synonym_type
    logger.info("parsed_synonyms", count=len(df))
    return df


def process_drugcentral_data(raw_dir: Path, processed_dir: Path):
    """Main processing function for DrugCentral data."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    files = {
        'structures': 'structures.tsv',
        'synonyms': 'synonyms.tsv',
        'indications': 'indications.tsv',
        'contraindications': 'contraindications.tsv',
        'pharmacologic_class': 'pharmacologic_class.tsv',
        'targets': 'targets.tsv',
        'drug_target': 'drug_target.tsv',
        'omop': 'omop.tsv',
    }
    
    parsed = {}
    for name, filename in files.items():
        path = raw_dir / filename
        if path.exists():
            parse_func = globals()[f'parse_drugcentral_{name}']
            parsed[name] = parse_func(path)
            parsed[name].to_parquet(processed_dir / f'drugcentral_{name}.parquet', index=False)
            logger.info(f"saved_{name}", path=str(processed_dir / f'drugcentral_{name}.parquet'))
        else:
            logger.warning("file_not_found", file=filename)
            # Create empty parquet for pipeline continuity
            pd.DataFrame().to_parquet(processed_dir / f'drugcentral_{name}.parquet', index=False)
    
    # Create filtered FDA-approved small molecules dataset
    if 'structures' in parsed and 'indications' in parsed:
        create_fda_approved_dataset(parsed, processed_dir)
    
    logger.info("drugcentral_processing_complete", output_dir=str(processed_dir))


def create_fda_approved_dataset(parsed: dict, processed_dir: Path):
    """Create dataset of FDA-approved small molecules with indications."""
    structures = parsed['structures']
    indications = parsed['indications']
    moa = parsed.get('pharmacologic_class', pd.DataFrame())
    drug_target = parsed.get('drug_target', pd.DataFrame())
    targets = parsed.get('targets', pd.DataFrame())
    
    # Filter indications to FDA-approved
    fda_indications = indications[
        (indications['approval_status'] == 'FDA') & 
        (indications['max_phase_for_ind'] >= 4)
    ].copy()
    
    # Get unique struct_ids with FDA approval
    fda_struct_ids = fda_indications['struct_id'].unique()
    
    # Filter structures
    fda_structures = structures[structures['struct_id'].isin(fda_struct_ids)].copy()
    
    # Merge MoA
    if not moa.empty:
        moa_agg = moa.groupby('struct_id')['class_name'].apply(lambda x: '; '.join(x.unique())).reset_index()
        moa_agg.columns = ['struct_id', 'moa_classes']
        fda_structures = fda_structures.merge(moa_agg, on='struct_id', how='left')
    
    # Merge targets via drug_target
    if not drug_target.empty and not targets.empty:
        dt = drug_target[drug_target['struct_id'].isin(fda_struct_ids)][['struct_id', 'target_id']].drop_duplicates()
        dt = dt.merge(targets[['target_id', 'target_name', 'gene', 'uniprot']], on='target_id', how='left')
        targets_agg = dt.groupby('struct_id').agg({
            'target_name': lambda x: '; '.join(x.dropna().unique()),
            'gene': lambda x: '; '.join(x.dropna().unique()),
            'uniprot': lambda x: '; '.join(x.dropna().unique()),
        }).reset_index()
        fda_structures = fda_structures.merge(targets_agg, on='struct_id', how='left')
    
    # Merge indications
    ind_agg = fda_indications.groupby('struct_id').agg({
        'umls_cui': lambda x: '; '.join(x.dropna().unique()),
        'indication_type': lambda x: '; '.join(x.unique()),
        'approval_year': 'min',
    }).reset_index()
    ind_agg.columns = ['struct_id', 'indication_umls', 'indication_types', 'first_approval_year']
    fda_structures = fda_structures.merge(ind_agg, on='struct_id', how='left')
    
    # Add approval status
    fda_structures['approval_status'] = 'FDA_approved'
    
    # Save
    fda_structures.to_parquet(processed_dir / 'drugcentral_fda_approved.parquet', index=False)
    logger.info("saved_fda_approved", count=len(fda_structures))
    
    return fda_structures


if __name__ == "__main__":
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data/raw/drugcentral")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/processed/drugcentral")
    process_drugcentral_data(raw_dir, processed_dir)
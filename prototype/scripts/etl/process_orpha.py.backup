#!/usr/bin/env python3
"""
Process Orphanet XML data to Parquet.
Parses: rare_diseases, genes, HPO, linearization, enzymes
"""
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import structlog
from tqdm import tqdm

logger = structlog.get_logger()


def parse_orphanet_rare_diseases(xml_path: Path) -> pd.DataFrame:
    """Parse Orphanet rare diseases XML."""
    logger.info("parsing_orphanet_diseases", path=str(xml_path))
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    diseases = []
    for association in tqdm(root.findall('.//HPODisorderAssociation'), desc="Parsing diseases"):
        disorder = association.find('Disorder')
        if disorder is None:
            continue
        orpha_code = disorder.find('OrphaCode')
        name = disorder.find('Name')
        
        if orpha_code is None or name is None:
            continue
        
        orpha_id = f"ORPHA:{orpha_code.text}"
        disease_name = name.text
        
        # Prevalence
        prevalence_elem = disorder.find('.//Prevalence/ValMoy')
        prevalence = float(prevalence_elem.text) if prevalence_elem is not None and prevalence_elem.text else None
        
        # Prevalence category
        prev_class = disorder.find('.//Prevalence/PrevalenceClass/Name')
        prevalence_category = prev_class.text if prev_class is not None else None
        
        # Inheritance
        inheritance = []
        for inh in disorder.findall('.//TypeOfInheritance/Name'):
            if inh.text:
                inheritance.append(inh.text)
        
        # Age of onset
        onset = []
        for age in disorder.findall('.//AverageAgeOfOnset/Name'):
            if age.text:
                onset.append(age.text)
        
        # Genes
        genes = []
        for gene in disorder.findall('.//GeneList/Gene'):
            hgnc_id = gene.find('HGNC_ID')
            symbol = gene.find('Symbol')
            gene_name = gene.find('Name')
            if hgnc_id is not None and symbol is not None and gene_name is not None:
                genes.append({
                    "hgnc_id": hgnc_id.text,
                    "symbol": symbol.text,
                    "name": gene_name.text,
                })
        
        # HPO terms (from the association)
        hpo_terms = []
        hpo_list = association.find('HPODisorderAssociationList')
        if hpo_list is not None:
            for hpo_assoc in hpo_list.findall('.//HPODisorderAssociation'):
                hpo_id = hpo_assoc.find('HPOId')
                hpo_term = hpo_assoc.find('HPOTerm')
                if hpo_id is not None and hpo_term is not None:
                    hpo_terms.append({
                        "id": hpo_id.text,
                        "term": hpo_term.text,
                    })
        
        diseases.append({
            "id": orpha_id,
            "name": disease_name,
            "prevalence": prevalence,
            "prevalence_category": prevalence_category,
            "inheritance": "|".join(inheritance) if inheritance else None,
            "age_of_onset": "|".join(onset) if onset else None,
            "genes": genes,
            "hpo_terms": hpo_terms,
        })
    
    logger.info("parsed_diseases", count=len(diseases))
    return pd.DataFrame(diseases)
def parse_orphanet_genes(xml_path: Path) -> pd.DataFrame:
    """Parse Orphanet genes XML for gene-disease associations."""
    logger.info("parsing_orphanet_genes", path=str(xml_path))
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    gene_disease = []
    for gene in tqdm(root.findall('.//Gene'), desc="Parsing genes"):
        hgnc = gene.find('HGNC_ID')
        symbol = gene.find('Symbol')
        gene_name = gene.find('Name')
        
        if hgnc is None or symbol is None:
            continue
        
        hgnc_id = f"HGNC:{hgnc.text}" if not hgnc.text.startswith('HGNC:') else hgnc.text
        
        for disorder in gene.findall('.//Disorder') :
            orpha_code = disorder.find('OrphaCode')
            if orpha_code is not None:
                gene_disease.append({
                    "hgnc_id": hgnc_id,
                    "symbol": symbol.text,
                    "gene_name": gene_name.text if gene_name is not None else "",
                    "orpha_id": f"ORPHA:{orpha_code.text}",
                })
    
    df = pd.DataFrame(gene_disease)
    # Ensure required columns exist even if no genes
    if df.empty:
        df = pd.DataFrame(columns=["hgnc_id", "symbol", "gene_name", "orpha_id"])
    logger.info("parsed_gene_disease", count=len(df))
    return df
def parse_orphanet_hpo(xml_path: Path) -> pd.DataFrame:
    """Parse Orphanet HPO associations."""
    logger.info("parsing_orphanet_hpo", path=str(xml_path))
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    hpo_assoc = []
    for assoc in tqdm(root.findall('.//HPODisorderAssociation'), desc="Parsing HPO"):
        orpha_code = assoc.find('OrphaCode')
        hpo_id = assoc.find('HPOId')
        hpo_term = assoc.find('HPOTerm')
        frequency = assoc.find('HPOFrequency/Name')
        
        if orpha_code is not None and hpo_id is not None:
            hpo_assoc.append({
                'orpha_id': f"ORPHA:{orpha_code.text}",
                'hpo_id': hpo_id.text,
                'hpo_term': hpo_term.text if hpo_term is not None else '',
                'frequency': frequency.text if frequency is not None else '',
            })
    
    df = pd.DataFrame(hpo_assoc)
    logger.info("parsed_hpo", count=len(df))
    return df


def parse_orphanet_linearization(xml_path: Path) -> pd.DataFrame:
    """Parse Orphanet linearization (classification hierarchy)."""
    logger.info("parsing_orphanet_linearization", path=str(xml_path))
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    linearization = []
    for node in tqdm(root.findall('.//ClassificationNode'), desc="Parsing linearization"):
        orpha_code = node.find('OrphaCode')
        name = node.find('Name')
        parent = node.find('Parent/OrphaCode')
        
        if orpha_code is not None and name is not None:
            linearization.append({
                'orpha_id': f"ORPHA:{orpha_code.text}",
                'name': name.text,
                'parent_orpha_id': f"ORPHA:{parent.text}" if parent is not None else None,
            })
    
    df = pd.DataFrame(linearization)
    logger.info("parsed_linearization", count=len(df))
    return df


def process_orpha_data(raw_dir: Path, processed_dir: Path):
    """Main processing function for Orphanet data."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find XML files
    rare_diseases_xml = list(raw_dir.glob('**/en_product4.xml'))[0] if list(raw_dir.glob('**/en_product4.xml')) else None
    genes_xml = list(raw_dir.glob('**/en_product*genes*.xml'))[0] if list(raw_dir.glob('**/en_product*genes*.xml')) else None
    hpo_xml = list(raw_dir.glob('**/en_product*hpo*.xml'))[0] if list(raw_dir.glob('**/en_product*hpo*.xml')) else None
    linearization_xml = list(raw_dir.glob('**/en_product*linearization*.xml'))[0] if list(raw_dir.glob('**/en_product*linearization*.xml')) else None
    
    # Fallback: try common names
    if rare_diseases_xml is None:
        rare_diseases_xml = raw_dir / 'rare_diseases' / 'en_product4.xml'
    if genes_xml is None:
        genes_xml = raw_dir / 'genes' / 'en_product6.xml'
    if hpo_xml is None:
        hpo_xml = raw_dir / 'hpo' / 'en_product9_ages.xml'
    if linearization_xml is None:
        linearization_xml = raw_dir / 'linearization' / 'en_product10.xml'
    
    # Process each file if exists
    if rare_diseases_xml and rare_diseases_xml.exists():
        diseases_df = parse_orphanet_rare_diseases(rare_diseases_xml)
        diseases_df.to_parquet(processed_dir / 'orpha_diseases.parquet', index=False)
        logger.info("saved_diseases_parquet", path=str(processed_dir / 'orpha_diseases.parquet'))
    
    if genes_xml and genes_xml.exists():
        gene_df = parse_orphanet_genes(genes_xml)
        gene_df.to_parquet(processed_dir / 'orpha_gene_disease.parquet', index=False)
    
    if hpo_xml and hpo_xml.exists():
        hpo_df = parse_orphanet_hpo(hpo_xml)
        hpo_df.to_parquet(processed_dir / 'orpha_hpo.parquet', index=False)
    
    if linearization_xml and linearization_xml.exists():
        lin_df = parse_orphanet_linearization(linearization_xml)
        lin_df.to_parquet(processed_dir / 'orpha_linearization.parquet', index=False)
    
    logger.info("orpha_processing_complete", output_dir=str(processed_dir))


if __name__ == "__main__":
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data/raw/orpha")
    processed_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/processed/orpha")
    process_orpha_data(raw_dir, processed_dir)
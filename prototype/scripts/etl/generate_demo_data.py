#!/usr/bin/env python3
"""
Generate demo dataset for Niemann-Pick Type C (ORPHA:635) end-to-end demo.
Creates realistic synthetic data that mirrors the structure of real Orphanet/DrugCentral data.
"""
import pandas as pd
from pathlib import Path
import structlog

logger = structlog.get_logger()


def generate_demo_data(data_dir: Path):
    """Generate demo dataset for NPC demo."""
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # Create directories
    (raw_dir / "orpha").mkdir(parents=True, exist_ok=True)
    (raw_dir / "drugcentral").mkdir(parents=True, exist_ok=True)
    (processed_dir / "orpha").mkdir(parents=True, exist_ok=True)
    (processed_dir / "drugcentral").mkdir(parents=True, exist_ok=True)
    
    # === Orphanet Diseases ===
    diseases = pd.DataFrame([
        {
            "id": "ORPHA:635",
            "name": "Niemann-Pick disease type C",
            "prevalence": 0.5,
            "prevalence_category": "1/200,000 - 1/2,000",
            "inheritance": "Autosomal recessive",
            "age_of_onset": "Infantile|Juvenile|Adult",
            "genes": [{"hgnc_id": "HGNC:7694", "symbol": "NPC1", "name": "NPC intracellular cholesterol transporter 1"},
                       {"hgnc_id": "HGNC:14133", "symbol": "NPC2", "name": "NPC intracellular cholesterol transporter 2"}],
            "hpo_terms": [{"id": "HP:0007325", "term": "Hepatosplenomegaly"},
                          {"id": "HP:0002072", "term": "Ataxia"},
                          {"id": "HP:0002015", "term": "Dysphagia"}],
        },
        {
            "id": "ORPHA:793",
            "name": "Cystic fibrosis",
            "prevalence": 3.5,
            "prevalence_category": "1/200,000 - 1/2,000",
            "inheritance": "Autosomal recessive",
            "age_of_onset": "Neonatal|Infantile|Childhood",
            "genes": [{"hgnc_id": "HGNC:2649", "symbol": "CFTR", "name": "Cystic fibrosis transmembrane conductance regulator"}],
            "hpo_terms": [{"id": "HP:0002722", "term": "Pancreatic insufficiency"}],
        },
        {
            "id": "ORPHA:98065",
            "name": "Huntington disease",
            "prevalence": 5.0,
            "prevalence_category": "1/200,000 - 1/2,000",
            "inheritance": "Autosomal dominant",
            "age_of_onset": "Adult",
            "genes": [{"hgnc_id": "HGNC:4848", "symbol": "HTT", "name": "Huntingtin"}],
            "hpo_terms": [{"id": "HP:0002072", "term": "Chorea"}],
        },
    ])
    diseases.to_parquet(processed_dir / "orpha" / "orpha_diseases.parquet", index=False)
    logger.info("generated_demo_diseases", count=len(diseases))
    
    # === Orphanet Gene-Disease ===
    gene_disease = pd.DataFrame([
        {"hgnc_id": "HGNC:7694", "symbol": "NPC1", "gene_name": "NPC intracellular cholesterol transporter 1", "orpha_id": "ORPHA:635"},
        {"hgnc_id": "HGNC:14133", "symbol": "NPC2", "gene_name": "NPC intracellular cholesterol transporter 2", "orpha_id": "ORPHA:635"},
        {"hgnc_id": "HGNC:2649", "symbol": "CFTR", "gene_name": "Cystic fibrosis transmembrane conductance regulator", "orpha_id": "ORPHA:793"},
        {"hgnc_id": "HGNC:4848", "symbol": "HTT", "gene_name": "Huntingtin", "orpha_id": "ORPHA:98065"},
    ])
    gene_disease.to_parquet(processed_dir / "orpha" / "orpha_gene_disease.parquet", index=False)
    logger.info("generated_demo_gene_disease", count=len(gene_disease))
    
    # === DrugCentral Structures ===
    structures = pd.DataFrame([
        {"struct_id": "1234", "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "inchi": "InChI=1S/C13H18O2/c1-9(2)8-11-4-6-12(7-5-11)10(3)13(14)15/h4-7,9H,8H2,1-3H3,(H,14,15)", "inchikey": "HEFNNWSXXWATRW-UHFFFAOYSA-N", "cas": "50-78-2", "molecular_weight": 206.28, "xlogp": 3.5, "tpsa": 37.3, "rotatable_bonds": 4, "hba": 2, "hbd": 1, "charge": 0},
        {"struct_id": "5678", "smiles": "CC1=CC=C(C=C1)C2=CC(=O)C3=C(C=C(C=C3O2)O)O", "inchi": "InChI=1S/C15H10O4/c16-9-6-11(18)15-12(7-9)19-10-3-1-8(2-4-10)13(17)5-14(15)1/h1-7,16-18H", "inchikey": "WUYWHIQUBZMVEB-UHFFFAOYSA-N", "cas": "520-36-5", "molecular_weight": 270.24, "xlogp": 2.5, "tpsa": 66.8, "rotatable_bonds": 1, "hba": 4, "hbd": 3, "charge": 0},
        {"struct_id": "9012", "smiles": "C1=CC=C(C=C1)C2=CC(=O)C3=C(C=C(C=C3O2)O)O", "inchi": "InChI=1S/C15H10O4/c16-9-6-11(18)15-12(7-9)19-10-3-1-8(2-4-10)13(17)5-14(15)1/h1-7,16-18H", "inchikey": "WUYWHIQUBZMVEB-UHFFFAOYSA-N", "cas": "520-36-5", "molecular_weight": 270.24, "xlogp": 2.5, "tpsa": 66.8, "rotatable_bonds": 1, "hba": 4, "hbd": 3, "charge": 0},
        {"struct_id": "3456", "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "inchi": "InChI=1S/C13H18O2/c1-9(2)8-11-4-6-12(7-5-11)10(3)13(14)15/h4-7,9H,8H2,1-3H3,(H,14,15)", "inchikey": "HEFNNWSXXWATRW-UHFFFAOYSA-N", "cas": "50-78-2", "molecular_weight": 206.28, "xlogp": 3.5, "tpsa": 37.3, "rotatable_bonds": 4, "hba": 2, "hbd": 1, "charge": 0},
        {"struct_id": "7890", "smiles": "C1=CC=C(C=C1)C2=CC(=O)C3=C(C=C(C=C3O2)O)O", "inchi": "InChI=1S/C15H10O4/c16-9-6-11(18)15-12(7-9)19-10-3-1-8(2-4-10)13(17)5-14(15)1/h1-7,16-18H", "inchikey": "WUYWHIQUBZMVEB-UHFFFAOYSA-N", "cas": "520-36-5", "molecular_weight": 270.24, "xlogp": 2.5, "tpsa": 66.8, "rotatable_bonds": 1, "hba": 4, "hbd": 3, "charge": 0},
    ])
    structures.to_parquet(processed_dir / "drugcentral" / "drugcentral_structures.parquet", index=False)
    logger.info("generated_demo_structures", count=len(structures))
    
    # === DrugCentral Indications ===
    indications = pd.DataFrame([
        {"struct_id": "1234", "umls_cui": "C0028042", "sme_id": "S001", "indication_type": "FDA", "max_phase_for_ind": 4, "approval_status": "FDA", "approval_year": 1996, "source": "DrugCentral"},
        {"struct_id": "5678", "umls_cui": "C0028042", "sme_id": "S002", "indication_type": "FDA", "max_phase_for_ind": 4, "approval_status": "FDA", "approval_year": 2003, "source": "DrugCentral"},
        {"struct_id": "9012", "umls_cui": "C0028042", "sme_id": "S003", "indication_type": "FDA", "max_phase_for_ind": 4, "approval_status": "FDA", "approval_year": 2010, "source": "DrugCentral"},
        {"struct_id": "3456", "umls_cui": "C0028042", "sme_id": "S004", "indication_type": "FDA", "max_phase_for_ind": 4, "approval_status": "FDA", "approval_year": 2015, "source": "DrugCentral"},
        {"struct_id": "7890", "umls_cui": "C0028042", "sme_id": "S005", "indication_type": "FDA", "max_phase_for_ind": 4, "approval_status": "FDA", "approval_year": 2018, "source": "DrugCentral"},
    ])
    indications.to_parquet(processed_dir / "drugcentral" / "drugcentral_indications.parquet", index=False)
    logger.info("generated_demo_indications", count=len(indications))
    
    # === DrugCentral Targets ===
    targets = pd.DataFrame([
        {"target_id": "T001", "target_name": "GBA", "gene": "GBA", "uniprot": "P04062", "organism": "Homo sapiens", "target_class": "Enzyme"},
        {"target_id": "T002", "target_name": "NPC1", "gene": "NPC1", "uniprot": "O15118", "organism": "Homo sapiens", "target_class": "Transporter"},
        {"target_id": "T003", "target_name": "NPC2", "gene": "NPC2", "uniprot": "P61916", "organism": "Homo sapiens", "target_class": "Transporter"},
        {"target_id": "T004", "target_name": "CFTR", "gene": "CFTR", "uniprot": "P13569", "organism": "Homo sapiens", "target_class": "Ion Channel"},
        {"target_id": "T005", "target_name": "HTT", "gene": "HTT", "uniprot": "P42858", "organism": "Homo sapiens", "target_class": "Unknown"},
    ])
    targets.to_parquet(processed_dir / "drugcentral" / "drugcentral_targets.parquet", index=False)
    logger.info("generated_demo_targets", count=len(targets))
    
    # === DrugCentral Drug-Target ===
    drug_target = pd.DataFrame([
        {"struct_id": "1234", "target_id": "T001", "action_type": "inhibitor", "action_comment": "Potent inhibitor", "selectivity_comment": "Selective", "binding_db_id": "B001", "binding_value": 50.0, "binding_unit": "nM", "binding_type": "Ki", "ph": 7.4, "temp": 25, "source": "DrugCentral"},
        {"struct_id": "5678", "target_id": "T002", "action_type": "modulator", "action_comment": "Allosteric modulator", "selectivity_comment": "Selective", "binding_db_id": "B002", "binding_value": 100.0, "binding_unit": "nM", "binding_type": "Kd", "ph": 7.4, "temp": 25, "source": "DrugCentral"},
        {"struct_id": "9012", "target_id": "T003", "action_type": "inhibitor", "action_comment": "Competitive inhibitor", "selectivity_comment": "Non-selective", "binding_db_id": "B003", "binding_value": 200.0, "binding_unit": "nM", "binding_type": "IC50", "ph": 7.4, "temp": 25, "source": "DrugCentral"},
        {"struct_id": "3456", "target_id": "T004", "action_type": "potentiator", "action_comment": "CFTR potentiator", "selectivity_comment": "Selective", "binding_db_id": "B004", "binding_value": 500.0, "binding_unit": "nM", "binding_type": "EC50", "ph": 7.4, "temp": 25, "source": "DrugCentral"},
        {"struct_id": "7890", "target_id": "T005", "action_type": "unknown", "action_comment": "Unknown mechanism", "selectivity_comment": "Unknown", "binding_db_id": "B005", "binding_value": 1000.0, "binding_unit": "nM", "binding_type": "Kd", "ph": 7.4, "temp": 25, "source": "DrugCentral"},
    ])
    drug_target.to_parquet(processed_dir / "drugcentral" / "drugcentral_drug_target.parquet", index=False)
    logger.info("generated_demo_drug_target", count=len(drug_target))
    
    # === DrugCentral FDA Approved ===
    fda_approved = pd.DataFrame([
        {"struct_id": "1234", "name": "Miglustat", "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "inchi": "InChI=1S/C13H18O2/c1-9(2)8-11-4-6-12(7-5-11)10(3)13(14)15/h4-7,9H,8H2,1-3H3,(H,14,15)", "inchikey": "HEFNNWSXXWATRW-UHFFFAOYSA-N", "cas": "50-78-2", "molecular_weight": 206.28, "xlogp": 3.5, "tpsa": 37.3, "rotatable_bonds": 4, "hba": 2, "hbd": 1, "charge": 0, "moa_classes": "glucosylceramide synthase inhibitor", "target_name": "GBA", "gene": "GBA", "uniprot": "P04062", "indication_umls": "C0028042", "indication_types": "FDA", "first_approval_year": 1996, "approval_status": "FDA_approved"},
        {"struct_id": "5678", "name": "Sirolimus", "smiles": "CC1=CC=C(C=C1)C2=CC(=O)C3=C(C=C(C=C3O2)O)O", "inchi": "InChI=1S/C15H10O4/c16-9-6-11(18)15-12(7-9)19-10-3-1-8(2-4-10)13(17)5-14(15)1/h1-7,16-18H", "inchikey": "WUYWHIQUBZMVEB-UHFFFAOYSA-N", "cas": "520-36-5", "molecular_weight": 270.24, "xlogp": 2.5, "tpsa": 66.8, "rotatable_bonds": 1, "hba": 4, "hbd": 3, "charge": 0, "moa_classes": "mTOR inhibitor", "target_name": "NPC1", "gene": "NPC1", "uniprot": "O15118", "indication_umls": "C0028042", "indication_types": "FDA", "first_approval_year": 2003, "approval_status": "FDA_approved"},
        {"struct_id": "9012", "name": "Ivacaftor", "smiles": "C1=CC=C(C=C1)C2=CC(=O)C3=C(C=C(C=C3O2)O)O", "inchi": "InChI=1S/C15H10O4/c16-9-6-11(18)15-12(7-9)19-10-3-1-8(2-4-10)13(17)5-14(15)1/h1-7,16-18H", "inchikey": "WUYWHIQUBZMVEB-UHFFFAOYSA-N", "cas": "520-36-5", "molecular_weight": 270.24, "xlogp": 2.5, "tpsa": 66.8, "rotatable_bonds": 1, "hba": 4, "hbd": 3, "charge": 0, "moa_classes": "CFTR potentiator", "target_name": "CFTR", "gene": "CFTR", "uniprot": "P13569", "indication_umls": "C0028042", "indication_types": "FDA", "first_approval_year": 2010, "approval_status": "FDA_approved"},
    ])
    fda_approved.to_parquet(processed_dir / "drugcentral" / "drugcentral_fda_approved.parquet", index=False)
    logger.info("generated_demo_fda_approved", count=len(fda_approved))
    
    # === DrugCentral Synonyms ===
    synonyms = pd.DataFrame([
        {"struct_id": "1234", "synonym": "Miglustat", "synonym_type": "INN"},
        {"struct_id": "1234", "synonym": "Zavesca", "synonym_type": "Brand"},
        {"struct_id": "5678", "synonym": "Sirolimus", "synonym_type": "INN"},
        {"struct_id": "5678", "synonym": "Rapamune", "synonym_type": "Brand"},
        {"struct_id": "9012", "synonym": "Ivacaftor", "synonym_type": "INN"},
        {"struct_id": "9012", "synonym": "Kalydeco", "synonym_type": "Brand"},
    ])
    synonyms.to_parquet(processed_dir / "drugcentral" / "drugcentral_synonyms.parquet", index=False)
    logger.info("generated_demo_synonyms", count=len(synonyms))
    
    # === DrugCentral Pharmacologic Class ===
    pharmacologic_class = pd.DataFrame([
        {"struct_id": "1234", "class_code": "C01", "class_name": "glucosylceramide synthase inhibitor", "source": "DrugCentral"},
        {"struct_id": "5678", "class_code": "C02", "class_name": "mTOR inhibitor", "source": "DrugCentral"},
        {"struct_id": "9012", "class_code": "C03", "class_name": "CFTR potentiator", "source": "DrugCentral"},
    ])
    pharmacologic_class.to_parquet(processed_dir / "drugcentral" / "drugcentral_pharmacologic_class.parquet", index=False)
    logger.info("generated_demo_pharmacologic_class", count=len(pharmacologic_class))
    
    # === DrugCentral Contraindications ===
    contraindications = pd.DataFrame([
        {"struct_id": "1234", "contraindication": "Severe hepatic impairment", "source": "DrugCentral"},
        {"struct_id": "5678", "contraindication": "Active infection", "source": "DrugCentral"},
        {"struct_id": "5678", "contraindication": "Severe hepatic impairment", "source": "DrugCentral"},
    ])
    contraindications.to_parquet(processed_dir / "drugcentral" / "drugcentral_contraindications.parquet", index=False)
    logger.info("generated_demo_contraindications", count=len(contraindications))
    
    # === DrugCentral OMOP ===
    omop = pd.DataFrame([
        {"struct_id": "1234", "concept_id": "19000001", "concept_name": "Miglustat", "domain_id": "Drug", "vocabulary_id": "RxNorm", "concept_class_id": "Ingredient", "standard_concept": "S"},
        {"struct_id": "5678", "concept_id": "19000002", "concept_name": "Sirolimus", "domain_id": "Drug", "vocabulary_id": "RxNorm", "concept_class_id": "Ingredient", "standard_concept": "S"},
        {"struct_id": "9012", "concept_id": "19000003", "concept_name": "Ivacaftor", "domain_id": "Drug", "vocabulary_id": "RxNorm", "concept_class_id": "Ingredient", "standard_concept": "S"},
    ])
    omop.to_parquet(processed_dir / "drugcentral" / "drugcentral_omop.parquet", index=False)
    logger.info("generated_demo_omop", count=len(omop))
    
    logger.info("demo_data_generation_complete", data_dir=str(data_dir))


if __name__ == "__main__":
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    generate_demo_data(data_dir)

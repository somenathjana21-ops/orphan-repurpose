#!/usr/bin/env python3
"""
Build Knowledge Graph in Kuzu from processed data.
Creates nodes and edges for all entity types.
"""
import kuzu
import pandas as pd
from pathlib import Path
import structlog
from tqdm import tqdm
import json

logger = structlog.get_logger()


NODE_TYPES = [
    "Disease",
    "Gene",
    "Pathway",
    "Drug",
    "Target",
    "MolecularStructure",
    "Indication",
    "Contraindication",
    "Publication",
    "Evidence",
    "AdverseEvent",
    "ADMETProperty",
]


EDGE_TYPES = [
    ("TREATS", "Drug", "Disease"),
    ("CONTRAINDICATES", "Drug", "Disease"),
    ("HAS_TARGET", "Drug", "Target"),
    ("PARTICIPATES_IN", "Target", "Pathway"),
    ("IMPLICATED_IN", "Pathway", "Disease"),
    ("HAS_GENE", "Disease", "Gene"),
    ("IN_PATHWAY", "Gene", "Pathway"),
    ("HAS_STRUCTURE", "Drug", "MolecularStructure"),
    ("SUPPORTS", "Publication", "Drug"),
    ("SUPPORTS", "Publication", "Disease"),
    ("SUPPORTS", "Publication", "Target"),
    ("CAUSES_AE", "Drug", "AdverseEvent"),
    ("HAS_ADMET", "Drug", "ADMETProperty"),
]


def create_kuzu_schema(conn: kuzu.Connection):
    """Create KG schema in Kuzu."""
    logger.info("creating_kuzu_schema")

    # Node tables
    node_schemas = {
        "Disease": """
            CREATE NODE TABLE Disease (
                id STRING, name STRING, prevalence DOUBLE, prevalence_category STRING,
                inheritance STRING[], age_of_onset STRING[], phenotypes STRING[],
                existing_treatments STRING[], unmet_need_score DOUBLE,
                description STRING, synonyms STRING[], omim_ids STRING[],
                mondo_id STRING, icar_id STRING,
                PRIMARY KEY (id)
            )
        """,
        "Gene": """
            CREATE NODE TABLE Gene (
                id STRING, symbol STRING, name STRING, uniprot_id STRING,
                ensembl_id STRING, hgnc_id STRING,
                PRIMARY KEY (id)
            )
        """,
        "Pathway": """
            CREATE NODE TABLE Pathway (
                id STRING, name STRING, species STRING, url STRING,
                reactome_id STRING,
                PRIMARY KEY (id)
            )
        """,
        "Drug": """
            CREATE NODE TABLE Drug (
                id STRING, name STRING, smiles STRING, inchi STRING, inchikey STRING,
                molecular_weight DOUBLE, xlogp DOUBLE, tpsa DOUBLE,
                rotatable_bonds INT, hba INT, hbd INT, charge INT,
                moa_classes STRING, target_names STRING, target_genes STRING, target_uniprots STRING,
                indication_umls STRING, indication_types STRING, first_approval_year INT,
                approval_status STRING, cas STRING,
                PRIMARY KEY (id)
            )
        """,
        "Target": """
            CREATE NODE TABLE Target (
                id STRING, name STRING, gene STRING, uniprot STRING,
                organism STRING, target_class STRING,
                PRIMARY KEY (id)
            )
        """,
        "MolecularStructure": """
            CREATE NODE TABLE MolecularStructure (
                id STRING, smiles STRING, inchi STRING, inchikey STRING,
                molecular_weight DOUBLE, formula STRING,
                PRIMARY KEY (id)
            )
        """,
        "Indication": """
            CREATE NODE TABLE Indication (
                id STRING, drug_id STRING, disease_id STRING, umls_cui STRING,
                indication_type STRING, max_phase INT, approval_status STRING,
                approval_year INT, source STRING,
                PRIMARY KEY (id)
            )
        """,
        "Contraindication": """
            CREATE NODE TABLE Contraindication (
                id STRING, drug_id STRING, disease_id STRING, umls_cui STRING,
                source STRING,
                PRIMARY KEY (id)
            )
        """,
        "Publication": """
            CREATE NODE TABLE Publication (
                id STRING, title STRING, abstract STRING, year INT,
                mesh_terms STRING[], pmid STRING,
                PRIMARY KEY (id)
            )
        """,
        "Evidence": """
            CREATE NODE TABLE Evidence (
                id STRING, publication_id STRING, subject_type STRING, subject_id STRING,
                predicate STRING, confidence DOUBLE,
                PRIMARY KEY (id)
            )
        """,
        "AdverseEvent": """
            CREATE NODE TABLE AdverseEvent (
                id STRING, meddra_pt STRING, meddra_soc STRING,
                PRIMARY KEY (id)
            )
        """,
        "ADMETProperty": """
            CREATE NODE TABLE ADMETProperty (
                id STRING, drug_id STRING, endpoint STRING, value DOUBLE,
                unit STRING, model_version STRING,
                PRIMARY KEY (id)
            )
        """,
    }

    for name, schema in node_schemas.items():
        try:
            conn.execute(schema)
            logger.info("created_node_table", table=name)
        except Exception as e:
            logger.warning("node_table_exists_or_failed", table=name, error=str(e))

    # Relationship tables
    rel_schemas = {
        "TREATS": "CREATE REL TABLE TREATS (FROM Drug TO Disease, evidence STRING, confidence DOUBLE)",
        "CONTRAINDICATES": "CREATE REL TABLE CONTRAINDICATES (FROM Drug TO Disease, source STRING)",
        "HAS_TARGET": "CREATE REL TABLE HAS_TARGET (FROM Drug TO Target, action_type STRING, binding_value DOUBLE, binding_unit STRING, source STRING)",
        "PARTICIPATES_IN": "CREATE REL TABLE PARTICIPATES_IN (FROM Target TO Pathway, source STRING)",
        "IMPLICATED_IN": "CREATE REL TABLE IMPLICATED_IN (FROM Pathway TO Disease, evidence_score DOUBLE, source STRING)",
        "HAS_GENE": "CREATE REL TABLE HAS_GENE (FROM Disease TO Gene, source STRING)",
        "IN_PATHWAY": "CREATE REL TABLE IN_PATHWAY (FROM Gene TO Pathway, source STRING)",
        "HAS_STRUCTURE": "CREATE REL TABLE HAS_STRUCTURE (FROM Drug TO MolecularStructure)",
        "SUPPORTS": "CREATE REL TABLE SUPPORTS (FROM Publication TO Drug, confidence DOUBLE)",
        "CAUSES_AE": "CREATE REL TABLE CAUSES_AE (FROM Drug TO AdverseEvent, ror DOUBLE, prr DOUBLE, bcpnn DOUBLE, n_reports INT)",
        "HAS_ADMET": "CREATE REL TABLE HAS_ADMET (FROM Drug TO ADMETProperty, predicted_value DOUBLE)",
    }

    for name, schema in rel_schemas.items():
        try:
            conn.execute(schema)
            logger.info("created_rel_table", table=name)
        except Exception as e:
            logger.warning("rel_table_exists_or_failed", table=name, error=str(e))


def load_diseases(conn: kuzu.Connection, processed_dir: Path):
    """Load diseases from Orphanet and DrugCentral."""
    # From Orphanet rare diseases
    path = processed_dir / "orpha" / "orpha_diseases.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        logger.info("loading_diseases_from_orpha", count=len(df))
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading diseases"):
            query = """
            MERGE (d:Disease {id: $id})
            ON CREATE SET d.name = $name, d.prevalence = $prevalence,
                      d.prevalence_category = $prevalence_category, d.inheritance = $inheritance,
                      d.age_of_onset = $age_of_onset, d.phenotypes = $phenotypes,
                      d.existing_treatments = $existing_treatments, d.unmet_need_score = $unmet_need_score
            """
            conn.execute(query, {
                "id": row["id"],
                "name": row["name"],
                "prevalence": float(row.get("prevalence")) if pd.notna(row.get("prevalence")) else None,
                "prevalence_category": row.get("prevalence_category") if pd.notna(row.get("prevalence_category")) else None,
                "inheritance": list(row.get("inheritance", [])),
                "age_of_onset": list(row.get("age_of_onset", [])),
                "phenotypes": list(row.get("phenotypes", [])),
                "existing_treatments": list(row.get("existing_treatments", [])),
                "unmet_need_score": float(row.get("unmet_need_score")) if pd.notna(row.get("unmet_need_score")) else None,
            })
    
    # From DrugCentral (FDA approved) - create disease nodes from indications
    indications_path = processed_dir / "drugcentral" / "drugcentral_indications.parquet"
    if indications_path.exists():
        df = pd.read_parquet(indications_path)
        logger.info("loading_diseases_from_drugcentral_indications", count=len(df))
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading diseases from DrugCentral indications"):
            # Use UMLS CUI as disease ID if available
            if pd.notna(row.get("umls_cui")):
                disease_id = f"UMLS:{row["umls_cui"]}"
                disease_name = str(row["umls_cui"])  # In reality, we'd map UMLS to name
            else:
                # Fallback to struct_id based ID
                disease_id = f"DRUGCENTRAL:{row["struct_id"]}"
                disease_name = f"DrugCentral compound {row["struct_id"]}"
            query = """
            MERGE (d:Disease {id: $id})
            ON CREATE SET d.name = $name
            """
            conn.execute(query, {
                "id": disease_id,
                "name": disease_name,
            })
def load_genes(conn: kuzu.Connection, processed_dir: Path):
    """Load genes from Orphanet and DrugCentral."""
    # From Orphanet gene-disease
    path = processed_dir / "orpha" / "orpha_gene_disease.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        logger.info("loading_genes_from_orpha", count=len(df))

        # Create unique genes
        genes = df[['hgnc_id', 'symbol', 'gene_name']].drop_duplicates()
        for _, row in tqdm(genes.iterrows(), total=len(genes), desc="Loading genes"):
            query = """
            MERGE (g:Gene {id: $id})
            ON CREATE SET g.symbol = $symbol, g.name = $name, g.hgnc_id = $id
            """
            conn.execute(query, {
                "id": row["hgnc_id"],
                "symbol": row["symbol"],
                "name": row["gene_name"],
            })


def load_drugs(conn: kuzu.Connection, processed_dir: Path):
    """Load FDA-approved drugs from DrugCentral."""
    path = processed_dir / "drugcentral" / "drugcentral_fda_approved.parquet"
    if not path.exists():
        logger.warning("fda_approved_parquet_not_found", path=str(path))
        return

    df = pd.read_parquet(path)
    logger.info("loading_drugs", count=len(df))

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading drugs"):
        query = """
        MERGE (d:Drug {id: $id})
        ON CREATE SET d.name = $name, d.smiles = $smiles, d.inchi = $inchi, d.inchikey = $inchikey,
                      d.molecular_weight = $mw, d.xlogp = $xlogp, d.tpsa = $tpsa,
                      d.rotatable_bonds = $rb, d.hba = $hba, d.hbd = $hbd, d.charge = $charge,
                      d.moa_classes = $moa, d.target_names = $tnames, d.target_genes = $tgenes, d.target_uniprots = $tuniprots,
                      d.indication_umls = $iumls, d.indication_types = $itypes, d.first_approval_year = $fyear,
                      d.approval_status = $astatus, d.cas = $cas
        """
        conn.execute(query, {
            "id": f"drugcentral:{row['struct_id']}",
            "name": row.get("name", ""),  # Will be filled from synonyms
            "smiles": row.get("smiles"),
            "inchi": row.get("inchi"),
            "inchikey": row.get("inchikey"),
            "mw": row.get("molecular_weight"),
            "xlogp": row.get("xlogp"),
            "tpsa": row.get("tpsa"),
            "rb": row.get("rotatable_bonds"),
            "hba": row.get("hba"),
            "hbd": row.get("hbd"),
            "charge": row.get("charge"),
            "moa": row.get("moa_classes", ""),
            "tnames": row.get("target_name", ""),
            "tgenes": row.get("gene", ""),
            "tuniprots": row.get("uniprot", ""),
            "iumls": row.get("indication_umls", ""),
            "itypes": row.get("indication_types", ""),
            "fyear": int(row["first_approval_year"]) if pd.notna(row.get("first_approval_year")) else None,
            "astatus": row.get("approval_status", "FDA_approved"),
            "cas": row.get("cas"),
        })


def load_targets(conn: kuzu.Connection, processed_dir: Path):
    """Load targets from DrugCentral."""
    path = processed_dir / "drugcentral" / "drugcentral_targets.parquet"
    if not path.exists():
        logger.warning("targets_parquet_not_found", path=str(path))
        return
    df = pd.read_parquet(path)
    logger.info("loading_targets", count=len(df))
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading targets"):
        query = """
        MERGE (t:Target {id: $id})
        ON CREATE SET t.name = $name, t.gene = $gene, t.uniprot = $uniprot
        """
        conn.execute(query, {
            "id": f"target:{row['target_id']}",
            "name": row.get("target_name", ""),
            "gene": row.get("gene", ""),
            "uniprot": row.get("uniprot", ""),
        })


def load_pathways(conn: kuzu.Connection, processed_dir: Path):
    """Load pathways (placeholder)."""
    # For now, skip as we don't have pathway data
    pass


def load_relationships(conn: kuzu.Connection, processed_dir: Path):
    """Load relationships between entities."""
    logger.info("loading_relationships")

    # Disease-Gene (HAS_GENE)
    path = processed_dir / "orpha" / "orpha_gene_disease.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading HAS_GENE"):
            query = """
            MATCH (d:Disease {id: $disease_id}), (g:Gene {id: $gene_id})
            CREATE (d)-[:HAS_GENE {source: "Orphanet"}]->(g)
            """
            conn.execute(query, {
                "disease_id": row["orpha_id"],
                "gene_id": row["hgnc_id"],
            })

    # Drug-Target (HAS_TARGET) - from DrugCentral drug_target
    path = processed_dir / "drugcentral" / "drugcentral_drug_target.parquet"
    if path.exists():
        df = pd.read_parquet(path)
        # Filter to FDA-approved drugs
        fda_drugs = set()  # Would need to load from fda_approved
        # For now, load all
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading HAS_TARGET"):
            query = """
            MATCH (d:Drug {id: $drug_id}), (t:Target {id: $target_id})
            CREATE (d)-[:HAS_TARGET {
                action_type: $action_type,
                binding_value: $binding_value,
                binding_unit: $binding_unit,
                source: "DrugCentral"
            }]->(t)
            """
            conn.execute(query, {
                "drug_id": f"drugcentral:{row['struct_id']}",
                "target_id": f"target:{row['target_id']}",
                "action_type": row.get("action_type"),
                "binding_value": row.get("binding_value"),
                "binding_unit": row.get("binding_unit"),
            })

    # Target-Pathway (PARTICIPATES_IN) - would need Reactome data
    # Pathway-Disease (IMPLICATED_IN) - would need pathway-disease mapping


def build_kg(processed_dir: Path, kuzu_db_path: Path):
    """Main function to build KG."""
    kuzu_db_path.mkdir(parents=True, exist_ok=True)

    db = kuzu.Database(str(kuzu_db_path / "kuzu.db"))
    conn = kuzu.Connection(db)

    try:
        # Create schema
        create_kuzu_schema(conn)

        # Load nodes
        load_diseases(conn, processed_dir)
        load_genes(conn, processed_dir)
        load_drugs(conn, processed_dir)
        load_targets(conn, processed_dir)
        load_pathways(conn, processed_dir)

        # Load relationships
        load_relationships(conn, processed_dir)

        # Verify
        result = conn.execute("MATCH (n) RETURN labels(n) as label, count(*) as count")
        logger.info("kg_node_counts")
        while result.has_next():
            row = result.get_next()
            logger.info("node_count", label=row[0], count=row[1])

        # Verify relationships - try to get relationship types and counts
        try:
            result = conn.execute("MATCH ()-[r]->() RETURN type(r) as rel, count(*) as count")
            logger.info("kg_edge_counts")
            while result.has_next():
                row = result.get_next()
                logger.info("edge_count", rel=row[0], count=row[1])
        except Exception as e:
            logger.warning("kg_edge_count_failed", error=str(e))

        logger.info("kg_build_complete", db_path=str(kuzu_db_path))

    finally:
        conn.close()
        db.close()


if __name__ == "__main__":
    import sys
    processed_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data/processed")
    kuzu_db_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./data/kuzu_db")
    build_kg(processed_dir, kuzu_db_path)

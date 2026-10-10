from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query

from app.services.kg_service import KGService

logger = structlog.get_logger()
router = APIRouter()

# Singleton KGService instance
_kg_service: KGService | None = None


def _get_kg_service() -> KGService:
    """Get or create the KGService singleton."""
    global _kg_service
    if _kg_service is None:
        _kg_service = KGService()
    return _kg_service


def _safe_get(node: dict, key: str, default=None):
    """Safely get a value from a Kuzu node dict, handling Kuzu's internal fields."""
    if key.startswith("_"):
        return default
    val = node.get(key)
    # Kuzu returns None for NULL values
    return val if val is not None else default


@router.get("/search")
async def search_kg(
    query: str | None = Query(None, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search across Drug, Disease, Target, Gene nodes by name or id."""
    try:
        kg = _get_kg_service()
        results = []
        seen_ids = set()

        if query:
            query.lower()

            # Search Drugs
            drug_results = kg.execute(
                "MATCH (d:Drug) WHERE toLower(d.name) CONTAINS toLower($query) "
                "OR toLower(d.id) CONTAINS toLower($query) "
                "RETURN d.id as id, d.name as name, labels(d) as labels, "
                "d.approval_status as approval_status, d.moa_classes as moa_classes "
                "LIMIT $limit",
                {"query": query, "limit": limit},
            )
            for row in drug_results:
                rid = f"drug:{row['id']}"
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    results.append(
                        {
                            "id": row["id"],
                            "type": "Drug",
                            "name": row["name"],
                            "properties": {
                                "approval_status": row.get("approval_status"),
                                "moa_classes": row.get("moa_classes"),
                            },
                        }
                    )

            # Search Diseases
            disease_results = kg.execute(
                "MATCH (d:Disease) WHERE toLower(d.name) CONTAINS toLower($query) "
                "OR toLower(d.id) CONTAINS toLower($query) "
                "RETURN d.id as id, d.name as name, "
                "d.prevalence as prevalence, d.unmet_need_score as unmet_need_score "
                "LIMIT $limit",
                {"query": query, "limit": limit},
            )
            for row in disease_results:
                rid = f"disease:{row['id']}"
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    results.append(
                        {
                            "id": row["id"],
                            "type": "Disease",
                            "name": row["name"],
                            "properties": {
                                "prevalence": row.get("prevalence"),
                                "unmet_need_score": row.get("unmet_need_score"),
                            },
                        }
                    )

            # Search Targets
            target_results = kg.execute(
                "MATCH (t:Target) WHERE toLower(t.name) CONTAINS toLower($query) "
                "OR toLower(t.id) CONTAINS toLower($query) "
                "OR toLower(t.gene) CONTAINS toLower($query) "
                "RETURN t.id as id, t.name as name, t.gene as gene, t.uniprot as uniprot "
                "LIMIT $limit",
                {"query": query, "limit": limit},
            )
            for row in target_results:
                rid = f"target:{row['id']}"
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    results.append(
                        {
                            "id": row["id"],
                            "type": "Target",
                            "name": row["name"],
                            "properties": {
                                "gene": row.get("gene"),
                                "uniprot": row.get("uniprot"),
                            },
                        }
                    )

            # Search Genes
            gene_results = kg.execute(
                "MATCH (g:Gene) WHERE toLower(g.symbol) CONTAINS toLower($query) "
                "OR toLower(g.name) CONTAINS toLower($query) "
                "OR toLower(g.id) CONTAINS toLower($query) "
                "RETURN g.id as id, g.symbol as symbol, g.name as name, "
                "g.uniprot_id as uniprot_id "
                "LIMIT $limit",
                {"query": query, "limit": limit},
            )
            for row in gene_results:
                rid = f"gene:{row['id']}"
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    results.append(
                        {
                            "id": row["id"],
                            "type": "Gene",
                            "name": row["symbol"] or row["name"],
                            "properties": {
                                "symbol": row.get("symbol"),
                                "name": row.get("name"),
                                "uniprot_id": row.get("uniprot_id"),
                            },
                        }
                    )
        else:
            # No query - return samples from each type
            for label, id_col, name_col in [
                ("Drug", "id", "name"),
                ("Disease", "id", "name"),
                ("Target", "id", "name"),
                ("Gene", "id", "symbol"),
            ]:
                sample = kg.execute(
                    f"MATCH (n:{label}) RETURN n.{id_col} as id, n.{name_col} as name "
                    f"ORDER BY n.{id_col} LIMIT 3",
                    {},
                )
                for row in sample:
                    rid = f"{label.lower()}:{row['id']}"
                    if rid not in seen_ids:
                        seen_ids.add(rid)
                        results.append(
                            {
                                "id": row["id"],
                                "type": label,
                                "name": row["name"],
                                "properties": {},
                            }
                        )

        return {"results": results[:limit], "total": len(results)}
    except Exception as e:
        logger.error("kg_search_failed", error=str(e))
        raise HTTPException(status_code=500, detail="KG search failed") from e


@router.get("/subgraph")
async def get_subgraph(
    drug_id: str = Query(..., description="Drug ID"),
    disease_id: str = Query(..., description="Disease ID"),
    max_depth: int = Query(3, ge=1, le=5),
):
    """Get KG subgraph connecting a drug to a disease using HAS_TARGET, TREATS, HAS_GENE edges.
    Returns nodes and edges in Cytoscape.js format.
    """
    try:
        kg = _get_kg_service()

        # Verify drug exists
        drug_check = kg.execute(
            "MATCH (d:Drug {id: $drug_id}) RETURN d.id as id",
            {"drug_id": drug_id},
        )
        if not drug_check:
            raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")

        # Verify disease exists
        disease_check = kg.execute(
            "MATCH (d:Disease {id: $disease_id}) RETURN d.id as id",
            {"disease_id": disease_id},
        )
        if not disease_check:
            raise HTTPException(status_code=404, detail=f"Disease {disease_id} not found")

        # Collect nodes and edges for Cytoscape.js format
        # Structure: {data: {id, label, type, ...properties}}
        nodes_dict: dict[str, dict[str, Any]] = {}
        edges_list: list[dict[str, Any]] = []

        def add_node(node_id: str, label: str, node_type: str, name: str, **properties):
            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "data": {
                        "id": node_id,
                        "label": label,
                        "type": node_type,
                        "name": name,
                        **properties,
                    }
                }

        def add_edge(source: str, target: str, edge_type: str, **properties):
            edge_id = f"{source}-{edge_type}-{target}"
            # Avoid duplicate edges
            for existing in edges_list:
                if (
                    existing["data"]["source"] == source
                    and existing["data"]["target"] == target
                    and existing["data"]["label"] == edge_type
                ):
                    return
            edges_list.append(
                {
                    "data": {
                        "id": edge_id,
                        "source": source,
                        "target": target,
                        "label": edge_type,
                        **properties,
                    }
                }
            )

        # 1. Direct TREATS edge: Drug -> Disease
        treats_results = kg.execute(
            "MATCH (dr:Drug {id: $drug_id})-[r:TREATS]->(d:Disease {id: $disease_id}) "
            "RETURN r.evidence as evidence, r.confidence as confidence",
            {"drug_id": drug_id, "disease_id": disease_id},
        )
        for row in treats_results:
            add_edge(
                drug_id,
                disease_id,
                "TREATS",
                evidence=row.get("evidence"),
                confidence=row.get("confidence"),
            )

        # 2. Drug -> Target via HAS_TARGET
        target_results = kg.execute(
            "MATCH (dr:Drug {id: $drug_id})-[r:HAS_TARGET]->(t:Target) "
            "RETURN t.id as target_id, t.name as target_name, t.gene as gene, "
            "t.uniprot as uniprot, t.organism as organism, t.target_class as target_class, "
            "r.action_type as action_type, r.binding_value as binding_value, "
            "r.binding_unit as binding_unit, r.source as source",
            {"drug_id": drug_id},
        )
        drug_targets = []
        for row in target_results:
            target_id = row["target_id"]
            add_node(
                target_id,
                target_id,
                "Target",
                row["target_name"],
                gene=row.get("gene"),
                uniprot=row.get("uniprot"),
                organism=row.get("organism"),
                target_class=row.get("target_class"),
                action_type=row.get("action_type"),
                binding_value=row.get("binding_value"),
                binding_unit=row.get("binding_unit"),
            )
            add_edge(
                drug_id,
                target_id,
                "HAS_TARGET",
                action_type=row.get("action_type"),
                binding_value=row.get("binding_value"),
                binding_unit=row.get("binding_unit"),
            )
            drug_targets.append(row)

        # 3. Disease -> Gene via HAS_GENE
        gene_results = kg.execute(
            "MATCH (d:Disease {id: $disease_id})-[r:HAS_GENE]->(g:Gene) "
            "RETURN g.id as gene_id, g.symbol as symbol, g.name as name, "
            "g.uniprot_id as uniprot_id, g.ensembl_id as ensembl_id, "
            "g.hgnc_id as hgnc_id, r.source as source",
            {"disease_id": disease_id},
        )
        disease_genes = []
        for row in gene_results:
            gene_id = row["gene_id"]
            add_node(
                gene_id,
                gene_id,
                "Gene",
                row["symbol"] or row["name"],
                symbol=row.get("symbol"),
                gene_name=row.get("name"),
                uniprot_id=row.get("uniprot_id"),
                ensembl_id=row.get("ensembl_id"),
                hgnc_id=row.get("hgnc_id"),
            )
            add_edge(
                disease_id,
                gene_id,
                "HAS_GENE",
                data_source=row.get("source"),
            )
            disease_genes.append(row)

        # 4. Connect Targets to Genes via gene symbol match
        # (Target.gene property matches Gene.symbol)
        target_gene_connections = []
        for t_row in drug_targets:
            target_gene = t_row.get("gene")
            if not target_gene:
                continue
            for g_row in disease_genes:
                if g_row["symbol"] == target_gene:
                    # Connect Target -> Gene (via gene symbol match)
                    add_edge(
                        t_row["target_id"],
                        g_row["gene_id"],
                        "ASSOCIATED_WITH",
                        match_type="gene_symbol",
                    )
                    target_gene_connections.append(
                        {
                            "target_id": t_row["target_id"],
                            "gene_id": g_row["gene_id"],
                            "gene_symbol": target_gene,
                        }
                    )

        # 5. Also find targets that connect through pathways or other diseases
        # Drug -> Target -> (gene) -> Gene <- Disease (via HAS_GENE from other diseases)
        if max_depth >= 3:
            extended_results = kg.execute(
                "MATCH (dr:Drug {id: $drug_id})-[:HAS_TARGET]->(t:Target) "
                "MATCH (g:Gene) WHERE t.gene = g.symbol "
                "MATCH (other_d:Disease)-[:HAS_GENE]->(g) "
                "WHERE other_d.id <> $disease_id "
                "RETURN DISTINCT t.id as target_id, g.id as gene_id, "
                "g.symbol as gene_symbol, other_d.id as other_disease_id, "
                "other_d.name as other_disease_name "
                "LIMIT 10",
                {"drug_id": drug_id, "disease_id": disease_id},
            )
            for row in extended_results:
                other_d_id = row["other_disease_id"]
                add_node(
                    other_d_id,
                    other_d_id,
                    "Disease",
                    row["other_disease_name"],
                )
                add_edge(
                    other_d_id,
                    row["gene_id"],
                    "HAS_GENE",
                    match_type="extended",
                )

        # Add the drug and disease nodes themselves
        drug_info = kg.execute(
            "MATCH (d:Drug {id: $drug_id}) RETURN d.id as id, d.name as name, "
            "d.approval_status as approval_status, d.moa_classes as moa_classes, "
            "d.smiles as smiles, d.molecular_weight as molecular_weight",
            {"drug_id": drug_id},
        )
        for row in drug_info:
            add_node(
                drug_id,
                drug_id,
                "Drug",
                row["name"],
                approval_status=row.get("approval_status"),
                moa_classes=row.get("moa_classes"),
                smiles=row.get("smiles"),
                molecular_weight=row.get("molecular_weight"),
            )

        disease_info = kg.execute(
            "MATCH (d:Disease {id: $disease_id}) RETURN d.id as id, d.name as name, "
            "d.prevalence as prevalence, d.unmet_need_score as unmet_need_score, "
            "d.description as description",
            {"disease_id": disease_id},
        )
        for row in disease_info:
            add_node(
                disease_id,
                disease_id,
                "Disease",
                row["name"],
                prevalence=row.get("prevalence"),
                unmet_need_score=row.get("unmet_need_score"),
                description=row.get("description"),
            )

        return {
            "drug_id": drug_id,
            "disease_id": disease_id,
            "nodes": list(nodes_dict.values()),
            "edges": edges_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("kg_subgraph_failed", error=str(e))
        raise HTTPException(status_code=500, detail="KG subgraph retrieval failed") from e


@router.get("/stats")
async def get_kg_stats():
    """Get real knowledge graph statistics from the Kuzu database."""
    try:
        kg = _get_kg_service()

        # Node counts
        node_counts = {}
        for label in [
            "Drug",
            "Disease",
            "Target",
            "Gene",
            "Pathway",
            "Indication",
            "AdverseEvent",
            "Contraindication",
            "ADMETProperty",
            "MolecularStructure",
            "Publication",
            "Evidence",
        ]:
            try:
                result = kg.execute(f"MATCH (n:{label}) RETURN count(n) as cnt", {})
                node_counts[label] = result[0]["cnt"] if result else 0
            except Exception:
                node_counts[label] = 0

        # Edge counts
        edge_counts = {}
        for edge_type in [
            "TREATS",
            "HAS_TARGET",
            "HAS_GENE",
            "HAS_PATHWAY",
            "PARTICIPATES_IN",
            "IMPLICATED_IN",
            "IN_PATHWAY",
            "CONTRAINDICATES",
            "HAS_ADMET",
            "HAS_STRUCTURE",
            "SUPPORTS",
            "CAUSES_AE",
        ]:
            try:
                result = kg.execute(f"MATCH ()-[r:{edge_type}]->() RETURN count(r) as cnt", {})
                edge_counts[edge_type] = result[0]["cnt"] if result else 0
            except Exception:
                edge_counts[edge_type] = 0

        total_nodes = sum(node_counts.values())
        total_edges = sum(edge_counts.values())

        return {
            "node_types": node_counts,
            "edge_types": edge_counts,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
        }
    except Exception as e:
        logger.error("kg_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail="KG stats retrieval failed") from e


@router.get("/drugs")
async def list_drugs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: str | None = Query(None, description="Filter by drug name or id"),
    approval_status: str | None = Query(None, description="Filter by approval status"),
):
    """List drugs with pagination."""
    try:
        kg = _get_kg_service()

        where_conditions = []
        params = {}

        if query:
            where_conditions.append(
                "(toLower(d.name) CONTAINS toLower($query) OR toLower(d.id) CONTAINS toLower($query))"
            )
            params["query"] = query

        if approval_status:
            where_conditions.append("d.approval_status = $approval_status")
            params["approval_status"] = approval_status

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        offset = (page - 1) * page_size

        # Count total
        count_result = kg.execute(
            f"MATCH (d:Drug) {where_clause} RETURN count(d) as total",
            params,
        )
        total = count_result[0]["total"] if count_result else 0

        # Get paginated results (SKIP/LIMIT inlined as f-string, not parameters)
        data_result = kg.execute(
            f"MATCH (d:Drug) {where_clause} "
            f"RETURN d.id as id, d.name as name, d.smiles as smiles, "
            f"d.molecular_weight as molecular_weight, d.approval_status as approval_status, "
            f"d.moa_classes as moa_classes, d.cas as cas, "
            f"d.first_approval_year as first_approval_year "
            f"ORDER BY d.name "
            f"SKIP {offset} LIMIT {page_size}",
            params,
        )

        drugs = []
        for row in data_result:
            drugs.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "smiles": row.get("smiles"),
                    "molecular_weight": row.get("molecular_weight"),
                    "approval_status": row.get("approval_status"),
                    "moa_classes": row.get("moa_classes"),
                    "cas": row.get("cas"),
                    "first_approval_year": row.get("first_approval_year"),
                }
            )

        return {
            "data": drugs,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error("kg_list_drugs_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list drugs") from e


@router.get("/drugs/{drug_id}")
async def get_drug_detail(drug_id: str):
    """Get detailed information about a specific drug."""
    try:
        kg = _get_kg_service()

        # Get drug properties
        drug_result = kg.execute(
            "MATCH (d:Drug {id: $drug_id}) RETURN d",
            {"drug_id": drug_id},
        )
        if not drug_result:
            raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")

        drug = drug_result[0]["d"]

        # Get targets
        target_result = kg.execute(
            "MATCH (d:Drug {id: $drug_id})-[r:HAS_TARGET]->(t:Target) "
            "RETURN t.id as target_id, t.name as target_name, t.gene as gene, "
            "t.uniprot as uniprot, t.organism as organism, t.target_class as target_class, "
            "r.action_type as action_type, r.binding_value as binding_value, "
            "r.binding_unit as binding_unit, r.source as source",
            {"drug_id": drug_id},
        )
        targets = []
        for row in target_result:
            targets.append(
                {
                    "target_id": row["target_id"],
                    "target_name": row["target_name"],
                    "gene": row.get("gene"),
                    "uniprot": row.get("uniprot"),
                    "organism": row.get("organism"),
                    "target_class": row.get("target_class"),
                    "action_type": row.get("action_type"),
                    "binding_value": row.get("binding_value"),
                    "binding_unit": row.get("binding_unit"),
                    "source": row.get("source"),
                }
            )

        # Get diseases this drug treats
        disease_result = kg.execute(
            "MATCH (d:Drug {id: $drug_id})-[r:TREATS]->(dis:Disease) "
            "RETURN dis.id as disease_id, dis.name as disease_name, "
            "dis.prevalence as prevalence, dis.unmet_need_score as unmet_need_score, "
            "r.evidence as evidence, r.confidence as confidence",
            {"drug_id": drug_id},
        )
        diseases = []
        for row in disease_result:
            diseases.append(
                {
                    "disease_id": row["disease_id"],
                    "disease_name": row["disease_name"],
                    "prevalence": row.get("prevalence"),
                    "unmet_need_score": row.get("unmet_need_score"),
                    "evidence": row.get("evidence"),
                    "confidence": row.get("confidence"),
                }
            )

        return {
            "id": drug.get("id"),
            "name": drug.get("name"),
            "smiles": drug.get("smiles"),
            "inchi": drug.get("inchi"),
            "inchikey": drug.get("inchikey"),
            "molecular_weight": drug.get("molecular_weight"),
            "xlogp": drug.get("xlogp"),
            "tpsa": drug.get("tpsa"),
            "rotatable_bonds": drug.get("rotatable_bonds"),
            "hba": drug.get("hba"),
            "hbd": drug.get("hbd"),
            "charge": drug.get("charge"),
            "moa_classes": drug.get("moa_classes"),
            "target_names": drug.get("target_names"),
            "target_genes": drug.get("target_genes"),
            "target_uniprots": drug.get("target_uniprots"),
            "indication_umls": drug.get("indication_umls"),
            "indication_types": drug.get("indication_types"),
            "first_approval_year": drug.get("first_approval_year"),
            "approval_status": drug.get("approval_status"),
            "cas": drug.get("cas"),
            "targets": targets,
            "diseases": diseases,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("kg_drug_detail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get drug detail") from e


@router.get("/diseases")
async def list_diseases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query: str | None = Query(None, description="Filter by disease name or id"),
    prevalence_max: float | None = Query(None, description="Maximum prevalence"),
):
    """List diseases with pagination."""
    try:
        kg = _get_kg_service()

        where_conditions = []
        params = {}

        if query:
            where_conditions.append(
                "(toLower(d.name) CONTAINS toLower($query) OR toLower(d.id) CONTAINS toLower($query))"
            )
            params["query"] = query

        if prevalence_max is not None:
            where_conditions.append("d.prevalence <= $prevalence_max")
            params["prevalence_max"] = prevalence_max

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        offset = (page - 1) * page_size

        # Count total
        count_result = kg.execute(
            f"MATCH (d:Disease) {where_clause} RETURN count(d) as total",
            params,
        )
        total = count_result[0]["total"] if count_result else 0

        # Get paginated results (SKIP/LIMIT inlined as f-string, not parameters)
        data_result = kg.execute(
            f"MATCH (d:Disease) {where_clause} "
            f"RETURN d.id as id, d.name as name, d.prevalence as prevalence, "
            f"d.prevalence_category as prevalence_category, d.inheritance as inheritance, "
            f"d.age_of_onset as age_of_onset, d.phenotypes as phenotypes, "
            f"d.existing_treatments as existing_treatments, "
            f"d.unmet_need_score as unmet_need_score, "
            f"d.synonyms as synonyms, d.omim_ids as omim_ids, "
            f"d.mondo_id as mondo_id, d.icar_id as icar_id "
            f"ORDER BY d.unmet_need_score DESC "
            f"SKIP {offset} LIMIT {page_size}",
            params,
        )

        diseases = []
        for row in data_result:
            diseases.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "prevalence": row.get("prevalence"),
                    "prevalence_category": row.get("prevalence_category"),
                    "inheritance": row.get("inheritance"),
                    "age_of_onset": row.get("age_of_onset"),
                    "phenotypes": row.get("phenotypes"),
                    "existing_treatments": row.get("existing_treatments"),
                    "unmet_need_score": row.get("unmet_need_score"),
                    "synonyms": row.get("synonyms"),
                    "omim_ids": row.get("omim_ids"),
                    "mondo_id": row.get("mondo_id"),
                    "icar_id": row.get("icar_id"),
                }
            )

        return {
            "data": diseases,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error("kg_list_diseases_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list diseases") from e


@router.get("/diseases/{disease_id}")
async def get_disease_detail(disease_id: str):
    """Get detailed information about a specific disease, including genes and targets."""
    try:
        kg = _get_kg_service()

        # Get disease properties
        disease_result = kg.execute(
            "MATCH (d:Disease {id: $disease_id}) RETURN d",
            {"disease_id": disease_id},
        )
        if not disease_result:
            raise HTTPException(status_code=404, detail=f"Disease {disease_id} not found")

        disease = disease_result[0]["d"]

        # Get genes
        gene_result = kg.execute(
            "MATCH (d:Disease {id: $disease_id})-[r:HAS_GENE]->(g:Gene) "
            "RETURN g.id as gene_id, g.symbol as symbol, g.name as name, "
            "g.uniprot_id as uniprot_id, g.ensembl_id as ensembl_id, "
            "g.hgnc_id as hgnc_id, r.source as source",
            {"disease_id": disease_id},
        )
        genes = []
        for row in gene_result:
            genes.append(
                {
                    "gene_id": row["gene_id"],
                    "symbol": row.get("symbol"),
                    "name": row.get("name"),
                    "uniprot_id": row.get("uniprot_id"),
                    "ensembl_id": row.get("ensembl_id"),
                    "hgnc_id": row.get("hgnc_id"),
                    "source": row.get("source"),
                }
            )

        # Get drugs that treat this disease
        drug_result = kg.execute(
            "MATCH (dr:Drug)-[r:TREATS]->(d:Disease {id: $disease_id}) "
            "RETURN dr.id as drug_id, dr.name as drug_name, "
            "dr.approval_status as approval_status, dr.moa_classes as moa_classes, "
            "r.evidence as evidence, r.confidence as confidence",
            {"disease_id": disease_id},
        )
        drugs = []
        for row in drug_result:
            drugs.append(
                {
                    "drug_id": row["drug_id"],
                    "drug_name": row["drug_name"],
                    "approval_status": row.get("approval_status"),
                    "moa_classes": row.get("moa_classes"),
                    "evidence": row.get("evidence"),
                    "confidence": row.get("confidence"),
                }
            )

        # Get targets (via gene symbol matching with targets)
        target_result = kg.execute(
            "MATCH (d:Disease {id: $disease_id})-[:HAS_GENE]->(g:Gene) "
            "MATCH (t:Target) WHERE t.gene = g.symbol "
            "RETURN DISTINCT t.id as target_id, t.name as target_name, "
            "t.gene as gene, t.uniprot as uniprot, t.organism as organism, "
            "t.target_class as target_class",
            {"disease_id": disease_id},
        )
        targets = []
        for row in target_result:
            targets.append(
                {
                    "target_id": row["target_id"],
                    "target_name": row["target_name"],
                    "gene": row.get("gene"),
                    "uniprot": row.get("uniprot"),
                    "organism": row.get("organism"),
                    "target_class": row.get("target_class"),
                }
            )

        return {
            "id": disease.get("id"),
            "name": disease.get("name"),
            "prevalence": disease.get("prevalence"),
            "prevalence_category": disease.get("prevalence_category"),
            "inheritance": disease.get("inheritance"),
            "age_of_onset": disease.get("age_of_onset"),
            "phenotypes": disease.get("phenotypes"),
            "existing_treatments": disease.get("existing_treatments"),
            "unmet_need_score": disease.get("unmet_need_score"),
            "description": disease.get("description"),
            "synonyms": disease.get("synonyms"),
            "omim_ids": disease.get("omim_ids"),
            "mondo_id": disease.get("mondo_id"),
            "icar_id": disease.get("icar_id"),
            "genes": genes,
            "drugs": drugs,
            "targets": targets,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("kg_disease_detail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get disease detail") from e

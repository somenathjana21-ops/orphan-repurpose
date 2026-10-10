from pathlib import Path

import kuzu
import structlog

from app.core.config import settings
from app.models.disease import DiseaseDetail, DiseaseSearchResult, Gene, Pathway

logger = structlog.get_logger()


class KGService:
    """Knowledge Graph service using Kuzu embedded database."""

    def __init__(self):
        self.db_path = Path(settings.KUZU_DB_PATH)
        self.db = None
        self.conn = None
        self._initialize()

    def _initialize(self):
        """Initialize Kuzu database connection."""
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.db_file = self.db_path / "kuzu.db"
        try:
            self.db = kuzu.Database(str(self.db_file), read_only=True)
        except Exception:
            self.db = kuzu.Database(str(self.db_file))
        self.conn = kuzu.Connection(self.db)
        logger.info("kuzu_initialized", path=str(self.db_file))

    def execute(self, query: str, params: dict = None) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts."""
        try:
            result = self.conn.execute(query, params or {})
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                row = result.get_next()
                rows.append(dict(zip(columns, row, strict=False)))
            return rows
        except Exception as e:
            logger.error("kuzu_query_failed", query=query, error=str(e))
            raise

    def search_diseases(
        self,
        query: str | None = None,
        prevalence_max: float | None = None,
        gene: str | None = None,
        pathway: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "unmet_need_score",
        sort_order: str = "desc",
    ) -> tuple[list[DiseaseSearchResult], int]:
        """Search diseases with filters and pagination."""
        # Build WHERE clause
        where_conditions = []
        params = {}

        if query:
            where_conditions.append("(d.name CONTAINS $query OR d.id CONTAINS $query)")
            params["query"] = query

        if prevalence_max:
            where_conditions.append("d.prevalence <= $prevalence_max")
            params["prevalence_max"] = prevalence_max

        if gene:
            where_conditions.append("EXISTS (d)-[:HAS_GENE]->(:Gene {symbol: $gene})")
            params["gene"] = gene

        if pathway:
            where_conditions.append("EXISTS (d)-[:HAS_PATHWAY]->(:Pathway {name: $pathway})")
            params["pathway"] = pathway

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Count total
        count_query = f"""
        MATCH (d:Disease)
        {where_clause}
        RETURN count(d) as total
        """
        count_result = self.execute(count_query, params)
        total = count_result[0]["total"] if count_result else 0

        # Paginated results
        offset = (page - 1) * page_size
        sort_direction = "DESC" if sort_order == "desc" else "ASC"

        data_query = f"""
        MATCH (d:Disease)
        {where_clause}
        RETURN d
        ORDER BY d.{sort_by} {sort_direction}
        SKIP {offset} LIMIT {page_size}
        """
        results = self.execute(data_query, params)

        diseases = []
        for row in results:
            d = row["d"]
            diseases.append(
                DiseaseSearchResult(
                    orpha_id=d["id"],
                    name=d["name"],
                    prevalence=d.get("prevalence"),
                    prevalence_category=d.get("prevalence_category"),
                    inheritance=d.get("inheritance"),
                    age_of_onset=d.get("age_of_onset"),
                    genes=[Gene(**g) for g in d.get("genes", [])],
                    pathways=[Pathway(**p) for p in d.get("pathways", [])],
                    phenotypes=d.get("phenotypes", []),
                    existing_treatments=d.get("existing_treatments", []),
                    unmet_need_score=d.get("unmet_need_score"),
                )
            )

        return diseases, total

    def get_disease(self, orpha_id: str) -> DiseaseDetail | None:
        """Get detailed disease information."""
        query = """
        MATCH (d:Disease {id: $orpha_id})
        RETURN d
        """
        results = self.execute(query, {"orpha_id": orpha_id})
        if not results:
            return None
        row = results[0]
        d = row["d"]

        # Get genes
        genes = []
        try:
            gene_query = """
            MATCH (d:Disease {id: $orpha_id})-[:HAS_GENE]->(g:Gene)
            RETURN g
            """
            gene_results = self.execute(gene_query, {"orpha_id": orpha_id})
            for gene_row in gene_results:
                genes.append(gene_row["g"])
        except Exception as e:
            if "Binder exception" in str(e) and "HAS_GENE" in str(e):
                genes = []
            else:
                raise

        # Get pathways
        pathways = []
        try:
            pathway_query = """
            MATCH (d:Disease {id: $orpha_id})-[:HAS_PATHWAY]->(p:Pathway)
            RETURN p
            """
            pathway_results = self.execute(pathway_query, {"orpha_id": orpha_id})
            for pathway_row in pathway_results:
                pathways.append(pathway_row["p"])
        except Exception as e:
            if "Binder exception" in str(e) and "HAS_PATHWAY" in str(e):
                pathways = []
            else:
                raise

        return DiseaseDetail(
            orpha_id=d["id"],
            name=d["name"],
            prevalence=d.get("prevalence"),
            prevalence_category=d.get("prevalence_category"),
            inheritance=d.get("inheritance"),
            age_of_onset=d.get("age_of_onset"),
            genes=[Gene(**g) for g in genes if g],
            pathways=[Pathway(**p) for p in pathways if p],
            phenotypes=d.get("phenotypes", []),
            existing_treatments=d.get("existing_treatments", []),
            unmet_need_score=d.get("unmet_need_score"),
            description=d.get("description"),
            synonyms=d.get("synonyms", []),
            omim_ids=d.get("omim_ids", []),
            mondo_id=d.get("mondo_id"),
            icar_id=d.get("icar_id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )

    def get_disease_genes(self, orpha_id: str) -> list[str]:
        """Get gene symbols for a disease."""
        query = """
        MATCH (d:Disease {id: $orpha_id})-[:HAS_GENE]->(g:Gene)
        RETURN g.symbol as symbol
        """
        results = self.execute(query, {"orpha_id": orpha_id})
        return [r["symbol"] for r in results]

    def get_disease_pathways(self, orpha_id: str) -> list[str]:
        """Get pathway names for a disease."""
        query = """
        MATCH (d:Disease {id: $orpha_id})-[:HAS_PATHWAY]->(p:Pathway)
        RETURN p.name as name
        """
        results = self.execute(query, {"orpha_id": orpha_id})
        return [r["name"] for r in results]

    def get_drug_candidates(self, disease_id: str, limit: int = 50) -> list[dict]:
        """Get potential drug candidates for a disease via KG paths."""
        query = """
        MATCH (d:Disease {id: $disease_id})
        MATCH path = (dr:Drug)-[:HAS_TARGET|TREATS*1..3]->(d)
        WHERE dr.approval_status = 'FDA_approved'
        RETURN dr.id as id, dr.name as name, dr.smiles as smiles,
               dr.moa_classes as moa, length(path) as path_length,
               [n in nodes(path) | labels(n)] as node_types,
               [r in relationships(path) | type(r)] as rel_types
        ORDER BY path_length, dr.name
        LIMIT $limit
        """
        results = self.execute(query, {"disease_id": disease_id, "limit": limit})
        return results

    def get_kg_subgraph(self, drug_id: str, disease_id: str, max_depth: int = 3) -> dict:
        """Get KG subgraph connecting drug to disease."""
        query = f"""
        MATCH (dr:Drug {{id: $drug_id}}), (d:Disease {{id: $disease_id}})
        MATCH path = (dr)-[:HAS_TARGET|PARTICIPATES_IN|IMPLICATED_IN|HAS_GENE*1..{max_depth}]->(d)
        RETURN path
        LIMIT 10
        """
        results = self.execute(query, {"drug_id": drug_id, "disease_id": disease_id})

        # Convert to Cytoscape.js format
        nodes = {}
        edges = []

        for row in results:
            # Extract nodes and edges from path
            # This is simplified - actual implementation depends on Kuzu path format
            pass

        return {"nodes": list(nodes.values()), "edges": edges}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
        if self.db:
            self.db.close()

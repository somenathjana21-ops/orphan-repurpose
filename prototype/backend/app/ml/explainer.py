"""
Explainability module for OrphanRepurpose.

Provides:
- KGPathExtractor: Yen's k-shortest paths in the knowledge graph
- SHAPExplainer: SHAP values for Morgan fingerprint bits
- CounterfactualExplainer: counterfactual explanations via bit flipping
- LLMRationaleGenerator: natural language rationale generation
- Explainer: facade composing all explainers
"""
from __future__ import annotations

import structlog
import torch
import numpy as np
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.models.disease import (
    KGPath, KGPathNode, KGPathEdge, Explanation, Counterfactual,
)

logger = structlog.get_logger()


class KGPathExtractor:
    """Extracts k-shortest paths from the knowledge graph using NetworkX."""

    def __init__(self, kg_service=None):
        self.kg_service = kg_service
        self._graph = None
        self._graph_drug_ids: set = set()
        self._graph_disease_ids: set = set()

    def _load_graph(self):
        """Load the Kuzu KG into a NetworkX directed graph."""
        if self._graph is not None:
            return

        import networkx as nx

        self._graph = nx.DiGraph()
        self._graph_drug_ids = set()
        self._graph_disease_ids = set()

        if self.kg_service is None:
            from app.services.kg_service import KGService
            self.kg_service = KGService()

        try:
            # Get all drugs
            drug_results = self.kg_service.execute(
                "MATCH (d:Drug) RETURN d.id as id, d.name as name, d.smiles as smiles"
            )
            for row in drug_results:
                drug_id = row["id"]
                self._graph.add_node(drug_id, type="drug", name=row.get("name", drug_id))
                self._graph_drug_ids.add(drug_id)

            # Get all diseases
            disease_results = self.kg_service.execute(
                "MATCH (d:Disease) RETURN d.id as id, d.name as name"
            )
            for row in disease_results:
                disease_id = row["id"]
                self._graph.add_node(disease_id, type="disease", name=row.get("name", disease_id))
                self._graph_disease_ids.add(disease_id)

            # Get all targets
            target_results = self.kg_service.execute(
                "MATCH (t:Target) RETURN t.id as id, t.name as name"
            )
            for row in target_results:
                target_id = row["id"]
                self._graph.add_node(target_id, type="target", name=row.get("name", target_id))

            # Get all genes
            gene_results = self.kg_service.execute(
                "MATCH (g:Gene) RETURN g.id as id, g.symbol as name"
            )
            for row in gene_results:
                gene_id = row["id"]
                self._graph.add_node(gene_id, type="gene", name=row.get("name", gene_id))

            # Get all pathways
            pathway_results = self.kg_service.execute(
                "MATCH (p:Pathway) RETURN p.id as id, p.name as name"
            )
            for row in pathway_results:
                pathway_id = row["id"]
                self._graph.add_node(pathway_id, type="pathway", name=row.get("name", pathway_id))

            # Get TREATS edges (drug-disease)
            treats_results = self.kg_service.execute(
                "MATCH (d:Drug)-[:TREATS]->(dis:Disease) RETURN d.id as source, dis.id as target"
            )
            for row in treats_results:
                self._graph.add_edge(row["source"], row["target"], type="TREATS", weight=1.0)

            # Get HAS_TARGET edges (drug-target)
            target_edges = self.kg_service.execute(
                "MATCH (d:Drug)-[:HAS_TARGET]->(t:Target) RETURN d.id as source, t.id as target"
            )
            for row in target_edges:
                self._graph.add_edge(row["source"], row["target"], type="HAS_TARGET", weight=1.0)

            # Get HAS_GENE edges (disease-gene)
            gene_edges = self.kg_service.execute(
                "MATCH (d:Disease)-[:HAS_GENE]->(g:Gene) RETURN d.id as source, g.id as target"
            )
            for row in gene_edges:
                self._graph.add_edge(row["source"], row["target"], type="HAS_GENE", weight=1.0)

            # Get HAS_PATHWAY edges (disease-pathway)
            pathway_edges = self.kg_service.execute(
                "MATCH (d:Disease)-[:HAS_PATHWAY]->(p:Pathway) RETURN d.id as source, p.id as target"
            )
            for row in pathway_edges:
                self._graph.add_edge(row["source"], row["target"], type="HAS_PATHWAY", weight=1.0)

            # Get PARTICIPATES_IN edges (target-pathway)
            participates_edges = self.kg_service.execute(
                "MATCH (t:Target)-[:PARTICIPATES_IN]->(p:Pathway) RETURN t.id as source, p.id as target"
            )
            for row in participates_edges:
                self._graph.add_edge(row["source"], row["target"], type="PARTICIPATES_IN", weight=1.0)

            # Get IMPLICATED_IN edges (target-disease)
            implicated_edges = self.kg_service.execute(
                "MATCH (t:Target)-[:IMPLICATED_IN]->(d:Disease) RETURN t.id as source, d.id as target"
            )
            for row in implicated_edges:
                self._graph.add_edge(row["source"], row["target"], type="IMPLICATED_IN", weight=1.0)

            logger.info(
                "kg_graph_loaded",
                nodes=self._graph.number_of_nodes(),
                edges=self._graph.number_of_edges(),
            )

        except Exception as e:
            logger.error("kg_graph_load_failed", error=str(e))
            self._graph = nx.DiGraph()

    def extract_paths(
        self, drug_id: str, disease_id: str, k: int = 5
    ) -> List[KGPath]:
        """Extract k-shortest paths from drug to disease using Yen's algorithm."""
        self._load_graph()

        if self._graph is None or self._graph.number_of_nodes() == 0:
            return []

        if drug_id not in self._graph or disease_id not in self._graph:
            return []

        try:
            import networkx as nx

            paths = []
            for path_nodes in nx.shortest_simple_paths(self._graph, drug_id, disease_id):
                if len(paths) >= k:
                    break

                # Build KGPath
                kg_nodes = []
                kg_edges = []
                for i, node_id in enumerate(path_nodes):
                    node_data = self._graph.nodes[node_id]
                    kg_nodes.append(KGPathNode(
                        id=node_id,
                        type=node_data.get("type", "unknown"),
                        name=node_data.get("name", node_id),
                        properties={},
                    ))
                    if i < len(path_nodes) - 1:
                        next_id = path_nodes[i + 1]
                        edge_data = self._graph.edges[node_id, next_id]
                        kg_edges.append(KGPathEdge(
                            source=node_id,
                            target=next_id,
                            type=edge_data.get("type", "unknown"),
                            weight=edge_data.get("weight", 1.0),
                        ))

                path_length = len(kg_edges)
                score = 1.0 / (1.0 + path_length)

                paths.append(KGPath(
                    nodes=kg_nodes,
                    edges=kg_edges,
                    score=score,
                ))

            return paths

        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            logger.warning("path_extraction_failed", error=str(e))
            return []


class SHAPExplainer:
    """Computes SHAP values for Morgan fingerprint bits using DeepExplainer-style
    pre-computed background gradients for fast inference.

    Instead of KernelExplainer (O(n_bits × n_background) per candidate),
    we pre-compute the gradient of the output w.r.t. the input at a single
    background point (all-zeros fingerprint), then use the approximation:
        shap_i ≈ grad_bg_i × (fp_i - bg_i) = grad_bg_i × fp_i  (since bg=0)
    This gives a fast, per-candidate attribution in O(n_bits) time.
    """

    def __init__(self, model, n_bits: int = 1024):
        self.model = model
        self.n_bits = n_bits
        self._background_grad = None  # [n_bits] gradient at background
        self._background = None

    def _init_shap(self):
        """Pre-compute background gradient for fast SHAP approximation."""
        if self._background_grad is not None:
            return

        try:
            # Background: all-zero fingerprint (mean of binary features)
            bg = torch.zeros(1, self.n_bits, dtype=torch.float32, requires_grad=True)
            disease_emb = torch.zeros(1, 256, dtype=torch.float32)

            self.model.eval()
            logits = self.model(bg, disease_emb)
            logits.backward()

            self._background_grad = bg.grad.data.numpy().flatten()
            self._background = np.zeros(self.n_bits, dtype=np.float32)

            logger.info("shap_explainer_initialized", method="deep_explainer_approx")

        except Exception as e:
            logger.error("shap_init_failed", error=str(e))
            self._background_grad = None

    def explain(self, drug_fp: np.ndarray, disease_emb: np.ndarray) -> Dict[str, float]:
        """Compute SHAP values for a drug fingerprint using fast gradient approximation."""
        self._init_shap()

        if self._background_grad is not None:
            try:
                # DeepExplainer-style: shap_i = grad_bg_i × (fp_i - bg_i)
                # Since bg=0, this simplifies to grad_bg_i × fp_i
                shap_values = self._background_grad * drug_fp

                # Get top 15 by absolute value
                top_indices = np.argsort(np.abs(shap_values))[-15:][::-1]
                result = {}
                for idx in top_indices:
                    result[f"morgan_bit_{idx}"] = float(shap_values[idx])
                return result

            except Exception as e:
                logger.warning("shap_explain_failed", error=str(e))

        # Fallback: per-candidate gradient attribution
        return self._gradient_attribution(drug_fp, disease_emb)

    def _gradient_attribution(
        self, drug_fp: np.ndarray, disease_emb: np.ndarray
    ) -> Dict[str, float]:
        """Gradient-based feature attribution fallback (per-candidate)."""
        try:
            fp_tensor = torch.tensor(drug_fp, dtype=torch.float32, requires_grad=True).unsqueeze(0)
            disease_tensor = torch.tensor(disease_emb, dtype=torch.float32).unsqueeze(0)

            logits = self.model(fp_tensor, disease_tensor)
            logits.backward()

            gradients = fp_tensor.grad.data.numpy().flatten()
            # Attribution = gradient × input (Integrated Gradients, single step)
            attributions = gradients * drug_fp

            # Top 15 by absolute attribution
            top_indices = np.argsort(np.abs(attributions))[-15:][::-1]
            result = {}
            for idx in top_indices:
                result[f"morgan_bit_{idx}"] = float(attributions[idx])
            return result

        except Exception as e:
            logger.error("gradient_attribution_failed", error=str(e))
            return {}


class CounterfactualExplainer:
    """Generates counterfactual explanations by flipping fingerprint bits."""

    def __init__(self, model, n_bits: int = 1024):
        self.model = model
        self.n_bits = n_bits

    def explain(
        self, drug_fp: np.ndarray, disease_emb: np.ndarray, n_cf: int = 3
    ) -> List[Counterfactual]:
        """Generate counterfactual explanations by flipping active bits."""
        try:
            fp_tensor = torch.tensor(drug_fp, dtype=torch.float32).unsqueeze(0)
            disease_tensor = torch.tensor(disease_emb, dtype=torch.float32).unsqueeze(0)

            with torch.no_grad():
                base_prob = float(torch.sigmoid(self.model(fp_tensor, disease_tensor)).item())

            # Find active bits (value = 1)
            active_bits = np.where(drug_fp > 0.5)[0]
            if len(active_bits) == 0:
                return []

            # Flip each active bit and measure probability change
            counterfactuals = []
            for bit_idx in active_bits[:20]:  # Limit to top 20 for efficiency
                cf_fp = drug_fp.copy()
                cf_fp[bit_idx] = 0.0

                cf_tensor = torch.tensor(cf_fp, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    cf_prob = float(torch.sigmoid(self.model(cf_tensor, disease_tensor)).item())

                delta = cf_prob - base_prob
                counterfactuals.append((bit_idx, delta, cf_prob))

            # Sort by absolute delta (largest change first)
            counterfactuals.sort(key=lambda x: abs(x[1]), reverse=True)

            # Take top n_cf
            results = []
            for bit_idx, delta, cf_prob in counterfactuals[:n_cf]:
                results.append(Counterfactual(
                    removed_edge=f"morgan_bit_{bit_idx}",
                    probability_delta=delta,
                    description=(
                        f"If this drug did not have the substructure at bit {bit_idx}, "
                        f"the indication probability would change by {delta:+.3f} "
                        f"(from {base_prob:.3f} to {cf_prob:.3f})."
                    ),
                ))

            return results

        except Exception as e:
            logger.error("counterfactual_explain_failed", error=str(e))
            return []


class LLMRationaleGenerator:
    """Generates natural language rationale for a drug-disease pair."""

    def __init__(self):
        self._model = None
        self._tokenizer = None

    def _try_load_biomistral(self):
        """Try to load BioMistral-7B for rationale generation."""
        if self._model is not None:
            return True

        try:
            # Check if model file exists
            model_path = Path("prototype/models/biomistral-7b-q4.gguf")
            if not model_path.exists():
                return False

            from llama_cpp import Llama
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=4,
            )
            logger.info("biomistral_loaded")
            return True

        except Exception as e:
            logger.warning("biomistral_load_failed", error=str(e))
            return False

    def generate(
        self,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
        kg_paths: List[KGPath],
    ) -> str:
        """Generate natural language rationale."""
        # Try BioMistral first
        if self._try_load_biomistral():
            try:
                return self._generate_with_llm(
                    drug_name, disease_name, probability, moa_summary, kg_paths
                )
            except Exception as e:
                logger.warning("llm_generation_failed_using_template", error=str(e))

        # Fallback: template-based generation
        return self._generate_template(drug_name, disease_name, probability, moa_summary, kg_paths)

    def _generate_with_llm(
        self,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
        kg_paths: List[KGPath],
    ) -> str:
        """Generate rationale using BioMistral."""
        path_desc = " -> ".join(
            [n.name for n in kg_paths[0].nodes]
        ) if kg_paths else "no known path"

        prompt = f"""You are a biomedical AI assistant. Provide a concise rationale for why {drug_name} might be repurposed for {disease_name}.

Predicted efficacy: {probability:.0%}
Mechanism of Action: {moa_summary}
Knowledge Graph Path: {path_desc}

Rationale (2-3 sentences):"""

        response = self._model(prompt, max_tokens=200, temperature=0.7)
        return response["choices"][0]["text"].strip()

    def _generate_template(
        self,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
        kg_paths: List[KGPath],
    ) -> str:
        """Generate rationale using templates."""
        if kg_paths:
            path = kg_paths[0]
            path_desc = " -> ".join([n.name for n in path.nodes])
            n_hops = len(path.edges)
            path_text = (
                f"The knowledge graph path suggests: {path_desc}. "
                f"This repurposing opportunity is supported by {n_hops} mechanistic step{'s' if n_hops != 1 else ''}."
            )
        else:
            path_text = "No direct knowledge graph path was found, but structural similarity supports this prediction."

        return (
            f"{drug_name} shows {probability:.0%} predicted efficacy for {disease_name}. "
            f"{moa_summary} {path_text}"
        )


class Explainer:
    """Facade composing all explainability methods."""

    def __init__(self):
        self.kg_extractor = None
        self.shap_explainer = None
        self.cf_explainer = None
        self.llm_generator = LLMRationaleGenerator()
        self._model = None
        self._indication_service = None

    def _get_model(self):
        """Lazy-load the indication model."""
        if self._model is not None:
            return self._model

        try:
            from app.services.indication_service import get_indication_service
            self._indication_service = get_indication_service()
            if self._indication_service.is_ready():
                self._model = self._indication_service.model
        except Exception as e:
            logger.warning("model_load_failed", error=str(e))

        return self._model

    def _get_kg_extractor(self) -> KGPathExtractor:
        """Lazy-load the KG path extractor."""
        if self.kg_extractor is None:
            try:
                from app.services.kg_service import KGService
                kg_service = KGService()
                self.kg_extractor = KGPathExtractor(kg_service)
            except Exception as e:
                logger.warning("kg_service_load_failed", error=str(e))
                self.kg_extractor = KGPathExtractor(None)
        return self.kg_extractor

    def _get_shap_explainer(self) -> SHAPExplainer:
        """Lazy-load the SHAP explainer."""
        if self.shap_explainer is None:
            model = self._get_model()
            if model is not None:
                self.shap_explainer = SHAPExplainer(model)
        return self.shap_explainer

    def _get_cf_explainer(self) -> CounterfactualExplainer:
        """Lazy-load the counterfactual explainer."""
        if self.cf_explainer is None:
            model = self._get_model()
            if model is not None:
                self.cf_explainer = CounterfactualExplainer(model)
        return self.cf_explainer

    def explain(
        self,
        drug_id: str,
        disease_id: str,
        drug_name: str,
        disease_name: str,
        probability: float,
        moa_summary: str,
    ) -> Dict[str, Any]:
        """Generate full explanation for a drug-disease pair."""
        # 1. KG paths
        kg_paths = self._get_kg_extractor().extract_paths(drug_id, disease_id, k=5)

        # 2. Get model inputs for SHAP and counterfactuals
        shap_values = {}
        counterfactuals = []

        model = self._get_model()
        if model is not None and self._indication_service is not None:
            try:
                # Get drug fingerprint
                drug_fps = getattr(self._indication_service, 'drug_fingerprints', {})
                if drug_id in drug_fps:
                    drug_fp = np.array(drug_fps[drug_id], dtype=np.float32)
                else:
                    # Compute from SMILES
                    drug_smiles = self._indication_service.drug_smiles.get(drug_id, "")
                    if drug_smiles:
                        from rdkit import Chem
                        from rdkit.Chem import AllChem
                        mol = Chem.MolFromSmiles(drug_smiles)
                        if mol:
                            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
                            drug_fp = np.array(fp, dtype=np.float32)
                        else:
                            drug_fp = np.zeros(1024, dtype=np.float32)
                    else:
                        drug_fp = np.zeros(1024, dtype=np.float32)

                # Get disease embedding
                disease_map = self._indication_service.disease_map
                disease_embeddings = self._indication_service.disease_embeddings
                if disease_id in disease_map and disease_embeddings is not None:
                    d_idx = disease_map[disease_id]
                    disease_emb = disease_embeddings[d_idx]
                else:
                    disease_emb = np.zeros(256, dtype=np.float32)

                # SHAP values
                shap_explainer = self._get_shap_explainer()
                if shap_explainer is not None:
                    shap_values = shap_explainer.explain(drug_fp, disease_emb)

                # Counterfactuals
                cf_explainer = self._get_cf_explainer()
                if cf_explainer is not None:
                    counterfactuals = cf_explainer.explain(drug_fp, disease_emb, n_cf=3)

            except Exception as e:
                logger.warning("model_explanation_failed", error=str(e))

        # 3. LLM rationale
        llm_rationale = self.llm_generator.generate(
            drug_name, disease_name, probability, moa_summary, kg_paths
        )

        return {
            "candidate_id": f"{drug_id}_{disease_id}",
            "kg_paths": [self._kg_path_to_dict(p) for p in kg_paths],
            "shap_values": shap_values,
            "counterfactuals": [self._cf_to_dict(c) for c in counterfactuals],
            "llm_rationale": llm_rationale,
        }

    @staticmethod
    def _kg_path_to_dict(path: KGPath) -> Dict[str, Any]:
        return {
            "nodes": [
                {"id": n.id, "type": n.type, "name": n.name, "properties": n.properties}
                for n in path.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, "type": e.type, "weight": e.weight}
                for e in path.edges
            ],
            "score": path.score,
        }

    @staticmethod
    def _cf_to_dict(cf: Counterfactual) -> Dict[str, Any]:
        return {
            "removed_edge": cf.removed_edge,
            "probability_delta": cf.probability_delta,
            "description": cf.description,
        }

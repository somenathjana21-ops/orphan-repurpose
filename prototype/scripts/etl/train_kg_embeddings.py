#!/usr/bin/env python3
"""
Train RGCN embeddings on the Knowledge Graph.
"""
import torch
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv
from torch_geometric.data import HeteroData
import kuzu
import pandas as pd
import numpy as np
from pathlib import Path
import structlog
from tqdm import tqdm
import pickle

logger = structlog.get_logger()


class RGCN(torch.nn.Module):
    def __init__(self, num_nodes_dict, hidden_dim, num_relations, num_bases, num_layers=2, dropout=0.2):
        super().__init__()
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Embedding layer for each node type
        self.embeddings = torch.nn.ModuleDict({
            node_type: torch.nn.Embedding(num_nodes, hidden_dim)
            for node_type, num_nodes in num_nodes_dict.items()
        })
        
        # RGCN layers
        self.convs = torch.nn.ModuleList()
        for i in range(num_layers):
            in_dim = hidden_dim if i == 0 else hidden_dim
            self.convs.append(RGCNConv(
                in_dim, hidden_dim, num_relations, num_bases=num_bases
            ))
    
    def forward(self, edge_index_dict, edge_type_dict):
        # Initialize embeddings
        h_dict = {node_type: self.embeddings[node_type](torch.arange(self.embeddings[node_type].weight.shape[0])) 
                  for node_type in self.embeddings.keys()}

        for i, conv in enumerate(self.convs):
            h_dict_new = {}
            for node_type in h_dict:
                # Collect messages from all relation types
                messages = []
                for (src, rel, dst), edge_index in edge_index_dict.items():
                    if dst == node_type:
                        edge_type = edge_type_dict[(src, rel, dst)]
                        msg = conv(h_dict[src], edge_index, edge_type)
                        messages.append(msg)
               
                if messages:
                    h_dict_new[node_type] = sum(messages) / len(messages)
                else:
                    h_dict_new[node_type] = h_dict[node_type]
               
                if i < self.num_layers - 1:
                    h_dict_new[node_type] = F.relu(h_dict_new[node_type])
                    h_dict_new[node_type] = F.dropout(h_dict_new[node_type], p=self.dropout, training=self.training)
           
            h_dict = h_dict_new
       
        return h_dict


def load_kg_for_training(kuzu_db_path: Path) -> HeteroData:
    """Load KG from Kuzu and convert to PyG HeteroData."""
    db = kuzu.Database(str(kuzu_db_path / "kuzu.db"))
    conn = kuzu.Connection(db)
    
    data = HeteroData()
    
    # Get node counts and mappings
    node_types = ["Disease", "Gene", "Pathway", "Drug", "Target", "MolecularStructure",
                  "Indication", "Contraindication", "Publication", "Evidence", "AdverseEvent", "ADMETProperty"]
    
    node_id_maps = {}
    node_counts = {}
    
    for node_type in node_types:
        try:
            result = conn.execute(f"MATCH (n:{node_type}) RETURN n.id as id")
            ids = []
            while result.has_next():
                ids.append(result.get_next()[0])
            
            if ids:
                node_id_maps[node_type] = {id: idx for idx, id in enumerate(ids)}
                node_counts[node_type] = len(ids)
                data[node_type.lower()].num_nodes = len(ids)
                logger.info(f"node_type_counts", type=node_type, count=len(ids))
        except Exception as e:
            logger.warning("node_type_load_failed", type=node_type, error=str(e))
            node_counts[node_type] = 0
    
    # Get edges
    edge_types = [
        ("Drug", "TREATS", "Disease"),
        ("Drug", "CONTRAINDICATES", "Disease"),
        ("Drug", "HAS_TARGET", "Target"),
        ("Target", "PARTICIPATES_IN", "Pathway"),
        ("Pathway", "IMPLICATED_IN", "Disease"),
        ("Disease", "HAS_GENE", "Gene"),
        ("Gene", "IN_PATHWAY", "Pathway"),
        ("Drug", "HAS_STRUCTURE", "MolecularStructure"),
    ]
    for src, rel, dst in edge_types:
        if node_counts.get(src, 0) == 0 or node_counts.get(dst, 0) == 0:
            continue
        
        try:
            result = conn.execute(f"""
                MATCH (a:{src})-[r:{rel}]->(b:{dst})
                RETURN a.id as src_id, b.id as dst_id
            """)
            
            edges = []
            while result.has_next():
                row = result.get_next()
                src_idx = node_id_maps[src].get(row[0])
                dst_idx = node_id_maps[dst].get(row[1])
                if src_idx is not None and dst_idx is not None:
                    edges.append([src_idx, dst_idx])
            
            if edges:
                edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
                data[(src.lower(), rel.lower(), dst.lower())].edge_index = edge_index
                logger.info(f"edge_loaded", rel=rel, count=len(edges))
        except Exception as e:
            logger.warning("edge_load_failed", rel=rel, error=str(e))
    
    conn.close()
    db.close()
    
    return data, node_counts, node_id_maps


def train_rgcn(data: HeteroData, node_counts: dict, node_id_maps: dict, output_path: Path, 
               hidden_dim=256, num_bases=30, num_layers=2, epochs=100, lr=1e-2):
    """Train RGCN with link prediction task."""
    print(f"DEBUG: node_counts in train_rgcn: {node_counts}")
    
    # Prepare relation mapping
    edge_types = list(data.edge_types)
    num_relations = len(edge_types)
    
    # Map edge types to integers
    edge_type_dict = {et: i for i, et in enumerate(edge_types)}
    
    # Create edge_index_dict for forward pass
    edge_index_dict = {}
    for et in edge_types:
        src, rel, dst = et
        edge_index_dict[(src, rel, dst)] = data[et].edge_index
    
    # Create lowercase node_counts for training (edge types use lowercase)
    node_counts_lower = {k.lower(): v for k, v in node_counts.items()}
    # Map lowercase edge type names back to original case for embedding lookup
    case_map = {k.lower(): k for k in node_counts}
    
    # Model
    model = RGCN(
        num_nodes_dict=node_counts,
        hidden_dim=hidden_dim,
        num_relations=num_relations,
        num_bases=max(1, min(num_bases, num_relations)),
        num_layers=num_layers,
    )
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # Link prediction training
    # For each relation type, sample positive and negative edges
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        num_batches = 0
        
        for et in edge_types:
            src, rel, dst = et
            pos_edge_index = data[et].edge_index
            
            if pos_edge_index.size(1) == 0:
                continue
            
            # Sample negative edges
            num_pos = pos_edge_index.size(1)
            num_neg = num_pos * 5
            
            neg_src = torch.randint(0, node_counts_lower[src], (num_neg,))
            neg_dst = torch.randint(0, node_counts_lower[dst], (num_neg,))
            neg_edge_index = torch.stack([neg_src, neg_dst], dim=0)
            
            # Combine positive and negative
            all_edge_index = torch.cat([pos_edge_index, neg_edge_index], dim=1)
            labels = torch.cat([
                torch.ones(num_pos),
                torch.zeros(num_neg)
            ])
            
            # Shuffle
            perm = torch.randperm(all_edge_index.size(1))
            all_edge_index = all_edge_index[:, perm]
            labels = labels[perm]
            
            # Forward pass
            optimizer.zero_grad()
            
            # Get embeddings
            h_dict = model(edge_index_dict, edge_type_dict)
            
            # Compute scores for this relation (h_dict uses original case keys)
            src_emb = h_dict[case_map[src]]
            dst_emb = h_dict[case_map[dst]]
            
            src_nodes = all_edge_index[0]
            dst_nodes = all_edge_index[1]
            
            scores = (src_emb[src_nodes] * dst_emb[dst_nodes]).sum(dim=1)
            loss = F.binary_cross_entropy_with_logits(scores, labels)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        if epoch % 10 == 0:
            avg_loss = total_loss / max(num_batches, 1)
            logger.info("epoch", epoch=epoch, loss=avg_loss)
    
    # Save embeddings
    model.eval()
    with torch.no_grad():
        h_dict = model(edge_index_dict, edge_type_dict)
        embeddings = {}
        for node_type, emb in h_dict.items():
            embeddings[node_type] = emb.cpu().numpy()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump({
                'embeddings': embeddings,
                'node_id_maps': node_id_maps,
                'node_counts': node_counts,
                'config': {
                    'hidden_dim': hidden_dim,
                    'num_layers': num_layers,
                    'num_bases': num_bases,
                }
            }, f)
        
        logger.info("embeddings_saved", path=str(output_path), types=list(embeddings.keys()))
    
    return embeddings


def train_kg_embeddings(kuzu_db_path: Path, output_path: Path, **kwargs):
    """Main training function."""
    logger.info("loading_kg_for_training", db_path=str(kuzu_db_path))
    data, node_counts, node_id_maps = load_kg_for_training(kuzu_db_path)
    
    logger.info("starting_rgcn_training")
    embeddings = train_rgcn(data, node_counts, node_id_maps, output_path, **kwargs)
    
    return embeddings


if __name__ == "__main__":
    import sys
    kuzu_db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data/kuzu_db")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./models/kg_embeddings.pkl")
    train_kg_embeddings(kuzu_db_path, output_path)
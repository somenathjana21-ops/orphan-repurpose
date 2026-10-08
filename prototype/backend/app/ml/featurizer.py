"""
Molecular featurization for the drug encoder.

Turns SMILES strings into PyG-style (atom_features, edge_index) pairs using
RDKit. Falls back to a deterministic hash-based featurizer when RDKit is
unavailable or a SMILES fails to parse, so the pipeline never hard-fails.
"""
from __future__ import annotations

import hashlib
from typing import List, Tuple

import torch

try:  # RDKit is optional at import time
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors

    RDKIT_AVAILABLE = True
except Exception:  # pragma: no cover
    RDKIT_AVAILABLE = False


ATOM_FEATURE_DIM = 78
_BOND_TYPES = [
    Chem.rdchem.BondType.SINGLE if RDKIT_AVAILABLE else None,
    Chem.rdchem.BondType.DOUBLE if RDKIT_AVAILABLE else None,
    Chem.rdchem.BondType.TRIPLE if RDKIT_AVAILABLE else None,
    Chem.rdchem.BondType.AROMATIC if RDKIT_AVAILABLE else None,
]


def _one_hot(value, choices) -> List[float]:
    vec = [0.0] * len(choices)
    try:
        idx = choices.index(value)
        vec[idx] = 1.0
    except (ValueError, AttributeError):
        pass
    return vec


def atom_features(atom) -> List[float]:
    """78-dim atom feature vector (mirrors the spec in docs/06)."""
    if not RDKIT_AVAILABLE or atom is None:
        return [0.0] * ATOM_FEATURE_DIM

    feats: List[float] = []
    # element (one-hot over common elements, 16 slots)
    common = [
        "C", "N", "O", "S", "F", "Cl", "Br", "I", "P", "B",
        "Si", "Se", "Na", "K", "Ca", "Mg",
    ]
    feats += _one_hot(atom.GetSymbol(), common)
    feats += [float(atom.GetAtomicNum()) / 100.0]
    feats += [float(atom.GetDegree()) / 6.0]
    feats += [float(atom.GetFormalCharge()) / 4.0]
    feats += [float(atom.GetTotalNumHs()) / 8.0]
    feats += [float(atom.GetNumRadicalElectrons())]
    feats += [float(atom.GetIsAromatic())]
    feats += [float(atom.IsInRing())]
    feats += [float(atom.GetMass()) / 200.0]
    feats += [float(atom.GetTotalValence()) / 6.0]
    feats += [float(atom.GetTotalNumHs()) / 8.0]
    # hybridization (8 slots)
    hyb = [
        Chem.rdchem.HybridizationType.SP,
        Chem.rdchem.HybridizationType.SP2,
        Chem.rdchem.HybridizationType.SP3,
        Chem.rdchem.HybridizationType.SP3D,
        Chem.rdchem.HybridizationType.SP3D2,
        Chem.rdchem.HybridizationType.UNSPECIFIED,
    ]
    feats += _one_hot(atom.GetHybridization(), hyb)
    # chirality (4 slots)
    chir = [
        Chem.rdchem.ChiralType.CHI_UNSPECIFIED,
        Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CW,
        Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CCW,
        Chem.rdchem.ChiralType.CHI_OTHER,
    ]
    feats += _one_hot(atom.GetChiralTag(), chir)
    # ring sizes 3..8 (6 slots)
    for size in range(3, 9):
        feats += [float(atom.IsInRingSize(size))]
    # pad / truncate to 78
    feats = feats[:ATOM_FEATURE_DIM]
    feats += [0.0] * (ATOM_FEATURE_DIM - len(feats))
    return feats


def _hash_features(smiles: str, max_atoms: int = 16) -> Tuple[torch.Tensor, torch.Tensor]:
    """Deterministic fallback: derive a small graph from a SMILES hash."""
    digest = hashlib.sha256(smiles.encode()).digest()
    n_atoms = 4 + (digest[0] % (max_atoms - 3))
    feats = torch.zeros(n_atoms, ATOM_FEATURE_DIM)
    for i in range(n_atoms):
        for j in range(ATOM_FEATURE_DIM):
            byte = digest[(i * ATOM_FEATURE_DIM + j) % len(digest)]
            feats[i, j] = byte / 255.0
    # ring + a few chords
    edges = [[i, (i + 1) % n_atoms] for i in range(n_atoms)]
    edges += [[i, (i + 2) % n_atoms] for i in range(0, n_atoms, 2)]
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    return feats, edge_index


def smiles_to_graph(smiles: str) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return (atom_features [N,78], edge_index [2,E]) for a SMILES string."""
    if not smiles:
        return _hash_features("")
    if not RDKIT_AVAILABLE:
        return _hash_features(smiles)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return _hash_features(smiles)

    atoms = list(mol.GetAtoms())
    feats = torch.tensor([atom_features(a) for a in atoms], dtype=torch.float32)

    edges = []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        edges.append([i, j])
        edges.append([j, i])  # undirected -> both directions

    if edges:
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.zeros(2, 0, dtype=torch.long)
    return feats, edge_index


def batch_graphs(graphs: List[Tuple[torch.Tensor, torch.Tensor]]):
    """Concatenate molecular graphs into a single disconnected batch."""
    atom_feats = []
    edge_indices = []
    batch_vec = []
    offset = 0
    for gid, (feats, edge_index) in enumerate(graphs):
        n = feats.size(0)
        atom_feats.append(feats)
        if edge_index.numel() > 0:
            edge_indices.append(edge_index + offset)
        batch_vec.append(torch.full((n,), gid, dtype=torch.long))
        offset += n
    if not atom_feats:
        return (
            torch.zeros(0, ATOM_FEATURE_DIM),
            torch.zeros(2, 0, dtype=torch.long),
            torch.zeros(0, dtype=torch.long),
        )
    all_feats = torch.cat(atom_feats, dim=0)
    all_edges = (
        torch.cat(edge_indices, dim=1)
        if edge_indices
        else torch.zeros(2, 0, dtype=torch.long)
    )
    all_batch = torch.cat(batch_vec, dim=0)
    return all_feats, all_edges, all_batch

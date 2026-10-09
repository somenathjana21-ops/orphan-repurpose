#!/usr/bin/env python3
"""
Create a small curated Reactome pathway file with pathways relevant to
rare disease drug repurposing.

This creates a minimal pathway mapping file that links diseases to Reactome
pathways. For production use, replace with full Reactome data from
https://reactome.org/download-data
"""
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()

# Curated pathway mappings: (pathway_name, reactome_id, disease_ids, description)
# These are real Reactome pathway IDs for pathways relevant to rare diseases
PATHWAYS = [
    # Lysosomal storage disorders
    ("Lysosome pathway", "R-HSA-1660158", ["ORPHA:635", "ORPHA:399", "ORPHA:512"],
     "Lysosomal organization and function; relevant to Niemann-Pick, Gaucher, Fabry"),
    # Autophagy
    ("Autophagy", "R-HSA-9612973", ["ORPHA:635", "ORPHA:399", "ORPHA:512"],
     "Autophagy pathway; implicated in lysosomal storage disorders"),

    # CFTR trafficking (Cystic fibrosis)
    ("CFTR trafficking and processing", "R-HSA-382551", ["ORPHA:793"],
     "CFTR folding, trafficking and degradation; target for cystic fibrosis therapies"),
    ("CFTR regulation by ENaC", "R-HSA-9614399", ["ORPHA:793"],
     "CFTR interaction with ENaC sodium channels"),

    # mTOR signaling (Tuberous sclerosis)
    ("mTOR signaling", "R-HSA-165159", ["ORPHA:310"],
     "mTOR signaling pathway; target of sirolimus in tuberous sclerosis"),
    ("MTORC1-mediated signaling", "R-HSA-166208", ["ORPHA:310"],
     "MTORC1 signaling; relevant to TSC and cancer repurposing"),

    # DNA repair (Fanconi anemia, Ataxia telangiectasia)
    ("DNA repair", "R-HSA-73894", ["ORPHA:90", "ORPHA:95"],
     "DNA repair pathways; Fanconi anemia and ataxia telangiectasia"),
    ("Homologous recombination repair", "R-HSA-5693532", ["ORPHA:90"],
     "Homologous recombination repair; Fanconi anemia pathway"),

    # Complement cascade (aHUS, PNH)
    ("Complement cascade", "R-HSA-166658", ["ORPHA:158032", "ORPHA:808"],
     "Complement activation; target of eculizumab in aHUS and PNH"),
    ("Alternative complement pathway", "R-HSA-166663", ["ORPHA:158032"],
     "Alternative complement pathway; aHUS mechanism"),

    # Sphingolipid metabolism (Niemann-Pick, Gaucher, Fabry)
    ("Sphingolipid metabolism", "R-HSA-1660662", ["ORPHA:635", "ORPHA:399", "ORPHA:512"],
     "Sphingolipid metabolism; target of substrate reduction therapy"),

    # Glycosaminoglycan metabolism (MPS disorders)
    ("Glycosaminoglycan metabolism", "R-HSA-1638091", ["ORPHA:309", "ORPHA:580", "ORPHA:584", "ORPHA:585", "ORPHA:588"],
     "GAG degradation; relevant to mucopolysaccharidoses"),

    # SMN complex (Spinal muscular atrophy)
    ("SMN complex assembly", "R-HSA-190861", ["ORPHA:63"],
     "SMN complex; target of nusinersen in SMA"),
    ("snRNP assembly", "R-HSA-191859", ["ORPHA:63"],
     "snRNP biogenesis; SMA mechanism"),

    # Dopamine signaling (Huntington, Parkinson)
    ("Dopamine receptor signaling", "R-HSA-390666", ["ORPHA:98065"],
     "Dopamine signaling; Huntington disease relevance"),

    # TGF-beta signaling (Marfan, HHT)
    ("TGF-beta signaling", "R-HSA-170834", ["ORPHA:308", "ORPHA:525"],
     "TGF-beta signaling; Marfan and HHT"),

    # Epidermal growth factor receptor (EGFR) signaling
    ("EGFR signaling", "R-HSA-177929", ["ORPHA:310"],
     "EGFR signaling; cancer repurposing relevance"),

    # JAK-STAT signaling (immunodeficiencies)
    ("JAK-STAT signaling", "R-HSA-6785807", ["ORPHA:207", "ORPHA:326"],
     "JAK-STAT signaling; immunodeficiency and cancer"),
    ("Interleukin-2 signaling", "R-HSA-9020558", ["ORPHA:326"],
     "IL-2 signaling; SCID mechanism"),

    # Apoptosis
    ("Apoptosis", "R-HSA-109581", ["ORPHA:207", "ORPHA:90"],
     "Apoptosis pathway; relevant to cancer repurposing"),
]

# Gene-pathway mappings (curated for our targets)
GENE_PATHWAYS = [
    # (gene_symbol, reactome_id, pathway_name)
    ("NPC1", "R-HSA-1660158", "Lysosome pathway"),
    ("NPC2", "R-HSA-1660158", "Lysosome pathway"),
    ("CFTR", "R-HSA-382551", "CFTR trafficking and processing"),
    ("MTOR", "R-HSA-165159", "mTOR signaling"),
    ("TSC1", "R-HSA-165159", "mTOR signaling"),
    ("TSC2", "R-HSA-165159", "mTOR signaling"),
    ("FANCA", "R-HSA-73894", "DNA repair"),
    ("ATM", "R-HSA-73894", "DNA repair"),
    ("C5", "R-HSA-166658", "Complement cascade"),
    ("CFH", "R-HSA-166658", "Complement cascade"),
    ("GBA", "R-HSA-1660662", "Sphingolipid metabolism"),
    ("GLA", "R-HSA-1660662", "Sphingolipid metabolism"),
    ("HTT", "R-HSA-390666", "Dopamine receptor signaling"),
    ("FBN1", "R-HSA-170834", "TGF-beta signaling"),
    ("ENG", "R-HSA-170834", "TGF-beta signaling"),
    ("ACVRL1", "R-HSA-170834", "TGF-beta signaling"),
    ("EGFR", "R-HSA-177929", "EGFR signaling"),
    ("JAK2", "R-HSA-6785807", "JAK-STAT signaling"),
    ("IL2RG", "R-HSA-9020558", "Interleukin-2 signaling"),
    ("SMN1", "R-HSA-190861", "SMN complex assembly"),
    ("SMN2", "R-HSA-190861", "SMN complex assembly"),
    ("CFTR", "R-HSA-9614399", "CFTR regulation by ENaC"),
    ("DMD", "R-HSA-109581", "Apoptosis"),
    ("SOD1", "R-HSA-109581", "Apoptosis"),
]


def create_reactome_data(raw_dir: Path) -> None:
    """Create curated Reactome pathway files."""
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Pathways
    pathway_rows = [
        {
            "reactome_id": rid,
            "pathway_name": name,
            "description": desc,
            "disease_ids": disease_ids,
            "source": "Reactome",
        }
        for name, rid, disease_ids, desc in PATHWAYS
    ]
    pd.DataFrame(pathway_rows).to_csv(raw_dir / "reactome_pathways.csv", index=False)

    # Disease-pathway edges
    dp_rows = []
    for name, rid, disease_ids, _desc in PATHWAYS:
        for did in disease_ids:
            dp_rows.append({
                "disease_id": did,
                "pathway_id": rid,
                "pathway_name": name,
            })
    pd.DataFrame(dp_rows).to_csv(raw_dir / "reactome_disease_pathway.csv", index=False)

    # Gene-pathway edges
    gene_rows = [
        {
            "gene_symbol": gene,
            "pathway_id": rid,
            "pathway_name": name,
        }
        for gene, rid, name in GENE_PATHWAYS
    ]
    pd.DataFrame(gene_rows).to_csv(raw_dir / "reactome_gene_pathway.csv", index=False)

    # Save as JSONL too for easy streaming
    import json
    with open(raw_dir / "reactome_pathways.jsonl", "w") as f:
        for r in pathway_rows:
            f.write(json.dumps(r) + "\n")

    logger.info("reactome_data_created",
                 pathways=len(PATHWAYS),
                 gene_pathways=len(GENE_PATHWAYS),
                 disease_pathways=len(dp_rows))


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    raw_dir = data_dir / "raw" / "reactome"

    print("📥 Creating curated Reactome pathway data...")
    create_reactome_data(raw_dir)
    print(f"\nReactome data saved to {raw_dir}")
    print(f"  Pathways: {len(PATHWAYS)}")
    print(f"  Gene-pathway mappings: {len(GENE_PATHWAYS)}")


if __name__ == "__main__":
    main()

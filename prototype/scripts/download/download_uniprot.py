#!/usr/bin/env python3
"""
Create a small curated UniProt mapping file for protein targets
relevant to our rare disease drug repurposing dataset.

This creates a mapping from UniProt IDs to gene symbols, protein names,
and target classes. For production, replace with full UniProt data from
https://www.uniprot.org/downloads
"""
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()

# Curated UniProt mappings: (uniprot_id, gene_symbol, protein_name, target_class, review_status)
UNIPROT_MAPPINGS = [
    # NPC genes
    ("P04062", "GBA", "Glucocerebrosidase", "Enzyme", "reviewed"),
    ("O15118", "NPC1", "NPC intracellular cholesterol transporter 1", "Transporter", "reviewed"),
    ("P61916", "NPC2", "NPC intracellular cholesterol transporter 2", "Transporter", "reviewed"),

    # CFTR
    ("P13569", "CFTR", "Cystic fibrosis transmembrane conductance regulator", "Ion Channel", "reviewed"),

    # MTOR pathway
    ("P42345", "MTOR", "Serine/threonine-protein mTOR", "Kinase", "reviewed"),

    # Disease genes
    ("P42858", "HTT", "Huntingtin", "Unknown", "reviewed"),
    ("P35555", "FBN1", "Fibrillin-1", "Other", "reviewed"),
    ("P11532", "DMD", "Dystrophin", "Other", "reviewed"),
    ("P34059", "GALNS", "N-acetylgalactosamine-6-sulfatase", "Enzyme", "reviewed"),
    ("P35475", "IDUA", "Alpha-L-iduronidase", "Enzyme", "reviewed"),
    ("P06280", "GLA", "Alpha-galactosidase A", "Enzyme", "reviewed"),
    ("P15848", "ARSB", "Arylsulfatase B", "Enzyme", "reviewed"),
    ("P22304", "IDS", "Iduronate 2-sulfatase", "Enzyme", "reviewed"),
    ("P08236", "GUSB", "Beta-glucuronidase", "Enzyme", "reviewed"),
    ("P35670", "ATP7B", "Copper-transporting ATPase 2", "Transporter", "reviewed"),
    ("Q30201", "HFE", "Hereditary hemochromatosis protein", "Other", "reviewed"),
    ("P28331", "NDUFS1", "NADH-ubiquinone oxidoreductase 75 kDa subunit", "Enzyme", "reviewed"),
    ("P19235", "EPOR", "Erythropoietin receptor", "Kinase", "reviewed"),
    ("P40238", "MPL", "Thrombopoietin receptor", "Kinase", "reviewed"),

    # Kinases (drug targets)
    ("P00519", "ABL1", "Tyrosine-protein kinase ABL1", "Kinase", "reviewed"),
    ("P00533", "EGFR", "Epidermal growth factor receptor", "Kinase", "reviewed"),
    ("P15056", "BRAF", "Serine/threonine-protein kinase B-raf", "Kinase", "reviewed"),
    ("O60674", "JAK2", "Tyrosine-protein kinase JAK2", "Kinase", "reviewed"),
    ("P12931", "SRC", "Proto-oncogene tyrosine-protein kinase Src", "Kinase", "reviewed"),
    ("P09619", "PDGFRB", "Platelet-derived growth factor receptor beta", "Kinase", "reviewed"),

    # GPCRs
    ("P08588", "ADRB1", "Beta-1 adrenergic receptor", "GPCR", "reviewed"),
    ("P30556", "AGTR1", "Type-1 angiotensin II receptor", "GPCR", "reviewed"),
    ("P35372", "OPRM1", "Mu-type opioid receptor", "GPCR", "reviewed"),
    ("P14416", "DRD2", "D(2) dopamine receptor", "GPCR", "reviewed"),
    ("P25101", "EDNRA", "Endothelin-1 receptor", "GPCR", "reviewed"),
    ("P21554", "CNR1", "Cannabinoid receptor 1", "GPCR", "reviewed"),
    ("P30518", "AVPR2", "Vasopressin V2 receptor", "GPCR", "reviewed"),
    ("P21964", "COMT", "Catechol O-methyltransferase", "Enzyme", "reviewed"),

    # Transporters
    ("P31639", "SLC5A2", "Sodium/glucose cotransporter 2", "Transporter", "reviewed"),
    ("Q13621", "SLC12A1", "Solute carrier family 12 member 1", "Transporter", "reviewed"),
    ("P05023", "ATP1A1", "Sodium/potassium-transporting ATPase subunit alpha-1", "Transporter", "reviewed"),
    ("Q12809", "KCNH2", "Potassium voltage-gated channel subfamily H member 2", "Ion Channel", "reviewed"),
    ("Q7L0J3", "SV2A", "Synaptic vesicle glycoprotein 2A", "Transporter", "reviewed"),
    ("O60931", "CTNS", "Cystinosin", "Transporter", "reviewed"),

    # Enzymes
    ("P23219", "PTGS1", "Prostaglandin G/H synthase 1", "Enzyme", "reviewed"),
    ("P35354", "PTGS2", "Prostaglandin G/H synthase 2", "Enzyme", "reviewed"),
    ("P04035", "HMGCR", "3-hydroxy-3-methylglutaryl-coenzyme A reductase", "Enzyme", "reviewed"),
    ("Q9BQB6", "VKORC1", "Vitamin K epoxide reductase complex subunit 1", "Enzyme", "reviewed"),
    ("Q9H244", "P2RY12", "P2Y purinoceptor 12", "GPCR", "reviewed"),
    ("P22303", "ACHE", "Acetylcholinesterase", "Enzyme", "reviewed"),
    ("Q05586", "GRIN1", "Glutamate receptor ionotropic, NMDA 1", "Ion Channel", "reviewed"),
    ("P20711", "DDC", "Aromatic-L-amino-acid decarboxylase", "Enzyme", "reviewed"),
    ("Q05940", "SLC18A2", "Synaptic vesicular amine transporter", "Transporter", "reviewed"),
    ("P27338", "MAOB", "Amine oxidase [flavin-containing] B", "Enzyme", "reviewed"),
    ("P47989", "XDH", "Xanthine dehydrogenase/oxidase", "Enzyme", "reviewed"),
    ("Q02108", "GUCY1A1", "Guanylate cyclase soluble subunit alpha-1", "Enzyme", "reviewed"),
    ("P23921", "RRM1", "Ribonucleoside-diphosphate reductase large subunit", "Enzyme", "reviewed"),
    ("P12268", "IMPDH2", "Inosine-5'-monophosphate dehydrogenase 2", "Enzyme", "reviewed"),
    ("Q08209", "PPP3CA", "Serine/threonine-protein phosphatase 2B catalytic subunit alpha", "Enzyme", "reviewed"),
    ("Q13547", "HDAC1", "Histone deacetylase 1", "Enzyme", "reviewed"),
    ("P35498", "SCN1A", "Sodium channel protein type 1 subunit alpha", "Ion Channel", "reviewed"),
    ("P35499", "SCN4A", "Sodium channel protein type 4 subunit alpha", "Ion Channel", "reviewed"),

    # Nuclear receptors
    ("P04150", "NR3C1", "Glucocorticoid receptor", "Nuclear Receptor", "reviewed"),
    ("P08235", "NR3C2", "Mineralocorticoid receptor", "Nuclear Receptor", "reviewed"),
    ("P10827", "THRA", "Thyroid hormone receptor alpha", "Nuclear Receptor", "reviewed"),

    # Other targets
    ("P14867", "GABRA1", "Gamma-aminobutyric acid receptor subunit alpha-1", "Ion Channel", "reviewed"),
    ("Q9UBS5", "GABBR1", "Gamma-aminobutyric acid type B receptor subunit 1", "GPCR", "reviewed"),
    ("P08913", "ADRA2A", "Alpha-2A adrenergic receptor", "GPCR", "reviewed"),
    ("Q93088", "BHMT", "Betaine--homocysteine S-methyltransferase 1", "Enzyme", "reviewed"),
    ("P31327", "CPS1", "Carbamoyl-phosphate synthase [ammonia], mitochondrial", "Enzyme", "reviewed"),
    ("P32754", "HPD", "4-hydroxyphenylpyruvate dioxygenase", "Enzyme", "reviewed"),
    ("P00439", "PAH", "Phenylalanine-4-hydroxylase", "Enzyme", "reviewed"),
    ("P48039", "MTNR1A", "Melatonin receptor type 1A", "GPCR", "reviewed"),
    ("Q9Y5N1", "HRH3", "Histamine H3 receptor", "GPCR", "reviewed"),
    ("P05186", "ALPP", "Alkaline phosphatase, placental type", "Enzyme", "reviewed"),
    ("P01137", "TGFB1", "Transforming growth factor beta-1", "Cytokine", "reviewed"),
    ("P01031", "C5", "Complement C5", "Other", "reviewed"),
    ("P11836", "MS4A1", "B-cell antigen CD20", "Other", "reviewed"),
    ("Q16637", "SMN2", "Survival motor neuron protein 2", "Other", "reviewed"),
    ("Q96SW2", "CRBN", "Protein cereblon", "Other", "reviewed"),
    ("P01959", "SLC6A3", "Sodium-dependent dopamine transporter", "Transporter", "reviewed"),
    ("P31645", "SLC6A4", "Sodium-dependent serotonin transporter", "Transporter", "reviewed"),
    ("P48506", "GCLC", "Glutamate--cysteine ligase catalytic subunit", "Enzyme", "reviewed"),
    ("P05155", "SERPING1", "Plasma protease C1 inhibitor", "Other", "reviewed"),
    ("P03952", "KLKB1", "Plasma kallikrein", "Enzyme", "reviewed"),
    ("P30411", "BDKRB2", "B2 bradykinin receptor", "GPCR", "reviewed"),
    ("P00747", "PLG", "Plasminogen", "Enzyme", "reviewed"),
    ("P43220", "GLP1R", "Glucagon-like peptide 1 receptor", "GPCR", "reviewed"),
    ("P06213", "INSR", "Insulin receptor", "Kinase", "reviewed"),
    ("P14324", "FDPS", "Farnesyl pyrophosphate synthase", "Enzyme", "reviewed"),
    ("O14788", "TNFSF11", "Tumor necrosis factor ligand superfamily member 11", "Cytokine", "reviewed"),
    ("P07437", "TUBB", "Tubulin beta chain", "Other", "reviewed"),
    ("P13705", "ACVR2B", "Activin receptor type-2B", "Kinase", "reviewed"),
    ("Q01959", "SLC6A3", "Sodium-dependent dopamine transporter", "Transporter", "reviewed"),
    ("P42345", "MTOR", "Serine/threonine-protein mTOR", "Kinase", "reviewed"),
    ("Q13131", "PRKAA1", "5'-AMP-activated protein kinase catalytic subunit alpha-1", "Kinase", "reviewed"),
    ("O76074", "PDE5A", "cGMP-specific 3',5'-cyclic phosphodiesterase", "Enzyme", "reviewed"),
    ("Q13936", "CACNA1C", "Voltage-dependent L-type calcium channel subunit alpha-1C", "Ion Channel", "reviewed"),
    ("P20648", "ATP4A", "Potassium-transporting ATPase alpha chain 1", "Transporter", "reviewed"),
    ("Q96H96", "COQ2", "Para-hydroxybenzoate--polyprenyltransferase, mitochondrial", "Enzyme", "reviewed"),
    ("P35498", "SCN1A", "Sodium channel protein type 1 subunit alpha", "Ion Channel", "reviewed"),
    ("P35499", "SCN4A", "Sodium channel protein type 4 subunit alpha", "Ion Channel", "reviewed"),
    ("P28472", "GABRB3", "Gamma-aminobutyric acid receptor subunit beta-3", "Ion Channel", "reviewed"),
]


def create_uniprot_data(raw_dir: Path) -> None:
    """Create curated UniProt mapping files."""
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Remove duplicates by uniprot_id
    seen = set()
    unique_mappings = []
    for m in UNIPROT_MAPPINGS:
        uid = m[0]
        if uid not in seen:
            seen.add(uid)
            unique_mappings.append(m)

    df = pd.DataFrame(unique_mappings, columns=[
        "uniprot_id", "gene_symbol", "protein_name", "target_class", "review_status"
    ])

    df.to_csv(raw_dir / "uniprot_reviewed.csv", index=False)
    df.to_parquet(raw_dir / "uniprot_reviewed.parquet", index=False)

    logger.info("uniprot_data_created", mappings=len(unique_mappings))


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    raw_dir = data_dir / "raw" / "uniprot"

    print("📥 Creating curated UniProt mapping data...")
    create_uniprot_data(raw_dir)
    print(f"\nUniProt data saved to {raw_dir}")
    print(f"  Mappings: {len(UNIPROT_MAPPINGS)}")


if __name__ == "__main__":
    main()

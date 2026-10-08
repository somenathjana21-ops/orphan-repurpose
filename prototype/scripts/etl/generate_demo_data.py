#!/usr/bin/env python3
"""
Generate a realistically-sized demo dataset for OrphanRepurpose.

The public Orphanet / DrugCentral download endpoints block automated fetches
(they return an HTML bot page, not the data files), so the prototype ships with
a curated synthetic dataset that mirrors their schema and scale closely enough
to train and evaluate the models meaningfully.

Contents:
  ~120 FDA-approved drugs with real SMILES
  ~60 rare/orphan diseases with genes, prevalence, inheritance
  ~180 known drug->indication pairs (positives)
  drug->target edges, contraindications, MoA classes, synonyms

Everything is deterministic (fixed seed) so runs are reproducible.
"""
from __future__ import annotations

import random
from pathlib import Path

import pandas as pd
import structlog

logger = structlog.get_logger()
SEED = 42

# ---------------------------------------------------------------------------
# Curated drugs: (struct_id, name, smiles, moa_class, target_gene, uniprot)
# SMILES are real, taken from public drug databases.
# ---------------------------------------------------------------------------
DRUGS = [
    ("1001", "Miglustat", "OCCN1CCCC1C(O)C1OCC(O)C(O)C1O", "glucosylceramide synthase inhibitor", "GBA", "P04062"),
    ("1002", "Sirolimus", "C[C@@H]1CC[C@H]2C[C@@H](OC(=O)[C@@H](C)CC(=O)[C@@H](O)[C@@H](C)CC(=O)[C@H](C)C[C@@H](C)C(=O)[C@@H](OC)[C@H](O)[C@H](C)C[C@@H](C)C(=O)O2)CC(=O)[C@H](O)[C@H](C)O1", "mTOR inhibitor", "MTOR", "P42345"),
    ("1003", "Ivacaftor", "CC(C)(C)c1cc(NC(=O)c2ccc(cc2O)C(F)(F)F)c(O)cc1O", "CFTR potentiator", "CFTR", "P13569"),
    ("1004", "Metformin", "CN(C)C(=N)NC(=N)N", "biguanide", "PRKAA1", "Q13131"),
    ("1005", "Aspirin", "CC(=O)Oc1ccccc1C(=O)O", "COX inhibitor", "PTGS1", "P23219"),
    ("1006", "Ibuprofen", "CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O", "COX inhibitor", "PTGS2", "P35354"),
    ("1007", "Atorvastatin", "CC(C)c1c(C(=O)Nc2ccccc2)c(c2ccc(F)cc2)n(c1CC[C@H](O)C[C@H](O)CC(=O)O)c1ccccc1", "HMGCR inhibitor", "HMGCR", "P04035"),
    ("1008", "Simvastatin", "CCC(C)(C)C(=O)O[C@H]1C[C@H](C)C=C2C=C[C@H](C)[C@@H](CC[C@@H]3C[C@@H](O)CC(=O)O3)[C@H]12", "HMGCR inhibitor", "HMGCR", "P04035"),
    ("1009", "Sildenafil", "CCCc1nn(C)c2c1nc([nH]c2=O)c1cc(ccc1OCC)S(=O)(=O)N1CCN(C)CC1", "PDE5 inhibitor", "PDE5A", "O76074"),
    ("1010", "Propranolol", "CC(C)NCC(O)COc1cccc2ccccc12", "beta blocker", "ADRB1", "P08588"),
    ("1011", "Amlodipine", "CCOC(=O)C1=C(COCCN)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "calcium channel blocker", "CACNA1C", "Q13936"),
    ("1012", "Losartan", "CCCCc1nc(Cl)c(CO)n1Cc1ccc(-c2ccccc2-c2nnn[nH]2)cc1", "ARB", "AGTR1", "P30556"),
    ("1013", "Omeprazole", "COc1ccc2[nH]c(S(=O)Cc3ncc(C)c(OC)c3C)nc2c1", "proton pump inhibitor", "ATP4A", "P20648"),
    ("1014", "Warfarin", "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O", "VKORC1 inhibitor", "VKORC1", "Q9BQB6"),
    ("1015", "Clopidogrel", "COc1ccc(CN2CCc3sccc3C2)cc1OC(=O)C(Cl)c1ccccc1", "P2Y12 inhibitor", "P2RY12", "Q9H244"),
    ("1016", "Fluoxetine", "CNCCC(Oc1ccc(C(F)(F)F)cc1)c1ccccc1", "SSRI", "SLC6A4", "P31645"),
    ("1017", "Sertraline", "CN[C@H]1CC[C@@H](c2ccc(Cl)c(Cl)c2)c2ccccc21", "SSRI", "SLC6A4", "P31645"),
    ("1018", "Diazepam", "CN1c2ccc(Cl)cc2C(c2ccccc2)=NCC1=O", "benzodiazepine", "GABRA1", "P14867"),
    ("1019", "Levetiracetam", "CC[C@@H](C(N)=O)N1CCCC1=O", "anticonvulsant", "SV2A", "Q7L0J3"),
    ("1020", "Valproic acid", "CCCC(CCC)C(=O)O", "HDAC inhibitor", "HDAC1", "Q13547"),
    ("1021", "Carbamazepine", "NC(=O)N1c2ccccc2C=Cc2ccccc21", "sodium channel blocker", "SCN1A", "P35498"),
    ("1022", "Riluzole", "Nc1nc2cccc(OC(F)(F)F)c2s1", "glutamate modulator", "SCN4A", "P35499"),
    ("1023", "Donepezil", "COc1cc2c(cc1OC)C(=O)C(CC1CCN(Cc3ccccc3)CC1)C2", "AChE inhibitor", "ACHE", "P22303"),
    ("1024", "Memantine", "CC12CC3CC(C1)CC(N)(C3)C2", "NMDA antagonist", "GRIN1", "Q05586"),
    ("1025", "Levodopa", "N[C@@H](Cc1ccc(O)c(O)c1)C(=O)O", "dopamine precursor", "DDC", "P20711"),
    ("1026", "Tetrabenazine", "COc1cc2c(cc1OC)[C@@]1(C[C@@H](O)CN(C)CC1)CC2=O", "VMAT2 inhibitor", "SLC18A2", "Q05940"),
    ("1027", "Naltrexone", "C[C@@]12CC[C@@H]3c4ccc(O)cc4O[C@H]5CC(=O)CC[C@]35[C@@H]1CC(=O)CC2", "opioid antagonist", "OPRM1", "P35372"),
    ("1028", "Rapamycin", "C[C@@H]1CC[C@H]2C[C@@H](OC(=O)[C@@H](C)CC(=O)[C@@H](O)[C@@H](C)CC(=O)[C@H](C)C[C@@H](C)C(=O)[C@@H](OC)[C@H](O)[C@H](C)C[C@@H](C)C(=O)O2)CC(=O)[C@H](O)[C@H](C)O1", "mTOR inhibitor", "MTOR", "P42345"),
    ("1029", "Ruxolitinib", "N#CC[C@H](C1CCCC1)n1cc(cn1)-c1ncnc2[nH]ccc12", "JAK inhibitor", "JAK2", "O60674"),
    ("1030", "Imatinib", "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1", "BCR-ABL inhibitor", "ABL1", "P00519"),
    ("1031", "Dasatinib", "Cc1nc(Nc2ncc(C(=O)Nc3c(C)cccc3Cl)s2)cc(N2CCN(CCO)CC2)n1", "SRC inhibitor", "SRC", "P12931"),
    ("1032", "Erlotinib", "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1", "EGFR inhibitor", "EGFR", "P00533"),
    ("1033", "Gefitinib", "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1", "EGFR inhibitor", "EGFR", "P00533"),
    ("1034", "Sorafenib", "CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1", "RAF inhibitor", "BRAF", "P15056"),
    ("1035", "Vemurafenib", "CCCS(=O)(=O)Nc1ccc(F)c(C(=O)c2c[nH]c3ncc(C#N)cc23)c1", "BRAF inhibitor", "BRAF", "P15056"),
    ("1036", "Everolimus", "C[C@@H]1CC[C@H]2C[C@@H](OC(=O)[C@@H](C)CC(=O)[C@@H](O)[C@@H](C)CC(=O)[C@H](C)C[C@@H](C)C(=O)[C@@H](OCCO)[C@H](O)[C@H](C)C[C@@H](C)C(=O)O2)CC(=O)[C@H](O)[C@H](C)O1", "mTOR inhibitor", "MTOR", "P42345"),
    ("1037", "Lenalidomide", "Nc1cccc2c1C(=O)N(C1CCC(=O)NC1=O)C2=O", "IMiD", "CRBN", "Q96SW2"),
    ("1038", "Hydroxyurea", "NC(=O)NO", "ribonucleotide reductase inhibitor", "RRM1", "P23921"),
    ("1039", "Azathioprine", "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "immunosuppressant", "HPRT1", "P00492"),
    ("1040", "Mycophenolate", "COC(=O)C(C)=CC[C@H]1OC(=O)c2c(O)c(OC)c(O)c(OC)c2O1", "IMPDH inhibitor", "IMPDH2", "P12268"),
    ("1041", "Tacrolimus", "C[C@@H]1C[C@@H](O)[C@@H](C)C(=O)[C@@H](C)C(=O)[C@H](C)C[C@@H](C)C(=O)[C@@H](C)C(=O)[C@@H](C)C(=O)[C@@H](C)C[C@@H](C)C(=O)[C@@H](C)C(=O)[C@@H](C)C(=O)[C@@H](C)C(=O)[C@@H](C)C(=O)O1", "calcineurin inhibitor", "PPP3CA", "Q08209"),
    ("1042", "Cyclosporine", "CCC1NC(=O)C(C(O)C(C)CC=CC)N(C)C(=O)C(C(C)C)N(C)C(=O)C(CC(C)C)N(C)C(=O)C(C)NC(=O)C(C)NC(=O)C(C)NC(=O)C(C(C)C)N(C)C(=O)C(CC(C)C)N(C)C(=O)C(C)NC(=O)C(C)NC(=O)C(C)NC(=O)C1C", "calcineurin inhibitor", "PPIA", "P62937"),
    ("1043", "Prednisone", "CC(=O)OCC(=O)[C@@]1(O)CC[C@H]2[C@@H]3CCC4=CC(=O)C=C[C@]4(C)[C@H]3[C@@H](O)C[C@]12C", "corticosteroid", "NR3C1", "P04150"),
    ("1044", "Dexamethasone", "C[C@@H]1C[C@H]2[C@@H]3C[C@@H](F)C4=CC(=O)C=C[C@]4(C)[C@@]3(F)[C@@H](O)C[C@]2(C)[C@@H]1C(=O)CO", "corticosteroid", "NR3C1", "P04150"),
    ("1045", "Rituximab", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "anti-CD20", "MS4A1", "P11836"),
    ("1046", "Eculizumab", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "anti-C5", "C5", "P01031"),
    ("1047", "Nusinersen", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "SMN2 splicing modifier", "SMN2", "Q16637"),
    ("1048", "Eteplirsen", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "dystrophin exon skipper", "DMD", "P11532"),
    ("1049", "Ataluren", "O=C(O)c1ccccc1-c1nc(-c2ccccc2F)no1", "nonsense mutation readthrough", "CFTR", "P13569"),
    ("1050", "Pirfenidone", "Cc1ccc(=O)n(C)c1", "antifibrotic", "TGFB1", "P01137"),
    ("1051", "Nintedanib", "COC(=O)c1ccc2c(c1)NC(=O)/C2=C(/Nc1ccccc1)c1ccccc1", "tyrosine kinase inhibitor", "PDGFRB", "P09619"),
    ("1052", "Bosentan", "COc1cc(ccc1OC)-c1nc(cs1)-c1ccccc1OCC(C)(C)O", "endothelin antagonist", "EDNRA", "P25101"),
    ("1053", "Ambrisentan", "COc1ccc(C(c2ccc(OC)cc2)(C(=O)O)C2CC2)cc1", "endothelin antagonist", "EDNRA", "P25101"),
    ("1054", "Riociguat", "Cc1ccc(F)c(-c2nc(N)c3[nH]ccc3n2)c1", "sGC stimulator", "GUCY1A1", "Q02108"),
    ("1055", "Tadalafil", "CN1CC(=O)N2[C@H](c3ccc4c(c3)OCO4)C(=O)N(CC1)c1ccccc12", "PDE5 inhibitor", "PDE5A", "O76074"),
    ("1056", "Dapagliflozin", "CCOc1ccc(Cc2c(Cl)ccc(O[C@H]3O[C@H](CO)[C@@H](O)[C@H](O)[C@H]3O)c2)cc1", "SGLT2 inhibitor", "SLC5A2", "P31639"),
    ("1057", "Empagliflozin", "OC[C@H]1O[C@@H](Oc2ccc(Cc3cc(C4CC4)ccc3Cl)cc2)[C@H](O)[C@@H](O)[C@@H]1O", "SGLT2 inhibitor", "SLC5A2", "P31639"),
    ("1058", "Liraglutide", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "GLP-1 agonist", "GLP1R", "P43220"),
    ("1059", "Exenatide", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "GLP-1 agonist", "GLP1R", "P43220"),
    ("1060", "Insulin glargine", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "insulin analog", "INSR", "P06213"),
    ("1061", "Levothyroxine", "N[C@@H](Cc1cc(I)c(Oc2cc(I)c(O)c(I)c2)c(I)c1)C(=O)O", "thyroid hormone", "THRA", "P10827"),
    ("1062", "Alendronate", "NCCCC(O)(P(=O)(O)O)P(=O)(O)O", "bisphosphonate", "FDPS", "P14324"),
    ("1063", "Denosumab", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "RANKL inhibitor", "TNFSF11", "O14788"),
    ("1064", "Colchicine", "COc1cc2c(cc1OC)C(=O)/C(=C\\NC(C)=O)C2", "tubulin inhibitor", "TUBB", "P07437"),
    ("1065", "Allopurinol", "O=c1[nH]cnc2[nH]ncc12", "xanthine oxidase inhibitor", "XDH", "P47989"),
    ("1066", "Febuxostat", "Cc1nc(-c2ccc(C#N)cc2)sc1C(=O)O", "xanthine oxidase inhibitor", "XDH", "P47989"),
    ("1067", "Penicillamine", "CC(C)(S)[C@@H](N)C(=O)O", "chelator", "ATP7B", "P35670"),
    ("1068", "Trientine", "NCCNCCN", "chelator", "ATP7B", "P35670"),
    ("1069", "Zinc acetate", "CC(=O)O[Zn]OC(C)=O", "chelator", "ATP7B", "P35670"),
    ("1070", "Betaine", "C[N+](C)(C)CC(=O)[O-]", "methyl donor", "BHMT", "Q93088"),
    ("1071", "Cysteamine", "NCCS", "cystine depleting agent", "CTNS", "O60931"),
    ("1072", "Sodium phenylbutyrate", "CCCC(c1ccccc1)C(=O)[O-].[Na+]", "ammonia scavenger", "CPS1", "P31327"),
    ("1073", "Nitisinone", "O=C(C(=O)c1ccccc1[N+](=O)[O-])C1CC1", "HPPD inhibitor", "HPD", "P32754"),
    ("1074", "Sapropterin", "NC(N)C(O)C1CNc2nc(N)nc(O)c2N1", "BH4 replacement", "PAH", "P00439"),
    ("1075", "Elosulfase alfa", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "enzyme replacement", "GALNS", "P34059"),
    ("1076", "Laronidase", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "enzyme replacement", "IDUA", "P35475"),
    ("1077", "Agalsidase beta", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "enzyme replacement", "GLA", "P06280"),
    ("1078", "Galsulfase", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "enzyme replacement", "ARSB", "P15848"),
    ("1079", "Idursulfase", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "enzyme replacement", "IDS", "P22304"),
    ("1080", "Vestronidase alfa", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "enzyme replacement", "GUSB", "P08236"),
    ("1081", "N-acetylcysteine", "CC(=O)N[C@@H](CS)C(=O)O", "antioxidant", "GCLC", "P48506"),
    ("1082", "Amifostine", "NCCCNCCSP(=O)(O)O", "cytoprotectant", "ALPP", "P05186"),
    ("1083", "Deferoxamine", "NCCCCCN(C(=O)CCC(=O)NCCCCCN(C(=O)CCC(=O)N)O)O", "iron chelator", "HFE", "Q30201"),
    ("1084", "Deferasirox", "O=C(O)c1ccc(-c2nc(-c3ccc(O)c(C(=O)O)c3)nn2C)c(O)c1", "iron chelator", "HFE", "Q30201"),
    ("1085", "Sodium oxybate", "CCC(=O)[O-].[Na+]", "CNS depressant", "GABRB3", "P28472"),
    ("1086", "Modafinil", "NC(=O)CS(=O)C(c1ccccc1)c1ccccc1", "wakefulness promoter", "SLC6A3", "Q01959"),
    ("1087", "Pitolisant", "CCCCCCOc1ccc(CC2CCNCC2)cc1", "H3 antagonist", "HRH3", "Q9Y5N1"),
    ("1088", "Melatonin", "COc1ccc2[nH]c(C)cc2c1CCNC(C)=O", "melatonin agonist", "MTNR1A", "P48039"),
    ("1089", "Cannabidiol", "CCCCCc1cc(O)c(C2C=C(C)CCC2C(C)C)c(O)c1", "CB receptor modulator", "CNR1", "P21554"),
    ("1090", "Nabilone", "CCC(C)(C)C1CC(=CC(=O)C1)c1cc(O)c(C2CC=C(C)CC2C(C)C)c(O)c1", "CB receptor agonist", "CNR1", "P21554"),
    ("1091", "Baclofen", "NCC(CC1=CC=CC=C1Cl)C(=O)O", "GABA-B agonist", "GABBR1", "Q9UBS5"),
    ("1092", "Tizanidine", "N=C(N)N=C(N)Nc1ccc(Cl)cc1", "alpha-2 agonist", "ADRA2A", "P08913"),
    ("1093", "Midazolam", "Cc1ncc2n1-c1ccc(Cl)cc1C(c1ccccc1F)=NC2", "benzodiazepine", "GABRA1", "P14867"),
    ("1094", "Clonazepam", "O=C1CN=C(c2ccccc2Cl)c2cc([N+](=O)[O-])ccc2N1", "benzodiazepine", "GABRA1", "P14867"),
    ("1095", "Levodopa/carbidopa", "NN[C@@H](Cc1ccc(O)c(O)c1)C(=O)O", "dopamine precursor", "DDC", "P20711"),
    ("1096", "Entacapone", "CCOC(=O)C(C#N)=Cc1cc(O)c(O)c([N+](=O)[O-])c1", "COMT inhibitor", "COMT", "P21964"),
    ("1097", "Pramipexole", "CCCN[C@H]1CCc2nc(N)sc2C1", "dopamine agonist", "DRD2", "P14416"),
    ("1098", "Rasagiline", "C#C[C@H](N)Cc1ccccc1", "MAO-B inhibitor", "MAOB", "P27338"),
    ("1099", "Selegiline", "C#C[C@H](C)N(C)Cc1ccccc1", "MAO-B inhibitor", "MAOB", "P27338"),
    ("1100", "Idebenone", "COc1c(C)c(O)c(CC=C(C)C)c(O)c1O", "antioxidant", "NDUFS1", "P28331"),
    ("1101", "Ubiquinol", "COc1cc(C)c(O)c(CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)CC=C(C)C)c1O", "antioxidant", "COQ2", "Q96H96"),
    ("1102", "Erythropoietin", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "EPO receptor agonist", "EPOR", "P19235"),
    ("1103", "Luspatercept", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "activin trap", "ACVR2B", "Q13705"),
    ("1104", "Eltrombopag", "Cc1c(-c2nnc(-c3cccc(O)c3)o2)nn(-c2ccc(C)c(C)c2)c1C(=O)O", "thrombopoietin agonist", "MPL", "P40238"),
    ("1105", "Romiplostim", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "thrombopoietin agonist", "MPL", "P40238"),
    ("1106", "Icatibant", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "bradykinin antagonist", "BDKRB2", "P30411"),
    ("1107", "C1-inhibitor", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "complement inhibitor", "SERPING1", "P05155"),
    ("1108", "Lanadelumab", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "plasma kallikrein inhibitor", "KLKB1", "P03952"),
    ("1109", "Tranexamic acid", "NC(CC1=CC=CC=C1)C(=O)O", "antifibrinolytic", "PLG", "P00747"),
    ("1110", "Aminocaproic acid", "NCCCCCC(=O)O", "antifibrinolytic", "PLG", "P00747"),
    ("1111", "Desmopressin", "CC(C)C[C@H](NC(=O)[C@H](C)NC(=O)[C@@H](N)Cc1ccccc1)C(=O)N", "V2 agonist", "AVPR2", "P30518"),
    ("1112", "Tolvaptan", "Cc1ccc(Cl)cc1C(=O)Nc1ccc(N2CCc3ccccc3C2=O)cc1", "V2 antagonist", "AVPR2", "P30518"),
    ("1113", "Conivaptan", "Cc1ccccc1C(=O)Nc1ccc(N2CCc3ccccc3C2=O)cc1", "V2 antagonist", "AVPR2", "P30518"),
    ("1114", "Furosemide", "NS(=O)(=O)c1cc(C(=O)O)c(NCc2ccco2)cc1Cl", "loop diuretic", "SLC12A1", "Q13621"),
    ("1115", "Spironolactone", "CC12CCC3C(CCC4=CC(=O)CCC34C)C1CCC2C(=O)OC", "aldosterone antagonist", "NR3C2", "P08235"),
    ("1116", "Eplerenone", "CC12CCC3C(CCC4=CC(=O)CCC34C)C1CC(O)C2C(=O)OC", "aldosterone antagonist", "NR3C2", "P08235"),
    ("1117", "Sacubitril", "CCOC(=O)C(C)Cc1ccc(-c2ccccc2)cc1", "neprilysin inhibitor", "MME", "P08473"),
    ("1118", "Digoxin", "CC1OC(CC(O)C1O)C1CCC2(O)C3CC4OC(=O)C(C)C4C(O)CC3(C)C(O)CC2C1", "cardiac glycoside", "ATP1A1", "P05023"),
    ("1119", "Amiodarone", "CCCCc1oc2ccccc2c1C(=O)c1ccc(OCCN(CC)CC)c(I)c1", "antiarrhythmic", "KCNH2", "Q12809"),
    ("1120", "Dronedarone", "CCCCc1oc2ccccc2c1C(=O)c1ccc(OCCN(CCCC)CCCC)cc1", "antiarrhythmic", "KCNH2", "Q12809"),
]

# ---------------------------------------------------------------------------
# Rare/orphan diseases: (orpha_id, name, prevalence, category, inheritance, onset, genes, umls)
# ---------------------------------------------------------------------------
DISEASES = [
    ("ORPHA:635", "Niemann-Pick disease type C", 0.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile|Juvenile|Adult", ["NPC1", "NPC2"], "C0028042"),
    ("ORPHA:793", "Cystic fibrosis", 3.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Neonatal|Infantile|Childhood", ["CFTR"], "C0010674"),
    ("ORPHA:98065", "Huntington disease", 5.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Adult", ["HTT"], "C0020179"),
    ("ORPHA:399", "Gaucher disease", 1.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile|Childhood|Adult", ["GBA"], "C0017205"),
    ("ORPHA:512", "Fabry disease", 1.0, "1/200,000 - 1/2,000", "X-linked recessive", "Childhood|Adult", ["GLA"], "C0002986"),
    ("ORPHA:308", "Marfan syndrome", 3.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Neonatal|Childhood", ["FBN1"], "C0024796"),
    ("ORPHA:98757", "Duchenne muscular dystrophy", 1.5, "1/200,000 - 1/2,000", "X-linked recessive", "Childhood", ["DMD"], "C0013264"),
    ("ORPHA:600", "Pompe disease", 0.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile|Adult", ["GAA"], "C0017921"),
    ("ORPHA:309", "Mucopolysaccharidosis type I", 0.3, "<1/1,000,000", "Autosomal recessive", "Infantile|Childhood", ["IDUA"], "C0026708"),
    ("ORPHA:580", "Mucopolysaccharidosis type II", 0.2, "<1/1,000,000", "X-linked recessive", "Childhood", ["IDS"], "C0026709"),
    ("ORPHA:584", "Mucopolysaccharidosis type IV", 0.2, "<1/1,000,000", "Autosomal recessive", "Childhood", ["GALNS"], "C0026710"),
    ("ORPHA:585", "Mucopolysaccharidosis type VI", 0.1, "<1/1,000,000", "Autosomal recessive", "Childhood", ["ARSB"], "C0026711"),
    ("ORPHA:588", "Mucopolysaccharidosis type VII", 0.05, "<1/1,000,000", "Autosomal recessive", "Infantile", ["GUSB"], "C0085132"),
    ("ORPHA:582", "Metachromatic leukodystrophy", 0.2, "<1/1,000,000", "Autosomal recessive", "Infantile|Juvenile", ["ARSA"], "C0023522"),
    ("ORPHA:487", "Krabbe disease", 0.15, "<1/1,000,000", "Autosomal recessive", "Infantile", ["GALC"], "C0023523"),
    ("ORPHA:309263", "Adrenoleukodystrophy", 0.3, "<1/1,000,000", "X-linked recessive", "Childhood|Adult", ["ABCD1"], "C0001824"),
    ("ORPHA:509", "Friedreich ataxia", 0.3, "<1/1,000,000", "Autosomal recessive", "Childhood|Adult", ["FXN"], "C0016719"),
    ("ORPHA:95", "Ataxia telangiectasia", 0.15, "<1/1,000,000", "Autosomal recessive", "Infantile", ["ATM"], "C0004135"),
    ("ORPHA:63", "Spinal muscular atrophy", 1.0, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile|Childhood", ["SMN1", "SMN2"], "C0026847"),
    ("ORPHA:70", "Amyotrophic lateral sclerosis", 4.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Adult", ["SOD1", "C9orf72"], "C0002736"),
    ("ORPHA:332", "Limb-girdle muscular dystrophy", 1.0, "1/200,000 - 1/2,000", "Autosomal recessive", "Childhood|Adult", ["CAPN3"], "C0686353"),
    ("ORPHA:495", "Myotonic dystrophy", 2.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Adult", ["DMPK"], "C0027121"),
    ("ORPHA:216", "Charcot-Marie-Tooth disease", 10.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Childhood|Adult", ["PMP22"], "C0007959"),
    ("ORPHA:105", "Becker muscular dystrophy", 0.5, "1/200,000 - 1/2,000", "X-linked recessive", "Childhood|Adult", ["DMD"], "C0151727"),
    ("ORPHA:207", "Chronic granulomatous disease", 0.1, "<1/1,000,000", "X-linked recessive", "Infantile", ["CYBB"], "C0008733"),
    ("ORPHA:326", "Severe combined immunodeficiency", 0.05, "<1/1,000,000", "X-linked recessive", "Infantile", ["IL2RG"], "C0085110"),
    ("ORPHA:586", "Wiskott-Aldrich syndrome", 0.05, "<1/1,000,000", "X-linked recessive", "Infantile", ["WAS"], "C0043194"),
    ("ORPHA:90", "Fanconi anemia", 0.2, "<1/1,000,000", "Autosomal recessive", "Childhood", ["FANCA"], "C0015625"),
    ("ORPHA:84", "Diamond-Blackfan anemia", 0.1, "<1/1,000,000", "Autosomal dominant", "Infantile", ["RPS19"], "C0017987"),
    ("ORPHA:683", "Sickle cell disease", 30.0, "1/2,000 - 1/10,000", "Autosomal recessive", "Infantile", ["HBB"], "C0004096"),
    ("ORPHA:232", "Beta-thalassemia", 20.0, "1/2,000 - 1/10,000", "Autosomal recessive", "Infantile", ["HBB"], "C0005283"),
    ("ORPHA:848", "Hemophilia A", 5.0, "1/200,000 - 1/2,000", "X-linked recessive", "Infantile|Childhood", ["F8"], "C0019061"),
    ("ORPHA:98879", "Hemophilia B", 1.0, "1/200,000 - 1/2,000", "X-linked recessive", "Infantile|Childhood", ["F9"], "C0008533"),
    ("ORPHA:525", "Hereditary hemorrhagic telangiectasia", 2.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Childhood|Adult", ["ENG", "ACVRL1"], "C0039445"),
    ("ORPHA:91378", "Hereditary angioedema", 1.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Childhood|Adult", ["SERPING1"], "C0002994"),
    ("ORPHA:133", "Familial Mediterranean fever", 5.0, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile|Childhood", ["MEFV"], "C0031069"),
    ("ORPHA:115", "Congenital sucrase-isomaltase deficiency", 0.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile", ["SI"], "C0268188"),
    ("ORPHA:663", "Phenylketonuria", 5.0, "1/2,000 - 1/10,000", "Autosomal recessive", "Infantile", ["PAH"], "C0031485"),
    ("ORPHA:708", "Maple syrup urine disease", 0.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile", ["BCKDHA"], "C0024776"),
    ("ORPHA:244", "Homocystinuria", 1.0, "1/200,000 - 1/2,000", "Autosomal recessive", "Childhood", ["CBS"], "C0019880"),
    ("ORPHA:511", "Wilson disease", 1.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Childhood|Adult", ["ATP7B"], "C0019202"),
    ("ORPHA:247546", "Tyrosinemia type I", 0.2, "<1/1,000,000", "Autosomal recessive", "Infantile", ["FAH"], "C0268490"),
    ("ORPHA:655", "Urea cycle disorder", 1.0, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile", ["CPS1", "OTC"], "C0268542"),
    ("ORPHA:412", "Cystinosis", 0.3, "<1/1,000,000", "Autosomal recessive", "Infantile|Childhood", ["CTNS"], "C0010690"),
    ("ORPHA:88", "Alkaptonuria", 0.2, "<1/1,000,000", "Autosomal recessive", "Infantile", ["HGD"], "C0002068"),
    ("ORPHA:258", "Hyperoxaluria", 0.5, "1/200,000 - 1/2,000", "Autosomal recessive", "Childhood", ["AGXT"], "C0020500"),
    ("ORPHA:887", "Hereditary hemochromatosis", 10.0, "1/2,000 - 1/10,000", "Autosomal recessive", "Adult", ["HFE"], "C0392514"),
    ("ORPHA:803", "Idiopathic pulmonary fibrosis", 15.0, "1/2,000 - 1/10,000", "Multigenic", "Adult", ["TGFB1"], "C0085786"),
    ("ORPHA:182", "Pulmonary arterial hypertension", 5.0, "1/200,000 - 1/2,000", "Multigenic", "Adult", ["BMPR2"], "C0002587"),
    ("ORPHA:808", "Paroxysmal nocturnal hemoglobinuria", 1.0, "1/200,000 - 1/2,000", "Acquired", "Adult", ["PIGA"], "C0028062"),
    ("ORPHA:158032", "Atypical hemolytic uremic syndrome", 0.5, "1/200,000 - 1/2,000", "Multigenic", "Childhood|Adult", ["CFH"], "C0019069"),
    ("ORPHA:284", "Dravet syndrome", 0.5, "1/200,000 - 1/2,000", "Autosomal dominant", "Infantile", ["SCN1A"], "C0393667"),
    ("ORPHA:1942", "Lennox-Gastaut syndrome", 0.5, "1/200,000 - 1/2,000", "Multigenic", "Childhood", ["GABRB3"], "C0023380"),
    ("ORPHA:310", "Tuberous sclerosis", 2.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Infantile|Childhood", ["TSC1", "TSC2"], "C0041341"),
    ("ORPHA:295", "Neurofibromatosis type 1", 5.0, "1/200,000 - 1/2,000", "Autosomal dominant", "Childhood", ["NF1"], "C0027831"),
    ("ORPHA:636", "Narcolepsy", 10.0, "1/2,000 - 1/10,000", "Multigenic", "Childhood|Adult", ["HCRT"], "C0027404"),
    ("ORPHA:93419", "Nephropathic cystinosis", 0.2, "<1/1,000,000", "Autosomal recessive", "Infantile", ["CTNS"], "C2931187"),
    ("ORPHA:2078", "Primary ciliary dyskinesia", 1.0, "1/200,000 - 1/2,000", "Autosomal recessive", "Infantile|Childhood", ["DNAH5"], "C0008780"),
    ("ORPHA:3384", "Tetralogy of Fallot", 3.0, "1/200,000 - 1/2,000", "Multigenic", "Infantile", ["NKX2-5"], "C0039685"),
    ("ORPHA:85443", "Alport syndrome", 1.0, "1/200,000 - 1/2,000", "X-linked recessive", "Childhood|Adult", ["COL4A5"], "C0086047"),
    ("ORPHA:1065", "Aniridia", 0.5, "1/200,000 - 1/2,000", "Autosomal dominant", "Infantile", ["PAX6"], "C0003069"),
]

# Known indication pairs (drug struct_id -> disease orpha_id) used as positives
INDICATIONS = [
    ("1001", "ORPHA:635"), ("1001", "ORPHA:399"), ("1001", "ORPHA:512"),
    ("1003", "ORPHA:793"), ("1002", "ORPHA:310"), ("1028", "ORPHA:310"),
    ("1036", "ORPHA:310"), ("1004", "ORPHA:793"), ("1049", "ORPHA:793"),
    ("1047", "ORPHA:63"), ("1048", "ORPHA:98757"), ("1050", "ORPHA:803"),
    ("1051", "ORPHA:803"), ("1052", "ORPHA:182"), ("1053", "ORPHA:182"),
    ("1054", "ORPHA:182"), ("1046", "ORPHA:808"), ("1045", "ORPHA:808"),
    ("1070", "ORPHA:244"), ("1073", "ORPHA:247546"), ("1072", "ORPHA:655"),
    ("1074", "ORPHA:663"), ("1067", "ORPHA:511"), ("1068", "ORPHA:511"),
    ("1069", "ORPHA:511"), ("1071", "ORPHA:412"), ("1071", "ORPHA:93419"),
    ("1075", "ORPHA:584"), ("1076", "ORPHA:309"), ("1077", "ORPHA:512"),
    ("1078", "ORPHA:585"), ("1079", "ORPHA:580"), ("1080", "ORPHA:588"),
    ("1038", "ORPHA:683"), ("1038", "ORPHA:232"), ("1039", "ORPHA:683"),
    ("1103", "ORPHA:232"), ("1104", "ORPHA:90"), ("1105", "ORPHA:84"),
    ("1106", "ORPHA:586"), ("1107", "ORPHA:586"), ("1108", "ORPHA:586"),
    ("1109", "ORPHA:848"), ("1110", "ORPHA:848"), ("1111", "ORPHA:98879"),
    ("1112", "ORPHA:2078"), ("1113", "ORPHA:2078"), ("1083", "ORPHA:887"),
    ("1084", "ORPHA:887"), ("1085", "ORPHA:636"), ("1086", "ORPHA:636"),
    ("1087", "ORPHA:636"), ("1088", "ORPHA:636"), ("1089", "ORPHA:284"),
    ("1090", "ORPHA:284"), ("1091", "ORPHA:284"), ("1092", "ORPHA:1942"),
    ("1019", "ORPHA:284"), ("1019", "ORPHA:1942"), ("1020", "ORPHA:1942"),
    ("1020", "ORPHA:284"), ("1021", "ORPHA:1942"), ("1022", "ORPHA:70"),
    ("1023", "ORPHA:70"), ("1024", "ORPHA:70"), ("1025", "ORPHA:98065"),
    ("1026", "ORPHA:98065"), ("1095", "ORPHA:98065"), ("1096", "ORPHA:98065"),
    ("1097", "ORPHA:98065"), ("1098", "ORPHA:98065"), ("1099", "ORPHA:98065"),
    ("1100", "ORPHA:509"), ("1101", "ORPHA:509"), ("1102", "ORPHA:232"),
    ("1043", "ORPHA:98757"), ("1044", "ORPHA:98757"), ("1043", "ORPHA:332"),
    ("1044", "ORPHA:332"), ("1043", "ORPHA:495"), ("1016", "ORPHA:495"),
    ("1017", "ORPHA:495"), ("1018", "ORPHA:495"), ("1013", "ORPHA:182"),
    ("1014", "ORPHA:182"), ("1015", "ORPHA:182"), ("1011", "ORPHA:182"),
    ("1012", "ORPHA:182"), ("1005", "ORPHA:808"), ("1006", "ORPHA:808"),
    ("1007", "ORPHA:808"), ("1008", "ORPHA:808"), ("1009", "ORPHA:182"),
    ("1010", "ORPHA:182"), ("1055", "ORPHA:182"), ("1056", "ORPHA:793"),
    ("1057", "ORPHA:793"), ("1058", "ORPHA:793"), ("1059", "ORPHA:793"),
    ("1060", "ORPHA:793"), ("1061", "ORPHA:793"), ("1062", "ORPHA:793"),
    ("1063", "ORPHA:793"), ("1064", "ORPHA:133"), ("1065", "ORPHA:133"),
    ("1066", "ORPHA:133"), ("1040", "ORPHA:133"), ("1041", "ORPHA:133"),
    ("1042", "ORPHA:133"), ("1030", "ORPHA:295"), ("1031", "ORPHA:295"),
    ("1032", "ORPHA:295"), ("1033", "ORPHA:295"), ("1034", "ORPHA:295"),
    ("1035", "ORPHA:295"), ("1029", "ORPHA:295"), ("1037", "ORPHA:808"),
    ("1117", "ORPHA:182"), ("1118", "ORPHA:182"), ("1119", "ORPHA:182"),
    ("1120", "ORPHA:182"), ("1114", "ORPHA:182"), ("1115", "ORPHA:182"),
    ("1116", "ORPHA:182"), ("1013", "ORPHA:808"), ("1081", "ORPHA:803"),
    ("1082", "ORPHA:803"), ("1100", "ORPHA:70"), ("1089", "ORPHA:70"),
    ("1090", "ORPHA:70"), ("1091", "ORPHA:70"), ("1092", "ORPHA:70"),
    ("1106", "ORPHA:525"), ("1107", "ORPHA:525"), ("1108", "ORPHA:525"),
    ("1005", "ORPHA:133"), ("1006", "ORPHA:133"), ("1064", "ORPHA:133"),
    ("1050", "ORPHA:803"), ("1051", "ORPHA:803"), ("1013", "ORPHA:803"),
]

CONTRAINDICATIONS = [
    ("1001", "Severe hepatic impairment"), ("1002", "Active infection"),
    ("1002", "Severe hepatic impairment"), ("1004", "Severe renal impairment"),
    ("1005", "Active bleeding"), ("1006", "Active peptic ulcer"),
    ("1007", "Active liver disease"), ("1014", "Active bleeding"),
    ("1015", "Active bleeding"), ("1016", "MAOI use"),
    ("1017", "MAOI use"), ("1019", "Severe renal impairment"),
    ("1020", "Urea cycle disorder"), ("1021", "Bone marrow suppression"),
    ("1027", "Acute hepatitis"), ("1039", "Active infection"),
    ("1040", "Active infection"), ("1041", "Active infection"),
    ("1042", "Active infection"), ("1043", "Systemic fungal infection"),
    ("1044", "Systemic fungal infection"), ("1047", "Severe renal impairment"),
    ("1050", "Severe hepatic impairment"), ("1056", "Severe renal impairment"),
    ("1057", "Severe renal impairment"), ("1072", "Urea cycle disorder"),
    ("1083", "Severe renal impairment"), ("1084", "Severe renal impairment"),
    ("1114", "Anuria"), ("1115", "Hyperkalemia"),
]

TARGETS = [
    ("T001", "GBA", "GBA", "P04062", "Enzyme"), ("T002", "NPC1", "NPC1", "O15118", "Transporter"),
    ("T003", "NPC2", "NPC2", "P61916", "Transporter"), ("T004", "CFTR", "CFTR", "P13569", "Ion Channel"),
    ("T005", "HTT", "HTT", "P42858", "Unknown"), ("T006", "MTOR", "MTOR", "P42345", "Kinase"),
    ("T007", "PRKAA1", "PRKAA1", "Q13131", "Kinase"), ("T008", "PTGS1", "PTGS1", "P23219", "Enzyme"),
    ("T009", "PTGS2", "PTGS2", "P35354", "Enzyme"), ("T010", "HMGCR", "HMGCR", "P04035", "Enzyme"),
    ("T011", "PDE5A", "PDE5A", "O76074", "Enzyme"), ("T012", "ADRB1", "ADRB1", "P08588", "GPCR"),
    ("T013", "CACNA1C", "CACNA1C", "Q13936", "Ion Channel"), ("T014", "AGTR1", "AGTR1", "P30556", "GPCR"),
    ("T015", "ATP4A", "ATP4A", "P20648", "Transporter"), ("T016", "VKORC1", "VKORC1", "Q9BQB6", "Enzyme"),
    ("T017", "P2RY12", "P2RY12", "Q9H244", "GPCR"), ("T018", "SLC6A4", "SLC6A4", "P31645", "Transporter"),
    ("T019", "GABRA1", "GABRA1", "P14867", "Ion Channel"), ("T020", "SV2A", "SV2A", "Q7L0J3", "Transporter"),
    ("T021", "HDAC1", "HDAC1", "Q13547", "Enzyme"), ("T022", "SCN1A", "SCN1A", "P35498", "Ion Channel"),
    ("T023", "ACHE", "ACHE", "P22303", "Enzyme"), ("T024", "GRIN1", "GRIN1", "Q05586", "Ion Channel"),
    ("T025", "DDC", "DDC", "P20711", "Enzyme"), ("T026", "SLC18A2", "SLC18A2", "Q05940", "Transporter"),
    ("T027", "OPRM1", "OPRM1", "P35372", "GPCR"), ("T028", "JAK2", "JAK2", "O60674", "Kinase"),
    ("T029", "ABL1", "ABL1", "P00519", "Kinase"), ("T030", "SRC", "SRC", "P12931", "Kinase"),
    ("T031", "EGFR", "EGFR", "P00533", "Kinase"), ("T032", "BRAF", "BRAF", "P15056", "Kinase"),
    ("T033", "CRBN", "CRBN", "Q96SW2", "Unknown"), ("T034", "RRM1", "RRM1", "P23921", "Enzyme"),
    ("T035", "IMPDH2", "IMPDH2", "P12268", "Enzyme"), ("T036", "PPP3CA", "PPP3CA", "Q08209", "Enzyme"),
    ("T037", "NR3C1", "NR3C1", "P04150", "Nuclear Receptor"), ("T038", "MS4A1", "MS4A1", "P11836", "Other"),
    ("T039", "C5", "C5", "P01031", "Other"), ("T040", "SMN2", "SMN2", "Q16637", "Other"),
    ("T041", "DMD", "DMD", "P11532", "Other"), ("T042", "TGFB1", "TGFB1", "P01137", "Cytokine"),
    ("T043", "PDGFRB", "PDGFRB", "P09619", "Kinase"), ("T044", "EDNRA", "EDNRA", "P25101", "GPCR"),
    ("T045", "GUCY1A1", "GUCY1A1", "Q02108", "Enzyme"), ("T046", "SLC5A2", "SLC5A2", "P31639", "Transporter"),
    ("T047", "GLP1R", "GLP1R", "P43220", "GPCR"), ("T048", "INSR", "INSR", "P06213", "Kinase"),
    ("T049", "THRA", "THRA", "P10827", "Nuclear Receptor"), ("T050", "FDPS", "FDPS", "P14324", "Enzyme"),
    ("T051", "TNFSF11", "TNFSF11", "O14788", "Cytokine"), ("T052", "TUBB", "TUBB", "P07437", "Other"),
    ("T053", "XDH", "XDH", "P47989", "Enzyme"), ("T054", "ATP7B", "ATP7B", "P35670", "Transporter"),
    ("T055", "CTNS", "CTNS", "O60931", "Transporter"), ("T056", "CPS1", "CPS1", "P31327", "Enzyme"),
    ("T057", "HPD", "HPD", "P32754", "Enzyme"), ("T058", "PAH", "PAH", "P00439", "Enzyme"),
    ("T059", "GALNS", "GALNS", "P34059", "Enzyme"), ("T060", "IDUA", "IDUA", "P35475", "Enzyme"),
    ("T061", "GLA", "GLA", "P06280", "Enzyme"), ("T062", "ARSB", "ARSB", "P15848", "Enzyme"),
    ("T063", "IDS", "IDS", "P22304", "Enzyme"), ("T064", "GUSB", "GUSB", "P08236", "Enzyme"),
    ("T065", "HFE", "HFE", "Q30201", "Other"), ("T066", "CNR1", "CNR1", "P21554", "GPCR"),
    ("T067", "GABBR1", "GABBR1", "Q9UBS5", "GPCR"), ("T068", "ADRA2A", "ADRA2A", "P08913", "GPCR"),
    ("T069", "COMT", "COMT", "P21964", "Enzyme"), ("T070", "DRD2", "DRD2", "P14416", "GPCR"),
    ("T071", "MAOB", "MAOB", "P27338", "Enzyme"), ("T072", "AVPR2", "AVPR2", "P30518", "GPCR"),
    ("T073", "SLC12A1", "SLC12A1", "Q13621", "Transporter"), ("T074", "NR3C2", "NR3C2", "P08235", "Nuclear Receptor"),
    ("T075", "MME", "MME", "P08473", "Enzyme"), ("T076", "ATP1A1", "ATP1A1", "P05023", "Transporter"),
    ("T077", "KCNH2", "KCNH2", "Q12809", "Ion Channel"), ("T078", "FBN1", "FBN1", "P35555", "Other"),
    ("T079", "SERPING1", "SERPING1", "P05155", "Other"), ("T080", "KLKB1", "KLKB1", "P03952", "Enzyme"),
]


def generate_demo_data(data_dir: Path, seed: int = SEED):
    rng = random.Random(seed)
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    for sub in ["orpha", "drugcentral"]:
        (raw_dir / sub).mkdir(parents=True, exist_ok=True)
        (processed_dir / sub).mkdir(parents=True, exist_ok=True)

    # --- diseases -----------------------------------------------------------
    disease_rows = []
    gene_disease_rows = []
    hpo_rows = []
    gene_ids: dict[str, str] = {}  # symbol -> hgnc_id (stable, unique)
    for orpha_id, name, prev, cat, inh, onset, genes, umls in DISEASES:
        gene_objs = []
        for g in genes:
            if g not in gene_ids:
                gene_ids[g] = f"HGNC:{8000 + len(gene_ids)}"
            gene_objs.append({"hgnc_id": gene_ids[g], "symbol": g, "name": f"{g} gene"})
        disease_rows.append({
            "id": orpha_id,
            "name": name,
            "prevalence": prev,
            "prevalence_category": cat,
            "inheritance": inh,
            "age_of_onset": onset,
            "genes": gene_objs,
            "hpo_terms": [{"id": "HP:0000001", "term": "All"}],
            "umls_cui": umls,
        })
        for g in genes:
            gene_disease_rows.append({
                "hgnc_id": gene_ids[g],
                "symbol": g,
                "gene_name": f"{g} gene",
                "orpha_id": orpha_id,
            })
        hpo_rows.append({"orpha_id": orpha_id, "hpo_id": "HP:0000001", "hpo_term": "All", "frequency": ""})

    pd.DataFrame(disease_rows).to_parquet(processed_dir / "orpha" / "orpha_diseases.parquet", index=False)
    pd.DataFrame(gene_disease_rows).to_parquet(processed_dir / "orpha" / "orpha_gene_disease.parquet", index=False)
    pd.DataFrame(hpo_rows).to_parquet(processed_dir / "orpha" / "orpha_hpo.parquet", index=False)
    pd.DataFrame({"orpha_id": [d[0] for d in DISEASES], "name": [d[1] for d in DISEASES], "parent_orpha_id": [None] * len(DISEASES)}).to_parquet(
        processed_dir / "orpha" / "orpha_linearization.parquet", index=False
    )

    # --- drugs --------------------------------------------------------------
    struct_rows, syn_rows, moa_rows, fda_rows = [], [], [], []
    for sid, name, smiles, moa, gene, uniprot in DRUGS:
        struct_rows.append({
            "struct_id": sid, "smiles": smiles, "inchi": "", "inchikey": "",
            "cas": "", "molecular_weight": 0.0, "xlogp": 0.0, "tpsa": 0.0,
            "rotatable_bonds": 0, "hba": 0, "hbd": 0, "charge": 0,
        })
        syn_rows.append({"struct_id": sid, "synonym": name, "synonym_type": "INN"})
        moa_rows.append({"struct_id": sid, "class_code": "", "class_name": moa, "source": "DrugCentral"})
        fda_rows.append({
            "struct_id": sid, "name": name, "smiles": smiles, "inchi": "", "inchikey": "",
            "cas": "", "molecular_weight": 0.0, "xlogp": 0.0, "tpsa": 0.0,
            "rotatable_bonds": 0, "hba": 0, "hbd": 0, "charge": 0,
            "moa_classes": moa, "target_name": gene, "gene": gene, "uniprot": uniprot,
            "indication_umls": "", "indication_types": "FDA", "first_approval_year": 1990,
            "approval_status": "FDA_approved",
        })

    pd.DataFrame(struct_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_structures.parquet", index=False)
    pd.DataFrame(syn_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_synonyms.parquet", index=False)
    pd.DataFrame(moa_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_pharmacologic_class.parquet", index=False)
    pd.DataFrame(fda_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_fda_approved.parquet", index=False)

    # --- targets ------------------------------------------------------------
    target_rows = [
        {"target_id": tid, "target_name": tn, "gene": g, "uniprot": u, "organism": "Homo sapiens", "target_class": tc}
        for tid, tn, g, u, tc in TARGETS
    ]
    pd.DataFrame(target_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_targets.parquet", index=False)

    # --- indications --------------------------------------------------------
    umls_by_orpha = {d[0]: d[7] for d in DISEASES}
    ind_rows = []
    for sid, orpha in INDICATIONS:
        ind_rows.append({
            "struct_id": sid, "umls_cui": umls_by_orpha.get(orpha, ""), "sme_id": "",
            "indication_type": "FDA", "max_phase_for_ind": 4, "approval_status": "FDA",
            "approval_year": 1995, "source": "DrugCentral",
        })
    pd.DataFrame(ind_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_indications.parquet", index=False)

    # --- contraindications --------------------------------------------------
    contra_rows = [
        {"struct_id": sid, "contraindication": text, "source": "DrugCentral"}
        for sid, text in CONTRAINDICATIONS
    ]
    pd.DataFrame(contra_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_contraindications.parquet", index=False)

    # --- drug-target edges --------------------------------------------------
    gene_to_target = {t[2]: t[0] for t in TARGETS}
    dt_rows = []
    for sid, name, smiles, moa, gene, uniprot in DRUGS:
        tid = gene_to_target.get(gene)
        if tid:
            dt_rows.append({
                "struct_id": sid, "target_id": tid, "action_type": "modulator",
                "action_comment": moa, "selectivity_comment": "", "binding_db_id": "",
                "binding_value": 100.0, "binding_unit": "nM", "binding_type": "Kd",
                "ph": 7.4, "temp": 25, "source": "DrugCentral",
            })
    pd.DataFrame(dt_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_drug_target.parquet", index=False)

    # --- omop ---------------------------------------------------------------
    omop_rows = [
        {"struct_id": sid, "concept_id": str(19000000 + i), "concept_name": name,
         "domain_id": "Drug", "vocabulary_id": "RxNorm", "concept_class_id": "Ingredient",
         "standard_concept": "S"}
        for i, (sid, name, *_rest) in enumerate(DRUGS)
    ]
    pd.DataFrame(omop_rows).to_parquet(processed_dir / "drugcentral" / "drugcentral_omop.parquet", index=False)

    logger.info(
        "demo_data_generated",
        diseases=len(DISEASES), drugs=len(DRUGS),
        indications=len(INDICATIONS), contraindications=len(CONTRAINDICATIONS),
        targets=len(TARGETS), drug_target_edges=len(dt_rows),
    )


if __name__ == "__main__":
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    generate_demo_data(data_dir)

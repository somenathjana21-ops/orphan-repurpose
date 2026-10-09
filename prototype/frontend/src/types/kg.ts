export interface KGEntity {
  id: string
  type: string
  name: string
  properties: Record<string, any>
}

export interface KGSearchResponse {
  results: KGEntity[]
  total: number
}

export interface KGSubgraphResponse {
  drug_id: string
  disease_id: string
  nodes: KGSubgraphNode[]
  edges: KGSubgraphEdge[]
}

export interface KGSubgraphNode {
  id: string
  type: string
  name: string
  properties: Record<string, any>
}

export interface KGSubgraphEdge {
  source: string
  target: string
  type: string
  weight: number
}

export interface KGStatsResponse {
  node_types: Record<string, number>
  edge_types: Record<string, number>
  total_nodes: number
  total_edges: number
}

export interface KGDrug {
  id: string
  name: string
  smiles: string
  molecular_weight: number
  xlogp: number
  tpsa: number
  rotatable_bonds: number
  hba: number
  hbd: number
  charge: number
  moa_classes: string
  target_names: string
  target_genes: string
  indication_umls: string
  indication_types: string
  first_approval_year: number
  approval_status: string
  cas: string
}

export interface KGDrugDetail extends KGDrug {
  targets: KGTarget[]
  indications: string[]
}

export interface KGTarget {
  id: string
  name: string
  gene: string
  uniprot: string
  organism: string | null
  target_class: string | null
}

export interface KGDisease {
  id: string
  name: string
  prevalence: number | null
  prevalence_category: string | null
  inheritance: string[]
  age_of_onset: string[]
  phenotypes: string[]
  existing_treatments: string[]
  unmet_need_score: number | null
  description: string | null
  synonyms: string[] | null
  omim_ids: string[] | null
  mondo_id: string | null
  icar_id: string | null
}

export interface KGDiseaseDetail extends KGDisease {
  genes: KGGene[]
  targets: KGTarget[]
  drugs: KGDrug[]
}

export interface KGGene {
  id: string
  symbol: string
  name: string
  uniprot_id: string | null
  ensembl_id: string | null
  hgnc_id: string
}

export interface KGPaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

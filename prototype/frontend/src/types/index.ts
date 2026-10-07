export interface Gene {
  hgnc_id: string
  symbol: string
  name: string
  uniprot_id?: string
  ensembl_id?: string
}

export interface Pathway {
  reactome_id: string
  name: string
  species?: string
  url?: string
}

export interface DiseaseSearchResult {
  orpha_id: string
  name: string
  prevalence?: number
  prevalence_category?: string
  inheritance?: string[]
  age_of_onset?: string[]
  genes: Gene[]
  pathways: Pathway[]
  phenotypes: string[]
  existing_treatments: string[]
  unmet_need_score?: number
}

export interface DiseaseDetail extends DiseaseSearchResult {
  description?: string
  synonyms: string[]
  omim_ids: string[]
  mondo_id?: string
  icar_id?: string
  created_at: string
  updated_at: string
}

export interface DiseaseSearchParams {
  q?: string
  prevalence_max?: number
  gene?: string
  pathway?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: string
}

export interface DiseaseSearchResponse {
  data: DiseaseSearchResult[]
  total: number
  page: number
  page_size: number
}

export interface Candidate {
  candidate_id: string
  drug_id: string
  drug_name: string
  indication_probability: number
  confidence_interval: [number, number]
  moa_summary: string
  safety_flags: SafetyFlags
  kg_paths: KGPath[]
  llm_rationale: string
  shap_values: Record<string, number>
}

export interface SafetyFlags {
  faers_signals: FAERSSignal[]
  admet_predictions: Record<string, number>
  contraindications: string[]
  overall: 'pass' | 'caution' | 'fail'
}

export interface FAERSSignal {
  reaction: string
  meddra_pt: string
  ror: number
  prr: number
  bcpnn: number
  n_reports: number
  level: 'pass' | 'caution' | 'fail'
}

export interface KGPath {
  nodes: KGPathNode[]
  edges: KGPathEdge[]
  score: number
}

export interface KGPathNode {
  id: string
  type: string
  name: string
  properties: Record<string, any>
}

export interface KGPathEdge {
  source: string
  target: string
  type: string
  weight: number
}

export interface CandidateGenerateRequest {
  disease_id: string
}

export interface CandidateGenerateResponse {
  candidates: Candidate[]
  session_id: string
}

export interface Explanation {
  candidate_id: string
  kg_paths: KGPath[]
  shap_values: Record<string, number>
  counterfactuals: Counterfactual[]
  llm_rationale: string
}

export interface Counterfactual {
  removed_edge: string
  probability_delta: number
  description: string
}

export interface ValidationRequest {
  validator: string
  assessment: 'plausible' | 'needs_data' | 'unlikely'
  rationale: string
}

export interface SelfAssessmentRequest {
  efficacy: number
  safety: number
  feasibility: number
  notes: string
}

export interface AuditEntry {
  timestamp: string
  type: 'validation' | 'self_assessment' | 'note' | 'generation'
  user: string
  data: Record<string, any>
  hash: string
}

export interface AuditTrail {
  session_id: string
  entries: AuditEntry[]
}

export interface DossierRequest {
  disease_id: string
  candidate_ids: string[]
  include_sections: string[]
}

export interface DossierResponse {
  pdf_base64: string
  json: DossierJSON
  audit_trail_id: string
}

export interface DossierJSON {
  disease: DiseaseDetail
  candidates: Candidate[]
  sections: {
    background: string
    drug_profile: string
    mechanistic_rationale: string
    preclinical_plan: string
    regulatory_strategy: string
    credibility_map: CredibilityMap
  }
  generated_at: string
  disclaimer: string
}

export interface CredibilityMap {
  step_1_cou: string
  step_2_risk: string
  step_3_data_quality: string
  step_4_model_development: string
  step_5_model_evaluation: string
  step_6_deployment: string
  step_7_lifecycle: string
}
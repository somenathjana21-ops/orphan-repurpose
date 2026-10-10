import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  DiseaseDetail,
  DiseaseSearchResponse,
  Candidate,
  CandidateGenerateResponse,
  Explanation,
  SafetyFlags,
  AuditTrail,
  DossierResponse,
  KGSearchResponse,
  KGSubgraphResponse,
  KGStatsResponse,
  KGDrug,
  KGDrugDetail,
  KGDisease,
  KGDiseaseDetail,
  KGPaginatedResponse,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
})

// Request interceptor for logging
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error(
      `[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}`,
      error.response?.data || error.message
    )
    return Promise.reject(error)
  }
)

// Disease API
export const diseasesApi = {
  search: async (params: {
    query?: string
    prevalence_max?: number
    gene?: string
    pathway?: string
    page?: number
    page_size?: number
    sort_by?: string
    sort_order?: string
  }): Promise<DiseaseSearchResponse> => {
    const { data } = await api.get<DiseaseSearchResponse>('/api/v1/diseases', { params })
    return data
  },

  get: async (orphaId: string): Promise<DiseaseDetail> => {
    const { data } = await api.get<DiseaseDetail>(`/api/v1/diseases/${orphaId}`)
    return data
  },

  getGenes: async (orphaId: string): Promise<string[]> => {
    const { data } = await api.get<string[]>(`/api/v1/diseases/${orphaId}/genes`)
    return data
  },

  getPathways: async (orphaId: string): Promise<string[]> => {
    const { data } = await api.get<string[]>(`/api/v1/diseases/${orphaId}/pathways`)
    return data
  },
}

// Candidate API
export const candidatesApi = {
  generate: async (diseaseId: string): Promise<CandidateGenerateResponse> => {
    const { data } = await api.post<CandidateGenerateResponse>('/api/v1/candidates/generate', {
      disease_id: diseaseId,
    })
    return data
  },

  get: async (candidateId: string): Promise<Candidate> => {
    const { data } = await api.get<Candidate>(`/api/v1/candidates/${candidateId}`)
    return data
  },

  getExplanation: async (candidateId: string): Promise<Explanation> => {
    const { data } = await api.get<Explanation>(`/api/v1/candidates/${candidateId}/explanation`)
    return data
  },

  getKGSubgraph: async (candidateId: string): Promise<{ nodes: unknown[]; edges: unknown[] }> => {
    const { data } = await api.get(`/api/v1/candidates/${candidateId}/kg-subgraph`)
    return data
  },

  getLiterature: async (candidateId: string): Promise<{ literature: unknown[] }> => {
    const { data } = await api.get(`/api/v1/candidates/${candidateId}/literature`)
    return data
  },

  getSafety: async (candidateId: string): Promise<SafetyFlags | import('../types/safety').SafetyAssessment> => {
    const { data } = await api.get<SafetyFlags | import('../types/safety').SafetyAssessment>(`/api/v1/candidates/${candidateId}/safety`)
    return data
  },

  validate: async (
    candidateId: string,
    payload: {
      validator: string
      assessment: 'plausible' | 'needs_data' | 'unlikely'
      rationale: string
    }
  ) => {
    const { data } = await api.post(
      `/api/v1/validation/candidates/${candidateId}/validate`,
      payload
    )
    return data
  },

  selfAssess: async (
    candidateId: string,
    payload: {
      efficacy: number
      safety: number
      feasibility: number
      notes: string
    }
  ) => {
    const { data } = await api.post(
      `/api/v1/validation/candidates/${candidateId}/assess`,
      payload
    )
    return data
  },
}

// Validation API
export const validationApi = {
  getAuditTrail: async (sessionId: string): Promise<AuditTrail> => {
    const { data } = await api.get<AuditTrail>(`/api/v1/audit/${sessionId}`)
    return data
  },
}

// Dossier API
export const dossierApi = {
  generate: async (payload: {
    disease_id: string
    candidate_ids: string[]
    include_sections: string[]
  }): Promise<DossierResponse> => {
    const { data } = await api.post<DossierResponse>('/api/v1/dossier/generate', payload)
    return data
  },
}

// KG API
export const kgApi = {
  search: async (params: { query?: string; limit?: number }): Promise<KGSearchResponse> => {
    const { data } = await api.get<KGSearchResponse>('/api/v1/kg/search', { params })
    return data
  },

  getSubgraph: async (drugId: string, diseaseId: string, maxDepth?: number): Promise<KGSubgraphResponse> => {
    const { data } = await api.get<KGSubgraphResponse>('/api/v1/kg/subgraph', {
      params: { drug_id: drugId, disease_id: diseaseId, max_depth: maxDepth },
    })
    return data
  },

  getStats: async (): Promise<KGStatsResponse> => {
    const { data } = await api.get<KGStatsResponse>('/api/v1/kg/stats')
    return data
  },

  getDrugs: async (params: { page?: number; page_size?: number; query?: string }): Promise<KGPaginatedResponse<KGDrug>> => {
    const { data } = await api.get<KGPaginatedResponse<KGDrug>>('/api/v1/kg/drugs', { params })
    return data
  },

  getDrug: async (drugId: string): Promise<KGDrugDetail> => {
    const { data } = await api.get<KGDrugDetail>(`/api/v1/kg/drugs/${drugId}`)
    return data
  },

  getDiseases: async (params: { page?: number; page_size?: number; query?: string }): Promise<KGPaginatedResponse<KGDisease>> => {
    const { data } = await api.get<KGPaginatedResponse<KGDisease>>('/api/v1/kg/diseases', { params })
    return data
  },

  getDisease: async (diseaseId: string): Promise<KGDiseaseDetail> => {
    const { data } = await api.get<KGDiseaseDetail>(`/api/v1/kg/diseases/${diseaseId}`)
    return data
  },
}

// Literature API
export const literatureApi = {
  search: async (params: { query: string; limit?: number }): Promise<{ results: any[]; total: number }> => {
    const { data } = await api.get('/api/v1/literature/search', { params })
    return data
  },

  summarize: async (pmids: string[]): Promise<{ summaries: any[] }> => {
    const { data } = await api.post('/api/v1/literature/summarize', pmids)
    return data
  },
}

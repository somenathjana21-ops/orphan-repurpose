import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}`, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Disease API
export const diseasesApi = {
  search: (params: {
    query?: string
    prevalenceMax?: number
    gene?: string
    pathway?: string
    page?: number
    pageSize?: number
    sortBy?: string
    sortOrder?: string
  }) => api.get('/api/v1/diseases', { params }),
  
  get: (orphaId: string) => api.get(`/api/v1/diseases/${orphaId}`),
  
  getGenes: (orphaId: string) => api.get(`/api/v1/diseases/${orphaId}/genes`),
  
  getPathways: (orphaId: string) => api.get(`/api/v1/diseases/${orphaId}/pathways`),
}

// Candidate API
export const candidatesApi = {
  generate: (diseaseId: string) => api.post('/api/v1/candidates/generate', { disease_id: diseaseId }),
  
  get: (candidateId: string) => api.get(`/api/v1/candidates/${candidateId}`),
  
  getExplanation: (candidateId: string) => api.get(`/api/v1/candidates/${candidateId}/explanation`),
  
  getKGSubgraph: (candidateId: string) => api.get(`/api/v1/candidates/${candidateId}/kg-subgraph`),
  
  getLiterature: (candidateId: string) => api.get(`/api/v1/candidates/${candidateId}/literature`),
  
  getSafety: (candidateId: string) => api.get(`/api/v1/candidates/${candidateId}/safety`),
  
  validate: (candidateId: string, data: {
    validator: string
    assessment: 'plausible' | 'needs_data' | 'unlikely'
    rationale: string
  }) => api.post(`/api/v1/validation/candidates/${candidateId}/validate`, data),
  
  selfAssess: (candidateId: string, data: {
    efficacy: number
    safety: number
    feasibility: number
    notes: string
  }) => api.post(`/api/v1/validation/candidates/${candidateId}/assess`, data),
}

// Validation API
export const validationApi = {
  getAuditTrail: (sessionId: string) => api.get(`/api/v1/audit/${sessionId}`),
}

// Dossier API
export const dossierApi = {
  generate: (data: {
    disease_id: string
    candidate_ids: string[]
    include_sections: string[]
  }) => api.post('/api/v1/dossier/generate', data),
}

// KG API
export const kgApi = {
  search: (params: { query?: string; limit?: number }) => api.get('/api/v1/kg/search', { params }),
  
  getSubgraph: (drugId: string, diseaseId: string, maxDepth?: number) => 
    api.get('/api/v1/kg/subgraph', { params: { drug_id: drugId, disease_id: diseaseId, max_depth: maxDepth } }),
}

// Literature API
export const literatureApi = {
  search: (params: { query: string; limit?: number }) => api.get('/api/v1/literature/search', { params }),
  
  summarize: (pmids: string[]) => api.post('/api/v1/literature/summarize', { pmids }),
}
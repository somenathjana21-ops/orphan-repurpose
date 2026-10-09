import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, ChevronDown, ChevronUp, AlertCircle, Info } from 'lucide-react'
import { kgApi } from '../services/api'
import type { KGDrug, KGDisease } from '../types'

export function KGBrowser() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [showFilters, setShowFilters] = useState(false)
  const [activeTab, setActiveTab] = useState<'drugs' | 'diseases' | 'stats'>('drugs')

  const { data: stats } = useQuery({
    queryKey: ['kg-stats'],
    queryFn: () => kgApi.getStats(),
  })

  const { data: drugs, isLoading: drugsLoading, error: drugsError } = useQuery({
    queryKey: ['kg-drugs', { query, page }],
    queryFn: () => kgApi.getDrugs({ query: query || undefined, page, page_size: pageSize }),
    enabled: activeTab === 'drugs',
  })

  const { data: diseases, isLoading: diseasesLoading, error: diseasesError } = useQuery({
    queryKey: ['kg-diseases', { query, page }],
    queryFn: () => kgApi.getDiseases({ query: query || undefined, page, page_size: pageSize }),
    enabled: activeTab === 'diseases',
  })

  const isLoading = drugsLoading || diseasesLoading
  const error = drugsError || diseasesError

  if (error) {
    return (
      <div className="p-6">
        <div className="card">
          <div className="card-body flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load knowledge graph</h3>
              <p className="text-gray-600 mb-4">{(error as Error).message}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Graph Browser</h1>
          <p className="text-gray-600 mt-1">
            Explore the integrated rare disease knowledge graph with real Kuzu database queries.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary" onClick={() => setShowFilters(!showFilters)}>
            <Filter className="h-4 w-4 mr-2" />
            Filters {showFilters ? <ChevronUp className="h-4 w-4 ml-1" /> : <ChevronDown className="h-4 w-4 ml-1" />}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="card">
            <div className="card-body text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.total_nodes.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Total Nodes</p>
            </div>
          </div>
          <div className="card">
            <div className="card-body text-center">
              <p className="text-2xl font-bold text-green-600">{stats.total_edges.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Total Edges</p>
            </div>
          </div>
          <div className="card">
            <div className="card-body text-center">
              <p className="text-2xl font-bold text-purple-600">{Object.keys(stats.node_types).length}</p>
              <p className="text-xs text-gray-500">Node Types</p>
            </div>
          </div>
          <div className="card">
            <div className="card-body text-center">
              <p className="text-2xl font-bold text-amber-600">{Object.keys(stats.edge_types).length}</p>
              <p className="text-xs text-gray-500">Edge Types</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {(['drugs', 'diseases', 'stats'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => { setActiveTab(tab); setPage(1) }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'drugs' ? 'Drugs' : tab === 'diseases' ? 'Diseases' : 'Statistics'}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="search"
                placeholder="Search by name, ID, gene, or pathway..."
                value={query}
                onChange={(e) => { setQuery(e.target.value); setPage(1) }}
                className="input pl-10"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading && <div className="h-4 bg-blue-500/20 animate-pulse" />}

      {/* Drugs Tab */}
      {activeTab === 'drugs' && drugs && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Approval</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Targets</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Indications</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {drugs.data.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center">
                      <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No drugs found matching your criteria.</p>
                    </td>
                  </tr>
                ) : (
                  drugs.data.map((drug: KGDrug) => (
                    <tr key={drug.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-4">
                        <span className="font-medium text-blue-600">{drug.name}</span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600 font-mono">{drug.id}</td>
                      <td className="px-4 py-4">
                        <span className={`badge-${drug.approval_status === 'FDA_approved' ? 'green' : 'gray'}`}>
                          {drug.approval_status}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600">
                        {drug.target_names || '—'}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600">
                        {drug.indication_umls ? '✓' : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {drugs.total > pageSize && (
            <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Page {page} of {Math.ceil(drugs.total / pageSize)} — {drugs.total.toLocaleString()} drugs total
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(Math.ceil(drugs.total / pageSize), p + 1))}
                  disabled={page >= Math.ceil(drugs.total / pageSize)}
                  className="btn-secondary text-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Diseases Tab */}
      {activeTab === 'diseases' && diseases && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ORPHA ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prevalence</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unmet Need</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {diseases.data.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center">
                      <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No diseases found matching your criteria.</p>
                    </td>
                  </tr>
                ) : (
                  diseases.data.map((disease: KGDisease) => (
                    <tr key={disease.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-4">
                        <span className="font-medium text-blue-600">{disease.name}</span>
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600 font-mono">{disease.id}</td>
                      <td className="px-4 py-4 text-sm text-gray-600">
                        {disease.prevalence !== null && disease.prevalence !== undefined
                          ? `${disease.prevalence.toFixed(2)} per 100k`
                          : '—'}
                      </td>
                      <td className="px-4 py-4 text-sm text-gray-600">
                        {disease.prevalence_category || '—'}
                      </td>
                      <td className="px-4 py-4">
                        {disease.unmet_need_score !== null && disease.unmet_need_score !== undefined ? (
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-600 rounded-full"
                                style={{ width: `${Math.min(disease.unmet_need_score * 100, 100)}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-900">{disease.unmet_need_score.toFixed(2)}</span>
                          </div>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {diseases.total > pageSize && (
            <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Page {page} of {Math.ceil(diseases.total / pageSize)} — {diseases.total.toLocaleString()} diseases total
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-sm"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => Math.min(Math.ceil(diseases.total / pageSize), p + 1))}
                  disabled={page >= Math.ceil(diseases.total / pageSize)}
                  className="btn-secondary text-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="card-body">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Node Types</h3>
              <div className="space-y-2">
                {Object.entries(stats.node_types).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm font-medium text-gray-700">{type}</span>
                    <span className="text-sm font-mono text-gray-900">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-body">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Edge Types</h3>
              <div className="space-y-2">
                {Object.entries(stats.edge_types).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm font-medium text-gray-700">{type}</span>
                    <span className="text-sm font-mono text-gray-900">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

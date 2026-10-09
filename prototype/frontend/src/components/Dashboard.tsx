import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Filter, ChevronDown, ChevronUp, AlertCircle, Info } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { diseasesApi } from '../services/api'
import type { DiseaseSearchResult } from '../types'

export function Dashboard() {
  const [query, setQuery] = useState('')
  const [prevalenceMax, setPrevalenceMax] = useState<number | ''>('')
  const [gene, setGene] = useState('')
  const [pathway, setPathway] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('unmet_need_score')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showFilters, setShowFilters] = useState(false)
  const pageSize = 20

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['diseases', { query, prevalenceMax, gene, pathway, page, pageSize, sortBy, sortOrder }],
    queryFn: () => diseasesApi.search({
      query: query || undefined,
      prevalence_max: prevalenceMax ? Number(prevalenceMax) : undefined,
      gene: gene || undefined,
      pathway: pathway || undefined,
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    }),
    placeholderData: (previous) => previous,
  })

  const diseases = data?.data || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / pageSize)

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return <ChevronDown className="h-4 w-4 text-gray-400" />
    return sortOrder === 'asc' ? <ChevronUp className="h-4 w-4 text-blue-600" /> : <ChevronDown className="h-4 w-4 text-blue-600" />
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body flex items-center justify-center py-12">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load diseases</h3>
            <p className="text-gray-600 mb-4">{error.message}</p>
            <button onClick={() => refetch()} className="btn-primary">Retry</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Rare Disease Browser</h1>
          <p className="text-gray-600 mt-1">
            Explore {total.toLocaleString()} rare diseases from Orphanet. Search, filter, and select a disease to generate repurposing candidates.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary" onClick={() => setShowFilters(!showFilters)}>
            <Filter className="h-4 w-4 mr-2" />
            Filters {showFilters ? <ChevronUp className="h-4 w-4 ml-1" /> : <ChevronDown className="h-4 w-4 ml-1" />}
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="search"
                placeholder="Search by name, ORPHA code, gene, or pathway..."
                value={query}
                onChange={(e) => { setQuery(e.target.value); setPage(1); }}
                className="input pl-10"
              />
            </div>
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-gray-100">
              <div>
                <label className="label">Max Prevalence (per 100k)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="e.g., 10"
                  value={prevalenceMax}
                  onChange={(e) => { setPrevalenceMax(e.target.value === '' ? '' : Number(e.target.value)); setPage(1); }}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Gene Symbol</label>
                <input
                  type="text"
                  placeholder="e.g., NPC1"
                  value={gene}
                  onChange={(e) => { setGene(e.target.value); setPage(1); }}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Pathway</label>
                <input
                  type="text"
                  placeholder="e.g., cholesterol metabolism"
                  value={pathway}
                  onChange={(e) => { setPathway(e.target.value); setPage(1); }}
                  className="input"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => { setQuery(''); setPrevalenceMax(''); setGene(''); setPathway(''); setPage(1); }}
                  className="btn-secondary w-full"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      <div className="card overflow-hidden">
        {isLoading && <div className="h-4 bg-blue-500/20 animate-pulse" />}

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('name')}>
                  Disease <SortIcon field="name" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('orpha_id')}>
                  ORPHA Code
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('prevalence')}>
                  Prevalence <SortIcon field="prevalence" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('unmet_need_score')}>
                  Unmet Need <SortIcon field="unmet_need_score" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Genes
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pathways
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {diseases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No diseases found matching your criteria.</p>
                  </td>
                </tr>
              ) : (
                diseases.map((disease: DiseaseSearchResult) => (
                  <tr key={disease.orpha_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-4">
                      <Link to={`/diseases/${disease.orpha_id}`} className="font-medium text-blue-600 hover:underline">
                        {disease.name}
                      </Link>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600 font-mono">{disease.orpha_id}</td>
                    <td className="px-4 py-4 text-sm text-gray-600">
                      {disease.prevalence !== null && disease.prevalence !== undefined
                        ? `${disease.prevalence.toFixed(2)} per 100k`
                        : '—'}
                      {disease.prevalence_category && (
                        <span className="ml-2 badge-gray">{disease.prevalence_category}</span>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      {disease.unmet_need_score !== null && disease.unmet_need_score !== undefined ? (
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-600 rounded-full transition-all"
                              style={{ width: `${Math.min(disease.unmet_need_score * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-900">{disease.unmet_need_score.toFixed(2)}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">
                      {disease.genes.length > 0 ? (
                        <span className="flex flex-wrap gap-1">
                          {disease.genes.slice(0, 3).map((g) => (
                            <span key={g.hgnc_id} className="badge-blue">{g.symbol}</span>
                          ))}
                          {disease.genes.length > 3 && (
                            <span className="badge-gray">+{disease.genes.length - 3}</span>
                          )}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">
                      {disease.pathways.length > 0 ? (
                        <span className="flex flex-wrap gap-1">
                          {disease.pathways.slice(0, 2).map((p) => (
                            <span key={p.reactome_id} className="badge-gray truncate max-w-[120px]">{p.name}</span>
                          ))}
                          {disease.pathways.length > 2 && (
                            <span className="badge-gray">+{disease.pathways.length - 2}</span>
                          )}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <Link
                        to={`/diseases/${disease.orpha_id}`}
                        className="btn-primary text-sm"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Page {page} of {totalPages} — {total.toLocaleString()} diseases total
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
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary text-sm"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
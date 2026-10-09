import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Search,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Info,
  Sparkles,
  Dna,
  ShieldCheck,
  Network,
  ArrowRight,
  TrendingUp,
  SlidersHorizontal,
  X,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { diseasesApi } from '../services/api'
import type { DiseaseSearchResult } from '../types'

const BENCHMARKS = [
  { name: 'Niemann-Pick Type C', orphaId: 'ORPHA:635', gene: 'NPC1', need: 0.85, tag: 'Benchmark' },
  { name: 'Cystic Fibrosis', orphaId: 'ORPHA:793', gene: 'CFTR', need: 0.60, tag: 'Targeted' },
  { name: 'Huntington Disease', orphaId: 'ORPHA:98065', gene: 'HTT', need: 0.75, tag: 'Neuro' },
]

export function Dashboard() {
  const [query, setQuery] = useState('')
  const [prevalenceMax, setPrevalenceMax] = useState<number | ''>('')
  const [gene, setGene] = useState('')
  const [pathway, setPathway] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('unmet_need_score')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showFilters, setShowFilters] = useState(false)
  const pageSize = 15

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['diseases', { query, prevalenceMax, gene, pathway, page, pageSize, sortBy, sortOrder }],
    queryFn: () =>
      diseasesApi.search({
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

  const handleBenchmarkClick = (b: typeof BENCHMARKS[0]) => {
    setQuery(b.orphaId)
    setPage(1)
  }

  const clearAllFilters = () => {
    setQuery('')
    setPrevalenceMax('')
    setGene('')
    setPathway('')
    setPage(1)
  }

  const hasActiveFilters = query || prevalenceMax !== '' || gene || pathway

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return <ChevronDown className="h-3.5 w-3.5 text-slate-400 inline ml-1 opacity-40" />
    return sortOrder === 'asc' ? (
      <ChevronUp className="h-3.5 w-3.5 text-indigo-600 inline ml-1" />
    ) : (
      <ChevronDown className="h-3.5 w-3.5 text-indigo-600 inline ml-1" />
    )
  }

  if (error) {
    return (
      <div className="card max-w-xl mx-auto my-12">
        <div className="card-body text-center py-12">
          <div className="h-14 w-14 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-4 border border-rose-100">
            <AlertCircle className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">Backend Connection Unavailable</h3>
          <p className="text-sm text-slate-500 mb-6 max-w-sm mx-auto">
            Unable to connect to the OrphanRepurpose API backend on <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded font-mono">http://localhost:8000</code>.
          </p>
          <button onClick={() => refetch()} className="btn-primary">
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-7">
      {/* Hero Platform Overview */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-950 via-slate-900 to-indigo-900 text-white p-7 sm:p-9 shadow-xl border border-indigo-900/50">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-12 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-200 text-xs font-semibold backdrop-blur-md border border-indigo-400/20">
            <Sparkles className="h-3.5 w-3.5 text-indigo-300" />
            <span>AI Rare Disease Therapeutics Engine</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Discover Repurposed Drugs for{' '}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-sky-300 to-emerald-300">
              Rare & Orphan Diseases
            </span>
          </h1>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Query across <strong className="text-white">4,357 orphan conditions</strong>, explore graph neural network (GNN) embeddings, calibrated efficacy probabilities, and safety profiles from FAERS post-market data.
          </p>

          {/* Quick Demo Shortcuts */}
          <div className="pt-2 flex flex-wrap items-center gap-2">
            <span className="text-xs text-indigo-200/70 font-medium mr-1">Quick Benchmarks:</span>
            {BENCHMARKS.map((b) => (
              <button
                key={b.orphaId}
                onClick={() => handleBenchmarkClick(b)}
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-white/10 hover:bg-white/20 text-white rounded-lg transition-all border border-white/10 active:scale-95"
              >
                <span>{b.name}</span>
                <span className="text-[10px] text-indigo-300 font-mono">({b.orphaId})</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5 hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Diseases</span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Dna className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">4,357</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span className="text-emerald-600 font-medium">Orphanet</span> curated rare cohort
          </div>
        </div>

        <div className="card p-5 hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Approved Drugs</span>
            <div className="p-2 rounded-xl bg-sky-50 text-sky-600">
              <Network className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">1,645</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span className="text-emerald-600 font-medium">DrugCentral</span> bioactive molecules
          </div>
        </div>

        <div className="card p-5 hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Prediction Engine</span>
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">DualEncoder</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span className="text-purple-600 font-medium">GNN + Cross-Attention</span> calibrated
          </div>
        </div>

        <div className="card p-5 hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Safety Engine</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">FAERS + ADMET</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span className="text-emerald-600 font-medium">Disproportionality</span> + RDKit
          </div>
        </div>
      </div>

      {/* Search & Filtering Card */}
      <div className="card p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-slate-400" />
            <input
              type="search"
              placeholder="Search 4,357 rare diseases by disease name, ORPHA code (e.g. ORPHA:635), gene (e.g. NPC1)..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setPage(1)
              }}
              className="input pl-10.5 pr-9"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-secondary flex items-center gap-2 ${
                showFilters || hasActiveFilters ? 'border-indigo-300 bg-indigo-50/50 text-indigo-700' : ''
              }`}
            >
              <SlidersHorizontal className="h-4 w-4 text-slate-500" />
              <span>Advanced Filters</span>
              {hasActiveFilters && (
                <span className="h-2 w-2 rounded-full bg-indigo-600" />
              )}
              {showFilters ? <ChevronUp className="h-4 w-4 ml-1" /> : <ChevronDown className="h-4 w-4 ml-1" />}
            </button>
          </div>
        </div>

        {/* Collapsible Filter Tray */}
        {showFilters && (
          <div className="pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-in fade-in duration-200">
            <div>
              <label className="label">Max Prevalence (per 100k)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                placeholder="e.g. 5.0 (rare)"
                value={prevalenceMax}
                onChange={(e) => {
                  setPrevalenceMax(e.target.value === '' ? '' : Number(e.target.value))
                  setPage(1)
                }}
                className="input"
              />
            </div>
            <div>
              <label className="label">Target Gene Symbol</label>
              <input
                type="text"
                placeholder="e.g. NPC1, CFTR, HTT"
                value={gene}
                onChange={(e) => {
                  setGene(e.target.value)
                  setPage(1)
                }}
                className="input uppercase"
              />
            </div>
            <div>
              <label className="label">Biological Pathway</label>
              <input
                type="text"
                placeholder="e.g. lipid storage, ion transport"
                value={pathway}
                onChange={(e) => {
                  setPathway(e.target.value)
                  setPage(1)
                }}
                className="input"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={clearAllFilters}
                disabled={!hasActiveFilters}
                className="btn-secondary w-full"
              >
                Reset Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Disease Results Section */}
      <div className="card overflow-hidden">
        {/* Table header bar */}
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-900">Rare Diseases</h2>
            <span className="badge-gray font-mono">{total.toLocaleString()} results</span>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span>Sort By:</span>
            <button
              onClick={() => handleSort('unmet_need_score')}
              className={`font-semibold cursor-pointer transition-colors ${
                sortBy === 'unmet_need_score' ? 'text-indigo-600' : 'hover:text-slate-700'
              }`}
            >
              Unmet Need <SortIcon field="unmet_need_score" />
            </button>
            <span className="text-slate-300">|</span>
            <button
              onClick={() => handleSort('name')}
              className={`font-semibold cursor-pointer transition-colors ${
                sortBy === 'name' ? 'text-indigo-600' : 'hover:text-slate-700'
              }`}
            >
              Name <SortIcon field="name" />
            </button>
            <span className="text-slate-300">|</span>
            <button
              onClick={() => handleSort('prevalence')}
              className={`font-semibold cursor-pointer transition-colors ${
                sortBy === 'prevalence' ? 'text-indigo-600' : 'hover:text-slate-700'
              }`}
            >
              Prevalence <SortIcon field="prevalence" />
            </button>
          </div>
        </div>

        {/* Loading Bar */}
        {isLoading && <div className="h-1 bg-indigo-600 animate-pulse" />}

        {/* Disease Items Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50/70">
                <th className="px-6 py-3.5">Disease & Identification</th>
                <th className="px-6 py-3.5">Prevalence / Rarity</th>
                <th className="px-6 py-3.5">Unmet Medical Need</th>
                <th className="px-6 py-3.5">Genetic Etiology</th>
                <th className="px-6 py-3.5 text-right">Repurposing Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {diseases.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-16 text-center">
                    <div className="h-12 w-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                      <Info className="h-6 w-6" />
                    </div>
                    <h4 className="text-base font-semibold text-slate-800">No matching diseases found</h4>
                    <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                      Try searching by generic disease name or clear existing filters.
                    </p>
                    {hasActiveFilters && (
                      <button onClick={clearAllFilters} className="btn-secondary text-xs mt-4">
                        Clear all filters
                      </button>
                    )}
                  </td>
                </tr>
              ) : (
                diseases.map((d: DiseaseSearchResult) => {
                  const needScore = d.unmet_need_score ?? 0
                  return (
                    <tr key={d.orpha_id} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="px-6 py-4">
                        <Link
                          to={`/diseases/${d.orpha_id}`}
                          className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors block text-base leading-tight mb-1"
                        >
                          {d.name}
                        </Link>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
                            {d.orpha_id}
                          </span>
                          {d.inheritance && d.inheritance.length > 0 && (
                            <span className="text-xs text-slate-400 hidden sm:inline">
                              {d.inheritance.slice(0, 1).join(', ')}
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="text-xs font-semibold text-slate-700">
                            {d.prevalence !== null && d.prevalence !== undefined
                              ? `${d.prevalence.toFixed(2)} per 100k`
                              : 'Not quantified'}
                          </div>
                          {d.prevalence_category && (
                            <span className="badge-gray text-[10px] block w-fit">
                              {d.prevalence_category}
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="space-y-1.5 w-40">
                          <div className="flex items-center justify-between text-xs font-semibold">
                            <span
                              className={
                                needScore >= 0.8
                                  ? 'text-rose-600'
                                  : needScore >= 0.65
                                  ? 'text-amber-600'
                                  : 'text-indigo-600'
                              }
                            >
                              {needScore >= 0.8 ? 'High Priority' : needScore >= 0.65 ? 'Elevated' : 'Moderate'}
                            </span>
                            <span className="font-mono text-slate-700 font-bold">
                              {(needScore * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${
                                needScore >= 0.8
                                  ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                                  : needScore >= 0.65
                                  ? 'bg-gradient-to-r from-indigo-500 to-amber-500'
                                  : 'bg-gradient-to-r from-emerald-500 to-indigo-500'
                              }`}
                              style={{ width: `${Math.min(needScore * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        {d.genes && d.genes.length > 0 ? (
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            {d.genes.slice(0, 3).map((g) => (
                              <span
                                key={g.hgnc_id || g.symbol}
                                className="badge-purple font-mono text-[11px] font-semibold"
                              >
                                {g.symbol}
                              </span>
                            ))}
                            {d.genes.length > 3 && (
                              <span className="badge-gray text-[10px]">+{d.genes.length - 3}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">Complex / Polygenic</span>
                        )}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/diseases/${d.orpha_id}/candidates`}
                          className="btn-primary text-xs py-2 px-3.5 inline-flex items-center gap-1.5 font-semibold group-hover:scale-102 transition-all"
                        >
                          <span>Repurpose</span>
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Modern Pagination Footer */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50/50">
            <span className="text-xs text-slate-500">
              Showing page <strong className="text-slate-800">{page}</strong> of{' '}
              <strong className="text-slate-800">{totalPages.toLocaleString()}</strong> ({total.toLocaleString()} total diseases)
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary text-xs px-3 py-1.5"
              >
                Previous
              </button>
              <div className="hidden sm:flex items-center gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  const pNum = Math.min(Math.max(1, page - 2), totalPages - 4) + i
                  if (pNum < 1 || pNum > totalPages) return null
                  return (
                    <button
                      key={pNum}
                      onClick={() => setPage(pNum)}
                      className={`h-8 w-8 rounded-lg text-xs font-semibold transition-all ${
                        pNum === page
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'text-slate-600 hover:bg-slate-200/60'
                      }`}
                    >
                      {pNum}
                    </button>
                  )
                })}
              </div>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary text-xs px-3 py-1.5"
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
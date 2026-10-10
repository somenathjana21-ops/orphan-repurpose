import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Search,
  AlertCircle,
  Network,
  ArrowRight,
  Sparkles,
  Layers,
  Share2,
} from 'lucide-react'
import { kgApi } from '../services/api'
import type { KGDrug, KGDisease } from '../types'

export function KGBrowser() {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 15
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

  const isLoading = (activeTab === 'drugs' && drugsLoading) || (activeTab === 'diseases' && diseasesLoading)
  const error = drugsError || diseasesError

  if (error) {
    return (
      <div className="glass-card max-w-xl mx-auto my-12 p-8 text-center">
        <AlertCircle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-900 mb-1">Failed to Query Knowledge Graph</h3>
        <p className="text-sm text-slate-500 mb-4">{(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="space-y-7">
      {/* Header Banner */}
      <div className="glass-card p-7 sm:p-9 bg-gradient-to-br from-white via-white to-blue-50/20 border border-slate-200/90 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/60 shadow-2xs">
              <Network className="h-3.5 w-3.5 text-blue-600" />
              <span>Kùzu Embedded Biological Knowledge Graph Engine</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Knowledge Graph Explorer
            </h1>
            <p className="text-slate-600 text-sm leading-relaxed">
              Explore interconnected nodes across drugs, rare diseases, targets, and Reactome biological pathways extracted directly from local graph storage.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/diseases/ORPHA:635/candidates"
              className="btn-cobalt text-xs py-2.5 px-4 rounded-xl shadow-md shadow-blue-500/20"
            >
              <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              Test Candidates
            </Link>
          </div>
        </div>
      </div>

      {/* Graph Metric Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          <div className="glass-card p-5.5 card-hover">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Total Graph Nodes
              </span>
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/50">
                <Network className="h-4 w-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {stats.total_nodes.toLocaleString()}
            </div>
            <div className="text-xs text-slate-500 mt-1">Entities in Kùzu DB</div>
          </div>

          <div className="glass-card p-5.5 card-hover">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Total Graph Edges
              </span>
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200/50">
                <Share2 className="h-4 w-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {stats.total_edges.toLocaleString()}
            </div>
            <div className="text-xs text-slate-500 mt-1">Relationships indexed</div>
          </div>

          <div className="glass-card p-5.5 card-hover">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Node Labels
              </span>
              <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-200/50">
                <Layers className="h-4 w-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {Object.keys(stats.node_types).length} Types
            </div>
            <div className="text-xs text-slate-500 mt-1">Disease, Drug, Gene, Pathway</div>
          </div>

          <div className="glass-card p-5.5 card-hover">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Edge Types
              </span>
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-200/50">
                <Sparkles className="h-4 w-4" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {Object.keys(stats.edge_types).length} Types
            </div>
            <div className="text-xs text-slate-500 mt-1">HAS_TARGET, TREATS, etc.</div>
          </div>
        </div>
      )}

      {/* Segmented Pill Tabs */}
      <div className="flex p-1 bg-slate-100 rounded-2xl w-fit">
        <button
          onClick={() => {
            setActiveTab('drugs')
            setPage(1)
          }}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === 'drugs'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Drug Nodes
        </button>
        <button
          onClick={() => {
            setActiveTab('diseases')
            setPage(1)
          }}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === 'diseases'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Disease Nodes
        </button>
        <button
          onClick={() => {
            setActiveTab('stats')
          }}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === 'stats'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Detailed Graph Schema
        </button>
      </div>

      {/* Search Input */}
      {activeTab !== 'stats' && (
        <div className="glass-card p-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-slate-400" />
            <input
              type="search"
              placeholder={`Search ${activeTab === 'drugs' ? 'drugs by name, DrugCentral ID, or MoA' : 'diseases by name or ORPHA ID'}...`}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setPage(1)
              }}
              className="input pl-11 py-2.5 rounded-2xl"
            />
          </div>
        </div>
      )}

      {/* Drugs Table */}
      {activeTab === 'drugs' && drugs && (
        <div className="glass-card overflow-hidden">
          {isLoading && <div className="h-1 bg-blue-600 animate-pulse" />}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50/50">
                  <th className="px-6 sm:px-8 py-4">Drug Name</th>
                  <th className="px-6 py-4">Entity ID</th>
                  <th className="px-6 py-4">Approval Status</th>
                  <th className="px-6 sm:px-8 py-4">Targets / MoA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {drugs.data.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-slate-500 text-xs">
                      No drugs found matching query.
                    </td>
                  </tr>
                ) : (
                  drugs.data.map((d: KGDrug) => (
                    <tr key={d.id} className="hover:bg-blue-50/30 transition-colors">
                      <td className="px-6 sm:px-8 py-4 font-bold text-slate-900">{d.name}</td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-600">{d.id}</td>
                      <td className="px-6 py-4">
                        <span
                          className={
                            d.approval_status === 'FDA_approved' ? 'badge-green' : 'badge-gray'
                          }
                        >
                          {d.approval_status}
                        </span>
                      </td>
                      <td className="px-6 sm:px-8 py-4 text-xs text-slate-600 max-w-md truncate">
                        {d.target_names || d.moa_classes || '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Drugs Pagination */}
          {drugs.total > pageSize && (
            <div className="px-6 sm:px-8 py-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 bg-white/70">
              <span>
                Page {page} of {Math.ceil(drugs.total / pageSize)} ({drugs.total.toLocaleString()} drugs total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-xs px-3.5 py-1.5 rounded-xl"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(Math.ceil(drugs.total / pageSize), p + 1))}
                  disabled={page >= Math.ceil(drugs.total / pageSize)}
                  className="btn-secondary text-xs px-3.5 py-1.5 rounded-xl"
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
        <div className="glass-card overflow-hidden">
          {isLoading && <div className="h-1 bg-blue-600 animate-pulse" />}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50/50">
                  <th className="px-6 sm:px-8 py-4">Disease Name</th>
                  <th className="px-6 py-4">ORPHA ID</th>
                  <th className="px-6 py-4">Prevalence</th>
                  <th className="px-6 py-4">Unmet Need</th>
                  <th className="px-6 sm:px-8 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {diseases.data.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-slate-500 text-xs">
                      No diseases found matching query.
                    </td>
                  </tr>
                ) : (
                  diseases.data.map((d: KGDisease) => (
                    <tr key={d.id} className="hover:bg-blue-50/30 transition-colors">
                      <td className="px-6 sm:px-8 py-4 font-bold text-slate-900">{d.name}</td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-600">{d.id}</td>
                      <td className="px-6 py-4 text-xs text-slate-600">
                        {d.prevalence !== null && d.prevalence !== undefined
                          ? `${d.prevalence.toFixed(2)} per 100k`
                          : '—'}
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-xs font-bold text-slate-700">
                          {d.unmet_need_score !== null && d.unmet_need_score !== undefined
                            ? `${(d.unmet_need_score * 100).toFixed(0)}%`
                            : '—'}
                        </span>
                      </td>
                      <td className="px-6 sm:px-8 py-4 text-right">
                        <Link
                          to={`/diseases/${d.id}`}
                          className="btn-secondary text-xs py-1.5 px-3.5 inline-flex items-center gap-1 font-semibold rounded-xl"
                        >
                          <span>Explore</span>
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Diseases Pagination */}
          {diseases.total > pageSize && (
            <div className="px-6 sm:px-8 py-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 bg-white/70">
              <span>
                Page {page} of {Math.ceil(diseases.total / pageSize)} ({diseases.total.toLocaleString()} diseases total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-xs px-3.5 py-1.5 rounded-xl"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(Math.ceil(diseases.total / pageSize), p + 1))}
                  disabled={page >= Math.ceil(diseases.total / pageSize)}
                  className="btn-secondary text-xs px-3.5 py-1.5 rounded-xl"
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <h3 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 uppercase tracking-wider">
              Node Distribution
            </h3>
            <div className="space-y-2.5">
              {Object.entries(stats.node_types).map(([type, count]) => (
                <div
                  key={type}
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/60"
                >
                  <span className="font-semibold text-slate-800 text-xs">{type}</span>
                  <span className="font-mono text-xs font-bold bg-white px-2.5 py-1 rounded-xl border border-slate-200 shadow-2xs">
                    {Number(count).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card p-6">
            <h3 className="text-sm font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 uppercase tracking-wider">
              Relationship (Edge) Schema
            </h3>
            <div className="space-y-2.5">
              {Object.entries(stats.edge_types).map(([type, count]) => (
                <div
                  key={type}
                  className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50/80 border border-slate-200/60"
                >
                  <span className="font-mono text-xs font-bold text-blue-700">{type}</span>
                  <span className="font-mono text-xs font-bold bg-white px-2.5 py-1 rounded-xl border border-slate-200 shadow-2xs">
                    {Number(count).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

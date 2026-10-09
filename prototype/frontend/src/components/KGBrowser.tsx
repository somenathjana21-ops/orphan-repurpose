import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Search,
  AlertCircle,
  Network,
  ArrowRight,
  Sparkles,
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
      <div className="card max-w-xl mx-auto my-12 p-8 text-center">
        <AlertCircle className="h-10 w-10 text-rose-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-900 mb-1">Failed to Query Knowledge Graph</h3>
        <p className="text-sm text-slate-500 mb-4">{(error as Error).message}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="card p-7 sm:p-8 bg-gradient-to-br from-white via-white to-sky-50/40 border border-slate-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-100/80 text-sky-800 text-xs font-semibold">
              <Network className="h-3.5 w-3.5" />
              <span>Kùzu Embedded Knowledge Graph Engine</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Knowledge Graph Explorer
            </h1>
            <p className="text-slate-600 text-sm max-w-2xl leading-relaxed">
              Explore interconnected nodes across drugs, rare diseases, targets, and Reactome biological pathways extracted directly from local graph storage.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link to="/diseases/ORPHA:635/candidates" className="btn-primary text-xs py-2 px-3.5">
              <Sparkles className="h-3.5 w-3.5 mr-1.5" />
              Test Candidates
            </Link>
          </div>
        </div>
      </div>

      {/* Graph Metric Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Total Graph Nodes
            </div>
            <div className="text-2xl font-extrabold text-indigo-600">
              {stats.total_nodes.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Entities in Kùzu DB</div>
          </div>

          <div className="card p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Total Graph Edges
            </div>
            <div className="text-2xl font-extrabold text-emerald-600">
              {stats.total_edges.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Relationships indexed</div>
          </div>

          <div className="card p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Node Labels
            </div>
            <div className="text-2xl font-extrabold text-purple-600">
              {Object.keys(stats.node_types).length} Types
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Disease, Drug, Gene, Pathway</div>
          </div>

          <div className="card p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Edge Relationships
            </div>
            <div className="text-2xl font-extrabold text-amber-600">
              {Object.keys(stats.edge_types).length} Types
            </div>
            <div className="text-[11px] text-slate-400 mt-1">HAS_TARGET, TREATS, etc.</div>
          </div>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        <button
          onClick={() => {
            setActiveTab('drugs')
            setPage(1)
          }}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === 'drugs'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Drug Nodes
        </button>
        <button
          onClick={() => {
            setActiveTab('diseases')
            setPage(1)
          }}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === 'diseases'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Disease Nodes
        </button>
        <button
          onClick={() => {
            setActiveTab('stats')
          }}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === 'stats'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Detailed Graph Schema
        </button>
      </div>

      {/* Search Input for Drugs & Diseases */}
      {activeTab !== 'stats' && (
        <div className="card p-4">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-slate-400" />
            <input
              type="search"
              placeholder={`Search ${activeTab === 'drugs' ? 'drugs by name, DrugCentral ID, or MoA' : 'diseases by name or ORPHA ID'}...`}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setPage(1)
              }}
              className="input pl-10.5"
            />
          </div>
        </div>
      )}

      {/* Drugs Table */}
      {activeTab === 'drugs' && drugs && (
        <div className="card overflow-hidden">
          {isLoading && <div className="h-1 bg-indigo-600 animate-pulse" />}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50/70">
                  <th className="px-6 py-3.5">Drug Name</th>
                  <th className="px-6 py-3.5">Entity ID</th>
                  <th className="px-6 py-3.5">Approval Status</th>
                  <th className="px-6 py-3.5">Targets / MoA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {drugs.data.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                      No drugs found matching query.
                    </td>
                  </tr>
                ) : (
                  drugs.data.map((d: KGDrug) => (
                    <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-bold text-slate-900">{d.name}</td>
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
                      <td className="px-6 py-4 text-xs text-slate-600 max-w-md truncate">
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
            <div className="px-6 py-3.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>
                Page {page} of {Math.ceil(drugs.total / pageSize)} ({drugs.total.toLocaleString()} drugs total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-xs px-3 py-1"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(Math.ceil(drugs.total / pageSize), p + 1))}
                  disabled={page >= Math.ceil(drugs.total / pageSize)}
                  className="btn-secondary text-xs px-3 py-1"
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
          {isLoading && <div className="h-1 bg-indigo-600 animate-pulse" />}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-slate-400 bg-slate-50/70">
                  <th className="px-6 py-3.5">Disease Name</th>
                  <th className="px-6 py-3.5">ORPHA ID</th>
                  <th className="px-6 py-3.5">Prevalence</th>
                  <th className="px-6 py-3.5">Unmet Need</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {diseases.data.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                      No diseases found matching query.
                    </td>
                  </tr>
                ) : (
                  diseases.data.map((d: KGDisease) => (
                    <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-bold text-slate-900">{d.name}</td>
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
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/diseases/${d.id}`}
                          className="btn-secondary text-xs py-1 px-3 inline-flex items-center gap-1 font-semibold"
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
            <div className="px-6 py-3.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>
                Page {page} of {Math.ceil(diseases.total / pageSize)} ({diseases.total.toLocaleString()} diseases total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary text-xs px-3 py-1"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(Math.ceil(diseases.total / pageSize), p + 1))}
                  disabled={page >= Math.ceil(diseases.total / pageSize)}
                  className="btn-secondary text-xs px-3 py-1"
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
          <div className="card p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100">
              Node Distribution
            </h3>
            <div className="space-y-3">
              {Object.entries(stats.node_types).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="font-semibold text-slate-800 text-sm">{type}</span>
                  <span className="font-mono text-xs font-bold bg-white px-2.5 py-1 rounded-md border border-slate-200">
                    {Number(count).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100">
              Relationship (Edge) Schema
            </h3>
            <div className="space-y-3">
              {Object.entries(stats.edge_types).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="font-mono text-xs font-bold text-indigo-700">{type}</span>
                  <span className="font-mono text-xs font-bold bg-white px-2.5 py-1 rounded-md border border-slate-200">
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

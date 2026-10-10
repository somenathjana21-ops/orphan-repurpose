import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Sparkles,
  Dna,
  Network,
  AlertCircle,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react'
import { diseasesApi } from '../services/api'

export function DiseaseDetail() {
  const { orphaId = 'ORPHA:635' } = useParams<{ orphaId: string }>()

  const { data: disease, isLoading, error } = useQuery({
    queryKey: ['disease', orphaId],
    queryFn: () => diseasesApi.get(orphaId),
    enabled: !!orphaId,
  })

  const { data: genes, isLoading: genesLoading } = useQuery({
    queryKey: ['disease-genes', orphaId],
    queryFn: () => diseasesApi.getGenes(orphaId),
    enabled: !!orphaId,
  })

  const { data: pathways, isLoading: pathwaysLoading } = useQuery({
    queryKey: ['disease-pathways', orphaId],
    queryFn: () => diseasesApi.getPathways(orphaId),
    enabled: !!orphaId,
  })

  if (error) {
    return (
      <div className="glass-card max-w-xl mx-auto my-12 p-8 text-center">
        <div className="h-14 w-14 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-4 border border-rose-100">
          <AlertCircle className="h-7 w-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Error Loading Disease Profile</h2>
        <p className="text-sm text-slate-500 mb-6">{(error as Error).message}</p>
        <Link to="/" className="btn-cobalt">
          Back to Disease Browser
        </Link>
      </div>
    )
  }

  if (!disease || isLoading) {
    return (
      <div className="glass-card max-w-xl mx-auto my-12 p-12 text-center space-y-4">
        <div className="h-12 w-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto animate-pulse">
          <Dna className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">Loading Rare Disease Profile...</h2>
        <div className="w-32 h-1 bg-blue-600 rounded-full mx-auto animate-pulse" />
      </div>
    )
  }

  const needScore = disease.unmet_need_score ?? 0

  return (
    <div className="space-y-6">
      {/* Top Navigation & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> All Rare Diseases
          </Link>
          <span className="text-slate-300">/</span>
          <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold">
            {disease.orpha_id}
          </span>
        </div>

        <Link
          to={`/diseases/${disease.orpha_id}/candidates`}
          className="btn-cobalt text-xs py-2.5 px-5 inline-flex items-center gap-2 font-semibold shadow-md shadow-blue-500/20 rounded-xl"
        >
          <Sparkles className="h-4 w-4" />
          <span>Generate Repurposing Candidates</span>
        </Link>
      </div>

      {/* Hero Disease Profile Card */}
      <div className="glass-card p-7 sm:p-9 bg-gradient-to-br from-white via-white to-blue-50/20 border border-slate-200/90 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="badge-purple font-mono text-xs font-semibold">
                {disease.orpha_id}
              </span>
              {disease.prevalence_category && (
                <span className="badge-gray text-xs">{disease.prevalence_category}</span>
              )}
              {disease.inheritance && disease.inheritance.length > 0 && (
                <span className="badge-blue text-xs">{disease.inheritance.join(', ')}</span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              {disease.name}
            </h1>

            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              {disease.description ||
                'Orphanet indexed clinical condition with designated orphan disease code.'}
            </p>
          </div>

          {/* Unmet Need Gauge Box */}
          <div className="p-5 rounded-2xl bg-white/90 backdrop-blur-md border border-slate-200/90 shadow-xs space-y-3 min-w-[240px]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Unmet Need Index
              </span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  needScore >= 0.8
                    ? 'bg-rose-50 text-rose-700 border border-rose-200/60'
                    : needScore >= 0.65
                    ? 'bg-amber-50 text-amber-700 border border-amber-200/60'
                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                }`}
              >
                {needScore >= 0.8 ? 'Critical' : needScore >= 0.65 ? 'High' : 'Moderate'}
              </span>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-slate-900">
                {(needScore * 100).toFixed(0)}%
              </span>
              <span className="text-xs font-mono text-slate-400">score: {needScore.toFixed(3)}</span>
            </div>

            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  needScore >= 0.8
                    ? 'bg-gradient-to-r from-amber-500 to-rose-600'
                    : needScore >= 0.65
                    ? 'bg-gradient-to-r from-blue-500 to-amber-500'
                    : 'bg-gradient-to-r from-emerald-500 to-blue-500'
                }`}
                style={{ width: `${Math.min(needScore * 100, 100)}%` }}
              />
            </div>

            <p className="text-[11px] text-slate-400 leading-tight">
              Calculated from disease prevalence, treatment availability gap, and genomic clarity.
            </p>
          </div>
        </div>

        {/* Existing Treatments Bar */}
        <div className="pt-6 flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Approved / Existing Standard of Care
            </span>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {disease.existing_treatments && disease.existing_treatments.length > 0 ? (
                disease.existing_treatments.map((t, idx) => (
                  <span key={idx} className="badge-green font-semibold text-xs">
                    {t}
                  </span>
                ))
              ) : (
                <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  No FDA/EMA Approved Disease-Modifying Therapies
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to={`/diseases/${disease.orpha_id}/candidates`}
              className="btn-cobalt text-xs py-2 px-4 flex items-center gap-1.5 rounded-xl"
            >
              <span>Repurposing Candidates</span>
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Genetic Etiology & Biological Pathways Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Genes Card */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-200/50">
                <Dna className="h-4 w-4" />
              </div>
              <h2 className="text-base font-bold text-slate-900">
                Associated Genes ({genes?.length || disease.genes?.length || 0})
              </h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">HGNC Curated</span>
          </div>

          {genesLoading ? (
            <p className="text-xs text-slate-400 py-4">Querying gene annotations...</p>
          ) : (
            <div className="space-y-3">
              {(genes && genes.length > 0) || (disease.genes && disease.genes.length > 0) ? (
                <div className="flex flex-wrap gap-2">
                  {(genes && genes.length > 0 ? genes : disease.genes.map((g) => g.symbol)).map(
                    (sym, idx) => (
                      <div
                        key={idx}
                        className="px-3 py-1.5 rounded-xl bg-purple-50/80 border border-purple-200/70 text-purple-900 font-mono text-xs font-bold flex items-center gap-2"
                      >
                        <span>{sym}</span>
                        <span className="text-[10px] text-purple-500 font-normal">HGNC</span>
                      </div>
                    )
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-3">
                  No single-gene Mendelian driver cataloged; condition may be polygenic or complex.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Pathways Card */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/50">
                <Network className="h-4 w-4" />
              </div>
              <h2 className="text-base font-bold text-slate-900">
                Reactome Biological Pathways ({pathways?.length || disease.pathways?.length || 0})
              </h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">Reactome</span>
          </div>

          {pathwaysLoading ? (
            <p className="text-xs text-slate-400 py-4">Querying pathway graph...</p>
          ) : (
            <div className="space-y-2">
              {(pathways && pathways.length > 0) || (disease.pathways && disease.pathways.length > 0) ? (
                (pathways && pathways.length > 0 ? pathways : disease.pathways.map((p) => p.name)).map(
                  (name, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-200/60 text-xs text-slate-700 flex items-center justify-between"
                    >
                      <span className="font-medium truncate max-w-sm">{name}</span>
                      <span className="text-[10px] font-mono text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                        Pathway
                      </span>
                    </div>
                  )
                )
              ) : (
                <p className="text-xs text-slate-500 py-3">
                  No curated Reactome pathways directly attached to this disease node.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

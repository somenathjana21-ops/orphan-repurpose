import type { Explanation, KGPath } from '../types'
import { Network, BarChart3, RotateCcw, Sparkles } from 'lucide-react'

interface ExplanationPanelProps {
  explanation: Explanation
  isLoading?: boolean
}

function Skeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-4 bg-slate-200 rounded-lg w-1/4" />
      <div className="h-20 bg-slate-100 rounded-2xl" />
      <div className="h-4 bg-slate-200 rounded-lg w-1/3" />
      <div className="h-16 bg-slate-100 rounded-2xl" />
    </div>
  )
}

function KGPathCard({ path, index }: { path: KGPath; index: number }) {
  return (
    <div className="p-4 bg-white/90 border border-slate-200/80 rounded-2xl shadow-xs hover:border-blue-300 transition-all">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          Path {index + 1}
        </h4>
        <span className="text-[11px] font-mono font-semibold text-blue-700 bg-blue-50 border border-blue-200/60 px-2.5 py-0.5 rounded-full">
          Score: {path.score.toFixed(3)}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-1.5">
        {path.nodes.map((node, nodeIndex) => (
          <span key={nodeIndex} className="flex items-center gap-1.5">
            <span className="bg-slate-50 border border-slate-200/80 px-2.5 py-1 text-xs rounded-xl shadow-2xs">
              <span className="font-semibold text-slate-900">{node.name}</span>
              <span className="text-slate-400 text-[11px] ml-1">({node.type})</span>
            </span>
            {nodeIndex < path.nodes.length - 1 && (
              <span className="text-blue-500 font-bold text-sm">→</span>
            )}
          </span>
        ))}
      </div>
      {path.edges.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {path.edges.map((edge, edgeIndex) => (
            <span
              key={edgeIndex}
              className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md"
            >
              {edge.type}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function SHAPBar({ feature, value }: { feature: string; value: number }) {
  const maxVal = 0.5
  const width = Math.min((Math.abs(value) / maxVal) * 100, 100)
  const isPositive = value > 0

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-600 w-36 truncate font-mono" title={feature}>
        {feature}
      </span>
      <div className="flex-1 h-3.5 bg-slate-100 rounded-full overflow-hidden relative">
        <div className="absolute inset-y-0 left-1/2 w-px bg-slate-300" />
        <div
          className={`absolute inset-y-0 rounded-full transition-all ${
            isPositive ? 'bg-blue-600 left-1/2' : 'bg-rose-500 right-1/2'
          }`}
          style={{ width: `${width / 2}%` }}
        />
      </div>
      <span
        className={`text-xs font-mono w-16 text-right font-semibold ${
          isPositive ? 'text-blue-600' : 'text-rose-600'
        }`}
      >
        {value >= 0 ? '+' : ''}
        {value.toFixed(4)}
      </span>
    </div>
  )
}

function CounterfactualCard({
  removedEdge,
  probabilityDelta,
  description,
}: {
  removedEdge: string
  probabilityDelta: number
  description: string
}) {
  return (
    <div className="p-4 bg-amber-50/50 border border-amber-200/70 rounded-2xl">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-xs font-mono bg-white text-slate-700 px-2 py-0.5 rounded-lg border border-amber-200 font-semibold">
          {removedEdge}
        </span>
        <span
          className={`text-xs font-bold px-2 py-0.5 rounded-full ${
            probabilityDelta < 0
              ? 'bg-rose-50 text-rose-700 border border-rose-200/60'
              : 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
          }`}
        >
          {probabilityDelta >= 0 ? '+' : ''}
          {probabilityDelta.toFixed(3)}
        </span>
      </div>
      <p className="text-xs text-slate-700 leading-relaxed">{description}</p>
    </div>
  )
}

export function ExplanationPanel({ explanation, isLoading }: ExplanationPanelProps) {
  if (isLoading) {
    return <Skeleton />
  }

  if (!explanation) {
    return (
      <div className="p-4 bg-slate-50 rounded-2xl text-slate-500 text-xs">
        No explanation available.
      </div>
    )
  }

  const hasKGPaths = explanation.kg_paths && explanation.kg_paths.length > 0
  const hasSHAP = explanation.shap_values && Object.keys(explanation.shap_values).length > 0
  const hasCF = explanation.counterfactuals && explanation.counterfactuals.length > 0
  const hasLLM = explanation.llm_rationale && explanation.llm_rationale.length > 0

  return (
    <div className="space-y-6">
      {/* Knowledge Graph Paths */}
      {hasKGPaths && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Network className="h-3.5 w-3.5 text-blue-600" />
            Biological Relation Paths
          </h3>
          <div className="space-y-2.5">
            {explanation.kg_paths.map((path, index) => (
              <KGPathCard key={index} path={path} index={index} />
            ))}
          </div>
        </div>
      )}

      {/* SHAP Values */}
      {hasSHAP && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <BarChart3 className="h-3.5 w-3.5 text-blue-600" />
            Feature Attribution Importance (SHAP)
          </h3>
          <div className="space-y-2 p-4 bg-white/90 border border-slate-200/80 rounded-2xl shadow-xs">
            {Object.entries(explanation.shap_values).map(([feature, value]) => (
              <SHAPBar key={feature} feature={feature} value={value} />
            ))}
            <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
              <span className="flex items-center gap-1 font-semibold text-blue-600">
                <span className="h-2 w-2 rounded-full bg-blue-600" /> Positive (Supports)
              </span>
              <span className="flex items-center gap-1 font-semibold text-rose-600">
                <span className="h-2 w-2 rounded-full bg-rose-500" /> Negative (Against)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Counterfactuals */}
      {hasCF && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <RotateCcw className="h-3.5 w-3.5 text-amber-600" />
            Counterfactual Perturbations
          </h3>
          <div className="space-y-2.5">
            {explanation.counterfactuals.map((cf, index) => (
              <CounterfactualCard
                key={index}
                removedEdge={cf.removed_edge}
                probabilityDelta={cf.probability_delta}
                description={cf.description}
              />
            ))}
          </div>
        </div>
      )}

      {/* LLM Rationale */}
      {hasLLM && (
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-blue-600" />
            BioMistral Mechanistic Synthesis
          </h3>
          <div className="p-4 bg-blue-50/40 border border-blue-200/60 rounded-2xl">
            <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
              {explanation.llm_rationale}
            </p>
          </div>
        </div>
      )}

      {!hasKGPaths && !hasSHAP && !hasCF && !hasLLM && (
        <div className="p-4 bg-slate-50 rounded-2xl text-slate-500 text-xs">
          No explanation data available for this candidate.
        </div>
      )}
    </div>
  )
}

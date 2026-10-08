import type { Explanation, KGPath } from '../types'

interface ExplanationPanelProps {
  explanation: Explanation
  isLoading?: boolean
}

function Skeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-4 bg-gray-200 rounded w-1/4" />
      <div className="h-20 bg-gray-200 rounded" />
      <div className="h-4 bg-gray-200 rounded w-1/3" />
      <div className="h-16 bg-gray-200 rounded" />
    </div>
  )
}

function KGPathCard({ path, index }: { path: KGPath; index: number }) {
  return (
    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-blue-900">
          Path {index + 1}
        </h3>
        <span className="text-xs font-mono text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
          Score: {path.score.toFixed(3)}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-1">
        {path.nodes.map((node, nodeIndex) => (
          <span key={nodeIndex} className="flex items-center gap-1">
            <span className="bg-white border border-blue-300 px-2 py-0.5 text-xs rounded shadow-sm">
              <span className="font-medium text-blue-800">{node.name}</span>
              <span className="text-blue-400 ml-1">({node.type})</span>
            </span>
            {nodeIndex < path.nodes.length - 1 && (
              <span className="text-blue-400 font-bold">→</span>
            )}
          </span>
        ))}
      </div>
      {path.edges.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {path.edges.map((edge, edgeIndex) => (
            <span
              key={edgeIndex}
              className="text-xs text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded"
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
  const width = Math.min(Math.abs(value) / maxVal * 100, 100)
  const isPositive = value > 0

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-600 w-32 truncate font-mono" title={feature}>
        {feature}
      </span>
      <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden relative">
        <div className="absolute inset-y-0 left-1/2 w-px bg-gray-300" />
        <div
          className={`absolute inset-y-0 rounded-full transition-all ${
            isPositive ? 'bg-green-500 left-1/2' : 'bg-red-500 right-1/2'
          }`}
          style={{ width: `${width / 2}%` }}
        />
      </div>
      <span
        className={`text-xs font-mono w-16 text-right ${
          isPositive ? 'text-green-700' : 'text-red-700'
        }`}
      >
        {value >= 0 ? '+' : ''}{value.toFixed(4)}
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
    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-mono bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
          {removedEdge}
        </span>
        <span
          className={`text-xs font-bold px-2 py-0.5 rounded ${
            probabilityDelta < 0
              ? 'bg-red-100 text-red-800'
              : 'bg-green-100 text-green-800'
          }`}
        >
          {probabilityDelta >= 0 ? '+' : ''}{probabilityDelta.toFixed(3)}
        </span>
      </div>
      <p className="text-sm text-gray-700">{description}</p>
    </div>
  )
}

export function ExplanationPanel({ explanation, isLoading }: ExplanationPanelProps) {
  if (isLoading) {
    return <Skeleton />
  }

  if (!explanation) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-gray-500 text-sm">
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
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-blue-600">🔗</span>
            Knowledge Graph Paths
          </h3>
          <div className="space-y-2">
            {explanation.kg_paths.map((path, index) => (
              <KGPathCard key={index} path={path} index={index} />
            ))}
          </div>
        </div>
      )}

      {/* SHAP Values */}
      {hasSHAP && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-purple-600">📊</span>
            Feature Importance (SHAP)
          </h3>
          <div className="space-y-1.5 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            {Object.entries(explanation.shap_values).map(([feature, value]) => (
              <SHAPBar key={feature} feature={feature} value={value} />
            ))}
            <div className="flex items-center gap-2 mt-3 pt-2 border-t border-purple-200">
              <span className="text-xs text-green-700 font-medium">+</span>
              <span className="text-xs text-gray-500">Supports prediction</span>
              <span className="text-xs text-red-700 font-medium ml-4">-</span>
              <span className="text-xs text-gray-500">Against prediction</span>
            </div>
          </div>
        </div>
      )}

      {/* Counterfactuals */}
      {hasCF && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-amber-600">🔄</span>
            Counterfactual Explanations
          </h3>
          <div className="space-y-2">
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
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-emerald-600">🧠</span>
            AI Rationale
          </h3>
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {explanation.llm_rationale}
            </p>
          </div>
        </div>
      )}

      {!hasKGPaths && !hasSHAP && !hasCF && !hasLLM && (
        <div className="p-4 bg-gray-50 rounded-lg text-gray-500 text-sm">
          No explanation data available for this candidate.
        </div>
      )}
    </div>
  )
}

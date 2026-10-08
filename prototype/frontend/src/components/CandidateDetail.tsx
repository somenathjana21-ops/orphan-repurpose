import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { candidatesApi, diseasesApi } from '../services/api'
import type { Candidate, DiseaseDetail } from '../types'

export function CandidateDetail() {
  const { candidateId } = useParams<{ candidateId: string }>()

  const { data: candidate, isLoading, error } = useQuery({
    queryKey: ['candidate', candidateId],
    queryFn: () => candidatesApi.get(candidateId),
    enabled: !!candidateId,
  })

  const { data: explanation, isLoading: explanationLoading } = useQuery({
    queryKey: ['candidate-explanation', candidateId],
    queryFn: () => candidatesApi.getExplanation(candidateId),
    enabled: !!candidateId,
  })

  const { data: safety, isLoading: safetyLoading } = useQuery({
    queryKey: ['candidate-safety', candidateId],
    queryFn: () => candidatesApi.getSafety(candidateId),
    enabled: !!candidateId,
  })

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Error loading candidate</h2>
        <p className="text-gray-600">{error.message}</p>
      </div>
    )
  }

  if (!candidate || isLoading || explanationLoading || safetyLoading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Loading candidate details...</h2>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{candidate.drug_name}</h1>
          <p className="text-sm text-gray-600">Drug ID: {candidate.drug_id}</p>
        </div>
        <div>
          {/* We don't have disease_id in candidate, but we can go back to candidates list if we had disease context.
            For now, we'll just show a button to go back (we'll need to adjust routing or pass state).
            Since we don't have disease context, we'll just show a placeholder. */}
          <button className="btn-secondary">Back to Candidates</button>
        </div>
      </div>

      {/* Probability and Confidence Interval */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Indication Probability</h2>
        <div className="flex items-center gap-4">
          <div className="w-40 h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-600 rounded-full transition-all"
              style={{ width: `${Math.min(candidate.indication_probability * 100, 100)}%` }}
            />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">{candidate.indication_probability.toFixed(2)}</p>
            <p className="text-xs text-gray-500">
              95% CI: [{candidate.confidence_interval[0].toFixed(2)}, {candidate.confidence_interval[1].toFixed(2)}]
            </p>
          </div>
        </div>
      </div>

      {/* Mechanism of Action */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Mechanism of Action</h2>
        <p className="text-gray-700">{candidate.moa_summary}</p>
      </div>

      {/* Knowledge Graph Paths */}
      {explanation?.kg_paths?.length && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Knowledge Graph Paths</h2>
          <div className="space-y-3">
            {explanation.kg_paths.map((path, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded">
                <h3 className="text-lg font-medium text-gray-800 mb-2">Path {index + 1} (Score: {path.score.toFixed(3)})</h3>
                <div className="flex flex-wrap gap-2">
                  {path.nodes.map((node, nodeIndex) => (
                    <React.Fragment key={nodeIndex}>
                      <span className="bg-blue-50 px-2 py-0.5 text-xs font-medium rounded text-blue-800">
                        {node.name}
                      </span>
                      {nodeIndex < path.nodes.length - 1 && <span className="text-gray-500"> → </span>}
                    </React.Fragment>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SHAP Values */}
      {explanation?.shap_values && Object.keys(explanation.shap_values).length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">SHAP Values (Feature Importance)</h2>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(explanation.shap_values).map(([feature, value]) => (
              <div key={feature} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-gray-700">{feature}</span>
                <span className="font-mono">{value.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Counterfactuals */}
      {explanation?.counterfactuals?.length && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Counterfactuals</h2>
          <div className="space-y-2">
            {explanation.counterfactuals.map((cf, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded">
                <p className="text-gray-700">{cf.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Probability delta: {cf.probability_delta.toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LLM Rationale */}
      {explanation?.llm_rationale && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">LLM Rationale</h2>
          <div className="p-4 bg-gray-50 rounded">
            <p className="text-gray-700 whitespace-pre-wrap">{explanation.llm_rationale}</p>
          </div>
        </div>
      )}

      {/* Safety */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Safety Assessment</h2>
        <div className="flex items-center gap-2">
          <div className="w-24 h-2.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full
                {safety.overall === 'pass' && 'bg-green-600'}
                {safety.overall === 'caution' && 'bg-amber-600'}
                {safety.overall === 'fail' && 'bg-red-600'}
                rounded-full transition-all
              "
              style={{ width: `${safety.overall === 'pass' ? 100 : safety.overall === 'caution' ? 60 : 20}%` }}
            />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {safety.overall === 'pass' && 'Pass'}
              {safety.overall === 'caution' && 'Caution'}
              {safety.overall === 'fail' && 'Fail'}
            </p>
          </div>
        </div>
        <div className="mt-2">
          <h3 className="text-lg font-semibold text-gray-800 mb-1">FAERS Signals</h3>
          {safety.faers_signals.length > 0 ? (
            <ul className="list-disc list-inside space-y-1 text-gray-700">
              {safety.faers_signals.map((signal, index) => (
                <li key={index}>
                  <strong>{signal.meddra_pt}:</strong> ROR={signal.ror.toFixed(2)}, PRR={signal.prr.toFixed(2)}, BCPNN={signal.bcpnn.toFixed(2)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No FAERS signals.</p>
          )}
          <h3 className="text-lg font-semibold text-gray-800 mb-1 mt-4">ADMET Predictions</h3>
          {Object.keys(safety.admet_predictions).length > 0 ? (
            <ul className="list-disc list-inside space-y-1 text-gray-700">
              {Object.entries(safety.admet_predictions).map(([endpoint, value]) => (
                <li key={endpoint}>
                  <strong>{endpoint}:</strong> {value.toFixed(3)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No ADMET predictions.</p>
          )}
          <h3 className="text-lg font-semibold text-gray-800 mb-1 mt-4">Contraindications</h3>
          {safety.contraindications.length > 0 ? (
            <ul className="list-disc list-inside space-y-1 text-gray-700">
              {safety.contraindications.map((contra, index) => (
                <li key={index}>{contra}</li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No contraindications.</p>
          )}
        </div>
      )
    </div>
  )
}
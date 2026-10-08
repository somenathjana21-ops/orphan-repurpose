import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { candidatesApi } from '../services/api'
import { ExplanationPanel } from './ExplanationPanel'
import { SafetyDashboard } from './SafetyDashboard'
import { ValidationPanel } from './ValidationPanel'

export function CandidateDetail() {
  const { candidateId } = useParams<{ candidateId: string }>()

  const { data: candidate, isLoading, error } = useQuery({
    queryKey: ['candidate', candidateId],
    queryFn: () => candidatesApi.get(candidateId!),
    enabled: !!candidateId,
  })

  const { data: explanation, isLoading: explanationLoading } = useQuery({
    queryKey: ['candidate-explanation', candidateId],
    queryFn: () => candidatesApi.getExplanation(candidateId!),
    enabled: !!candidateId,
  })

  const { data: safety, isLoading: safetyLoading } = useQuery({
    queryKey: ['candidate-safety', candidateId],
    queryFn: () => candidatesApi.getSafety(candidateId!),
    enabled: !!candidateId,
  })

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Error loading candidate</h2>
        <p className="text-gray-600">{(error as Error).message}</p>
      </div>
    )
  }

  if (!candidate || isLoading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Loading candidate details...</h2>
      </div>
    )
  }

  const safetyLevel = safety && 'overall' in safety ? safety.overall : candidate.safety_flags.overall
  const safetyAssessment = safety && 'admet_classifications' in safety
    ? (safety as import('../types/safety').SafetyAssessment)
    : null

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{candidate.drug_name}</h1>
          <p className="text-sm text-gray-600">Drug ID: {candidate.drug_id}</p>
        </div>
        <div>
          <Link to="/" className="btn-secondary">
            Back to Dashboard
          </Link>
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
            <p className="text-2xl font-bold text-gray-900">
              {candidate.indication_probability.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500">
              95% CI: [{candidate.confidence_interval[0].toFixed(2)},{' '}
              {candidate.confidence_interval[1].toFixed(2)}]
            </p>
          </div>
        </div>
      </div>

      {/* Mechanism of Action */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Mechanism of Action</h2>
        <p className="text-gray-700">{candidate.moa_summary}</p>
      </div>

      {/* Explanation Panel */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Explanation</h2>
        <ExplanationPanel
          explanation={explanation ?? { candidate_id: '', kg_paths: [], shap_values: {}, counterfactuals: [], llm_rationale: '' }}
          isLoading={explanationLoading}
        />
      </div>

      {/* Safety */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Safety Assessment</h2>
        {safetyLoading ? (
          <p className="text-gray-500">Loading safety data...</p>
        ) : safetyAssessment ? (
          <SafetyDashboard
            overall={safetyAssessment.overall}
            faersSignals={safetyAssessment.faers_signals}
            admetPredictions={safetyAssessment.admet_predictions}
            admetClassifications={safetyAssessment.admet_classifications}
            contraindications={safetyAssessment.contraindications}
          />
        ) : (
          <>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    safetyLevel === 'pass'
                      ? 'bg-green-600'
                      : safetyLevel === 'caution'
                        ? 'bg-amber-600'
                        : 'bg-red-600'
                  }`}
                  style={{
                    width: `${safetyLevel === 'pass' ? 100 : safetyLevel === 'caution' ? 60 : 20}%`,
                  }}
                />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {safetyLevel === 'pass' ? 'Pass' : safetyLevel === 'caution' ? 'Caution' : 'Fail'}
                </p>
              </div>
            </div>
            <div className="mt-2">
              <h3 className="text-lg font-semibold text-gray-800 mb-1">FAERS Signals</h3>
              {candidate.safety_flags.faers_signals.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-gray-700">
                  {candidate.safety_flags.faers_signals.map((signal, index) => (
                    <li key={index}>
                      <strong>{signal.meddra_pt}:</strong> ROR={signal.ror.toFixed(2)}, PRR=
                      {signal.prr.toFixed(2)}, BCPNN={signal.bcpnn.toFixed(2)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No FAERS signals.</p>
              )}
              <h3 className="text-lg font-semibold text-gray-800 mb-1 mt-4">ADMET Predictions</h3>
              {Object.keys(candidate.safety_flags.admet_predictions).length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-gray-700">
                  {Object.entries(candidate.safety_flags.admet_predictions).map(
                    ([endpoint, value]) => (
                      <li key={endpoint}>
                        <strong>{endpoint}:</strong> {Number(value).toFixed(3)}
                      </li>
                    )
                  )}
                </ul>
              ) : (
                <p className="text-gray-500">No ADMET predictions.</p>
              )}
              <h3 className="text-lg font-semibold text-gray-800 mb-1 mt-4">Contraindications</h3>
              {candidate.safety_flags.contraindications.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-gray-700">
                  {candidate.safety_flags.contraindications.map((contra, index) => (
                    <li key={index}>{contra}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No contraindications.</p>
              )}
            </div>
          </>
        )}
      </div>

      {/* Validation */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Validation</h2>
        <ValidationPanel candidateId={candidate.candidate_id} />
      </div>
    </div>
  )
}

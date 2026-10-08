import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { candidatesApi, diseasesApi } from '../services/api'
import type { Candidate } from '../types'

export function CandidateList() {
  const { orphaId } = useParams<{ orphaId: string }>()
  const navigate = useNavigate()

  const { data: disease, isLoading: diseaseLoading } = useQuery({
    queryKey: ['disease', orphaId],
    queryFn: () => diseasesApi.get(orphaId),
    enabled: !!orphaId,
  })

  const { data: candidates, isLoading, error } = useQuery({
    queryKey: ['candidates', orphaId],
    queryFn: () => candidatesApi.generate(orphaId),
    enabled: !!orphaId,
  })

  const mutation = useMutation({
    mutationFn: (candidateId: string) => 
      candidatesApi.validate(candidateId, {
        validator: 'clinician',
        assessment: 'plausible',
        rationale: 'Looks promising based on mechanism and safety profile.'
      }),
    onSuccess: () => {
      // Refetch the candidate list after validation
      // In a real app, we might want to update optimistically
    },
  })

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Error loading candidates</h2>
        <p className="text-gray-600">{error.message}</p>
      </div>
    )
  }

  if (diseaseLoading || isLoading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Loading candidates...</h2>
      </div>
    )
  }

  if (!disease) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Disease not found</h2>
        <p className="text-gray-600">Please go back and select a valid disease.</p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Repurposing Candidates for {disease.name}
          </h1>
          <p className="text-gray-600">
            ORPHA Code: {disease.orpha_id}
          </p>
        </div>
        <div>
          <a
            href={`/diseases/${disease.orpha_id}`}
            className="btn-secondary"
          >
            Back to Disease Details
          </a>
        </div>
      </div>

      {candidates.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No candidates generated for this disease.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((candidate) => (
            <div key={candidate.candidate_id} className="card hover:shadow-md transition-shadow duration-200">
              <div className="card-body p-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-3">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{candidate.drug_name}</h2>
                    <p className="text-sm text-gray-600">Drug ID: {candidate.drug_id}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-600 rounded-full transition-all"
                        style={{ width: `${Math.min(candidate.indication_probability * 100, 100)}%` }}
                      />
                    </div>
                    <p className="text-gray-900 font-medium">
                      {candidate.indication_probability.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500 ml-2">
                      ({candidate.confidence_interval[0].toFixed(2)} - {candidate.confidence_interval[1].toFixed(2)})
                    </p>
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Mechanism of Action</h3>
                  <p className="text-gray-700">{candidate.moa_summary}</p>
                </div>

                <div className="mt-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Safety Flags</h3>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 text-xs font-medium rounded 
                      {candidate.safety_flags.overall === 'pass' && 'bg-green-50 text-green-800'}
                      {candidate.safety_flags.overall === 'caution' && 'bg-amber-50 text-amber-800'}
                      {candidate.safety_flags.overall === 'fail' && 'bg-red-50 text-red-800'}
                    ">
                      {candidate.safety_flags.overall === 'pass' && 'Pass'}
                      {candidate.safety_flags.overall === 'caution' && 'Caution'}
                      {candidate.safety_flags.overall === 'fail' && 'Fail'}
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex justify-end">
                  <button
                    onClick={() => mutation.mutate(candidate.candidate_id)}
                    disabled={mutation.isLoading}
                    className="btn-primary"
                  >
                    {mutation.isLoading ? 'Validating...' : 'Validate as Plausible'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
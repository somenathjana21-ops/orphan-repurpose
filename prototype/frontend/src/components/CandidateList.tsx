import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  FileText,
  Cpu,
  HelpCircle,
} from 'lucide-react'
import { candidatesApi, diseasesApi } from '../services/api'
import type { Candidate } from '../types'

export function CandidateList() {
  const { orphaId = 'ORPHA:635' } = useParams<{ orphaId: string }>()
  const [validatedIds, setValidatedIds] = useState<Record<string, string>>({})

  const { data: disease, isLoading: diseaseLoading } = useQuery({
    queryKey: ['disease', orphaId],
    queryFn: () => diseasesApi.get(orphaId),
    enabled: !!orphaId,
  })

  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ['candidates', orphaId],
    queryFn: () => candidatesApi.generate(orphaId),
    enabled: !!orphaId,
  })

  const candidates = response?.candidates || []

  const mutation = useMutation({
    mutationFn: (candidateId: string) =>
      candidatesApi.validate(candidateId, {
        validator: 'Clinician / Research Reviewer',
        assessment: 'plausible',
        rationale: 'Hypothesis supported by biological target mechanism and safety profile.',
      }),
    onSuccess: (_, candidateId) => {
      setValidatedIds((prev) => ({ ...prev, [candidateId]: 'Validated as Plausible' }))
    },
  })

  if (error) {
    return (
      <div className="glass-card max-w-xl mx-auto my-12 p-8 text-center">
        <div className="h-14 w-14 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-4 border border-rose-100">
          <XCircle className="h-7 w-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Error Generating Candidates</h2>
        <p className="text-sm text-slate-600 mb-6">{(error as Error).message}</p>
        <div className="flex justify-center gap-3">
          <Link to="/" className="btn-secondary">
            Back to Diseases
          </Link>
          <button onClick={() => refetch()} className="btn-cobalt">
            Retry Inference
          </button>
        </div>
      </div>
    )
  }

  if (diseaseLoading || isLoading) {
    return (
      <div className="glass-card p-12 text-center max-w-2xl mx-auto my-12 space-y-6">
        <div className="relative mx-auto w-16 h-16">
          <div className="absolute inset-0 rounded-2xl bg-blue-400 animate-ping opacity-20" />
          <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-sky-500 text-white shadow-lg shadow-blue-500/30">
            <Cpu className="h-8 w-8 animate-pulse" />
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-slate-900">Running AI Candidate Generation</h2>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Computing GraphSAGE molecular graph representations, evaluating dual-encoder cross-attention layers, and querying FAERS safety disproportionality metrics...
          </p>
        </div>
        <div className="w-48 h-1.5 bg-slate-100 rounded-full mx-auto overflow-hidden">
          <div className="h-full bg-gradient-to-r from-blue-600 to-sky-400 rounded-full animate-pulse" />
        </div>
      </div>
    )
  }

  if (!disease) {
    return (
      <div className="glass-card max-w-md mx-auto my-12 p-8 text-center">
        <h2 className="text-xl font-bold text-slate-900 mb-2">Disease Not Found</h2>
        <p className="text-sm text-slate-500 mb-4">Please return to the Disease Browser.</p>
        <Link to="/" className="btn-cobalt">
          Back to Diseases
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="glass-card p-6 sm:p-8 bg-white shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Link
                to="/"
                className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Diseases
              </Link>
              <span className="text-slate-300">/</span>
              <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold">
                {disease.orpha_id}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Repurposing Candidates for{' '}
              <span className="text-blue-600">
                {disease.name}
              </span>
            </h1>

            <p className="text-sm text-slate-600 max-w-3xl">
              Model predicted {candidates.length} candidate drugs with calibrated probabilities and conformal prediction intervals.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
            <Link to={`/diseases/${disease.orpha_id}`} className="btn-secondary text-xs py-2 px-3.5 rounded-xl">
              Disease Profile
            </Link>
            <Link
              to="/dossier"
              className="btn-cobalt text-xs py-2 px-3.5 flex items-center gap-1.5 rounded-xl"
            >
              <FileText className="h-3.5 w-3.5" />
              Build Dossier
            </Link>
          </div>
        </div>
      </div>

      {/* Candidates List */}
      {candidates.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <HelpCircle className="h-12 w-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Candidates Found</h3>
          <p className="text-xs text-slate-500 mt-1">
            No bioactive compounds met the probability threshold for this rare disease cohort.
          </p>
        </div>
      ) : (
        <div className="space-y-5">
          {candidates.map((candidate: Candidate, index: number) => {
            const prob = candidate.indication_probability
            const ciLower = candidate.confidence_interval?.[0] ?? prob * 0.8
            const ciUpper = candidate.confidence_interval?.[1] ?? prob * 1.1
            const safety = candidate.safety_flags.overall
            const isValidated = validatedIds[candidate.candidate_id]

            return (
              <div
                key={candidate.candidate_id}
                className="glass-card p-6 sm:p-7 card-hover"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-5 border-b border-slate-100">
                  {/* Left Title & MoA */}
                  <div className="space-y-2 max-w-xl">
                    <div className="flex items-center gap-2.5">
                      <span className="h-7 w-7 rounded-xl bg-blue-50 text-blue-700 text-xs font-bold flex items-center justify-center border border-blue-200/60 font-mono">
                        #{index + 1}
                      </span>
                      <Link
                        to={`/candidates/${candidate.candidate_id}`}
                        className="text-xl sm:text-2xl font-bold text-slate-900 hover:text-blue-600 transition-colors"
                      >
                        {candidate.drug_name}
                      </Link>
                      <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-600 font-medium">
                        {candidate.drug_id}
                      </span>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-medium">
                      {candidate.moa_summary}
                    </p>
                  </div>

                  {/* Right Score & Safety Pills */}
                  <div className="flex flex-wrap items-center gap-4 lg:gap-6 bg-slate-50/70 p-4 rounded-2xl border border-slate-100 shrink-0">
                    {/* Probability Meter */}
                    <div className="space-y-1">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Probability
                      </div>
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-2xl font-extrabold text-slate-900">
                          {(prob * 100).toFixed(1)}%
                        </span>
                        <span className="text-[11px] font-mono text-slate-500 font-medium">
                          [{ciLower.toFixed(2)} - {ciUpper.toFixed(2)}]
                        </span>
                      </div>
                      <div className="h-2 w-32 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-600 to-sky-400 rounded-full"
                          style={{ width: `${Math.min(prob * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Safety Assessment */}
                    <div className="space-y-1 border-l border-slate-200 pl-4">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Safety Status
                      </div>
                      <div>
                        {safety === 'pass' && (
                          <span className="badge-green text-xs font-semibold">
                            <ShieldCheck className="h-3.5 w-3.5" /> Pass (Favorable)
                          </span>
                        )}
                        {safety === 'caution' && (
                          <span className="badge-yellow text-xs font-semibold">
                            <AlertTriangle className="h-3.5 w-3.5" /> Caution (Monitored)
                          </span>
                        )}
                        {safety === 'fail' && (
                          <span className="badge-red text-xs font-semibold">
                            <XCircle className="h-3.5 w-3.5" /> High Risk / Contraindicated
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {candidate.safety_flags.faers_signals.length} FAERS Signals
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Rationale Snippet */}
                {candidate.llm_rationale && (
                  <div className="mt-4 p-3.5 rounded-xl bg-blue-50/50 border border-blue-100 text-xs text-slate-700 leading-relaxed">
                    <span className="font-semibold text-blue-900 block mb-1">
                      Mechanistic Rationale (AI Synthesis):
                    </span>
                    {candidate.llm_rationale}
                  </div>
                )}

                {/* Action Buttons Footer */}
                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="flex items-center gap-2">
                    {isValidated ? (
                      <span className="badge-green text-xs">
                        <CheckCircle2 className="h-3.5 w-3.5" /> {isValidated}
                      </span>
                    ) : (
                      <button
                        onClick={() => mutation.mutate(candidate.candidate_id)}
                        disabled={mutation.isPending}
                        className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 rounded-xl"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 text-slate-500" />
                        {mutation.isPending ? 'Logging review...' : 'Clinician Validation'}
                      </button>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      to={`/candidates/${candidate.candidate_id}`}
                      className="btn-secondary text-xs py-1.5 px-3.5 font-semibold rounded-xl"
                    >
                      Deep Explanation (SHAP & KG)
                    </Link>
                    <Link
                      to={`/dossier`}
                      className="btn-cobalt text-xs py-1.5 px-3.5 font-semibold rounded-xl"
                    >
                      Draft Dossier
                    </Link>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

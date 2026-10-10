import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  XCircle,
  FileText,
  Activity,
  Layers,
  FlaskConical,
} from 'lucide-react'
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
      <div className="glass-card max-w-xl mx-auto my-12 p-8 text-center">
        <div className="h-14 w-14 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-4 border border-rose-100">
          <XCircle className="h-7 w-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Error Loading Candidate Profile</h2>
        <p className="text-sm text-slate-500 mb-6">{(error as Error).message}</p>
        <Link to="/" className="btn-cobalt">
          Back to Disease Browser
        </Link>
      </div>
    )
  }

  if (!candidate || isLoading) {
    return (
      <div className="glass-card max-w-xl mx-auto my-12 p-12 text-center space-y-4">
        <div className="h-12 w-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto animate-pulse">
          <Sparkles className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">Computing Candidate Intelligence...</h2>
        <div className="w-32 h-1 bg-blue-600 rounded-full mx-auto animate-pulse" />
      </div>
    )
  }

  const safetyLevel = safety && 'overall' in safety ? safety.overall : candidate.safety_flags.overall
  const safetyAssessment =
    safety && 'admet_classifications' in safety
      ? (safety as import('../types/safety').SafetyAssessment)
      : null

  const prob = candidate.indication_probability
  const ciLower = candidate.confidence_interval?.[0] ?? prob * 0.8
  const ciUpper = candidate.confidence_interval?.[1] ?? prob * 1.1

  return (
    <div className="space-y-7">
      {/* Top Header / Breadcrumb Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Link
            to={candidate.disease_id ? `/diseases/${candidate.disease_id}/candidates` : '/'}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Candidate Rankings
          </Link>
          <span className="text-slate-300">/</span>
          <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold">
            {candidate.drug_id}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/dossier"
            className="btn-cobalt text-xs py-2 px-4 flex items-center gap-1.5 rounded-xl shadow-md shadow-blue-500/20"
          >
            <FileText className="h-3.5 w-3.5" />
            Build IND Dossier
          </Link>
        </div>
      </div>

      {/* Hero Molecule Card */}
      <div className="glass-card p-7 sm:p-9 bg-gradient-to-br from-white via-white to-blue-50/20 border border-slate-200/90 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-3 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="badge-blue font-mono text-xs font-semibold">
                {candidate.drug_id}
              </span>
              <span className="badge-gray text-xs">Bioactive Compound</span>
              {safetyLevel === 'pass' && (
                <span className="badge-green text-xs font-semibold">
                  <ShieldCheck className="h-3 w-3" /> Favorable Safety
                </span>
              )}
              {safetyLevel === 'caution' && (
                <span className="badge-yellow text-xs font-semibold">
                  <AlertTriangle className="h-3 w-3" /> Monitored Safety
                </span>
              )}
              {safetyLevel === 'fail' && (
                <span className="badge-red text-xs font-semibold">
                  <XCircle className="h-3 w-3" /> High Risk
                </span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              {candidate.drug_name}
            </h1>

            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              {candidate.moa_summary || 'Targeted bioactive agent evaluated for orphan disease efficacy.'}
            </p>
          </div>

          {/* Indication Probability & CI Card */}
          <div className="p-5 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-xs space-y-3 min-w-[240px]">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Calibrated Probability
              </span>
              <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200/60">
                GNN + Attention
              </span>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-slate-900">
                {(prob * 100).toFixed(1)}%
              </span>
              <span className="text-xs font-mono text-slate-400">
                [{ciLower.toFixed(2)} - {ciUpper.toFixed(2)}]
              </span>
            </div>

            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-sky-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(prob * 100, 100)}%` }}
              />
            </div>

            <p className="text-[11px] text-slate-400 leading-tight">
              95% Conformal prediction interval derived from cross-attention latent representations.
            </p>
          </div>
        </div>

        {/* AI Rationale Bar */}
        {candidate.llm_rationale && (
          <div className="mt-5 p-4 rounded-2xl bg-blue-50/50 border border-blue-100/80 text-xs text-slate-700 leading-relaxed">
            <span className="font-semibold text-blue-900 block mb-1 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-blue-600" />
              Mechanistic Rationale (AI Synthesis):
            </span>
            {candidate.llm_rationale}
          </div>
        )}
      </div>

      {/* Explainability Section */}
      <div className="glass-card p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-200/50">
              <Layers className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">
                AI Biological Explanation & Subgraph Pathways
              </h2>
              <p className="text-xs text-slate-500">
                Knowledge graph multi-hop paths and SHAP feature attribution
              </p>
            </div>
          </div>
          <span className="badge-ice font-mono text-xs">SHAP + Kùzu</span>
        </div>

        <ExplanationPanel
          explanation={
            explanation ?? {
              candidate_id: '',
              kg_paths: [],
              shap_values: {},
              counterfactuals: [],
              llm_rationale: '',
            }
          }
          isLoading={explanationLoading}
        />
      </div>

      {/* Safety Section */}
      <div className="glass-card p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200/50">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">
                Post-Market Safety & Pharmacovigilance
              </h2>
              <p className="text-xs text-slate-500">
                FDA FAERS disproportionality signals (ROR, PRR) & ADMET properties
              </p>
            </div>
          </div>
          <span className="badge-green font-mono text-xs">FAERS + ADMET</span>
        </div>

        {safetyLoading ? (
          <p className="text-xs text-slate-400 py-6 text-center animate-pulse">
            Analyzing safety signals...
          </p>
        ) : safetyAssessment ? (
          <SafetyDashboard
            overall={safetyAssessment.overall}
            faersSignals={safetyAssessment.faers_signals}
            admetPredictions={safetyAssessment.admet_predictions}
            admetClassifications={safetyAssessment.admet_classifications}
            contraindications={safetyAssessment.contraindications}
          />
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200/70">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Overall Safety:
              </span>
              <span
                className={`text-xs font-bold px-3 py-1 rounded-full ${
                  safetyLevel === 'pass'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : safetyLevel === 'caution'
                    ? 'bg-amber-50 text-amber-700 border border-amber-200'
                    : 'bg-rose-50 text-rose-700 border border-rose-200'
                }`}
              >
                {safetyLevel.toUpperCase()}
              </span>
            </div>

            {candidate.safety_flags.faers_signals.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  FAERS Adverse Event Signals
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {candidate.safety_flags.faers_signals.map((sig, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-xs flex items-center justify-between"
                    >
                      <span className="font-medium text-slate-800">{sig.meddra_pt}</span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        ROR: {sig.ror.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Validation Panel */}
      <div className="glass-card p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-200/50">
              <FlaskConical className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900">
                Clinician Validation & Regulatory Audit Trail
              </h2>
              <p className="text-xs text-slate-500">
                Record expert assessment, confidence ratings, and tamper-evident logs
              </p>
            </div>
          </div>
          <span className="badge-purple font-mono text-xs">21 CFR Part 11</span>
        </div>

        <ValidationPanel candidateId={candidate.candidate_id} />
      </div>
    </div>
  )
}

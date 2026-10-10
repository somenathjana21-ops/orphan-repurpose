import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { candidatesApi, validationApi } from '../services/api'
import { CheckCircle2, Sliders, ShieldCheck } from 'lucide-react'

interface ValidationPanelProps {
  candidateId: string
}

type Assessment = 'plausible' | 'needs_data' | 'unlikely'

const ASSESSMENT_LABELS: Record<Assessment, { label: string; color: string }> = {
  plausible: { label: 'Plausible', color: 'bg-emerald-50 text-emerald-800 border-emerald-300' },
  needs_data: { label: 'Needs More Data', color: 'bg-amber-50 text-amber-800 border-amber-300' },
  unlikely: { label: 'Unlikely', color: 'bg-rose-50 text-rose-800 border-rose-300' },
}

export function ValidationPanel({ candidateId }: ValidationPanelProps) {
  const queryClient = useQueryClient()
  const [validator, setValidator] = useState('')
  const [assessment, setAssessment] = useState<Assessment>('plausible')
  const [rationale, setRationale] = useState('')
  const [efficacy, setEfficacy] = useState(5)
  const [safety, setSafety] = useState(5)
  const [feasibility, setFeasibility] = useState(5)
  const [notes, setNotes] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'validate' | 'assess' | 'audit'>('validate')

  const validateMutation = useMutation({
    mutationFn: () =>
      candidatesApi.validate(candidateId, {
        validator: validator || 'anonymous',
        assessment,
        rationale,
      }),
    onSuccess: (data) => {
      setSessionId(data.session_id)
      queryClient.invalidateQueries({ queryKey: ['audit-trail', data.session_id] })
    },
  })

  const assessMutation = useMutation({
    mutationFn: () =>
      candidatesApi.selfAssess(candidateId, {
        efficacy,
        safety,
        feasibility,
        notes,
      }),
    onSuccess: (data) => {
      setSessionId(data.session_id)
      queryClient.invalidateQueries({ queryKey: ['audit-trail', data.session_id] })
    },
  })

  const { data: auditTrail, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-trail', sessionId],
    queryFn: () => validationApi.getAuditTrail(sessionId!),
    enabled: !!sessionId,
  })

  return (
    <div className="space-y-5">
      {/* Modern Segmented Pill Tabs */}
      <div className="flex p-1 bg-slate-100 rounded-2xl w-fit">
        {(['validate', 'assess', 'audit'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all ${
              activeTab === tab
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            {tab === 'validate'
              ? 'Expert Validation'
              : tab === 'assess'
              ? 'Clinician Scoring'
              : 'Audit Trail'}
          </button>
        ))}
      </div>

      {/* Expert Validation Tab */}
      {activeTab === 'validate' && (
        <div className="space-y-4 max-w-xl">
          <div>
            <label className="label">Validator Name / Affiliation</label>
            <input
              type="text"
              value={validator}
              onChange={(e) => setValidator(e.target.value)}
              placeholder="Dr. S. Chen (Principal Investigator)"
              className="input"
            />
          </div>
          <div>
            <label className="label">Plausibility Assessment</label>
            <div className="flex flex-wrap gap-2">
              {(Object.keys(ASSESSMENT_LABELS) as Assessment[]).map((a) => (
                <button
                  key={a}
                  onClick={() => setAssessment(a)}
                  className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl border transition-all ${
                    assessment === a
                      ? ASSESSMENT_LABELS[a].color
                      : 'bg-white text-slate-600 border-slate-200/80 hover:bg-slate-50'
                  }`}
                >
                  {ASSESSMENT_LABELS[a].label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Biological & Clinical Rationale</label>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Explain mechanistic plausibility, phenotypic overlap, or safety considerations..."
              rows={3}
              className="input"
            />
          </div>
          <button
            onClick={() => validateMutation.mutate()}
            disabled={validateMutation.isPending}
            className="btn-cobalt text-xs py-2.5 px-5 rounded-xl font-semibold"
          >
            {validateMutation.isPending ? 'Logging review...' : 'Submit Expert Validation'}
          </button>
          {validateMutation.isSuccess && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200/70 rounded-2xl flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <p className="text-xs text-emerald-900">
                Validation recorded securely. Session ID:{' '}
                <code className="font-mono font-bold">{validateMutation.data.session_id.slice(0, 8)}...</code>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Self-Assessment Scoring Tab */}
      {activeTab === 'assess' && (
        <div className="space-y-4 max-w-xl">
          {[
            { label: 'Efficacy Probability', value: efficacy, set: setEfficacy },
            { label: 'Safety & Tolerability Profile', value: safety, set: setSafety },
            { label: 'Translational Feasibility', value: feasibility, set: setFeasibility },
          ].map(({ label, value, set }) => (
            <div key={label} className="p-3.5 bg-slate-50/70 border border-slate-200/60 rounded-2xl space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Sliders className="h-3 w-3 text-blue-600" />
                  {label}
                </label>
                <span className="text-xs font-mono font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">
                  {value}/10
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={value}
                onChange={(e) => set(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>
          ))}
          <div>
            <label className="label">Evaluation Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional observational notes..."
              rows={2}
              className="input"
            />
          </div>
          <button
            onClick={() => assessMutation.mutate()}
            disabled={assessMutation.isPending}
            className="btn-cobalt text-xs py-2.5 px-5 rounded-xl font-semibold"
          >
            {assessMutation.isPending ? 'Logging score...' : 'Submit Clinician Scoring'}
          </button>
          {assessMutation.isSuccess && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200/70 rounded-2xl flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <p className="text-xs text-emerald-900">
                Score recorded. Session ID:{' '}
                <code className="font-mono font-bold">{assessMutation.data.session_id.slice(0, 8)}...</code>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Audit Trail Tab */}
      {activeTab === 'audit' && (
        <div className="space-y-3">
          {!sessionId ? (
            <p className="text-xs text-slate-500 p-4 bg-slate-50 rounded-2xl border border-slate-200/60">
              Submit a validation or scoring entry to review the cryptographically hashed audit trail.
            </p>
          ) : auditLoading ? (
            <p className="text-xs text-slate-400">Loading audit trail...</p>
          ) : auditTrail ? (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-2xl border border-slate-200/70">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-purple-600" />
                  <span className="text-xs font-bold text-slate-900">
                    Audit Log · {auditTrail.entries.length} Entries
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  ID: {auditTrail.session_id.slice(0, 8)}...
                </span>
              </div>
              {auditTrail.entries.map((entry, i) => (
                <div key={i} className="p-3.5 bg-white border border-slate-200/80 rounded-2xl shadow-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        entry.type === 'validation'
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'bg-purple-50 text-purple-700 border border-purple-200'
                      }`}
                    >
                      {entry.type}
                    </span>
                  </div>
                  <p className="text-xs text-slate-800">
                    <strong>{entry.user}</strong>: {JSON.stringify(entry.data)}
                  </p>
                  <p className="text-[10px] font-mono text-slate-400 truncate">
                    Hash: {entry.hash.slice(0, 24)}...
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No audit trail found.</p>
          )}
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { candidatesApi, validationApi } from '../services/api'

interface ValidationPanelProps {
  candidateId: string
}

type Assessment = 'plausible' | 'needs_data' | 'unlikely'

const ASSESSMENT_LABELS: Record<Assessment, { label: string; color: string }> = {
  plausible: { label: 'Plausible', color: 'bg-green-100 text-green-800 border-green-300' },
  needs_data: { label: 'Needs More Data', color: 'bg-amber-100 text-amber-800 border-amber-300' },
  unlikely: { label: 'Unlikely', color: 'bg-red-100 text-red-800 border-red-300' },
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
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {(['validate', 'assess', 'audit'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'validate' ? 'Expert Validation' : tab === 'assess' ? 'Self-Assessment' : 'Audit Trail'}
          </button>
        ))}
      </div>

      {/* Expert Validation */}
      {activeTab === 'validate' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Validator Name</label>
            <input
              type="text"
              value={validator}
              onChange={(e) => setValidator(e.target.value)}
              placeholder="Dr. Smith"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Assessment</label>
            <div className="flex gap-2">
              {(Object.keys(ASSESSMENT_LABELS) as Assessment[]).map((a) => (
                <button
                  key={a}
                  onClick={() => setAssessment(a)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
                    assessment === a
                      ? ASSESSMENT_LABELS[a].color
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {ASSESSMENT_LABELS[a].label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rationale</label>
            <textarea
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Explain your assessment..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            onClick={() => validateMutation.mutate()}
            disabled={validateMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {validateMutation.isPending ? 'Submitting...' : 'Submit Validation'}
          </button>
          {validateMutation.isSuccess && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                Validation recorded. Session ID: <code className="text-xs">{validateMutation.data.session_id.slice(0, 8)}...</code>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Self-Assessment */}
      {activeTab === 'assess' && (
        <div className="space-y-4">
          {[
            { label: 'Efficacy', value: efficacy, set: setEfficacy },
            { label: 'Safety', value: safety, set: setSafety },
            { label: 'Feasibility', value: feasibility, set: setFeasibility },
          ].map(({ label, value, set }) => (
            <div key={label}>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-gray-700">{label}</label>
                <span className="text-sm font-mono text-gray-500">{value}/10</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={value}
                onChange={(e) => set(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional observations..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            onClick={() => assessMutation.mutate()}
            disabled={assessMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {assessMutation.isPending ? 'Submitting...' : 'Submit Self-Assessment'}
          </button>
          {assessMutation.isSuccess && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                Self-assessment recorded. Session ID: <code className="text-xs">{assessMutation.data.session_id.slice(0, 8)}...</code>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Audit Trail */}
      {activeTab === 'audit' && (
        <div className="space-y-3">
          {!sessionId ? (
            <p className="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg">
              Submit a validation or self-assessment to see the audit trail.
            </p>
          ) : auditLoading ? (
            <p className="text-sm text-gray-500">Loading audit trail...</p>
          ) : auditTrail ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-800">Audit Trail</p>
                  <p className="text-xs text-gray-500">{auditTrail.entries.length} entries</p>
                </div>
                <span className="text-xs font-mono text-gray-400">{auditTrail.session_id.slice(0, 8)}...</span>
              </div>
              {auditTrail.entries.map((entry, i) => (
                <div key={i} className="p-3 bg-white border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        entry.type === 'validation'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}
                    >
                      {entry.type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">
                    <strong>{entry.user}</strong>: {JSON.stringify(entry.data)}
                  </p>
                  <p className="text-xs font-mono text-gray-400 mt-1 truncate">
                    Hash: {entry.hash.slice(0, 16)}...
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No audit trail found.</p>
          )}
        </div>
      )}
    </div>
  )
}

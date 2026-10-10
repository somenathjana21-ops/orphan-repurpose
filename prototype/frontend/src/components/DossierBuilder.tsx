import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  FileText,
  Download,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Zap,
} from 'lucide-react'
import { dossierApi } from '../services/api'
import type { DossierResponse } from '../types'

export function DossierBuilder() {
  const [diseaseId, setDiseaseId] = useState('ORPHA:635')
  const [candidateIds, setCandidateIds] = useState<string[]>(['drugcentral:1001'])
  const [candidateInput, setCandidateInput] = useState('')
  const [includeSections, setIncludeSections] = useState<string[]>([
    'background',
    'drug_profile',
    'mechanistic_rationale',
    'preclinical_plan',
    'regulatory_strategy',
    'credibility_map',
  ])
  const [isGenerating, setIsGenerating] = useState(false)
  const [dossier, setDossier] = useState<DossierResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const allSections = [
    { id: 'background', label: '1. Rare Disease Background & Medical Unmet Need' },
    { id: 'drug_profile', label: '2. Drug Characterization & Bioactivity' },
    { id: 'mechanistic_rationale', label: '3. Biological Target & Mechanistic Rationale' },
    { id: 'preclinical_plan', label: '4. Suggested Preclinical Validation Plan' },
    { id: 'regulatory_strategy', label: '5. Orphan Drug Designation Strategy (FDA/EMA)' },
    { id: 'credibility_map', label: '6. AI Credibility & Evidence Trails' },
  ]

  const mutation = useMutation({
    mutationFn: (data: { disease_id: string; candidate_ids: string[]; include_sections: string[] }) =>
      dossierApi.generate(data),
    onSuccess: (data) => {
      setDossier(data)
      setIsGenerating(false)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || err.message || 'Generation failed')
      setIsGenerating(false)
    },
  })

  const handleGenerate = () => {
    if (!diseaseId || candidateIds.length === 0) {
      setError('Please provide an ORPHA disease ID and at least one drug candidate ID.')
      return
    }
    setIsGenerating(true)
    setError(null)
    mutation.mutate({
      disease_id: diseaseId,
      candidate_ids: candidateIds,
      include_sections: includeSections,
    })
  }

  const handleAddCandidate = () => {
    if (candidateInput.trim() && !candidateIds.includes(candidateInput.trim())) {
      setCandidateIds([...candidateIds, candidateInput.trim()])
      setCandidateInput('')
    }
  }

  const loadNpcPreset = () => {
    setDiseaseId('ORPHA:635')
    setCandidateIds(['drugcentral:1001', 'drugcentral:1002'])
    setError(null)
  }

  return (
    <div className="space-y-7">
      {/* Header Banner */}
      <div className="glass-card p-7 sm:p-9 bg-gradient-to-br from-white via-white to-blue-50/20 border border-slate-200/90 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/60 shadow-2xs">
              <FileText className="h-3.5 w-3.5 text-blue-600" />
              <span>Regulatory Document Generator</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Orphan Designation Dossier Builder
            </h1>
            <p className="text-slate-600 text-sm leading-relaxed">
              Compile evidence-based regulatory dossiers conforming to FDA/EMA Orphan Drug Designation requirements, backed by mechanistic GNN predictions, safety alerts, and citation trails.
            </p>
          </div>

          <button
            onClick={loadNpcPreset}
            className="btn-secondary text-xs py-2 px-3.5 flex items-center gap-1.5 shrink-0 rounded-xl"
          >
            <Zap className="h-3.5 w-3.5 text-amber-500" />
            <span>Pre-fill NPC Demo</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200/80 rounded-2xl text-rose-800 text-xs flex items-start gap-3">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <strong>Error generating dossier:</strong> {error}
          </div>
        </div>
      )}

      {/* Builder Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1 & 2 Inputs */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 sm:p-7 space-y-5">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 uppercase tracking-wider">
              <span className="h-6 w-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
                1
              </span>
              Target Disease
            </h2>

            <div>
              <label className="label">ORPHA Disease Identifier</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={diseaseId}
                  onChange={(e) => setDiseaseId(e.target.value.trim())}
                  placeholder="e.g. ORPHA:635"
                  className="input font-mono max-w-sm"
                />
              </div>
              <p className="text-xs text-slate-400 mt-1.5">
                Example: <strong className="text-slate-600">ORPHA:635</strong> (Niemann-Pick Type C), <strong className="text-slate-600">ORPHA:793</strong> (Cystic Fibrosis)
              </p>
            </div>
          </div>

          <div className="glass-card p-6 sm:p-7 space-y-5">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 uppercase tracking-wider">
              <span className="h-6 w-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
                2
              </span>
              Repurposing Candidates to Include
            </h2>

            <div className="space-y-3">
              <label className="label">Drug Identifiers</label>
              <div className="flex gap-2 max-w-md">
                <input
                  type="text"
                  value={candidateInput}
                  onChange={(e) => setCandidateInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddCandidate()
                    }
                  }}
                  placeholder="e.g. drugcentral:1001"
                  className="input font-mono"
                />
                <button
                  type="button"
                  onClick={handleAddCandidate}
                  className="btn-secondary text-xs px-3.5 rounded-xl"
                >
                  Add
                </button>
              </div>

              {/* Tag Pills */}
              <div className="flex flex-wrap gap-2 pt-1">
                {candidateIds.map((id, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-blue-50 text-blue-700 border border-blue-200/80 font-mono text-xs font-semibold"
                  >
                    <span>{id}</span>
                    <button
                      type="button"
                      onClick={() => setCandidateIds(candidateIds.filter((_, i) => i !== index))}
                      className="text-blue-400 hover:text-blue-900 transition-colors cursor-pointer text-sm font-bold"
                      title="Remove"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: Sections checklist & Generate CTA */}
        <div className="space-y-6">
          <div className="glass-card p-6 sm:p-7 space-y-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 uppercase tracking-wider">
              <span className="h-6 w-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center">
                3
              </span>
              Dossier Sections
            </h2>

            <div className="space-y-2">
              {allSections.map((sec) => (
                <label
                  key={sec.id}
                  className="flex items-start gap-2.5 p-2 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer text-xs text-slate-700"
                >
                  <input
                    type="checkbox"
                    checked={includeSections.includes(sec.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setIncludeSections([...includeSections, sec.id])
                      } else {
                        setIncludeSections(includeSections.filter((s) => s !== sec.id))
                      }
                    }}
                    className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="font-medium leading-tight">{sec.label}</span>
                </label>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setIncludeSections(allSections.map((s) => s.id))}
                className="text-xs text-blue-600 font-semibold hover:underline"
              >
                Select All
              </button>
              <button
                type="button"
                onClick={() => setIncludeSections([])}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                Clear All
              </button>
            </div>

            <div className="pt-2">
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !diseaseId || candidateIds.length === 0}
                className="btn-cobalt w-full py-3 text-xs font-semibold flex items-center justify-center gap-2 rounded-xl shadow-md shadow-blue-500/25"
              >
                <Sparkles className="h-4 w-4" />
                <span>{isGenerating ? 'Compiling Dossier...' : 'Generate Regulatory Dossier'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Generated Dossier Preview Output */}
      {dossier && (
        <div className="glass-card p-7 space-y-6 border-blue-200 bg-gradient-to-br from-white to-slate-50 shadow-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="badge-green text-xs font-semibold">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Dossier Compiled Successfully
                </span>
                <span className="font-mono text-xs text-slate-400">
                  ID: {dossier.audit_trail_id?.slice(0, 12)}
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-900">
                Orphan Drug Designation Application Dossier
              </h3>
            </div>

            {/* Download Buttons */}
            <div className="flex items-center gap-2.5">
              {dossier.pdf_base64 && (
                <button
                  onClick={() => {
                    const binary = atob(dossier.pdf_base64)
                    const bytes = new Uint8Array(binary.length)
                    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
                    const blob = new Blob([bytes], { type: 'application/pdf' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `orphan_dossier_${diseaseId.replace(':', '_')}.pdf`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="btn-cobalt text-xs py-2 px-3.5 flex items-center gap-1.5 font-semibold rounded-xl"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download PDF</span>
                </button>
              )}

              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(dossier.dossier_json, null, 2)], {
                    type: 'application/json',
                  })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `orphan_dossier_${diseaseId.replace(':', '_')}.json`
                  a.click()
                  URL.revokeObjectURL(url)
                }}
                className="btn-secondary text-xs py-2 px-3.5 flex items-center gap-1.5 font-semibold rounded-xl"
              >
                <Download className="h-3.5 w-3.5 text-slate-500" />
                <span>Export JSON</span>
              </button>
            </div>
          </div>

          {!dossier.pdf_base64 && (
            <p role="status" className="text-sm text-amber-800">
              PDF export is unavailable. You can still export this dossier as JSON.
            </p>
          )}

          {/* Dossier Structured Content Preview */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 space-y-4 max-h-96 overflow-y-auto scrollbar-thin font-mono text-xs text-slate-700">
            <div className="font-sans">
              <h4 className="text-sm font-bold text-slate-900 mb-1">
                Executive Scientific Summary
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed font-sans mb-3">
                {dossier.dossier_json?.sections?.background ||
                  'Scientific justification for orphan drug designation based on biological plausibility, unmet need, and drug mechanism.'}
              </p>
            </div>
            <pre className="bg-slate-50 p-3.5 rounded-xl border border-slate-100 overflow-x-auto text-[11px] leading-relaxed text-slate-600">
              {JSON.stringify(dossier.dossier_json, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

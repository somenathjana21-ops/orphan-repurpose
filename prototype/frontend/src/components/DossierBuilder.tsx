import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { dossierApi } from '../services/api'
import type { DossierResponse } from '../types'

export function DossierBuilder() {
  const [diseaseId, setDiseaseId] = useState('')
  const [candidateIds, setCandidateIds] = useState<string[]>([])
  const [includeSections, setIncludeSections] = useState<string[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [dossier, setDossier] = useState<DossierResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const allSections = [
    'background',
    'drug_profile',
    'mechanistic_rationale',
    'preclinical_plan',
    'regulatory_strategy',
    'credibility_map'
  ]

  const mutation = useMutation({
    mutationFn: (data: { disease_id: string; candidate_ids: string[]; include_sections: string[] }) =>
      dossierApi.generate(data),
    onSuccess: (data) => {
      setDossier(data)
      setIsGenerating(false)
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || error.message)
      setIsGenerating(false)
    },
  })

  const handleGenerate = () => {
    if (!diseaseId || candidateIds.length === 0) {
      setError('Please provide a disease ID and at least one candidate ID')
      return
    }
    setIsGenerating(true)
    setError(null)
    mutation.mutate({ disease_id: diseaseId, candidate_ids: candidateIds, include_sections: includeSections })
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Orphan Designation Dossier Generator</h1>
      <p className="text-gray-600 mb-6">
        Generate a draft orphan drug designation dossier for regulatory submission.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-800 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Disease Information</h2>
          <div className="flex flex-col">
            <label className="mb-2 text-gray-700 font-medium">ORPHA ID (e.g., ORPHA:635 for Niemann-Pick Type C)</label>
            <input
              type="text"
              value={diseaseId}
              onChange={(e) => setDiseaseId(e.target.value.trim())}
              placeholder="Enter ORPHA ID"
              className="input w-64"
            />
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Candidate Drugs</h2>
          <div className="flex flex-col">
            <label className="mb-2 text-gray-700 font-medium">Candidate IDs (comma-separated)</label>
            <input
              type="text"
              value={candidateIds.join(', ')}
              onChange={(e) => {
                const ids = e.target.value
                  .split(',')
                  .map(id => id.trim())
                  .filter(id => id.length > 0)
                setCandidateIds(ids)
              }}
              placeholder="e.g., CHEMBL123, CHEMBL456"
              className="input w-64"
            />
            {candidateIds.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {candidateIds.map((id, index) => (
                  <span key={index} className="bg-blue-50 px-3 py-1 text-xs font-medium rounded">
                    {id}
                    <button
                      onClick={() => {
                        const newIds = [...candidateIds]
                        newIds.splice(index, 1)
                        setCandidateIds(newIds)
                      }}
                      className="ml-2 text-xs text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Sections to Include</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {allSections.map((section) => (
              <div key={section} className="flex items-center">
                <input
                  type="checkbox"
                  id={`section-${section}`}
                  checked={includeSections.includes(section)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setIncludeSections([...includeSections, section])
                    } else {
                      setIncludeSections(includeSections.filter(s => s !== section))
                    }
                  }}
                  className="h-4 w-4 text-blue-600"
                />
                <label className="ml-2 text-gray-700" htmlFor={`section-${section}`}>
                  {section.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </label>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center">
            <button
              onClick={() => setIncludeSections([...allSections])}
              className="btn-secondary text-sm mr-2"
            >
              Select All
            </button>
            <button
              onClick={() => setIncludeSections([])}
              className="btn-secondary text-sm"
            >
              Select None
            </button>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !diseaseId || candidateIds.length === 0}
          className="btn-primary px-6 py-2"
        >
          {isGenerating ? 'Generating Dossier...' : 'Generate Dossier'}
        </button>
      </div>

      {dossier && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Generated Dossier</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Dossier Metadata</h3>
              <p className="text-gray-700">
                Generated at: {new Date(dossier.dossier_json.generated_at).toLocaleString()}
              </p>
              <p className="text-gray-700">
                Audit Trail ID: {dossier.audit_trail_id}
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Download Options</h3>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    const binary = atob(dossier.pdf_base64)
                    const bytes = new Uint8Array(binary.length)
                    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
                    const blob = new Blob([bytes], { type: 'application/pdf' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `dossier_${dossier.audit_trail_id.slice(0, 8)}.pdf`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="btn-secondary"
                >
                  Download PDF
                </button>
                <button
                  onClick={() => {
                    const blob = new Blob([JSON.stringify(dossier.dossier_json, null, 2)], { type: 'application/json' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `dossier_${dossier.audit_trail_id.slice(0, 8)}.json`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  className="btn-secondary"
                >
                  Download JSON
                </button>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Disclaimer</h3>
              <p className="text-gray-600 italic">
                {dossier.dossier_json.disclaimer}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
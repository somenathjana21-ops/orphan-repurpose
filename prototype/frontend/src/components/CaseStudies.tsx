import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { candidatesApi } from '../services/api'

const CASE_STUDIES = [
  {
    id: 'npc',
    disease: 'Niemann-Pick Disease Type C',
    orphaId: 'ORPHA:635',
    prevalence: '0.5 per 100,000 (ultra-rare)',
    genes: 'NPC1, NPC2',
    topDrug: 'Miglustat',
    probability: 0.85,
    rationale: 'Inhibits glucosylceramide synthase, reducing glycosphingolipid accumulation in lysosomes.',
    safety: 'Approved drug with known safety profile. Caution: GI side effects.',
    status: 'Phase 2/3 (repurposing)',
  },
  {
    id: 'cf',
    disease: 'Cystic Fibrosis',
    orphaId: 'ORPHA:793',
    prevalence: '3.5 per 100,000',
    genes: 'CFTR',
    topDrug: 'Ivacaftor',
    probability: 0.90,
    rationale: 'CFTR potentiator that increases channel open probability, improving chloride transport.',
    safety: 'Approved for specific CFTR mutations. Well-tolerated.',
    status: 'Approved (subset)',
  },
  {
    id: 'hd',
    disease: 'Huntington Disease',
    orphaId: 'ORPHA:98065',
    prevalence: '5.0 per 100,000',
    genes: 'HTT',
    topDrug: 'Tetrabenazine',
    probability: 0.65,
    rationale: 'VMAT2 inhibitor reducing chorea symptoms. Repurposing for neuroprotection.',
    safety: 'Black box warning: depression/suicidality. Requires monitoring.',
    status: 'Approved (symptomatic)',
  },
]

export function CaseStudies() {
  const { data: npcCandidates } = useQuery({
    queryKey: ['candidates', 'ORPHA:635'],
    queryFn: () => candidatesApi.generate('ORPHA:635'),
    staleTime: 30000,
  })

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Case Studies</h1>
          <p className="text-gray-600 mt-1">
            Real-world validation of AI-generated repurposing hypotheses for rare diseases.
          </p>
        </div>
        <Link to="/dossier" className="btn-primary">Generate Dossier</Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {CASE_STUDIES.map((study) => (
          <div key={study.id} className="card hover:shadow-lg transition-shadow">
            <div className="card-body">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{study.disease}</h3>
                  <p className="text-xs text-gray-500 font-mono">{study.orphaId}</p>
                </div>
                <span className="badge-blue text-xs">{study.status}</span>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Prevalence</span>
                  <span className="text-gray-900">{study.prevalence}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Genes</span>
                  <span className="text-gray-900">{study.genes}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Top Drug</span>
                  <span className="font-medium text-blue-600">{study.topDrug}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 text-sm">Probability</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-600 rounded-full"
                      style={{ width: `${study.probability * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono">{study.probability.toFixed(2)}</span>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Rationale: </span>
                  <span className="text-gray-600">{study.rationale}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Safety: </span>
                  <span className="text-gray-600">{study.safety}</span>
                </div>
              </div>

              {study.id === 'npc' && npcCandidates && (
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-2">Live Model Output</p>
                  <div className="space-y-1">
                    {npcCandidates.candidates.slice(0, 3).map((c) => (
                      <div key={c.candidate_id} className="flex justify-between text-xs">
                        <span className="text-gray-700">{c.drug_name}</span>
                        <span className="font-mono text-gray-500">{c.indication_probability.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Methodology */}
      <div className="card">
        <div className="card-body">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Methodology</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600">
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Data Sources</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>ChEMBL: 14,578 drug-disease indications</li>
                <li>DrugCentral: FDA-approved drugs with safety data</li>
                <li>Orphanet: Rare disease classification</li>
                <li>Reactome: Biological pathways</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800 mb-2">Model</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>SimpleIndicationModel_MLP (Morgan FP + KG embeddings)</li>
                <li>KG: 3,532 nodes, 15,504 edges</li>
                <li>AUPRC 0.817, Recall@20 91.7%</li>
                <li>Conformal prediction intervals (90% coverage)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

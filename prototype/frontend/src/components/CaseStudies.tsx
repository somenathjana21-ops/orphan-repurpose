import { Link } from 'react-router-dom'
import {
  BookmarkCheck,
  ArrowRight,
  ShieldCheck,
  FileText,
  Sparkles,
} from 'lucide-react'

const CASE_STUDIES = [
  {
    id: 'npc',
    disease: 'Niemann-Pick Disease Type C',
    orphaId: 'ORPHA:635',
    prevalence: '0.5 per 100,000 (Ultra-rare)',
    genes: 'NPC1, NPC2',
    topDrug: 'Miglustat',
    drugId: 'drugcentral:1001',
    probability: 0.85,
    rationale:
      'Inhibits glucosylceramide synthase, reducing harmful glycosphingolipid accumulation in lysosomes caused by impaired intracellular cholesterol transport.',
    safety: 'Approved drug with established safety profile. GI monitoring recommended (mild diarrhea signal in FAERS).',
    status: 'Phase 2/3 Benchmark (Repurposed)',
    statusBadge: 'badge-green',
  },
  {
    id: 'cf',
    disease: 'Cystic Fibrosis',
    orphaId: 'ORPHA:793',
    prevalence: '3.5 per 100,000 (Rare)',
    genes: 'CFTR',
    topDrug: 'Ivacaftor',
    drugId: 'drugcentral:1003',
    probability: 0.90,
    rationale:
      'CFTR potentiator increasing channel open probability to restore chloride and fluid transport across epithelial tissues in lung and digestive system.',
    safety: 'Approved for specific CFTR gating mutations. Favorable safety profile with regular liver enzyme monitoring.',
    status: 'FDA/EMA Approved (Subset)',
    statusBadge: 'badge-blue',
  },
  {
    id: 'hd',
    disease: 'Huntington Disease',
    orphaId: 'ORPHA:98065',
    prevalence: '5.0 per 100,000 (Rare)',
    genes: 'HTT',
    topDrug: 'Tetrabenazine',
    drugId: 'drugcentral:1004',
    probability: 0.65,
    rationale:
      'Reversible vesicular monoamine transporter 2 (VMAT2) inhibitor reducing hyperkinetic chorea movements; investigated for broader neuroprotective mechanisms.',
    safety: 'Requires neuropsychiatric monitoring (depression/suicidality warning on label). Clinical supervision required.',
    status: 'Approved (Symptomatic Relief)',
    statusBadge: 'badge-purple',
  },
]

export function CaseStudies() {
  return (
    <div className="space-y-7">
      {/* Header Banner */}
      <div className="glass-card p-7 sm:p-9 bg-gradient-to-br from-white via-white to-blue-50/20 border border-slate-200/90 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/60 shadow-2xs">
              <BookmarkCheck className="h-3.5 w-3.5 text-blue-600" />
              <span>Clinical Benchmark Validation Studies</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Rare Disease Case Studies
            </h1>
            <p className="text-slate-600 text-sm leading-relaxed">
              Real-world validation demonstrating how the platform recovers approved and investigated repositioned therapies using biological knowledge graphs and cross-attention embeddings.
            </p>
          </div>

          <Link
            to="/dossier"
            className="btn-cobalt text-xs py-2.5 px-4 shrink-0 flex items-center gap-2 rounded-xl shadow-md shadow-blue-500/20"
          >
            <FileText className="h-4 w-4" />
            <span>Generate Regulatory Dossier</span>
          </Link>
        </div>
      </div>

      {/* Case Study Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {CASE_STUDIES.map((study) => (
          <div
            key={study.id}
            className="glass-card p-6 sm:p-7 flex flex-col justify-between card-hover group"
          >
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-100">
                <div>
                  <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-600 font-semibold block w-fit mb-1.5">
                    {study.orphaId}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors leading-snug">
                    {study.disease}
                  </h3>
                </div>
                <span className={`text-[11px] font-semibold ${study.statusBadge}`}>
                  {study.status}
                </span>
              </div>

              {/* Repurposed Candidate Callout */}
              <div className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Lead Candidate
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-slate-900 font-mono">
                      {(study.probability * 100).toFixed(0)}% Prob
                    </span>
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  </div>
                </div>
                <div className="text-base font-bold text-blue-600 flex items-center gap-2">
                  <span>{study.topDrug}</span>
                  <span className="font-mono text-[11px] text-slate-400 font-normal">
                    ({study.drugId})
                  </span>
                </div>
              </div>

              {/* Etiology Info */}
              <div className="space-y-2 text-xs text-slate-600">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-400">Prevalence</span>
                  <span className="font-medium text-slate-800">{study.prevalence}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-400">Driver Genes</span>
                  <span className="font-mono font-bold text-purple-700">{study.genes}</span>
                </div>
              </div>

              {/* Rationale Quote */}
              <div className="text-xs text-slate-700 bg-blue-50/40 p-3.5 rounded-xl border border-blue-100/60 leading-relaxed">
                <strong className="text-blue-900 block mb-1 flex items-center gap-1">
                  <Sparkles className="h-3 w-3 text-blue-600" />
                  Biological Mechanism:
                </strong>
                {study.rationale}
              </div>

              {/* Safety note */}
              <div className="text-[11px] text-slate-500 flex items-start gap-1.5 pt-1">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                <span>{study.safety}</span>
              </div>
            </div>

            {/* Card Action */}
            <div className="pt-6 mt-4 border-t border-slate-100">
              <Link
                to={`/diseases/${study.orphaId}/candidates`}
                className="btn-cobalt w-full text-xs py-2.5 flex items-center justify-center gap-2 font-semibold rounded-xl shadow-xs"
              >
                <span>Run {study.disease.split(' ')[0]} Pipeline</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

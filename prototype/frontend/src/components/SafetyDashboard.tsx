import type { FAERSSignal } from '../types'
import { ShieldCheck, AlertTriangle, XCircle, FlaskConical, AlertOctagon } from 'lucide-react'

interface SafetyDashboardProps {
  overall: 'pass' | 'caution' | 'fail'
  faersSignals: FAERSSignal[]
  admetPredictions: Record<string, number>
  admetClassifications: Record<string, 'pass' | 'caution' | 'fail'>
  contraindications: string[]
}

function SafetyBadge({ level }: { level: 'pass' | 'caution' | 'fail' }) {
  const colors = {
    pass: 'bg-emerald-50 text-emerald-700 border-emerald-200/70',
    caution: 'bg-amber-50 text-amber-700 border-amber-200/70',
    fail: 'bg-rose-50 text-rose-700 border-rose-200/70',
  }
  return (
    <span className={`px-3 py-1 text-xs font-bold rounded-full border ${colors[level]} flex items-center gap-1`}>
      {level === 'pass' && <ShieldCheck className="h-3 w-3" />}
      {level === 'caution' && <AlertTriangle className="h-3 w-3" />}
      {level === 'fail' && <XCircle className="h-3 w-3" />}
      {level.toUpperCase()}
    </span>
  )
}

function ADMETBar({
  name,
  value,
  classification,
}: {
  name: string
  value: number
  classification: 'pass' | 'caution' | 'fail'
}) {
  const colors = {
    pass: 'bg-emerald-500',
    caution: 'bg-amber-500',
    fail: 'bg-rose-500',
  }
  const maxVal = Math.max(value, 1.0)
  const width = Math.min((value / maxVal) * 100, 100)
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-600 w-32 truncate font-mono" title={name}>
        {name}
      </span>
      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${colors[classification]}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="text-xs font-mono w-14 text-right text-slate-700 font-semibold">
        {value.toFixed(2)}
      </span>
    </div>
  )
}

export function SafetyDashboard({
  overall,
  faersSignals,
  admetPredictions,
  admetClassifications,
  contraindications,
}: SafetyDashboardProps) {
  const admetEntries = Object.entries(admetPredictions)
  const nFail = admetEntries.filter(([k]) => admetClassifications[k] === 'fail').length
  const nCaution = admetEntries.filter(([k]) => admetClassifications[k] === 'caution').length

  return (
    <div className="space-y-6">
      {/* Overall Safety */}
      <div className="flex items-center justify-between p-4.5 bg-white/90 border border-slate-200/80 rounded-2xl shadow-xs">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Overall Safety Assessment</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {nFail} failed · {nCaution} caution · {admetEntries.length - nFail - nCaution} passed
          </p>
        </div>
        <SafetyBadge level={overall} />
      </div>

      {/* FAERS Signals */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
          FAERS Pharmacovigilance Signals
        </h3>
        {faersSignals.length > 0 ? (
          <div className="space-y-2">
            {faersSignals.map((signal, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3.5 bg-rose-50/50 border border-rose-200/70 rounded-2xl"
              >
                <div>
                  <p className="text-xs font-bold text-rose-950">{signal.meddra_pt}</p>
                  <p className="text-[11px] font-mono text-rose-700 mt-0.5">
                    ROR={signal.ror.toFixed(2)} · PRR={signal.prr.toFixed(2)} · BCPNN={signal.bcpnn.toFixed(2)} · N={signal.n_reports}
                  </p>
                </div>
                <SafetyBadge level={signal.level} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500 p-3 bg-slate-50 rounded-xl">
            No FAERS disproportionate signals detected.
          </p>
        )}
      </div>

      {/* ADMET Predictions */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <FlaskConical className="h-3.5 w-3.5 text-blue-600" />
          ADMET Pharmacokinetic Predictions
        </h3>
        <div className="space-y-2 p-4 bg-white/90 border border-slate-200/80 rounded-2xl shadow-xs">
          {admetEntries.map(([endpoint, value]) => (
            <ADMETBar
              key={endpoint}
              name={endpoint}
              value={value}
              classification={admetClassifications[endpoint] || 'pass'}
            />
          ))}
        </div>
      </div>

      {/* Contraindications */}
      {contraindications.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
            <AlertOctagon className="h-3.5 w-3.5 text-amber-600" />
            Contraindications & Black-Box Warnings
          </h3>
          <div className="space-y-1.5">
            {contraindications.map((c, i) => (
              <div
                key={i}
                className="p-3 bg-amber-50/60 border border-amber-200/70 rounded-xl text-xs text-amber-900"
              >
                {c}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

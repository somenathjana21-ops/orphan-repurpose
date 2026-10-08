import type { FAERSSignal } from '../types'

interface SafetyDashboardProps {
  overall: 'pass' | 'caution' | 'fail'
  faersSignals: FAERSSignal[]
  admetPredictions: Record<string, number>
  admetClassifications: Record<string, 'pass' | 'caution' | 'fail'>
  contraindications: string[]
}

function SafetyBadge({ level }: { level: 'pass' | 'caution' | 'fail' }) {
  const colors = {
    pass: 'bg-green-100 text-green-800 border-green-300',
    caution: 'bg-amber-100 text-amber-800 border-amber-300',
    fail: 'bg-red-100 text-red-800 border-red-300',
  }
  return (
    <span className={`px-3 py-1 text-sm font-semibold rounded-full border ${colors[level]}`}>
      {level.toUpperCase()}
    </span>
  )
}

function ADMETBar({ name, value, classification }: { name: string; value: number; classification: 'pass' | 'caution' | 'fail' }) {
  const colors = { pass: 'bg-green-500', caution: 'bg-amber-500', fail: 'bg-red-500' }
  const maxVal = Math.max(value, 1.0)
  const width = Math.min((value / maxVal) * 100, 100)
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-600 w-28 truncate">{name}</span>
      <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${colors[classification]}`} style={{ width: `${width}%` }} />
      </div>
      <span className="text-xs font-mono w-14 text-right">{value.toFixed(2)}</span>
    </div>
  )
}

export function SafetyDashboard({ overall, faersSignals, admetPredictions, admetClassifications, contraindications }: SafetyDashboardProps) {
  const admetEntries = Object.entries(admetPredictions)
  const nFail = admetEntries.filter(([k]) => admetClassifications[k] === 'fail').length
  const nCaution = admetEntries.filter(([k]) => admetClassifications[k] === 'caution').length

  return (
    <div className="space-y-6">
      {/* Overall Safety */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">Overall Safety Assessment</h3>
          <p className="text-sm text-gray-500">
            {nFail} failed · {nCaution} caution · {admetEntries.length - nFail - nCaution} passed
          </p>
        </div>
        <SafetyBadge level={overall} />
      </div>

      {/* FAERS Signals */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <span className="text-red-500">⚠️</span> FAERS Pharmacovigilance Signals
        </h3>
        {faersSignals.length > 0 ? (
          <div className="space-y-2">
            {faersSignals.map((signal, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-red-900">{signal.meddra_pt}</p>
                  <p className="text-xs text-red-700">ROR={signal.ror.toFixed(2)} · PRR={signal.prr.toFixed(2)} · BCPNN={signal.bcpnn.toFixed(2)} · N={signal.n_reports}</p>
                </div>
                <SafetyBadge level={signal.level} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 p-3 bg-gray-50 rounded-lg">No FAERS signals detected.</p>
        )}
      </div>

      {/* ADMET Predictions */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <span className="text-blue-500">🧪</span> ADMET Predictions
        </h3>
        <div className="space-y-1.5 p-3 bg-blue-50 border border-blue-200 rounded-lg">
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
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="text-amber-500">🚫</span> Contraindications
          </h3>
          <div className="space-y-1">
            {contraindications.map((c, i) => (
              <div key={i} className="p-2 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
                {c}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

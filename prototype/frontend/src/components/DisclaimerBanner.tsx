import { AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'

export function DisclaimerBanner({ onDismiss }: { onDismiss?: () => void }) {
  const [dismissed, setDismissed] = useState(false)
  
  if (dismissed) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-amber-100 border-b border-amber-300 px-4 py-2 lg:px-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-amber-900">
              <strong>RESEARCH PROTOTYPE</strong> — Not for clinical use.
            </p>
            <p className="text-xs text-amber-800">
              All outputs require human expert validation. This platform generates hypotheses for further investigation only.
            </p>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={() => { setDismissed(true); onDismiss(); }}
            className="p-1 text-amber-600 hover:text-amber-900 transition-colors"
            aria-label="Dismiss disclaimer"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  )
}
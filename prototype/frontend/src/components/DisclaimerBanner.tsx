import { AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'

export function DisclaimerBanner({ onDismiss }: { onDismiss?: () => void }) {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem('disclaimer_dismissed') === 'true'
    } catch {
      return false
    }
  })
  
  if (dismissed) return null

  const handleDismiss = () => {
    setDismissed(true)
    try {
      sessionStorage.setItem('disclaimer_dismissed', 'true')
    } catch {
      // ignore
    }
    if (onDismiss) onDismiss()
  }

  return (
    <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/15 to-orange-500/10 border-b border-amber-200/80 backdrop-blur-md px-4 py-2.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/20 text-amber-700 ring-1 ring-amber-500/30 shrink-0">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          </span>
          <div className="text-xs sm:text-sm text-amber-900 leading-snug">
            <span className="font-semibold uppercase tracking-wider text-amber-950 bg-amber-200/80 px-2 py-0.5 rounded text-[11px] mr-2">
              Research Prototype
            </span>
            Not for clinical use. All predictions require human expert validation & experimental verification.
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="p-1 rounded-lg text-amber-700 hover:text-amber-900 hover:bg-amber-500/15 transition-colors shrink-0"
          aria-label="Dismiss disclaimer"
          title="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
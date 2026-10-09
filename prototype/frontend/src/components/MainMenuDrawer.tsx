import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  X,
  LayoutDashboard,
  Sparkles,
  Network,
  BookmarkCheck,
  FileText,
  ExternalLink,
  FlaskConical,
  Cpu,
} from 'lucide-react'

interface MainMenuDrawerProps {
  isOpen: boolean
  onClose: () => void
  backendOnline: boolean | null
}

const navSections = [
  {
    title: 'Platform Modules',
    items: [
      { name: 'Disease Browser', href: '/', icon: LayoutDashboard, desc: 'Search 4,357 orphan conditions' },
      { name: 'Drug Candidate Engine', href: '/diseases/ORPHA:635/candidates', icon: Sparkles, desc: 'DualEncoder GNN predictions' },
      { name: 'Knowledge Graph Explorer', href: '/kg', icon: Network, desc: 'Kùzu biological relation graph' },
      { name: 'Clinical Case Studies', href: '/case-studies', icon: BookmarkCheck, desc: 'Niemann-Pick Type C & CF validation' },
      { name: 'IND Dossier Builder', href: '/dossier', icon: FileText, desc: 'Pre-IND regulatory packet & export' },
    ],
  },
]

const benchmarkShortcuts = [
  { name: 'Niemann-Pick Type C', orphaId: 'ORPHA:635', gene: 'NPC1', badge: 'Primary Benchmark' },
  { name: 'Cystic Fibrosis', orphaId: 'ORPHA:793', gene: 'CFTR', badge: 'Targeted' },
  { name: 'Huntington Disease', orphaId: 'ORPHA:98065', gene: 'HTT', badge: 'Neuro' },
]

export function MainMenuDrawer({ isOpen, onClose, backendOnline }: MainMenuDrawerProps) {
  const location = useLocation()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeyDown)
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Frosted Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Card */}
      <div className="relative w-full max-w-md bg-white/95 backdrop-blur-2xl shadow-2xl border-l border-slate-200/80 flex flex-col justify-between overflow-y-auto scrollbar-thin z-10 transition-transform animate-in slide-in-from-right duration-200">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-base shadow-sm">
                +
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-slate-900 block leading-tight">
                  orphan repurpose
                </span>
                <span className="text-[10px] font-semibold tracking-wider text-blue-600 uppercase">
                  asklepios biotech
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Quick Benchmarks */}
          <div className="p-6 border-b border-slate-100 bg-slate-50/50">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <FlaskConical className="h-3.5 w-3.5 text-blue-600" />
              <span>Quick Benchmarks</span>
            </div>
            <div className="space-y-2">
              {benchmarkShortcuts.map((b) => (
                <Link
                  key={b.orphaId}
                  to={`/diseases/${b.orphaId}`}
                  onClick={onClose}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-slate-200/70 hover:border-blue-300 hover:shadow-xs transition-all group"
                >
                  <div>
                    <div className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {b.name}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {b.orphaId} · Gene: {b.gene}
                    </div>
                  </div>
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200/60">
                    {b.badge}
                  </span>
                </Link>
              ))}
            </div>
          </div>

          {/* Nav Items */}
          <div className="p-6 space-y-6">
            {navSections.map((section) => (
              <div key={section.title}>
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                  {section.title}
                </div>
                <div className="space-y-1.5">
                  {section.items.map((item) => {
                    const isActive =
                      item.href === '/'
                        ? location.pathname === '/' || location.pathname === '/diseases'
                        : location.pathname.startsWith(item.href)

                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        onClick={onClose}
                        className={`flex items-start gap-3.5 p-3 rounded-2xl transition-all ${
                          isActive
                            ? 'bg-blue-50/80 border border-blue-200/70 shadow-xs'
                            : 'hover:bg-slate-50 border border-transparent'
                        }`}
                      >
                        <div
                          className={`p-2 rounded-xl mt-0.5 ${
                            isActive
                              ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          <item.icon className="h-4 w-4" />
                        </div>
                        <div>
                          <div
                            className={`text-sm font-semibold ${
                              isActive ? 'text-blue-900' : 'text-slate-800'
                            }`}
                          >
                            {item.name}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5 leading-snug">
                            {item.desc}
                          </div>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer System Telemetry */}
        <div className="p-6 border-t border-slate-100 bg-slate-50/70 space-y-3">
          <div className="rounded-2xl bg-white p-3.5 border border-slate-200/70 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5 text-blue-600" />
                AI Inference Stack
              </span>
              <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-600">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                DualEncoder
              </span>
            </div>
            <div className="text-[11px] text-slate-500 leading-relaxed">
              PyTorch Graph Neural Network cross-attention reasoning with Kùzu graph DB & FAERS post-market safety.
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  backendOnline ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
              <span>{backendOnline ? 'API Connected (:8000)' : 'API Offline'}</span>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 transition-colors"
            >
              FastAPI Docs <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

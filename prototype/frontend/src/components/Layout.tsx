import { ReactNode, useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  Menu,
  X,
  LayoutDashboard,
  Network,
  FlaskConical,
  Sparkles,
  FileText,
  BookmarkCheck,
  ExternalLink,
  Dna,
} from 'lucide-react'

const navigation = [
  { name: 'Disease Browser', href: '/', icon: LayoutDashboard, badge: '4,357' },
  { name: 'Knowledge Graph', href: '/kg', icon: Network, badge: 'Kùzu' },
  { name: 'Drug Candidates', href: '/diseases/ORPHA:635/candidates', icon: Sparkles, badge: 'AI Models' },
  { name: 'Case Studies', href: '/case-studies', icon: BookmarkCheck, badge: 'NPC / CF' },
  { name: 'Dossier Builder', href: '/dossier', icon: FileText, badge: 'PDF' },
]

export function Layout({ children }: { children?: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const location = useLocation()

  useEffect(() => {
    // Quick health probe to show connection status
    fetch('/health')
      .then((res) => (res.ok ? setBackendOnline(true) : setBackendOnline(false)))
      .catch(() => setBackendOnline(false))
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50/50">
      {/* Mobile sidebar overlay */}
      <div
        className={`fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs lg:hidden transition-opacity ${
          sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-slate-200/90 flex flex-col justify-between transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div>
          {/* Brand header */}
          <div className="flex h-18 items-center justify-between px-6 border-b border-slate-100">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <Dna className="h-5 w-5" />
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight text-slate-900 block leading-tight">
                  Orphan<span className="text-indigo-600">Repurpose</span>
                </span>
                <span className="text-[11px] font-medium text-slate-400 tracking-wide uppercase">
                  Biotech AI Platform
                </span>
              </div>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Nav Items */}
          <nav className="p-4 space-y-1.5">
            <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Platform Modules
            </div>
            {navigation.map((item) => {
              const isActive =
                item.href === '/'
                  ? location.pathname === '/' || location.pathname === '/diseases'
                  : location.pathname.startsWith(item.href)

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-xs ring-1 ring-indigo-500/10'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <div className="flex items-center gap-3">
                    <item.icon
                      className={`h-4.5 w-4.5 transition-colors ${
                        isActive ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'
                      }`}
                      aria-hidden="true"
                    />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-md font-medium tracking-tight ${
                        isActive
                          ? 'bg-indigo-100 text-indigo-800'
                          : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200/70 group-hover:text-slate-700'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Sidebar Footer info */}
        <div className="p-4 border-t border-slate-100 space-y-3">
          <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200/60">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-700">Platform Pipeline</span>
              <span className="flex items-center gap-1.5 text-[11px] text-emerald-600 font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              PyTorch GNN + Cross Attention indication prediction model connected to local Kùzu Knowledge Graph.
            </p>
          </div>

          <div className="flex items-center justify-between px-1 text-xs text-slate-400">
            <span>Research Prototype</span>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-indigo-600 flex items-center gap-1 transition-colors"
            >
              FastAPI Docs <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-18 bg-white/95 backdrop-blur-md border-b border-slate-200/80 flex items-center justify-between px-4 lg:px-8 shrink-0 z-10">
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Benchmark Disease:</span>
              <Link
                to="/diseases/ORPHA:635"
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-indigo-50/80 text-indigo-700 border border-indigo-200/70 rounded-lg hover:bg-indigo-100 transition-colors"
              >
                <FlaskConical className="h-3.5 w-3.5" />
                Niemann-Pick Type C (ORPHA:635)
              </Link>
              <Link
                to="/diseases/ORPHA:793"
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200/70 rounded-lg hover:bg-slate-200/70 transition-colors"
              >
                Cystic Fibrosis (ORPHA:793)
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Backend connection badge */}
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${
                backendOnline === true
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : backendOnline === false
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-slate-50 text-slate-600 border-slate-200'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  backendOnline === true
                    ? 'bg-emerald-500 animate-pulse'
                    : backendOnline === false
                    ? 'bg-amber-500'
                    : 'bg-slate-400'
                }`}
              />
              <span className="hidden sm:inline">
                {backendOnline === true ? 'Backend: :8000 Connected' : 'Checking Backend...'}
              </span>
              <span className="sm:hidden">{backendOnline === true ? ':8000' : 'Offline'}</span>
            </div>

            <Link
              to="/dossier"
              className="hidden md:inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-xs transition-colors"
            >
              <FileText className="h-3.5 w-3.5" />
              Build Dossier
            </Link>
          </div>
        </header>

        {/* Scrollable Main content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 scrollbar-thin">
          <div className="max-w-7xl mx-auto">{children ?? <Outlet />}</div>
        </main>
      </div>
    </div>
  )
}
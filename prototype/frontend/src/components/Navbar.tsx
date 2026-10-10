import { Link, useLocation } from 'react-router-dom'
import { FlaskConical } from 'lucide-react'

interface NavbarProps {
  onOpenMenu: () => void
  backendOnline: boolean | null
}

const navLinks = [
  { name: 'Diseases', href: '/' },
  { name: 'Candidates', href: '/diseases/ORPHA:635/candidates' },
  { name: 'Knowledge Graph', href: '/kg' },
  { name: 'Case Studies', href: '/case-studies' },
  { name: 'Dossier', href: '/dossier' },
]

export function Navbar({ onOpenMenu, backendOnline }: NavbarProps) {
  const location = useLocation()

  return (
    <header className="h-20 px-6 sm:px-10 flex items-center justify-between border-b border-slate-100/90 bg-white/80 backdrop-blur-md shrink-0">
      {/* Brand Logo & Mark */}
      <div className="flex items-center gap-8">
        <Link to="/" className="flex flex-col group">
          <span className="text-lg font-bold tracking-tight text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
            orphan repurpose
          </span>
          <span className="text-[10px] font-semibold tracking-wider text-blue-600 uppercase">
            asklepios biotech ai
          </span>
        </Link>

        {/* Primary Desktop Nav Links */}
        <nav className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive =
              link.href === '/'
                ? location.pathname === '/' || location.pathname === '/diseases'
                : location.pathname.startsWith(link.href)

            return (
              <Link
                key={link.name}
                to={link.href}
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-slate-100 text-slate-900 font-semibold shadow-2xs'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                {link.name}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Right Controls: Benchmark Pill + Status + Main Menu */}
      <div className="flex items-center gap-3.5 sm:gap-5">
        {/* Benchmark Quick Access Chip */}
        <div className="hidden xl:flex items-center gap-2">
          <span className="text-[11px] font-medium text-slate-400">Benchmark:</span>
          <Link
            to="/diseases/ORPHA:635"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-50/70 text-blue-700 border border-blue-200/50 hover:bg-blue-100/70 transition-colors"
          >
            <FlaskConical className="h-3 w-3" />
            NPC (ORPHA:635)
          </Link>
        </div>

        {/* Backend health status badge */}
        <div
          className={`hidden sm:flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-medium border ${
            backendOnline === true
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200/60'
              : backendOnline === false
              ? 'bg-amber-50 text-amber-700 border-amber-200/60'
              : 'bg-slate-50 text-slate-500 border-slate-200/60'
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              backendOnline === true
                ? 'bg-emerald-500 animate-pulse'
                : backendOnline === false
                ? 'bg-amber-500'
                : 'bg-slate-400'
            }`}
          />
          <span>{backendOnline === true ? 'Backend Connected' : 'Checking Backend'}</span>
        </div>

        {/* Main Menu Button (Matching Reference Design Pill/Bracket) */}
        <button
          onClick={onOpenMenu}
          className="group flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-slate-800 hover:text-slate-950 hover:bg-slate-50 transition-all cursor-pointer"
          aria-label="Open main menu"
        >
          <span>Main Menu</span>
          {/* Minimalist stylized bracket indicator matching reference mockup */}
          <div className="flex items-center text-slate-700 group-hover:text-blue-600 transition-colors">
            <svg
              className="w-5 h-3.5 stroke-current"
              viewBox="0 0 20 12"
              fill="none"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M1 2v7h18V2" />
            </svg>
          </div>
        </button>
      </div>
    </header>
  )
}

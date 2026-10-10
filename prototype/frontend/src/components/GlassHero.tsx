import { Sparkles, ArrowRight, Dna, ShieldCheck, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'

interface GlassHeroProps {
  onSelectBenchmark: (orphaId: string) => void
}

const BENCHMARKS = [
  { name: 'Niemann-Pick Type C', orphaId: 'ORPHA:635', gene: 'NPC1', tag: 'Benchmark' },
  { name: 'Cystic Fibrosis', orphaId: 'ORPHA:793', gene: 'CFTR', tag: 'Targeted' },
  { name: 'Huntington Disease', orphaId: 'ORPHA:98065', gene: 'HTT', tag: 'Neuro' },
]

export function GlassHero({ onSelectBenchmark }: GlassHeroProps) {
  return (
    <div className="relative overflow-hidden rounded-3xl sm:rounded-4xl bg-gradient-to-br from-white via-slate-50/70 to-blue-50/30 border border-slate-200/80 p-8 sm:p-12 lg:p-14 shadow-xs">
      {/* Background Soft Glows */}
      <div className="absolute top-0 right-1/4 -mt-20 w-96 h-96 bg-sky-200/30 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-10 -mb-20 w-80 h-80 bg-blue-400/20 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Column: Asklepios Typography & CTAs */}
        <div className="lg:col-span-7 space-y-7 max-w-2xl">
          {/* Micro Tag */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50/80 text-blue-700 text-xs font-semibold border border-blue-200/60 shadow-2xs">
            <Sparkles className="h-3.5 w-3.5 text-blue-600" />
            <span>asklepios · Personalized Healthcare AI Therapeutics</span>
          </div>

          {/* Hero Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.08]">
            Personalized <br />
            Healthcare <br />
            <span className="text-slate-900">AI Diagnosis</span>
          </h1>

          {/* Subtitle */}
          <p className="text-slate-500 text-base sm:text-lg leading-relaxed max-w-xl font-normal">
            asklepios provides personalized healthcare AI analytics to empower rare disease discovery.
            Query graph neural reasoning across <strong className="text-slate-800 font-semibold">4,357 orphan conditions</strong> with calibrated efficacy and post-market safety.
          </p>

          {/* CTAs matching reference: Pill Button + Cobalt Squircle '+' Button */}
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={() => onSelectBenchmark('ORPHA:635')}
              className="btn-pill px-6 py-3 text-sm font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 shadow-xs cursor-pointer"
            >
              Try Demo (NPC)
            </button>

            <Link
              to="/diseases/ORPHA:635/candidates"
              className="w-12 h-12 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center font-bold text-2xl shadow-lg shadow-blue-500/25 transition-all hover:scale-105 active:scale-95 cursor-pointer"
              aria-label="Explore AI Drug Candidates"
              title="Explore AI Drug Candidates"
            >
              +
            </Link>

            <Link
              to="/kg"
              className="ml-3 hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-600 transition-colors"
            >
              <span>Explore Knowledge Graph</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Quick Benchmarks */}
          <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 font-medium mr-1">Quick Benchmarks:</span>
            {BENCHMARKS.map((b) => (
              <button
                key={b.orphaId}
                onClick={() => onSelectBenchmark(b.orphaId)}
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 rounded-lg transition-all border border-slate-200/80 hover:border-blue-300 shadow-2xs active:scale-95 cursor-pointer"
              >
                <span>{b.name}</span>
                <span className="text-[10px] text-blue-600 font-mono font-semibold">({b.orphaId})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Right Column: Layered 3D Frosted-Glass Composition */}
        <div className="lg:col-span-5 relative flex items-center justify-center min-h-[360px] sm:min-h-[420px] select-none">
          {/* Fan-stacked Frosted Glass Slabs (matching the Asklepios reference graphic) */}
          <div className="relative w-full max-w-[380px] h-[360px] sm:h-[400px]">
            {/* Slab 1 (Backmost, steep angle) */}
            <div
              className="absolute -right-6 sm:-right-8 top-0 w-64 sm:w-72 h-44 rounded-2xl bg-gradient-to-tr from-sky-400/20 via-blue-400/30 to-indigo-500/20 backdrop-blur-md border border-white/70 shadow-xl transform rotate-[-22deg] origin-bottom-left transition-transform hover:rotate-[-24deg]"
              style={{
                boxShadow: '0 20px 50px rgba(59, 130, 246, 0.15)',
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/40 via-transparent to-transparent rounded-2xl" />
            </div>

            {/* Slab 2 */}
            <div
              className="absolute -right-3 sm:-right-4 top-8 w-68 sm:w-76 h-48 rounded-2xl bg-gradient-to-tr from-cyan-300/30 via-sky-400/35 to-blue-500/25 backdrop-blur-lg border border-white/80 shadow-2xl transform rotate-[-15deg] origin-bottom-left transition-transform hover:rotate-[-17deg]"
              style={{
                boxShadow: '0 25px 60px rgba(37, 99, 235, 0.18)',
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/50 via-transparent to-white/20 rounded-2xl" />
            </div>

            {/* Slab 3 */}
            <div
              className="absolute right-0 sm:right-2 top-20 w-72 sm:w-80 h-52 rounded-2xl bg-gradient-to-tr from-blue-300/35 via-cyan-400/40 to-sky-500/30 backdrop-blur-xl border border-white/90 shadow-2xl transform rotate-[-8deg] origin-bottom-left transition-transform hover:rotate-[-10deg]"
              style={{
                boxShadow: '0 30px 70px rgba(14, 165, 233, 0.22)',
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/60 via-transparent to-transparent rounded-2xl" />
              {/* Subtle Refraction Line */}
              <div className="absolute top-3 left-4 right-4 h-[1px] bg-white/70" />
            </div>

            {/* Slab 4 (Foreground Primary Glass Plate) */}
            <div
              className="absolute right-2 sm:right-6 top-36 w-72 sm:w-84 h-56 rounded-3xl bg-gradient-to-tr from-white/80 via-sky-100/50 to-blue-200/40 backdrop-blur-2xl border border-white/95 shadow-2xl transform rotate-[-1deg] origin-bottom-left p-5 flex flex-col justify-between transition-transform hover:rotate-[0deg]"
              style={{
                boxShadow: '0 25px 50px -12px rgba(30, 58, 138, 0.2)',
              }}
            >
              {/* Glass Sheen */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/70 via-transparent to-blue-500/10 rounded-3xl pointer-events-none" />

              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                      +
                    </div>
                    <span className="text-xs font-bold text-slate-900 tracking-tight">AI Reasoning Stack</span>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/70">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Calibrated
                  </span>
                </div>

                <div className="space-y-2 pt-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5 text-blue-600" />
                      Model AUROC
                    </span>
                    <span className="font-bold text-slate-900 font-mono">98.2%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-600 to-sky-400 h-1.5 rounded-full w-[98%]" />
                  </div>
                </div>
              </div>

              {/* Badges in Glass Slab */}
              <div className="relative z-10 pt-3 border-t border-slate-200/50 flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-1.5 text-slate-600">
                  <Dna className="h-3.5 w-3.5 text-blue-600" />
                  <span>4,357 Diseases</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-600">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                  <span>FAERS Safety</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

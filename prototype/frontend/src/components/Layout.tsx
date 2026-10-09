import { ReactNode, useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'
import { MainMenuDrawer } from './MainMenuDrawer'

export function Layout({ children }: { children?: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)

  useEffect(() => {
    // Quick health probe to show connection status
    fetch('/health')
      .then((res) => (res.ok ? setBackendOnline(true) : setBackendOnline(false)))
      .catch(() => setBackendOnline(false))
  }, [])

  return (
    <div className="w-full flex-1 flex flex-col">
      {/* Framed Application Card Container */}
      <div className="w-full max-w-[1536px] mx-auto bg-white rounded-3xl sm:rounded-4xl shadow-2xl shadow-slate-300/40 border border-slate-200/70 flex flex-col min-h-[calc(100vh-3rem)] overflow-hidden transition-all my-2 sm:my-3">
        {/* Top Navbar */}
        <Navbar onOpenMenu={() => setMenuOpen(true)} backendOnline={backendOnline} />

        {/* Scrollable Main content */}
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 sm:py-8 space-y-8 scrollbar-thin">
          <div className="max-w-7xl mx-auto w-full">
            {children ?? <Outlet />}
          </div>
        </main>
      </div>

      {/* Slide-over Main Menu Drawer */}
      <MainMenuDrawer
        isOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
        backendOnline={backendOnline}
      />
    </div>
  )
}
import { ReactNode } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Menu, Home, FlaskConical, FileText, Network } from 'lucide-react'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Knowledge Graph', href: '/kg', icon: Network },
  { name: 'Diseases', href: '/diseases', icon: FlaskConical },
  { name: 'Candidates', href: '/candidates', icon: FlaskConical },
  { name: 'Dossiers', href: '/dossier', icon: FileText },
  { name: 'Case Studies', href: '/case-studies', icon: FlaskConical },
]

export function Layout({ children }: { children?: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile sidebar */}
      <div
        className={`fixed inset-0 z-40 bg-gray-900/50 lg:hidden transition-opacity ${
          sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 lg:relative lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center px-6 border-b border-gray-200">
          <Link to="/" className="flex items-center gap-2">
            <FlaskConical className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">OrphanRepurpose</span>
          </Link>
        </div>
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href))
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" aria-hidden="true" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 lg:px-6">
          <button
            className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <div className="flex-1 lg:flex-none" />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  )
}
import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import { DisclaimerBanner } from './components/DisclaimerBanner'
import { Layout } from './components/Layout'

const DiseaseDetail = lazy(() => import('./components/DiseaseDetail').then(m => ({ default: m.DiseaseDetail })))
const CandidateList = lazy(() => import('./components/CandidateList').then(m => ({ default: m.CandidateList })))
const CandidateDetail = lazy(() => import('./components/CandidateDetail').then(m => ({ default: m.CandidateDetail })))
const DossierBuilder = lazy(() => import('./components/DossierBuilder').then(m => ({ default: m.DossierBuilder })))
const CaseStudies = lazy(() => import('./components/CaseStudies').then(m => ({ default: m.CaseStudies })))
const KGBrowser = lazy(() => import('./components/KGBrowser').then(m => ({ default: m.KGBrowser })))

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-100/90 text-slate-900 font-sans selection:bg-blue-600 selection:text-white p-2 sm:p-4 lg:p-6">
      <DisclaimerBanner />
      <Layout>
        <Suspense fallback={<div role="status" className="glass-card p-8 text-center text-slate-600">Loading page…</div>}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/diseases" element={<Navigate to="/" replace />} />
            <Route path="/diseases/:orphaId" element={<DiseaseDetail />} />
            <Route path="/diseases/:orphaId/candidates" element={<CandidateList />} />
            <Route path="/candidates" element={<Navigate to="/diseases/ORPHA:646/candidates" replace />} />
            <Route path="/candidates/:candidateId" element={<CandidateDetail />} />
            <Route path="/dossier" element={<DossierBuilder />} />
            <Route path="/case-studies" element={<CaseStudies />} />
            <Route path="/kg" element={<KGBrowser />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </div>
  )
}

export default App

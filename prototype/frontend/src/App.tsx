import { Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import { DiseaseDetail } from './components/DiseaseDetail'
import { CandidateList } from './components/CandidateList'
import { CandidateDetail } from './components/CandidateDetail'
import { DossierBuilder } from './components/DossierBuilder'
import { CaseStudies } from './components/CaseStudies'
import { KGBrowser } from './components/KGBrowser'
import { DisclaimerBanner } from './components/DisclaimerBanner'
import { Layout } from './components/Layout'

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-100/90 text-slate-900 font-sans selection:bg-blue-600 selection:text-white p-2 sm:p-4 lg:p-6">
      <DisclaimerBanner />
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/diseases" element={<Navigate to="/" replace />} />
          <Route path="/diseases/:orphaId" element={<DiseaseDetail />} />
          <Route path="/diseases/:orphaId/candidates" element={<CandidateList />} />
          <Route path="/candidates" element={<Navigate to="/diseases/ORPHA:635/candidates" replace />} />
          <Route path="/candidates/:candidateId" element={<CandidateDetail />} />
          <Route path="/dossier" element={<DossierBuilder />} />
          <Route path="/case-studies" element={<CaseStudies />} />
          <Route path="/kg" element={<KGBrowser />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </div>
  )
}

export default App
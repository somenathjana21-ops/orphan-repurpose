import { Routes, Route } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import { DiseaseDetail } from './components/DiseaseDetail'
import { CandidateList } from './components/CandidateList'
import { CandidateDetail } from './components/CandidateDetail'
import { DossierBuilder } from './components/DossierBuilder'
import { CaseStudies } from './components/CaseStudies'
import { DisclaimerBanner } from './components/DisclaimerBanner'
import { Layout } from './components/Layout'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <DisclaimerBanner />
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/diseases/:orphaId" element={<DiseaseDetail />} />
          <Route path="/diseases/:orphaId/candidates" element={<CandidateList />} />
          <Route path="/candidates/:candidateId" element={<CandidateDetail />} />
          <Route path="/dossier" element={<DossierBuilder />} />
          <Route path="/case-studies" element={<CaseStudies />} />
        </Routes>
      </Layout>
    </div>
  )
}

export default App
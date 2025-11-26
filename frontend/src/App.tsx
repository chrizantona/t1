import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import CandidateDashboard from './pages/CandidateDashboard'
import AdminDashboard from './pages/AdminDashboard'
import PreparePage from './pages/PreparePage'
import InterviewPage from './pages/InterviewPage'
import TheoryPage from './pages/TheoryPage'
import ResultPage from './pages/ResultPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import { QuestionsTestPage } from './pages/QuestionsTestPage'
import './styles/questions.css'

function App() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/landing" element={<LandingPage />} />
        
        {/* Candidate routes */}
        <Route path="/candidate" element={<CandidateDashboard />} />
        <Route path="/prepare" element={<PreparePage />} />
        <Route path="/prepare/:interviewId" element={<PreparePage />} />
        <Route path="/interview/:interviewId" element={<InterviewPage />} />
        <Route path="/theory/:interviewId" element={<TheoryPage />} />
        <Route path="/result/:interviewId" element={<ResultPage />} />
        
        {/* Admin routes */}
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/old" element={<AdminDashboardPage />} />
        
        {/* Test routes */}
        <Route path="/questions-test" element={<QuestionsTestPage />} />
      </Routes>
    </Router>
  )
}

export default App


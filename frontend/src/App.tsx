import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
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
        <Route path="/" element={<LandingPage />} />
        <Route path="/prepare/:interviewId" element={<PreparePage />} />
        <Route path="/interview/:interviewId" element={<InterviewPage />} />
        <Route path="/theory/:interviewId" element={<TheoryPage />} />
        <Route path="/result/:interviewId" element={<ResultPage />} />
        <Route path="/admin" element={<AdminDashboardPage />} />
        <Route path="/questions-test" element={<QuestionsTestPage />} />
      </Routes>
    </Router>
  )
}

export default App


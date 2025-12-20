import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { vacancyAPI, setAuthToken } from '../api/client'
import '../styles/dashboard.css'

function CandidateDashboard() {
  const navigate = useNavigate()
  const [vacancies, setVacancies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userData = localStorage.getItem('vibecode_user')
    if (userData) {
      setUser(JSON.parse(userData))
    }
    loadVacancies()
  }, [])

  const loadVacancies = async () => {
    try {
      const data = await vacancyAPI.listVacancies()
      setVacancies(data)
    } catch (error) {
      console.error('Failed to load vacancies:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setAuthToken(null)
    localStorage.removeItem('vibecode_user')
    navigate('/login')
  }

  const startInterview = (vacancyId?: number) => {
    // Navigate to prepare page (existing flow)
    navigate('/prepare', { state: { vacancyId } })
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>🚀 VibeCode</h1>
          <span className="role-badge candidate">Кандидат</span>
        </div>
        <div className="header-right">
          <span className="user-name">👤 {user?.full_name || user?.email}</span>
          <button className="logout-btn" onClick={handleLogout}>Выйти</button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-welcome">
          <h2>Добро пожаловать, {user?.full_name || 'Кандидат'}! 👋</h2>
          <p>Выберите вакансию для прохождения технического собеседования</p>
        </div>

        {/* Quick start without vacancy */}
        <div className="quick-start-card">
          <div className="quick-start-content">
            <h3>🎯 Быстрый старт</h3>
            <p>Пройдите общее техническое интервью без привязки к конкретной вакансии</p>
          </div>
          <button className="start-btn" onClick={() => startInterview()}>
            Начать интервью →
          </button>
        </div>

        {/* Vacancies list */}
        <section className="vacancies-section">
          <h3>📋 Доступные вакансии</h3>
          
          {loading ? (
            <div className="loading">Загрузка вакансий...</div>
          ) : vacancies.length === 0 ? (
            <div className="empty-state">
              <p>Пока нет открытых вакансий</p>
              <p className="hint">Вы можете пройти общее интервью выше</p>
            </div>
          ) : (
            <div className="vacancies-grid">
              {vacancies.map((vacancy) => (
                <div key={vacancy.id} className="vacancy-card">
                  <div className="vacancy-header">
                    <h4>{vacancy.title}</h4>
                    <span className={`level-badge ${vacancy.level}`}>
                      {vacancy.level}
                    </span>
                  </div>
                  <div className="vacancy-meta">
                    <span className="track">{vacancy.track}</span>
                    {vacancy.company_name && (
                      <span className="company">{vacancy.company_name}</span>
                    )}
                  </div>
                  {vacancy.description && (
                    <p className="vacancy-desc">{vacancy.description.slice(0, 150)}...</p>
                  )}
                  <button 
                    className="apply-btn"
                    onClick={() => startInterview(vacancy.id)}
                  >
                    Пройти собеседование
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default CandidateDashboard


// пидормот

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interviewAPI, resumeAPI } from '../api/client'
import '../styles/landing.css'

function LandingPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [selectedLevel, setSelectedLevel] = useState('middle')
  const [selectedDirection, setSelectedDirection] = useState('backend')
  const [cvText, setCvText] = useState('')
  const [suggestion, setSuggestion] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'quick' | 'cv'>('quick')

  const analyzeCV = async () => {
    if (!cvText.trim()) return
    
    setLoading(true)
    try {
      const result = await resumeAPI.analyzeCV(cvText)
      setSuggestion(result)
      setSelectedLevel(result.suggested_level)
      setSelectedDirection(result.suggested_direction)
    } catch (error) {
      console.error('CV analysis failed:', error)
      alert('Не удалось проанализировать резюме')
    } finally {
      setLoading(false)
    }
  }

  const startInterview = async () => {
    setLoading(true)
    
    const payload = {
      candidate_name: name || undefined,
      candidate_email: email || undefined,
      selected_level: selectedLevel,
      direction: selectedDirection,
      cv_text: cvText || undefined,
    }
    
    console.log('Starting interview with payload:', payload)
    
    try {
      const interview = await interviewAPI.startInterview(payload)
      navigate(`/interview/${interview.id}`)
    } catch (error: any) {
      console.error('Failed to start interview:', error)
      console.error('Error response:', error.response?.data)
      alert(`Не удалось начать интервью: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="landing-page">
      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div className="logo">
            <span className="logo-icon">+</span>
            <span className="logo-text">VibeCode</span>
          </div>
          <nav className="nav">
            <a href="#features">Возможности</a>
            <a href="#start">Начать</a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-container">
          <h1 className="hero-title">Умное техническое собеседование</h1>
          <p className="hero-subtitle">
            AI-платформа для проведения технических интервью с адаптивными задачами,
            интеллектуальным ассистентом и объективной оценкой навыков
          </p>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="features">
        <div className="container">
          <div className="features-grid">
            <div className="feature">
              <div className="feature-number">01</div>
              <h3 className="feature-title">CV Analysis</h3>
              <p className="feature-text">
                Загрузите резюме, и AI автоматически определит оптимальный уровень сложности
              </p>
            </div>

            <div className="feature">
              <div className="feature-number">02</div>
              <h3 className="feature-title">AI Interviewer</h3>
              <p className="feature-text">
                Умный интервьюер задаёт вопросы, помогает подсказками и анализирует решения
              </p>
            </div>

            <div className="feature">
              <div className="feature-number">03</div>
              <h3 className="feature-title">Skill Radar</h3>
              <p className="feature-text">
                Детальная карта навыков с оценкой по 5 критериям: алгоритмы, архитектура, код
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Start Section */}
      <section id="start" className="start">
        <div className="container">
          <div className="start-card">
            <div className="tabs-header">
              <button 
                className={`tab-btn ${activeTab === 'quick' ? 'active' : ''}`}
                onClick={() => setActiveTab('quick')}
              >
                Быстрый старт
              </button>
              <button 
                className={`tab-btn ${activeTab === 'cv' ? 'active' : ''}`}
                onClick={() => setActiveTab('cv')}
              >
                Анализ резюме
              </button>
            </div>

            {activeTab === 'quick' && (
              <div className="form">
                <div className="form-row">
                  <div className="form-field">
                    <label>Имя (опционально)</label>
                    <input
                      type="text"
                      placeholder="Иван Иванов"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>

                  <div className="form-field">
                    <label>Email (опционально)</label>
                    <input
                      type="email"
                      placeholder="ivan@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-field">
                    <label>Уровень</label>
                    <select value={selectedLevel} onChange={(e) => setSelectedLevel(e.target.value)}>
                      <option value="intern">Intern (Стажёр)</option>
                      <option value="junior">Junior</option>
                      <option value="junior+">Junior+</option>
                      <option value="middle">Middle</option>
                      <option value="middle+">Middle+</option>
                      <option value="senior">Senior</option>
                    </select>
                  </div>

                  <div className="form-field">
                    <label>Направление</label>
                    <select value={selectedDirection} onChange={(e) => setSelectedDirection(e.target.value)}>
                      <option value="backend">Backend Developer</option>
                      <option value="frontend">Frontend Developer</option>
                      <option value="fullstack">Fullstack Developer</option>
                      <option value="algorithms">Algorithms & DS</option>
                      <option value="ml">Machine Learning Engineer</option>
                      <option value="data-science">Data Scientist</option>
                      <option value="data-engineer">Data Engineer</option>
                      <option value="devops">DevOps Engineer</option>
                      <option value="mobile">Mobile Developer</option>
                    </select>
                  </div>
                </div>

                <button 
                  className="btn-primary-large"
                  onClick={startInterview}
                  disabled={loading}
                >
                  {loading ? 'Загрузка...' : 'Начать собеседование →'}
                </button>

                <p className="form-hint">Интервью займёт примерно 30-45 минут</p>
              </div>
            )}

            {activeTab === 'cv' && (
              <div className="form">
                <div className="form-field">
                  <label>Текст резюме</label>
                  <textarea
                    placeholder="Вставьте текст резюме...

Пример: Алан Халибеков, изучаю ML с 1 курса, сейчас на 3 курсе. В конце 2 курса прошел стажировку в Яндекс, предложили грейд джуна..."
                    value={cvText}
                    onChange={(e) => setCvText(e.target.value)}
                    rows={10}
                  />
                </div>

                <button
                  className="btn-primary-large"
                  onClick={analyzeCV}
                  disabled={loading || !cvText.trim()}
                >
                  {loading ? 'Анализ резюме...' : 'Проанализировать резюме →'}
                </button>

                {suggestion && (
                  <div className="suggestion">
                    <div className="suggestion-header">
                      <h3>Рекомендация AI</h3>
                      <div className="suggestion-badges">
                        <span className="badge">{suggestion.suggested_level.toUpperCase()}</span>
                        <span className="badge">{suggestion.suggested_direction}</span>
                      </div>
                    </div>
                    
                    {suggestion.key_technologies.length > 0 && (
                      <div className="tech-stack">
                        {suggestion.key_technologies.slice(0, 5).map((tech: string, i: number) => (
                          <span key={i} className="tech-badge">{tech}</span>
                        ))}
                      </div>
                    )}
                    
                    <p className="suggestion-text">{suggestion.reasoning}</p>
                    
                    <button
                      className="btn-primary-large"
                      onClick={startInterview}
                      disabled={loading}
                    >
                      Начать с этими настройками →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>Powered by T1 SciBox LLM</p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage

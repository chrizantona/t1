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
    <div className="landing-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">VibeCode</h1>
          <h2 className="hero-subtitle">Умное техническое собеседование</h2>
          <p className="hero-description">
            AI-платформа для проведения технических интервью с адаптивными задачами,
            умным ассистентом и объективной оценкой навыков
          </p>
          <div className="hero-badge">
            <span>⚡</span>
            Powered by T1 SciBox LLM
          </div>
        </div>
      </section>

      <div className="main-content">
        {/* Features */}
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3 className="feature-title">CV Analysis</h3>
            <p className="feature-description">
              Загрузите резюме, и AI автоматически определит оптимальный уровень сложности
              и направление собеседования
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3 className="feature-title">AI Interviewer</h3>
            <p className="feature-description">
              Умный интервьюер на базе нейросети задаёт вопросы, помогает подсказками
              и анализирует ваши решения
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3 className="feature-title">Skill Radar</h3>
            <p className="feature-description">
              Детальная карта навыков с оценкой по 5 критериям: алгоритмы, архитектура,
              код, дебаг, коммуникация
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3 className="feature-title">Anti-Cheat</h3>
            <p className="feature-description">
              Система отслеживания подозрительных действий и оценки похожести кода
              на AI-генерацию
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">💡</div>
            <h3 className="feature-title">Hint System</h3>
            <p className="feature-description">
              Подсказки разного уровня помогают не застрять, но влияют на итоговый балл
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3 className="feature-title">Progress Tracking</h3>
            <p className="feature-description">
              Отслеживайте свой прогресс между грейдами и получайте персональные рекомендации
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="stats-section">
          <div className="stat-item">
            <div className="stat-number">30-45</div>
            <div className="stat-text">минут</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">2-3</div>
            <div className="stat-text">задачи</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">5</div>
            <div className="stat-text">критериев оценки</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">100%</div>
            <div className="stat-text">AI-powered</div>
          </div>
        </div>

        {/* Start Interview Section */}
        <section className="start-section">
          <h2 className="section-title">Начать собеседование</h2>
          <p className="section-subtitle">Выберите способ: быстрый старт или анализ резюме</p>

          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'quick' ? 'active' : ''}`}
              onClick={() => setActiveTab('quick')}
            >
              ⚡ Быстрый старт
            </button>
            <button 
              className={`tab ${activeTab === 'cv' ? 'active' : ''}`}
              onClick={() => setActiveTab('cv')}
            >
              📄 Анализ резюме
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'quick' ? (
              <div>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">
                      Имя <span className="form-label-optional">(опционально)</span>
                    </label>
                    <input
                      type="text"
                      placeholder="Иван Иванов"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Email <span className="form-label-optional">(опционально)</span>
                    </label>
                    <input
                      type="email"
                      placeholder="ivan@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Уровень</label>
                    <select
                      value={selectedLevel}
                      onChange={(e) => setSelectedLevel(e.target.value)}
                    >
                      <option value="junior">Junior</option>
                      <option value="middle">Middle</option>
                      <option value="middle+">Middle+</option>
                      <option value="senior">Senior</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Направление</label>
                    <select
                      value={selectedDirection}
                      onChange={(e) => setSelectedDirection(e.target.value)}
                    >
                      <option value="backend">Backend</option>
                      <option value="frontend">Frontend</option>
                      <option value="algorithms">Algorithms</option>
                      <option value="fullstack">Fullstack</option>
                    </select>
                  </div>
                </div>

                <button
                  className="cta-button"
                  onClick={startInterview}
                  disabled={loading}
                >
                  {loading ? '⏳ Загрузка...' : '🚀 Начать собеседование'}
                </button>

                <div className="time-estimate">
                  <span>⏱️</span>
                  Интервью займёт примерно 30-45 минут
                </div>
              </div>
            ) : (
              <div>
                <div className="cv-upload-area">
                  <div className="cv-upload-icon">📄</div>
                  <h3 style={{ marginBottom: '12px', color: 'var(--color-text-primary)' }}>
                    Загрузите текст резюме
                  </h3>
                  <p style={{ color: 'var(--color-text-grey)', marginBottom: '24px' }}>
                    AI проанализирует опыт и автоматически подберёт уровень сложности
                  </p>
                  <textarea
                    placeholder="Вставьте текст резюме сюда...

Пример: Senior Backend Developer с 5+ годами опыта в Python, Django, PostgreSQL..."
                    value={cvText}
                    onChange={(e) => setCvText(e.target.value)}
                    rows={8}
                    style={{ 
                      width: '100%', 
                      padding: '20px',
                      borderRadius: '12px',
                      border: '2px solid var(--color-border)',
                      fontSize: '1rem',
                      fontFamily: 'inherit',
                      resize: 'vertical'
                    }}
                  />
                </div>

                <button
                  className="cta-button"
                  onClick={analyzeCV}
                  disabled={loading || !cvText.trim()}
                  style={{ marginTop: '24px' }}
                >
                  {loading ? '🔄 Анализ резюме...' : '🎯 Проанализировать резюме'}
                </button>

                {suggestion && (
                  <div className="suggestion-card">
                    <div className="suggestion-header">
                      <span className="suggestion-icon">🎯</span>
                      <div>
                        <h3 style={{ margin: 0, color: 'var(--color-primary)', fontSize: '1.5rem' }}>
                          AI рекомендация
                        </h3>
                        <p style={{ margin: '4px 0 0', color: 'var(--color-text-grey)' }}>
                          Анализ завершён успешно
                        </p>
                      </div>
                    </div>

                    <div className="suggestion-stats">
                      <div className="stat-box">
                        <div className="stat-label">Рекомендуемый уровень</div>
                        <div className="stat-value">{suggestion.suggested_level.toUpperCase()}</div>
                      </div>

                      <div className="stat-box">
                        <div className="stat-label">Направление</div>
                        <div className="stat-value">{suggestion.suggested_direction}</div>
                      </div>

                      {suggestion.years_of_experience && (
                        <div className="stat-box">
                          <div className="stat-label">Опыт</div>
                          <div className="stat-value">{suggestion.years_of_experience} лет</div>
                        </div>
                      )}
                    </div>

                    {suggestion.key_technologies?.length > 0 && (
                      <div>
                        <div style={{ 
                          fontSize: '0.9rem', 
                          color: 'var(--color-text-grey)', 
                          marginBottom: '12px',
                          fontWeight: 600
                        }}>
                          Ключевые технологии:
                        </div>
                        <div className="tech-tags">
                          {suggestion.key_technologies.map((tech: string, i: number) => (
                            <span key={i} className="tech-tag">
                              {tech}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {suggestion.reasoning && (
                      <div style={{ 
                        padding: '20px',
                        background: 'white',
                        borderRadius: '12px',
                        borderLeft: '4px solid var(--color-primary)',
                        marginBottom: '24px'
                      }}>
                        <div style={{ 
                          fontSize: '0.9rem',
                          fontWeight: 600,
                          color: 'var(--color-text-grey)',
                          marginBottom: '8px'
                        }}>
                          💡 Обоснование:
                        </div>
                        <p style={{ margin: 0, color: 'var(--color-text-grey)', lineHeight: '1.6' }}>
                          {suggestion.reasoning}
                        </p>
                      </div>
                    )}

                    <button
                      className="cta-button"
                      onClick={startInterview}
                      disabled={loading}
                    >
                      {loading ? '⏳ Загрузка...' : '🚀 Начать с рекомендованными параметрами'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default LandingPage

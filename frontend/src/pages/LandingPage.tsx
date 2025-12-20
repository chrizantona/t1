import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { interviewAPI, resumeAPI, vacancyAPI } from '../api/client'
import '../styles/landing.css'

interface Vacancy {
  id: string
  title: string
  description: string
  company: string
  direction: string
  grade_required: string
  skills: any[]
}

interface VacancyMatch {
  vacancy: Vacancy
  matchScore: number
  matchReasons: string[]
}

function LandingPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [cvText, setCvText] = useState('')
  const [suggestion, setSuggestion] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'vacancy' | 'cv'>('vacancy')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('file')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Vacancies
  const [vacancies, setVacancies] = useState<Vacancy[]>([])
  const [selectedVacancy, setSelectedVacancy] = useState<Vacancy | null>(null)
  const [vacanciesLoading, setVacanciesLoading] = useState(true)
  
  // CV-Vacancy matching
  const [vacancyMatches, setVacancyMatches] = useState<VacancyMatch[]>([])
  const [showMatches, setShowMatches] = useState(false)
  
  // Launch animation
  const [showLaunch, setShowLaunch] = useState(false)
  const [launchPhase, setLaunchPhase] = useState<'init' | 'scanning' | 'generating' | 'ready' | 'go'>('init')
  const [interviewId, setInterviewId] = useState<number | null>(null)

  // Load vacancies on mount
  useEffect(() => {
    loadVacancies()
  }, [])

  const loadVacancies = async () => {
    try {
      const data = await vacancyAPI.listVacancies()
      setVacancies(data)
      if (data.length > 0) {
        setSelectedVacancy(data[0])
      }
    } catch (error) {
      console.error('Failed to load vacancies:', error)
      setVacancies([
        { id: 'ml_engineer_junior', title: 'ML Engineer Junior', description: 'Machine Learning разработка', company: 'T1 Digital', direction: 'ML', grade_required: 'junior', skills: [] },
        { id: 'backend_developer_middle', title: 'Backend Developer Middle', description: 'Высоконагруженные сервисы', company: 'T1 Digital', direction: 'Backend', grade_required: 'middle', skills: [] },
        { id: 'frontend_developer_junior', title: 'Frontend Developer Junior', description: 'React/TypeScript интерфейсы', company: 'T1 Digital', direction: 'Frontend', grade_required: 'junior', skills: [] },
      ])
    } finally {
      setVacanciesLoading(false)
    }
  }

  // Calculate vacancy match based on CV analysis
  const calculateVacancyMatches = (cvAnalysis: any) => {
    const matches: VacancyMatch[] = vacancies.map(vacancy => {
      let score = 0
      const reasons: string[] = []
      
      // Direction match (40 points)
      const cvDirection = cvAnalysis.suggested_direction?.toLowerCase() || ''
      const vacancyDirection = vacancy.direction.toLowerCase()
      if (cvDirection === vacancyDirection || 
          (cvDirection === 'backend' && vacancyDirection === 'backend') ||
          (cvDirection === 'ml' && vacancyDirection === 'ml') ||
          (cvDirection === 'frontend' && vacancyDirection === 'frontend') ||
          (cvDirection === 'data' && (vacancyDirection === 'data' || vacancyDirection === 'ml'))) {
        score += 40
        reasons.push(`Направление совпадает: ${vacancy.direction}`)
      } else if (cvDirection.includes(vacancyDirection) || vacancyDirection.includes(cvDirection)) {
        score += 20
        reasons.push(`Смежное направление`)
      }
      
      // Grade match (30 points)
      const cvGrade = cvAnalysis.suggested_level?.toLowerCase() || 'junior'
      const vacancyGrade = vacancy.grade_required.toLowerCase()
      if (cvGrade === vacancyGrade) {
        score += 30
        reasons.push(`Уровень совпадает: ${vacancyGrade}`)
      } else if (
        (cvGrade === 'middle' && vacancyGrade === 'junior') ||
        (cvGrade === 'senior' && (vacancyGrade === 'junior' || vacancyGrade === 'middle'))
      ) {
        score += 25
        reasons.push(`Уровень выше требуемого`)
      } else if (
        (cvGrade === 'junior' && vacancyGrade === 'middle') ||
        (cvGrade === 'middle' && vacancyGrade === 'senior')
      ) {
        score += 10
        reasons.push(`Можно попробовать на рост`)
      }
      
      // Technology match (30 points)
      const cvTechs = (cvAnalysis.key_technologies || []).map((t: string) => t.toLowerCase())
      const techKeywords: Record<string, string[]> = {
        'ML': ['python', 'tensorflow', 'pytorch', 'sklearn', 'ml', 'machine learning', 'pandas', 'numpy'],
        'Backend': ['python', 'java', 'go', 'node', 'fastapi', 'django', 'postgresql', 'redis', 'kafka'],
        'Frontend': ['react', 'typescript', 'javascript', 'vue', 'angular', 'css', 'html'],
        'DevOps': ['docker', 'kubernetes', 'ci/cd', 'aws', 'terraform', 'linux', 'bash'],
        'Data': ['sql', 'python', 'spark', 'airflow', 'etl', 'pandas', 'postgresql']
      }
      
      const relevantTechs = techKeywords[vacancy.direction] || []
      const matchedTechs = cvTechs.filter((t: string) => 
        relevantTechs.some(rt => t.includes(rt) || rt.includes(t))
      )
      
      if (matchedTechs.length > 0) {
        const techScore = Math.min(30, matchedTechs.length * 10)
        score += techScore
        reasons.push(`Технологии: ${matchedTechs.slice(0, 3).join(', ')}`)
      }
      
      return {
        vacancy,
        matchScore: Math.min(100, score),
        matchReasons: reasons
      }
    })
    
    // Sort by score
    return matches.sort((a, b) => b.matchScore - a.matchScore)
  }

  const validateAndSetFile = (file: File) => {
    const allowedTypes = ['application/pdf', 'text/plain']
    const allowedExtensions = ['.pdf', '.txt']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExt)) {
      alert('Используйте PDF или TXT')
      return false
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('Максимум 10MB')
      return false
    }
    
    setSelectedFile(file)
    setSuggestion(null)
    setShowMatches(false)
    return true
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) validateAndSetFile(file)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files?.[0]) validateAndSetFile(e.dataTransfer.files[0])
  }

  const analyzeCV = async () => {
    setLoading(true)
    try {
      let result
      if (uploadMode === 'file' && selectedFile) {
        result = await resumeAPI.uploadCV(selectedFile)
      } else if (uploadMode === 'text' && cvText.trim()) {
        result = await resumeAPI.analyzeCV(cvText)
      } else {
        alert('Загрузите файл или введите текст резюме')
        setLoading(false)
        return
      }
      setSuggestion(result)
      
      // Calculate vacancy matches
      const matches = calculateVacancyMatches(result)
      setVacancyMatches(matches)
      setShowMatches(true)
      
      // Auto-select best matching vacancy
      if (matches.length > 0 && matches[0].matchScore >= 50) {
        setSelectedVacancy(matches[0].vacancy)
      }
      
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Ошибка анализа')
    } finally {
      setLoading(false)
    }
  }

  // Launch sequence animation
  useEffect(() => {
    if (!showLaunch) return
    
    const sequence = async () => {
      setLaunchPhase('scanning')
      await new Promise(r => setTimeout(r, 1500))
      setLaunchPhase('generating')
      await new Promise(r => setTimeout(r, 2000))
      setLaunchPhase('ready')
      await new Promise(r => setTimeout(r, 1000))
      setLaunchPhase('go')
      await new Promise(r => setTimeout(r, 800))
      if (interviewId) navigate(`/interview/${interviewId}`)
    }
    
    sequence()
  }, [showLaunch, interviewId, navigate])

  const startInterview = async () => {
    if (!selectedVacancy) {
      alert('Выберите вакансию')
      return
    }
    
    setLoading(true)
    
    try {
      const payload = {
        candidate_name: name || undefined,
        candidate_email: email || undefined,
        selected_level: selectedVacancy.grade_required,
        direction: selectedVacancy.direction.toLowerCase(),
        cv_text: cvText || undefined,
        vacancy_id: selectedVacancy.id
      }
      
      const interview = await interviewAPI.startInterview(payload)
      setInterviewId(interview.id)
      setShowLaunch(true)
      
    } catch (error: any) {
      console.error('Failed to start:', error)
      alert(`Ошибка: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const startWithMatch = async (match: VacancyMatch) => {
    setSelectedVacancy(match.vacancy)
    
    setLoading(true)
    
    try {
      const payload = {
        candidate_name: name || undefined,
        candidate_email: email || undefined,
        selected_level: suggestion?.suggested_level || match.vacancy.grade_required,
        direction: match.vacancy.direction.toLowerCase(),
        cv_text: cvText || undefined,
        vacancy_id: match.vacancy.id
      }
      
      const interview = await interviewAPI.startInterview(payload)
      setInterviewId(interview.id)
      setShowLaunch(true)
      
    } catch (error: any) {
      alert(`Ошибка: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="landing-page">
      {/* Launch Animation Overlay */}
      {showLaunch && (
        <div className="launch-overlay">
          <div className="launch-container">
            <div className="launch-bg">
              <div className="launch-grid"></div>
              <div className="launch-glow"></div>
            </div>
            
            <div className="launch-content">
              {launchPhase === 'scanning' && (
                <>
                  <div className="launch-icon scanning">
                    <div className="scan-line"></div>
                  </div>
                  <h2 className="launch-title">Анализ профиля</h2>
                  <p className="launch-subtitle">Подбираем задачи под ваш уровень...</p>
                </>
              )}
              
              {launchPhase === 'generating' && (
                <>
                  <div className="launch-icon generating">
                    <div className="code-rain">
                      {[...Array(20)].map((_, i) => (
                        <span key={i} style={{animationDelay: `${i * 0.1}s`}}>
                          {['0', '1', '{', '}', '(', ')', ';', '=', '+', '-'][i % 10]}
                        </span>
                      ))}
                    </div>
                  </div>
                  <h2 className="launch-title">Генерация задач</h2>
                  <p className="launch-subtitle">AI формирует персональное интервью...</p>
                  <div className="launch-progress">
                    <div className="launch-progress-bar"></div>
                  </div>
                </>
              )}
              
              {launchPhase === 'ready' && (
                <>
                  <div className="launch-icon ready">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 6L9 17l-5-5"/>
                    </svg>
                  </div>
                  <h2 className="launch-title">Готово!</h2>
                  <p className="launch-subtitle">Интервью подготовлено</p>
                </>
              )}
              
              {launchPhase === 'go' && (
                <div className="launch-go">
                  <span>START</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="header-container">
          <div className="logo">
            <div className="logo-mark">V</div>
            <span className="logo-text">VibeCode</span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-badge">AI-Powered Technical Interviews</div>
          <h1 className="hero-title">
            Проходи собеседование<br/>
            <span className="gradient-text">с умным AI</span>
          </h1>
          <p className="hero-subtitle">
            Адаптивные задачи, честная оценка навыков, мгновенный фидбек
          </p>
        </div>
      </section>

      {/* Main Section */}
      <section className="main-section">
        <div className="container">
          <div className="tabs-wrapper">
            <div className="tabs-header">
              <button 
                className={`tab-btn ${activeTab === 'vacancy' ? 'active' : ''}`}
                onClick={() => setActiveTab('vacancy')}
              >
                <span className="tab-icon">💼</span>
                Выбрать вакансию
              </button>
              <button 
                className={`tab-btn ${activeTab === 'cv' ? 'active' : ''}`}
                onClick={() => setActiveTab('cv')}
              >
                <span className="tab-icon">📄</span>
                Загрузить резюме
              </button>
            </div>

            {activeTab === 'vacancy' && (
              <div className="tab-content">
                {/* Vacancy List */}
                <div className="vacancy-section">
                  <h3 className="section-title">Доступные позиции</h3>
                  
                  {vacanciesLoading ? (
                    <div className="loading-vacancies">Загрузка вакансий...</div>
                  ) : (
                    <div className="vacancy-grid">
                      {vacancies.map(vacancy => (
                        <div 
                          key={vacancy.id}
                          className={`vacancy-card ${selectedVacancy?.id === vacancy.id ? 'selected' : ''}`}
                          onClick={() => setSelectedVacancy(vacancy)}
                        >
                          <div className="vacancy-header">
                            <span className="vacancy-company">{vacancy.company}</span>
                            <span className={`vacancy-grade grade-${vacancy.grade_required}`}>
                              {vacancy.grade_required.toUpperCase()}
                            </span>
                          </div>
                          <h4 className="vacancy-title">{vacancy.title}</h4>
                          <p className="vacancy-desc">{vacancy.description}</p>
                          <div className="vacancy-direction">{vacancy.direction}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Candidate Info */}
                <div className="info-section">
                  <div className="form-row">
                    <div className="form-field">
                      <label>Имя</label>
                      <input
                        type="text"
                        placeholder="Иван Иванов"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                      />
                    </div>
                    <div className="form-field">
                      <label>Email</label>
                      <input
                        type="email"
                        placeholder="ivan@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <button 
                  className="btn-start"
                  onClick={startInterview}
                  disabled={loading || !selectedVacancy}
                >
                  {loading ? (
                    <span className="btn-loading">Загрузка...</span>
                  ) : (
                    <>
                      <span>Начать интервью</span>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14M12 5l7 7-7 7"/>
                      </svg>
                    </>
                  )}
                </button>
              </div>
            )}

            {activeTab === 'cv' && (
              <div className="tab-content">
                <div className="upload-mode-toggle">
                  <button
                    className={`toggle-btn ${uploadMode === 'file' ? 'active' : ''}`}
                    onClick={() => setUploadMode('file')}
                  >
                    Загрузить файл
                  </button>
                  <button
                    className={`toggle-btn ${uploadMode === 'text' ? 'active' : ''}`}
                    onClick={() => setUploadMode('text')}
                  >
                    Вставить текст
                  </button>
                </div>

                {uploadMode === 'file' ? (
                  <div 
                    className={`file-drop-zone ${selectedFile ? 'has-file' : ''} ${isDragging ? 'dragging' : ''}`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.txt"
                      onChange={handleFileSelect}
                      style={{ display: 'none' }}
                    />
                    {selectedFile ? (
                      <div className="file-info">
                        <span className="file-icon">📄</span>
                        <span className="file-name">{selectedFile.name}</span>
                        <button
                          className="file-remove"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedFile(null)
                            setSuggestion(null)
                            setShowMatches(false)
                          }}
                        >×</button>
                      </div>
                    ) : (
                      <div className="drop-placeholder">
                        <div className="drop-icon">📤</div>
                        <p>Перетащите файл или нажмите для выбора</p>
                        <span>PDF или TXT, до 10MB</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <textarea
                    className="cv-textarea"
                    placeholder="Вставьте текст резюме..."
                    value={cvText}
                    onChange={(e) => {
                      setCvText(e.target.value)
                      setShowMatches(false)
                    }}
                    rows={8}
                  />
                )}

                <button
                  className="btn-analyze"
                  onClick={analyzeCV}
                  disabled={loading || (uploadMode === 'file' ? !selectedFile : !cvText.trim())}
                >
                  {loading ? 'Анализ...' : '🔍 Проанализировать и подобрать вакансии'}
                </button>

                {/* CV Analysis Result */}
                {suggestion && (
                  <div className="cv-result">
                    <div className="cv-result-header">
                      <h3>Ваш профиль</h3>
                      <div className="cv-badges">
                        <span className="badge grade">{suggestion.suggested_level?.toUpperCase()}</span>
                        <span className="badge direction">{suggestion.suggested_direction}</span>
                        {suggestion.years_of_experience && (
                          <span className="badge years">{suggestion.years_of_experience} лет опыта</span>
                        )}
                      </div>
                    </div>
                    
                    {suggestion.key_technologies?.length > 0 && (
                      <div className="tech-tags">
                        {suggestion.key_technologies.slice(0, 8).map((tech: string, i: number) => (
                          <span key={i} className="tech-tag">{tech}</span>
                        ))}
                      </div>
                    )}
                    
                    <p className="cv-reasoning">{suggestion.reasoning}</p>
                  </div>
                )}

                {/* Vacancy Matches */}
                {showMatches && vacancyMatches.length > 0 && (
                  <div className="vacancy-matches">
                    <h3 className="section-title">🎯 Подходящие вакансии</h3>
                    <div className="matches-grid">
                      {vacancyMatches.map((match, i) => (
                        <div 
                          key={match.vacancy.id}
                          className={`match-card ${i === 0 ? 'best-match' : ''} ${selectedVacancy?.id === match.vacancy.id ? 'selected' : ''}`}
                          onClick={() => setSelectedVacancy(match.vacancy)}
                        >
                          {i === 0 && <div className="best-badge">Лучшее совпадение</div>}
                          <div className="match-header">
                            <h4>{match.vacancy.title}</h4>
                            <div className="match-score">
                              <span className="score-value">{match.matchScore}%</span>
                              <div className="score-bar">
                                <div 
                                  className="score-fill" 
                                  style={{width: `${match.matchScore}%`}}
                                ></div>
                              </div>
                            </div>
                          </div>
                          <div className="match-reasons">
                            {match.matchReasons.map((reason, j) => (
                              <span key={j} className="reason-tag">✓ {reason}</span>
                            ))}
                          </div>
                          <button 
                            className="btn-start-match"
                            onClick={(e) => {
                              e.stopPropagation()
                              startWithMatch(match)
                            }}
                            disabled={loading}
                          >
                            Начать интервью →
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>Powered by T1 SciBox LLM</p>
      </footer>
    </div>
  )
}

export default LandingPage

// пидормот

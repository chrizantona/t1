import { useState, useRef } from 'react'
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('file')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [showInfoModal, setShowInfoModal] = useState(false)

  const validateAndSetFile = (file: File) => {
    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain']
    const allowedExtensions = ['.pdf', '.txt']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExt)) {
      alert('Неподдерживаемый формат файла. Используйте PDF или TXT.')
      return false
    }
    
    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      alert('Файл слишком большой. Максимальный размер: 10MB')
      return false
    }
    
    setSelectedFile(file)
    setSuggestion(null)
    return true
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      validateAndSetFile(file)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      validateAndSetFile(files[0])
    }
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
        alert('Пожалуйста, загрузите файл или введите текст резюме')
        setLoading(false)
        return
      }
      
      setSuggestion(result)
      setSelectedLevel(result.suggested_level)
      setSelectedDirection(result.suggested_direction)
    } catch (error: any) {
      console.error('CV analysis failed:', error)
      const errorMessage = error.response?.data?.detail || 'Не удалось проанализировать резюме'
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // Show info modal first
  const handleStartClick = () => {
    setShowInfoModal(true)
  }

  // Actually start the interview after confirmation
  const confirmAndStartInterview = async () => {
    setShowInfoModal(false)
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
      // Use V1 API (more stable)
      const interview = await interviewAPI.startInterview(payload)
      // Navigate directly to interview page
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
                  onClick={handleStartClick}
                  disabled={loading}
                >
                  {loading ? 'Загрузка...' : 'Начать собеседование →'}
                </button>

                <p className="form-hint">Интервью займёт примерно 30-45 минут</p>
              </div>
            )}

            {activeTab === 'cv' && (
              <div className="form">
                {/* Upload mode toggle */}
                <div className="upload-mode-toggle">
                  <button
                    className={`toggle-btn ${uploadMode === 'file' ? 'active' : ''}`}
                    onClick={() => setUploadMode('file')}
                    type="button"
                  >
                    📄 Загрузить файл
                  </button>
                  <button
                    className={`toggle-btn ${uploadMode === 'text' ? 'active' : ''}`}
                    onClick={() => setUploadMode('text')}
                    type="button"
                  >
                    ✏️ Вставить текст
                  </button>
                </div>

                {uploadMode === 'file' ? (
                  <div className="form-field">
                    <label>Загрузить резюме (PDF или TXT)</label>
                    <div 
                      className={`file-upload-zone ${selectedFile ? 'has-file' : ''} ${isDragging ? 'dragging' : ''}`}
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.txt,application/pdf,text/plain"
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                      />
                      {selectedFile ? (
                        <div className="file-info">
                          <span className="file-icon">📄</span>
                          <span className="file-name">{selectedFile.name}</span>
                          <span className="file-size">
                            ({(selectedFile.size / 1024).toFixed(1)} KB)
                          </span>
                          <button
                            className="remove-file"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedFile(null)
                              setSuggestion(null)
                              if (fileInputRef.current) fileInputRef.current.value = ''
                            }}
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div className="upload-placeholder">
                          <span className="upload-icon">📤</span>
                          <span className="upload-text">
                            Нажмите или перетащите файл сюда
                          </span>
                          <span className="upload-hint">PDF или TXT, до 10MB</span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
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
                )}

                <button
                  className="btn-primary-large"
                  onClick={analyzeCV}
                  disabled={loading || (uploadMode === 'file' ? !selectedFile : !cvText.trim())}
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
                      onClick={handleStartClick}
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

      {/* Info Modal */}
      {showInfoModal && (
        <div className="modal-overlay" onClick={() => setShowInfoModal(false)}>
          <div className="modal-content info-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowInfoModal(false)}>✕</button>
            
            <div className="modal-header">
              <div className="modal-icon">📋</div>
              <h2>Информация о собеседовании</h2>
            </div>

            <div className="modal-body">
              <div className="info-section">
                <h3>🎯 Структура интервью</h3>
                <p>Собеседование состоит из двух частей:</p>
                <ul>
                  <li><strong>Практические задачи</strong> — решение алгоритмических задач с написанием кода</li>
                  <li><strong>Теоретические вопросы</strong> — вопросы по выбранному направлению</li>
                </ul>
              </div>

              <div className="info-section">
                <h3>⏱️ Учёт времени</h3>
                <p>Время на каждую задачу и вопрос <strong>фиксируется</strong>. Быстрые и правильные ответы оцениваются выше. Рекомендуемое время на задачу: 15-20 минут.</p>
              </div>

              <div className="info-section warning">
                <h3>🛡️ Система антиплагиата</h3>
                <p>Платформа использует <strong>AI-систему обнаружения списывания</strong>:</p>
                <ul>
                  <li>Анализ паттернов копирования кода</li>
                  <li>Отслеживание переключений между вкладками</li>
                  <li>Детекция AI-сгенерированного кода</li>
                  <li>Мониторинг аномального поведения</li>
                </ul>
                <p className="warning-text">⚠️ Нарушения влияют на итоговый Trust Score и результат собеседования</p>
              </div>

              <div className="info-section">
                <h3>💡 Подсказки</h3>
                <p>Вы можете запрашивать подсказки, но каждая <strong>уменьшает максимальный балл</strong> за задачу. Используйте их с умом!</p>
              </div>

              <div className="info-section">
                <h3>🤖 AI-ассистент</h3>
                <p>Во время интервью доступен AI-ассистент для уточняющих вопросов по условию задачи. Он не даёт готовых решений, но помогает понять задачу.</p>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowInfoModal(false)}>
                Отмена
              </button>
              <button 
                className="btn-primary-large" 
                onClick={confirmAndStartInterview}
                disabled={loading}
              >
                {loading ? 'Подготовка...' : 'Я готов, начать! →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LandingPage

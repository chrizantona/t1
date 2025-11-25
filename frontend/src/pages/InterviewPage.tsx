import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { interviewAPI } from '../api/client'
import '../styles/interview.css'

function InterviewPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  
  const [interview, setInterview] = useState<any>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0)
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<any[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [showHintPanel, setShowHintPanel] = useState(false)
  const [hintLoading, setHintLoading] = useState(false)
  const [currentHint, setCurrentHint] = useState<any>(null)
  const [showHints, setShowHints] = useState(false)
  const [hint, setHint] = useState<any>(null)
  const [hintLoading, setHintLoading] = useState(false)

  useEffect(() => {
    loadInterview()
    loadTasks()
  }, [interviewId])

  const loadInterview = async () => {
    try {
      const data = await interviewAPI.getInterview(Number(interviewId))
      setInterview(data)
    } catch (error) {
      console.error('Failed to load interview:', error)
    }
  }

  const loadTasks = async () => {
    try {
      const data = await interviewAPI.getTasks(Number(interviewId))
      setTasks(data)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const submitCode = async () => {
    if (!currentTask || !code.trim()) return
    
    setLoading(true)
    setResult(null)
    
    try {
      const submission = await interviewAPI.submitCode({
        task_id: currentTask.id,
        code,
        language,
      })
      setResult(submission)
    } catch (error) {
      console.error('Submission failed:', error)
      alert('Ошибка при отправке кода')
    } finally {
      setLoading(false)
    }
  }

  const moveToNextTask = async () => {
    if (currentTaskIndex < tasks.length - 1) {
      // Переход к следующей существующей задаче
      setCurrentTaskIndex(currentTaskIndex + 1)
      setCode('')
      setResult(null)
      setCurrentHint(null)
    } else {
      // Генерируем новую задачу через API
      try {
        const newTask = await interviewAPI.generateNextTask(Number(interviewId))
        setTasks([...tasks, newTask])
        setCurrentTaskIndex(tasks.length)
        setCode('')
        setResult(null)
        setCurrentHint(null)
      } catch (error) {
        console.error('Failed to generate next task:', error)
        if (confirm('Не удалось сгенерировать новую задачу. Завершить интервью?')) {
          completeInterview()
        }
      }
    }
  }

  const requestHint = async (level: string) => {
    if (!currentTask) return
    
    setHintLoading(true)
    try {
      const hint = await interviewAPI.requestHint({
        task_id: currentTask.id,
        hint_level: level,
        current_code: code || undefined
      })
      setCurrentHint(hint)
    } catch (error) {
      console.error('Failed to get hint:', error)
      alert('Не удалось получить подсказку')
    } finally {
      setHintLoading(false)
    }
  }

  const completeInterview = async () => {
    try {
      await interviewAPI.completeInterview(Number(interviewId))
      navigate(`/result/${interviewId}`)
    } catch (error) {
      console.error('Failed to complete interview:', error)
      alert('Ошибка при завершении интервью')
    }
  }

  const sendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return

    const userMessage = {
      role: 'user',
      content: chatInput,
      created_at: new Date().toISOString()
    }
    
    setMessages([...messages, userMessage])
    setChatInput('')
    setChatLoading(true)

    try {
      const response = await interviewAPI.sendMessage({
        interview_id: Number(interviewId),
        content: chatInput,
        task_id: currentTask?.id,
      })
      setMessages(prev => [...prev, response])
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMsg = {
        role: 'assistant',
        content: 'Извините, произошла ошибка. Попробуйте ещё раз.',
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setChatLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const requestHint = async (level: string) => {
    if (!currentTask) return
    
    setHintLoading(true)
    try {
      const response = await interviewAPI.requestHint({
        task_id: currentTask.id,
        hint_level: level,
        current_code: code
      })
      setHint(response)
    } catch (error) {
      console.error('Failed to get hint:', error)
      alert('Ошибка при получении подсказки')
    } finally {
      setHintLoading(false)
    }
  }

  if (!interview || tasks.length === 0) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '1.2rem',
        color: 'var(--color-text-grey)'
      }}>
        ⏳ Загрузка интервью...
      </div>
    )
  }

  const currentTask = tasks[currentTaskIndex]
  const totalTests = result ? result.total_visible + result.total_hidden : 0
  const passedTests = result ? result.passed_visible + result.passed_hidden : 0

  return (
    <div className="interview-container">
      {/* Header */}
      <header className="interview-header">
        <div className="header-info">
          <h1>🎯 Техническое интервью</h1>
          <div className="header-meta">
            <span>📂 {interview.direction}</span>
            <span>🎓 {interview.selected_level}</span>
            <span>⏱️ {new Date(interview.created_at).toLocaleDateString('ru-RU')}</span>
          </div>
        </div>
        
        <div className="progress-indicator">
          <span>Задача {currentTaskIndex + 1} из {tasks.length}</span>
          <div className="progress-dots">
            {tasks.map((_, index) => (
              <div
                key={index}
                className={`progress-dot ${
                  index < currentTaskIndex ? 'completed' : 
                  index === currentTaskIndex ? 'active' : ''
                }`}
              />
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="interview-main">
        {/* Task & Editor Section */}
        <div className="task-section">
          {/* Task Description */}
          <div className="task-panel">
            <div className="task-header">
              <div className="task-title-group">
                <h2>{currentTask.title}</h2>
                <span className={`task-difficulty ${currentTask.difficulty}`}>
                  {currentTask.difficulty}
                </span>
              </div>
              
              <div className="task-score">
                <div className="score-label">Максимальный балл</div>
                <div className="score-value">{currentTask.max_score}/100</div>
              </div>
            </div>

            <p className="task-description">{currentTask.description}</p>

            {currentTask.visible_tests && currentTask.visible_tests.length > 0 && (
              <div className="test-cases">
                <div className="test-cases-title">📝 Примеры тестов</div>
                {currentTask.visible_tests.slice(0, 3).map((test: any, index: number) => (
                  <div key={index} className="test-case">
                    <div>Вход: {JSON.stringify(test.input)}</div>
                    <div>Выход: {JSON.stringify(test.expected_output)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Code Editor */}
          <div className="editor-section">
            <div className="editor-toolbar">
              <div className="language-selector">
                <span>💻</span>
                <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="java">Java</option>
                  <option value="cpp">C++</option>
                </select>
              </div>
              
              <div className="editor-actions">
                <button 
                  className="btn-hint" 
                  onClick={() => setShowHints(!showHints)}
                >
                  💡 Подсказка
                </button>
                <button 
                  className="btn-submit" 
                  onClick={submitCode}
                  disabled={loading || !code.trim()}
                >
                  {loading ? '⏳ Проверка...' : '▶️ Запустить код'}
                </button>
              </div>
            </div>

            <textarea
              className="code-editor"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder={`# Напишите решение на ${language}...\n\ndef solution():\n    pass`}
              spellCheck={false}
            />

            {/* Hint Panel */}
            {showHintPanel && (
              <div style={{
                position: 'absolute',
                top: '60px',
                right: '24px',
                width: '400px',
                background: 'white',
                borderRadius: '16px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
                padding: '24px',
                zIndex: 100,
                border: '2px solid var(--color-primary)',
                animation: 'slideIn 0.3s ease'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h3 style={{ margin: 0, color: 'var(--color-primary)' }}>💡 Подсказки</h3>
                  <button 
                    onClick={() => setShowHintPanel(false)}
                    style={{ 
                      background: 'none', 
                      border: 'none', 
                      fontSize: '1.5rem', 
                      cursor: 'pointer',
                      padding: '4px 8px'
                    }}
                  >
                    ✕
                  </button>
                </div>

                {!currentHint ? (
                  <div>
                    <p style={{ color: 'var(--color-text-grey)', marginBottom: '16px', fontSize: '0.95rem' }}>
                      Выберите уровень подсказки. Каждая подсказка уменьшает максимальный балл за задачу.
                    </p>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <button
                        onClick={() => requestHint('light')}
                        disabled={hintLoading}
                        style={{
                          padding: '16px',
                          background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '12px',
                          cursor: 'pointer',
                          fontSize: '1rem',
                          fontWeight: 600,
                          transition: 'all 0.3s ease'
                        }}
                      >
                        🟢 Лёгкая подсказка (-10%)
                      </button>

                      <button
                        onClick={() => requestHint('medium')}
                        disabled={hintLoading}
                        style={{
                          padding: '16px',
                          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '12px',
                          cursor: 'pointer',
                          fontSize: '1rem',
                          fontWeight: 600
                        }}
                      >
                        🟡 Средняя подсказка (-20%)
                      </button>

                      <button
                        onClick={() => requestHint('heavy')}
                        disabled={hintLoading}
                        style={{
                          padding: '16px',
                          background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '12px',
                          cursor: 'pointer',
                          fontSize: '1rem',
                          fontWeight: 600
                        }}
                      >
                        🔴 Жёсткая подсказка (-35%)
                      </button>
                    </div>

                    {hintLoading && (
                      <p style={{ textAlign: 'center', marginTop: '16px', color: 'var(--color-text-light)' }}>
                        ⏳ Генерация подсказки...
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <div style={{
                      padding: '16px',
                      background: '#fee2e2',
                      borderRadius: '12px',
                      marginBottom: '16px',
                      border: '2px solid #ef4444',
                      color: '#991b1b',
                      fontWeight: 600
                    }}>
                      ⚠️ Штраф: -{currentHint.score_penalty}%
                      <br />
                      Новый максимум: {currentHint.new_max_score}/100
                    </div>

                    <div style={{
                      padding: '20px',
                      background: 'var(--color-bg-light)',
                      borderRadius: '12px',
                      lineHeight: '1.6',
                      color: 'var(--color-text-primary)'
                    }}>
                      {currentHint.hint_content}
                    </div>

                    <button
                      onClick={() => setCurrentHint(null)}
                      style={{
                        width: '100%',
                        marginTop: '16px',
                        padding: '12px',
                        background: 'var(--color-primary)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '10px',
                        cursor: 'pointer',
                        fontWeight: 600
                      }}
                    >
                      Получить ещё подсказку
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons - Always visible */}
          <div style={{ 
            padding: '20px 24px', 
            background: 'white',
            borderTop: '2px solid var(--color-border)',
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '12px' 
          }}>
            <button 
              className="next-task-btn" 
              onClick={moveToNextTask}
              style={{ margin: 0 }}
            >
              ➡️ Следующая задача
            </button>
            <button 
              className="next-task-btn" 
              onClick={() => {
                if (confirm('Вы уверены что хотите завершить интервью?')) {
                  completeInterview()
                }
              }}
              style={{ 
                margin: 0,
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                boxShadow: '0 4px 12px rgba(239, 68, 68, 0.3)'
              }}
            >
              🏁 Завершить интервью
            </button>
          </div>

          {/* Results */}
          {result && (
            <div className="results-panel">
              <div className="results-header">
                <span className="results-icon">
                  {passedTests === totalTests ? '✅' : '⚠️'}
                </span>
                <span>Результаты тестирования</span>
              </div>

              <div className="results-grid">
                <div className="result-box">
                  <div className="result-label">Видимые тесты</div>
                  <div className={`result-value ${
                    result.passed_visible === result.total_visible ? 'success' : 
                    result.passed_visible > 0 ? 'partial' : 'failed'
                  }`}>
                    {result.passed_visible}/{result.total_visible}
                  </div>
                </div>

                <div className="result-box">
                  <div className="result-label">Скрытые тесты</div>
                  <div className={`result-value ${
                    result.passed_hidden === result.total_hidden ? 'success' : 
                    result.passed_hidden > 0 ? 'partial' : 'failed'
                  }`}>
                    {result.passed_hidden}/{result.total_hidden}
                  </div>
                </div>

                {result.execution_time_ms && (
                  <div className="result-box">
                    <div className="result-label">Время выполнения</div>
                    <div className="result-value">{result.execution_time_ms}ms</div>
                  </div>
                )}
              </div>

              {result.error_message && (
                <div className="error-message">
                  ❌ Ошибка: {result.error_message}
                </div>
              )}

            </div>
          )}
        </div>

        {/* Chat Section */}
        <div className="chat-section">
          <div className="chat-header">
            <h2>🤖 AI Интервьюер</h2>
            <p className="chat-subtitle">
              Задавайте вопросы о задаче и получайте советы
            </p>
          </div>

          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <div className="chat-empty-icon">💬</div>
                <p>Начните диалог с AI интервьюером</p>
                <p style={{ fontSize: '0.85rem', marginTop: '8px' }}>
                  Спросите о подходе к решению или попросите разъяснить условие
                </p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className={`message ${msg.role}`}>
                  <div className="message-header">
                    <div className="message-avatar">
                      {msg.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <span className="message-author">
                      {msg.role === 'user' ? 'Вы' : 'AI Интервьюер'}
                    </span>
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))
            )}
            
            {chatLoading && (
              <div className="chat-loading">AI думает...</div>
            )}
          </div>

          <div className="chat-input">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Напишите сообщение..."
              rows={3}
            />
            <button 
              className="chat-send-btn"
              onClick={sendMessage}
              disabled={chatLoading || !chatInput.trim()}
            >
              {chatLoading ? '⏳ Отправка...' : '📤 Отправить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InterviewPage

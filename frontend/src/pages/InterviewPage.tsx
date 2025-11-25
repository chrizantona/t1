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
    } else {
      // Генерируем новую задачу через API (если нужно)
      // TODO: Добавить генерацию следующей задачи
      if (confirm('Вы решили все задачи! Завершить интервью?')) {
        completeInterview()
      }
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
                <button className="btn-hint">💡 Подсказка</button>
                <button 
                  className="btn-submit" 
                  onClick={submitCode}
                  disabled={loading || !code.trim()}
                >
                  {loading ? '⏳ Проверка...' : '▶️ Запустить'}
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

              {passedTests === totalTests && (
                <button className="next-task-btn" onClick={moveToNextTask}>
                  {currentTaskIndex < tasks.length - 1 ? 
                    '➡️ Следующая задача' : 
                    '🏁 Завершить интервью'
                  }
                </button>
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

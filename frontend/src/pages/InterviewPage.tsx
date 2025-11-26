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
  const [result, setResult] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [hintLoading, setHintLoading] = useState(false)
  const [currentHints, setCurrentHints] = useState<any[]>([])

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
      if (data.length > 0) {
        setCurrentTaskIndex(0)
      }
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const currentTask = tasks[currentTaskIndex]

  const submitCode = async () => {
    if (!currentTask || !code.trim()) return

    try {
      const submission = await interviewAPI.submitCode({
        task_id: currentTask.id,
        code: code,
        language: 'python'
      })
      setResult(submission)
      
      // Reload tasks to get updated scores
      await loadTasks()
    } catch (error) {
      console.error('Failed to submit code:', error)
      alert('Не удалось отправить код')
    }
  }

  const moveToNextTask = async () => {
    // Check if there's already a next task
    if (currentTaskIndex < tasks.length - 1) {
      setCurrentTaskIndex(currentTaskIndex + 1)
      setCode('')
      setResult(null)
      setCurrentHints([])
    } else {
      // Generate new task
      try {
        const newTask = await interviewAPI.generateNextTask(Number(interviewId))
        setTasks([...tasks, newTask])
        setCurrentTaskIndex(tasks.length)
        setCode('')
        setResult(null)
        setCurrentHints([])
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
      setCurrentHints([...currentHints, { level, ...hint }])
      
      // Reload task to get updated max_score
      await loadTasks()
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

  if (!interview || !currentTask) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Загрузка интервью...</p>
      </div>
    )
  }

  return (
    <div className="interview-container">
      {/* Header */}
      <header className="interview-header">
        <div className="header-left">
          <h1>VibeCode</h1>
          <span className="header-divider">|</span>
          <span className="interview-direction">{interview.direction}</span>
          <span className="interview-level">{interview.selected_level}</span>
        </div>
        
        <div className="header-center">
          <div className="task-nav">
            {tasks.map((_, index) => (
              <button
                key={index}
                className={`task-dot ${index === currentTaskIndex ? 'active' : ''} ${tasks[index].status === 'completed' ? 'completed' : ''}`}
                onClick={() => {
                  setCurrentTaskIndex(index)
                  setCode('')
                  setResult(null)
                  setCurrentHints([])
                }}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>
        
        <div className="header-right">
          <button className="btn-complete" onClick={completeInterview}>
            Завершить интервью
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="interview-layout">
        {/* Left Panel - Task */}
        <div className="task-panel">
          <div className="task-header">
            <h2>{currentTask.title}</h2>
            <div className="task-meta">
              <span className={`difficulty-badge ${currentTask.difficulty}`}>
                {currentTask.difficulty}
              </span>
              <span className="category-badge">{currentTask.category}</span>
              <span className="score-badge">💯 {currentTask.max_score}pts</span>
            </div>
          </div>

          <div className="task-content">
            <div className="task-description">
              {currentTask.description}
            </div>

            {currentTask.visible_tests && currentTask.visible_tests.length > 0 && (
              <div className="test-examples">
                <h3>Примеры тестов:</h3>
                {currentTask.visible_tests.map((test: any, i: number) => (
                  <div key={i} className="test-example">
                    <div className="test-label">Тест {i + 1}:</div>
                    <div className="test-io">
                      <div><strong>Вход:</strong> {JSON.stringify(test.input)}</div>
                      <div><strong>Выход:</strong> {JSON.stringify(test.expected_output)}</div>
                    </div>
                    {test.description && (
                      <div className="test-desc">{test.description}</div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Hints Section */}
            {currentHints.length > 0 && (
              <div className="hints-section">
                <h3>💡 Полученные подсказки:</h3>
                {currentHints.map((hint, i) => (
                  <div key={i} className={`hint-card hint-${hint.level}`}>
                    <div className="hint-header">
                      <span className="hint-level">
                        {hint.level === 'light' ? '🟢 Лёгкая' : hint.level === 'medium' ? '🟡 Средняя' : '🔴 Жёсткая'}
                      </span>
                      <span className="hint-penalty">-{hint.score_penalty}pts</span>
                    </div>
                    <div className="hint-content">{hint.hint_content}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Hint Buttons */}
            <div className="hint-actions">
              <h3>Нужна подсказка?</h3>
              <div className="hint-buttons">
                <button
                  className="hint-btn hint-light"
                  onClick={() => requestHint('light')}
                  disabled={hintLoading}
                >
                  🟢 Лёгкая (-10pts)
                </button>
                <button
                  className="hint-btn hint-medium"
                  onClick={() => requestHint('medium')}
                  disabled={hintLoading}
                >
                  🟡 Средняя (-20pts)
                </button>
                <button
                  className="hint-btn hint-heavy"
                  onClick={() => requestHint('heavy')}
                  disabled={hintLoading}
                >
                  🔴 Жёсткая (-35pts)
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Code & Chat */}
        <div className="code-panel">
          {/* Code Editor */}
          <div className="editor-section">
            <div className="editor-header">
              <span>Python 3</span>
              <button className="btn-run" onClick={submitCode}>
                ▶️ Запустить
              </button>
            </div>
            
            <textarea
              className="code-editor"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="def solution(...):\n    # Ваш код здесь\n    pass"
              spellCheck={false}
            />
          </div>

          {/* Result */}
          {result && (
            <div className="result-section">
              <h3>✅ Результаты:</h3>
              <div className="result-stats">
                <div className="stat">
                  <span>Видимые тесты:</span>
                  <strong className={result.passed_visible === result.total_visible ? 'success' : 'warning'}>
                    {result.passed_visible}/{result.total_visible}
                  </strong>
                </div>
                <div className="stat">
                  <span>Скрытые тесты:</span>
                  <strong className={result.passed_hidden === result.total_hidden ? 'success' : 'warning'}>
                    {result.passed_hidden}/{result.total_hidden}
                  </strong>
                </div>
                <div className="stat">
                  <span>Время:</span>
                  <strong className="score">{result.execution_time_ms ? result.execution_time_ms.toFixed(0) + 'ms' : '-'}</strong>
                </div>
              </div>

              {result.error_message && (
                <div className="error-section">
                  <h4>⚠️ Ошибка:</h4>
                  <pre>{result.error_message}</pre>
                </div>
              )}

              {!result.error_message && result.passed_visible === result.total_visible && result.passed_hidden === result.total_hidden && (
                <div className="success-section">
                  <h4>🎉 Все тесты пройдены!</h4>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="task-actions">
            <button className="btn-next" onClick={moveToNextTask}>
              Следующая задача →
            </button>
          </div>

          {/* Chat */}
          <div className="chat-section">
            <h3>💬 AI Ассистент</h3>
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`chat-message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))}
              {chatLoading && (
                <div className="chat-message assistant">
                  <div className="message-avatar">🤖</div>
                  <div className="message-content">Печатает...</div>
                </div>
              )}
            </div>
            
            <div className="chat-input">
              <input
                type="text"
                placeholder="Задайте вопрос ассистенту..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button onClick={sendMessage} disabled={chatLoading}>
                📤
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InterviewPage

import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import { interviewAPI } from '../api/client'
import '../styles/interview.css'

function InterviewPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  
  const [interview, setInterview] = useState<any>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0)
  // Store code per task: { [taskId]: code }
  const [taskCodes, setTaskCodes] = useState<Record<number, string>>({})
  const [result, setResult] = useState<any>(null)
  // Store test details for showing failures
  const [testDetails, setTestDetails] = useState<any[]>([])
  const [messages, setMessages] = useState<any[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [hintLoading, setHintLoading] = useState(false)
  const [currentHints, setCurrentHints] = useState<any[]>([])
  const [submitLoading, setSubmitLoading] = useState(false)
  const [progress, setProgress] = useState<any>(null)

  // Get current code for current task
  const currentTask = tasks[currentTaskIndex]
  const code = currentTask ? (taskCodes[currentTask.id] || '') : ''
  
  // Update code for current task
  const setCode = useCallback((newCode: string) => {
    if (currentTask) {
      setTaskCodes(prev => ({
        ...prev,
        [currentTask.id]: newCode
      }))
    }
  }, [currentTask])

  useEffect(() => {
    loadInterview()
    loadTasks()
    loadProgress()
  }, [interviewId])

  const loadInterview = async () => {
    try {
      const data = await interviewAPI.getInterviewV2(Number(interviewId))
      setInterview(data)
      
      // If interview is in theory stage, redirect
      if (data.current_stage === 'theory') {
        navigate(`/theory/${interviewId}`)
      } else if (data.current_stage === 'completed') {
        navigate(`/result/${interviewId}`)
      }
    } catch (error) {
      console.error('Failed to load interview:', error)
    }
  }

  const loadTasks = async () => {
    try {
      const data = await interviewAPI.getAllTasks(Number(interviewId))
      setTasks(data.tasks || [])
      if (data.tasks && data.tasks.length > 0) {
        setCurrentTaskIndex(0)
      }
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const loadProgress = async () => {
    try {
      const data = await interviewAPI.getProgress(Number(interviewId))
      setProgress(data)
    } catch (error) {
      console.error('Failed to load progress:', error)
    }
  }

  const submitCode = async () => {
    if (!currentTask || !code.trim()) return
    
    setSubmitLoading(true)
    setTestDetails([])

    try {
      const submission = await interviewAPI.submitCode({
        task_id: currentTask.id,
        code: code,
        language: 'python'
      })
      setResult(submission)
      
      // Use test details from API response
      if (submission.visible_test_details && submission.visible_test_details.length > 0) {
        setTestDetails(submission.visible_test_details)
      }
      
      // Reload tasks and progress to get updated scores
      await loadTasks()
      await loadProgress()
    } catch (error: any) {
      console.error('Failed to submit code:', error)
      setResult({
        error_message: error.response?.data?.detail || 'Не удалось выполнить код',
        passed_visible: 0,
        total_visible: currentTask.visible_tests?.length || 0,
        passed_hidden: 0,
        total_hidden: 0
      })
    } finally {
      setSubmitLoading(false)
    }
  }

  // Switch to specific task (from navigation)
  const switchToTask = (index: number) => {
    setCurrentTaskIndex(index)
    // Don't reset code - it's stored per task in taskCodes
    setResult(null)
    setTestDetails([])
    setCurrentHints([])
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

  const proceedToTheoryStage = async () => {
    if (!progress?.can_proceed_to_theory) {
      alert('Сначала попробуйте решить хотя бы одну задачу')
      return
    }

    try {
      await interviewAPI.proceedToTheory(Number(interviewId))
      navigate(`/theory/${interviewId}`)
    } catch (error: any) {
      console.error('Failed to proceed to theory:', error)
      alert(`Ошибка: ${error.response?.data?.detail || error.message}`)
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

  // Count completed tasks
  const completedTasks = tasks.filter(t => t.status === 'completed').length

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
            {tasks.map((task, index) => (
              <button
                key={index}
                className={`task-dot ${index === currentTaskIndex ? 'active' : ''} ${task.status === 'completed' ? 'completed' : ''} ${taskCodes[task.id] ? 'has-code' : ''}`}
                onClick={() => switchToTask(index)}
                title={`Задача ${index + 1}: ${task.difficulty}${task.status === 'completed' ? ' ✓' : ''}${taskCodes[task.id] ? ' (есть код)' : ''}`}
              >
                {task.status === 'completed' ? '✓' : index + 1}
              </button>
            ))}
          </div>
          <div className="progress-info">
            <span className="progress-text">
              Решено: {completedTasks}/{tasks.length}
            </span>
          </div>
        </div>
        
        <div className="header-right">
          <button 
            className="btn-proceed"
            onClick={proceedToTheoryStage}
            disabled={!progress?.can_proceed_to_theory}
            title={progress?.can_proceed_to_theory ? 'Перейти к теоретическим вопросам' : 'Сначала попробуйте решить задачи'}
          >
            Перейти к вопросам →
          </button>
        </div>
      </header>

      {/* Stage Indicator */}
      <div className="stage-indicator">
        <div className="stage active">
          <span className="stage-number">1</span>
          <span className="stage-name">Задачи</span>
        </div>
        <div className="stage-connector"></div>
        <div className="stage">
          <span className="stage-number">2</span>
          <span className="stage-name">Вопросы</span>
        </div>
        <div className="stage-connector"></div>
        <div className="stage">
          <span className="stage-number">3</span>
          <span className="stage-name">Результат</span>
        </div>
      </div>

      {/* Main Layout */}
      <div className="interview-layout">
        {/* Left Panel - Task */}
        <div className="task-panel">
          <div className="task-header">
            <div className="task-title-row">
              <span className="task-number">Задача {currentTask.task_order || currentTaskIndex + 1}</span>
              <h2>{currentTask.title}</h2>
            </div>
            <div className="task-meta">
              <span className={`difficulty-badge ${currentTask.difficulty}`}>
                {currentTask.difficulty === 'easy' ? '🟢 Лёгкая' : 
                 currentTask.difficulty === 'medium' ? '🟡 Средняя' : '🔴 Сложная'}
              </span>
              <span className="category-badge">{currentTask.category}</span>
              <span className="score-badge">
                {currentTask.status === 'completed' ? '✅' : '💯'} {currentTask.actual_score || 0}/{currentTask.max_score}pts
              </span>
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
              <button className="btn-run" onClick={submitCode} disabled={submitLoading}>
                {submitLoading ? '⏳ Выполняется...' : '▶️ Запустить'}
              </button>
            </div>
            
            <div className="monaco-editor-container">
              <Editor
                height="100%"
                language="python"
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  fontFamily: "'JetBrains Mono', 'Fira Code', Monaco, Menlo, 'Courier New', monospace",
                  lineNumbers: 'on',
                  tabSize: 4,
                  insertSpaces: true,
                  automaticLayout: true,
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  padding: { top: 16, bottom: 16 },
                  suggest: {
                    showKeywords: true,
                    showSnippets: true,
                  },
                  quickSuggestions: true,
                  folding: true,
                  bracketPairColorization: { enabled: true },
                }}
              />
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="result-section">
              <h3>{result.error_message ? '❌' : result.passed_visible === result.total_visible ? '✅' : '⚠️'} Результаты:</h3>
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

              {/* Show detailed test results */}
              {testDetails.length > 0 && !result.error_message && (
                <div className="test-details-section">
                  <h4>📋 Детали тестов:</h4>
                  <div className="test-details-list">
                    {testDetails.map((test, i) => (
                      <div key={i} className={`test-detail ${test.passed ? 'passed' : 'failed'}`}>
                        <div className="test-detail-header">
                          <span className="test-status-icon">{test.passed ? '✅' : '❌'}</span>
                          <span className="test-number">Тест {test.index}</span>
                          {test.description && <span className="test-description">— {test.description}</span>}
                        </div>
                        {!test.passed && (
                          <div className="test-detail-body">
                            <div className="test-io-row">
                              <span className="label">Вход:</span>
                              <code>{JSON.stringify(test.input)}</code>
                            </div>
                            <div className="test-io-row">
                              <span className="label">Ожидалось:</span>
                              <code>{JSON.stringify(test.expected)}</code>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!result.error_message && result.passed_visible === result.total_visible && result.passed_hidden === result.total_hidden && (
                <div className="success-section">
                  <h4>🎉 Все тесты пройдены!</h4>
                </div>
              )}
            </div>
          )}

          {/* Task Navigation */}
          <div className="task-actions">
            <div className="task-nav-buttons">
              {tasks.map((task, index) => (
                <button
                  key={task.id}
                  className={`task-nav-btn ${index === currentTaskIndex ? 'active' : ''} ${task.status === 'completed' ? 'completed' : ''}`}
                  onClick={() => switchToTask(index)}
                >
                  {task.status === 'completed' ? '✓' : ''} Задача {index + 1}
                  <span className="task-difficulty-mini">
                    {task.difficulty === 'easy' ? '🟢' : task.difficulty === 'medium' ? '🟡' : '🔴'}
                  </span>
                </button>
              ))}
            </div>
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

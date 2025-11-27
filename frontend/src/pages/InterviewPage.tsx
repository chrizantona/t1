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
  const [generatingTask, setGeneratingTask] = useState(false)
  const [taskCompleted, setTaskCompleted] = useState(false)
  const [generationMeta, setGenerationMeta] = useState<any>(null)
  const [showGenerationInfo, setShowGenerationInfo] = useState(false)
  const [generationSteps, setGenerationSteps] = useState<{ step: number; text: string; done: boolean }[]>([])
  
  // Solution follow-up state
  const [followupQuestion, setFollowupQuestion] = useState<any>(null)
  const [followupAnswer, setFollowupAnswer] = useState('')
  const [followupLoading, setFollowupLoading] = useState(false)
  const [followupResult, setFollowupResult] = useState<any>(null)

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
  }, [interviewId])

  // Load chat messages when switching tasks
  useEffect(() => {
    if (currentTask?.id && interviewId) {
      loadTaskChatMessages(currentTask.id)
      // Update generation meta for current task
      if (currentTask.generation_meta) {
        setGenerationMeta(currentTask.generation_meta)
      }
    }
  }, [currentTask?.id, interviewId])

  const loadInterview = async () => {
    try {
      // Try V1 API (more reliable)
      const data = await interviewAPI.getInterview(Number(interviewId))
      setInterview(data)
      
      // Check if interview is completed
      if (data.status === 'completed') {
        navigate(`/result/${interviewId}`)
      }
    } catch (error) {
      console.error('Failed to load interview:', error)
    }
  }

  const loadTasks = async () => {
    try {
      // Use V1 API to get tasks
      const tasksData = await interviewAPI.getTasks(Number(interviewId))
      const tasksList = Array.isArray(tasksData) ? tasksData : (tasksData.tasks || [])
      setTasks(tasksList)
      
      if (tasksList.length > 0) {
        setCurrentTaskIndex(0)
        // Load chat messages for first task
        if (tasksList[0]?.id) {
          loadTaskChatMessages(tasksList[0].id)
          if (tasksList[0].generation_meta) {
            setGenerationMeta(tasksList[0].generation_meta)
          }
        }
      }
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const loadTaskChatMessages = async (taskId: number) => {
    try {
      const messages = await interviewAPI.getTaskChatMessages(Number(interviewId), taskId)
      if (messages && messages.length > 0) {
        setMessages(messages)
      }
    } catch (error) {
      console.error('Failed to load task chat messages:', error)
      // Keep existing messages if load fails
    }
  }

  const submitCode = async () => {
    if (!currentTask || !code.trim()) return
    
    setSubmitLoading(true)
    setTestDetails([])
    setTaskCompleted(false)
    setFollowupQuestion(null)
    setFollowupResult(null)

    try {
      const submission = await interviewAPI.submitCode({
        task_id: currentTask.id,
        code: code,
        language: 'python'
      })
      console.log('Submission result:', submission)
      console.log('Visible:', submission.passed_visible, '/', submission.total_visible)
      console.log('Hidden:', submission.passed_hidden, '/', submission.total_hidden)
      setResult(submission)
      
      // Use test details from API response
      if (submission.visible_test_details && submission.visible_test_details.length > 0) {
        setTestDetails(submission.visible_test_details)
      }
      
      // Check if task is completed (all tests passed)
      const allPassed = submission.passed_visible === submission.total_visible && 
                       submission.passed_hidden === submission.total_hidden &&
                       !submission.error_message
      
      if (allPassed) {
        setTaskCompleted(true)
        // Generate follow-up question about the solution
        try {
          const followup = await interviewAPI.getSolutionFollowup(currentTask.id)
          if (followup && followup.question) {
            setFollowupQuestion(followup)
            // Add to chat messages
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: followup.question,
              created_at: new Date().toISOString()
            }])
          }
        } catch (e) {
          console.error('Failed to get followup question:', e)
        }
      }
      
      // Reload tasks to get updated scores
      await loadTasks()
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

  // Submit answer to followup question
  const submitFollowupAnswer = async () => {
    if (!followupQuestion || !followupAnswer.trim()) return
    
    setFollowupLoading(true)
    
    // Add user message to chat
    setMessages(prev => [...prev, {
      role: 'user',
      content: followupAnswer,
      created_at: new Date().toISOString()
    }])
    
    try {
      const result = await interviewAPI.submitFollowupAnswer(followupQuestion.followup_id, followupAnswer)
      setFollowupResult(result)
      
      // Add feedback to chat
      let feedbackContent = result.feedback || 'Ответ учтён.'
      if (result.correct_answer) {
        feedbackContent += `\n\n📚 Правильный ответ: ${result.correct_answer}`
      }
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: feedbackContent,
        created_at: new Date().toISOString()
      }])
      
      setFollowupAnswer('')
      
      // Reload tasks to see updated score
      await loadTasks()
    } catch (error) {
      console.error('Failed to submit followup answer:', error)
    } finally {
      setFollowupLoading(false)
    }
  }

  // Generate next task adaptively with generation animation
  const generateNextTask = async () => {
    if (tasks.length >= 3) {
      alert('Все задачи пройдены! Можете завершить интервью.')
      return
    }
    
    setGeneratingTask(true)
    setTaskCompleted(false)
    setShowGenerationInfo(true)
    
    // Show generation steps animation
    const steps = [
      { step: 1, text: '📊 Анализ вакансии и вашего профиля...', done: false },
      { step: 2, text: '🎯 Выбор трека и сложности...', done: false },
      { step: 3, text: '🧩 Подбор задачи под ваш уровень...', done: false },
      { step: 4, text: '💬 Формирование первого вопроса...', done: false },
    ]
    setGenerationSteps(steps)
    
    // Animate steps
    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 500))
      setGenerationSteps(prev => prev.map((s, idx) => 
        idx <= i ? { ...s, done: true } : s
      ))
    }
    
    try {
      // Use new API with metadata
      const response = await interviewAPI.generateNextTaskWithMeta(Number(interviewId))
      
      // Set generation metadata
      if (response.generation_meta) {
        setGenerationMeta(response.generation_meta)
      }
      
      // Set initial messages (opening question)
      if (response.initial_messages && response.initial_messages.length > 0) {
        const openingMessages = response.initial_messages.map((msg: any) => ({
          role: 'assistant',
          content: msg.message_text,
          created_at: new Date().toISOString()
        }))
        setMessages(openingMessages)
      }
      
      // Reload tasks and switch to the new one
      await loadTasks()
      
      // Switch to new task
      setCurrentTaskIndex(tasks.length) // Will be the index of new task
      setResult(null)
      setTestDetails([])
      setCurrentHints([])
      
    } catch (error: any) {
      console.error('Failed to generate next task:', error)
      alert(error.response?.data?.detail || 'Не удалось сгенерировать задачу')
    } finally {
      setGeneratingTask(false)
      setTimeout(() => setShowGenerationInfo(false), 2000)
    }
  }

  // Switch to specific task (from navigation)
  const switchToTask = async (index: number) => {
    setCurrentTaskIndex(index)
    // Don't reset code - it's stored per task in taskCodes
    setResult(null)
    setTestDetails([])
    setCurrentHints([])
    
    // Load chat messages for the task
    const task = tasks[index]
    if (task?.id) {
      await loadTaskChatMessages(task.id)
      if (task.generation_meta) {
        setGenerationMeta(task.generation_meta)
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

  const goToQuestions = () => {
    // Navigate directly to questions page
    navigate(`/questions/${interviewId}`)
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
            onClick={goToQuestions}
            title="Перейти к теоретическим вопросам (Часть 2)"
          >
            📚 К вопросам →
          </button>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(completedTasks / tasks.length) * 100}%` }}
          ></div>
        </div>
        <span className="progress-label">
          Решено {completedTasks} из {tasks.length} задач
        </span>
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
            
            {/* Generation Info Badge */}
            {generationMeta && (
              <div className="generation-info-badge" onClick={() => setShowGenerationInfo(!showGenerationInfo)}>
                <span className="llm-badge">🤖 LLM-подбор</span>
                <span className="toggle-info">{showGenerationInfo ? '▲' : '▼'}</span>
              </div>
            )}
          </div>
          
          {/* Generation Info Panel */}
          {showGenerationInfo && generationMeta && (
            <div className="generation-info-panel">
              <h4>📋 Как была подобрана задача:</h4>
              <div className="generation-meta-details">
                <div className="meta-row">
                  <span className="meta-label">Трек:</span>
                  <span className="meta-value">{generationMeta.track}</span>
                </div>
                <div className="meta-row">
                  <span className="meta-label">Сложность:</span>
                  <span className="meta-value">{generationMeta.difficulty}</span>
                </div>
                {generationMeta.target_skills && (
                  <div className="meta-row">
                    <span className="meta-label">Навыки:</span>
                    <span className="meta-value">{generationMeta.target_skills.join(', ')}</span>
                  </div>
                )}
              </div>
              {generationMeta.selection_reason && (
                <div className="selection-reason">
                  <h5>💡 Почему именно она:</h5>
                  <p>{generationMeta.selection_reason}</p>
                </div>
              )}
            </div>
          )}
          
          {/* Generation Steps Animation */}
          {generatingTask && generationSteps.length > 0 && (
            <div className="generation-steps">
              <h4>🔄 Подбор задачи...</h4>
              {generationSteps.map((step) => (
                <div key={step.step} className={`generation-step ${step.done ? 'done' : 'pending'}`}>
                  <span className="step-icon">{step.done ? '✓' : '○'}</span>
                  <span className="step-text">{step.text}</span>
                </div>
              ))}
            </div>
          )}

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

              {/* Success if ALL visible tests passed (hidden tests optional) */}
              {!result.error_message && result.passed_visible === result.total_visible && result.total_visible > 0 && (
                <div className="success-section">
                  <h4>
                    {result.passed_hidden === result.total_hidden 
                      ? '🎉 Все тесты пройдены!' 
                      : `✅ Публичные тесты пройдены! (скрытые: ${result.passed_hidden}/${result.total_hidden})`
                    }
                  </h4>
                  
                  {/* Follow-up question section */}
                  {followupQuestion && followupQuestion.status === 'pending' && !followupResult && (
                    <div className="followup-section">
                      <div className="followup-question">
                        <span className="followup-label">🤖 Вопрос по решению:</span>
                        <p>{followupQuestion.question}</p>
                      </div>
                      <div className="followup-input">
                        <textarea
                          placeholder="Введите ваш ответ..."
                          value={followupAnswer}
                          onChange={(e) => setFollowupAnswer(e.target.value)}
                          rows={3}
                        />
                        <button 
                          className="btn-followup-submit"
                          onClick={submitFollowupAnswer}
                          disabled={followupLoading || !followupAnswer.trim()}
                        >
                          {followupLoading ? 'Отправка...' : 'Ответить'}
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Follow-up result */}
                  {followupResult && (
                    <div className={`followup-result ${followupResult.score >= 70 ? 'good' : followupResult.score >= 40 ? 'medium' : 'poor'}`}>
                      <div className="followup-score">
                        <span className="score-label">Оценка ответа:</span>
                        <span className="score-value">{followupResult.score}/100</span>
                      </div>
                      <p className="followup-feedback">{followupResult.feedback}</p>
                      {followupResult.correct_answer && (
                        <div className="correct-answer">
                          <span>📚 Правильный ответ:</span>
                          <p>{followupResult.correct_answer}</p>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Show next task button only after answering followup or if no followup */}
                  {(!followupQuestion || followupResult || followupQuestion.status === 'answered') && tasks.length < 3 && (
                    <button 
                      className="btn-next-task"
                      onClick={generateNextTask}
                      disabled={generatingTask}
                    >
                      {generatingTask ? (
                        <>
                          <span className="generating-spinner"></span>
                          Генерация следующей задачи...
                        </>
                      ) : (
                        <>Следующая задача →</>
                      )}
                    </button>
                  )}
                  {tasks.length >= 3 && (
                    <div className="all-tasks-done">
                      <p>🎉 Все задачи пройдены!</p>
                      <button 
                        className="btn-next-task btn-to-questions"
                        onClick={goToQuestions}
                      >
                        📚 Перейти к теоретическим вопросам →
                      </button>
                    </div>
                  )}
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

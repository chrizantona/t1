import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import { interviewAPI, antiCheatAPI, voiceAPI } from '../api/client'
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

  // Anti-cheat: Tab switch detection
  const [tabSwitchCount, setTabSwitchCount] = useState(0)
  const [showTabWarning, setShowTabWarning] = useState(false)
  const [trustScore, setTrustScore] = useState(100)
  const tabSwitchCountRef = useRef(0)

  // Auto-hint on failed submission
  const [autoHint, setAutoHint] = useState<any>(null)

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Voice input state
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

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

  // Anti-cheat: Detect tab switching / Alt+Tab
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.hidden) {
        // User switched away from tab
        const newCount = tabSwitchCountRef.current + 1
        tabSwitchCountRef.current = newCount
        setTabSwitchCount(newCount)

        // Send event to backend
        if (interviewId && currentTask) {
          try {
            await antiCheatAPI.submitEvents({
              interviewId: Number(interviewId),
              events: [{
                type: 'visibility_change',
                taskId: String(currentTask.id),
                timestamp: Date.now(),
                meta: { visible: false, switchCount: newCount }
              }]
            })
          } catch (e) {
            console.error('Failed to send anti-cheat event:', e)
          }
        }

        // First time: show warning
        if (newCount === 1) {
          setShowTabWarning(true)
        } else {
          // Subsequent times: reduce trust score significantly
          const penalty = Math.min(15, 5 + newCount * 3) // Progressive penalty
          setTrustScore(prev => Math.max(0, prev - penalty))
        }
      } else {
        // User came back - send focus event
        if (interviewId && currentTask) {
          try {
            await antiCheatAPI.submitEvents({
              interviewId: Number(interviewId),
              events: [{
                type: 'visibility_change',
                taskId: String(currentTask.id),
                timestamp: Date.now(),
                meta: { visible: true }
              }]
            })
          } catch (e) {
            console.error('Failed to send anti-cheat event:', e)
          }
        }
      }
    }

    // Also detect window blur (covers more cases)
    const handleWindowBlur = () => {
      if (!document.hidden) {
        // Window lost focus but tab still visible (e.g., clicked outside browser)
        handleVisibilityChange()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('blur', handleWindowBlur)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('blur', handleWindowBlur)
    }
  }, [interviewId, currentTask])

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

  // Use ref to track current task ID to avoid stale closure
  const currentTaskIdRef = useRef<number | null>(null)
  
  // Update ref when currentTask changes
  useEffect(() => {
    currentTaskIdRef.current = currentTask?.id || null
  }, [currentTask?.id])

  const loadTasks = async () => {
    try {
      const tasksData = await interviewAPI.getTasks(Number(interviewId))
      const tasksList = Array.isArray(tasksData) ? tasksData : (tasksData.tasks || [])
      
      // Save current task ID before updating
      const savedTaskId = currentTaskIdRef.current
      
      setTasks(tasksList)
      
      // Restore position if we had a task selected
      if (savedTaskId && tasksList.length > 0) {
        const savedIdx = tasksList.findIndex((t: any) => t.id === savedTaskId)
        if (savedIdx >= 0) {
          setCurrentTaskIndex(savedIdx)
          return // Don't change anything else
        }
      }
      
      // First load - go to first task
      if (tasksList.length > 0) {
        setCurrentTaskIndex(0)
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
    setAutoHint(null)

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
      
      // Handle auto-hint on failed submission
      if (submission.auto_hint) {
        setAutoHint(submission.auto_hint)
        // Add hint to chat as assistant message
        const hintMessage = `💡 **Подсказка** (-15 баллов)\n\n${submission.auto_hint.hint_text}\n\n📝 ${submission.auto_hint.input_format_tip}\n\n⚠️ ${submission.auto_hint.common_mistake}`
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: hintMessage,
          created_at: new Date().toISOString()
        }])
      }
      
      // Check if at least 1 test passed - ask follow-up question
      const hasProgress = submission.passed_visible > 0 && !submission.error_message
      const allPassed = submission.passed_visible === submission.total_visible && 
                       submission.passed_hidden === submission.total_hidden &&
                       !submission.error_message
      
      if (allPassed) {
        setTaskCompleted(true)
        setAutoHint(null)
      }
      
      // Generate follow-up question if at least 1 test passed (not just all)
      if (hasProgress && !followupQuestion) {
        try {
          const followup = await interviewAPI.getSolutionFollowup(currentTask.id)
          if (followup && followup.question) {
            setFollowupQuestion(followup)
            // Add to chat messages
            const prefix = allPassed ? '🎉 Отлично! Все тесты пройдены!\n\n' : '👍 Хороший прогресс!\n\n'
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: prefix + followup.question,
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

  // Generate next task adaptively with FULLSCREEN generation animation
  const generateNextTask = async (skipped: boolean = false) => {
    if (tasks.length >= 3) {
      alert('Все задачи пройдены! Можете завершить интервью.')
      return
    }
    
    setGeneratingTask(true)
    setTaskCompleted(false)
    setFollowupQuestion(null)
    setFollowupResult(null)
    
    // Show generation steps animation
    const steps = [
      { step: 1, text: '📊 Анализ вашего профиля и результатов...', done: false },
      { step: 2, text: '🎯 Определение оптимальной сложности...', done: false },
      { step: 3, text: '🧩 Подбор задачи под ваш уровень...', done: false },
      { step: 4, text: '✨ Подготовка условия задачи...', done: false },
    ]
    setGenerationSteps(steps)
    
    // Animate steps with delays
    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 800))
      setGenerationSteps(prev => prev.map((s, idx) => 
        idx <= i ? { ...s, done: true } : s
      ))
    }
    
    try {
      // Use API with metadata
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
      } else {
        setMessages([])
      }
      
      // Reload tasks and switch to the new one
      const tasksData = await interviewAPI.getTasks(Number(interviewId))
      const tasksList = Array.isArray(tasksData) ? tasksData : (tasksData.tasks || [])
      setTasks(tasksList)
      
      // Switch to new task (last one)
      setCurrentTaskIndex(tasksList.length - 1)
      setResult(null)
      setTestDetails([])
      setCurrentHints([])
      setAutoHint(null)
      
      // Small delay before hiding animation
      await new Promise(resolve => setTimeout(resolve, 500))
      
    } catch (error: any) {
      console.error('Failed to generate next task:', error)
      alert(error.response?.data?.detail || 'Не удалось сгенерировать задачу')
    } finally {
      setGeneratingTask(false)
    }
  }

  // Skip current task and generate next
  const skipTask = async () => {
    if (!currentTask) return
    
    const confirmed = window.confirm(
      'Вы уверены, что хотите пропустить задачу?\n\nЗа пропущенную задачу вы получите 0 баллов.'
    )
    
    if (!confirmed) return
    
    // Mark task as skipped (0 score)
    try {
      // Submit empty solution to mark as attempted
      await interviewAPI.submitCode({
        task_id: currentTask.id,
        code: '# Задача пропущена',
        language: 'python'
      })
    } catch (e) {
      // Ignore errors
    }
    
    // Generate next task
    await generateNextTask(true)
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
    const messageText = chatInput
    setChatInput('')
    setChatLoading(true)

    try {
      // Check if there's a pending followup question - answer it instead of regular chat
      if (followupQuestion && followupQuestion.status === 'pending' && !followupResult) {
        const result = await interviewAPI.submitFollowupAnswer(followupQuestion.followup_id, messageText)
        setFollowupResult(result)
        
        // Add feedback to chat
        let feedbackContent = `📊 **Оценка ответа: ${result.score}/100**\n\n${result.feedback || 'Ответ учтён.'}`
        if (result.correct_answer) {
          feedbackContent += `\n\n📚 **Правильный ответ:** ${result.correct_answer}`
        }
        
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: feedbackContent,
          created_at: new Date().toISOString()
        }])
        
        // Reload tasks to see updated score
        await loadTasks()
      } else {
        // Regular chat message
        const response = await interviewAPI.sendMessage({
          interview_id: Number(interviewId),
          content: messageText,
          task_id: currentTask?.id,
        })
        setMessages(prev => [...prev, response])
      }
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

  // Voice recording with Cloud.ru Whisper API
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach(track => track.stop())
        
        setIsTranscribing(true)
        try {
          const result = await voiceAPI.transcribe(audioBlob)
          if (result.success && result.text) {
            // Auto-send voice message to chat
            const voiceText = result.text
            
            // Add user message with voice indicator
            const userMessage = {
              role: 'user',
              content: `🎤 ${voiceText}`,
              created_at: new Date().toISOString()
            }
            setMessages(prev => [...prev, userMessage])
            
            // Send to AI
            setIsTranscribing(false)
            setChatLoading(true)
            try {
              const response = await interviewAPI.sendMessage({
                interview_id: Number(interviewId),
                content: voiceText,
                task_id: currentTask?.id,
              })
              setMessages(prev => [...prev, response])
            } catch (e) {
              setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Извините, произошла ошибка.',
                created_at: new Date().toISOString()
              }])
            } finally {
              setChatLoading(false)
            }
          } else {
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `🎤 ${result.message || 'Не удалось распознать речь.'}`,
              created_at: new Date().toISOString()
            }])
            setIsTranscribing(false)
          }
        } catch (error) {
          console.error('Transcription error:', error)
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: '🎤 Ошибка распознавания речи.',
            created_at: new Date().toISOString()
          }])
          setIsTranscribing(false)
        }
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Failed to start recording:', error)
      alert('Не удалось получить доступ к микрофону.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
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
      {/* FULLSCREEN Task Generation Overlay */}
      {generatingTask && (
        <div className="fullscreen-generation-overlay">
          <div className="generation-content">
            <div className="generation-logo">
              <span className="logo-icon">🧠</span>
              <h1>VibeCode</h1>
            </div>
            <div className="generation-title">
              <h2>Генерация следующей задачи</h2>
              <p>Анализируем ваши результаты и подбираем оптимальную задачу...</p>
            </div>
            <div className="generation-steps-fullscreen">
              {generationSteps.map((step) => (
                <div key={step.step} className={`gen-step ${step.done ? 'done' : 'pending'}`}>
                  <div className="step-indicator">
                    {step.done ? (
                      <span className="step-check">✓</span>
                    ) : (
                      <span className="step-spinner"></span>
                    )}
                  </div>
                  <span className="step-text">{step.text}</span>
                </div>
              ))}
            </div>
            <div className="generation-progress">
              <div className="progress-bar-gen">
                <div 
                  className="progress-fill-gen" 
                  style={{ width: `${(generationSteps.filter(s => s.done).length / generationSteps.length) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Switch Warning Modal */}
      {showTabWarning && (
        <div className="tab-warning-overlay">
          <div className="tab-warning-modal">
            <div className="warning-icon">⚠️</div>
            <h2>Внимание!</h2>
            <p>
              Вы покинули страницу собеседования. 
              <br />
              <strong>Переключение вкладок отслеживается</strong> и влияет на вашу оценку доверия.
            </p>
            <p className="warning-detail">
              При повторных переключениях ваш Trust Score будет снижаться.
              <br />
              Текущий счёт: <span className="trust-value">{trustScore}</span>/100
            </p>
            <button 
              className="btn-warning-close"
              onClick={() => setShowTabWarning(false)}
            >
              Понятно, продолжить
            </button>
          </div>
        </div>
      )}

      {/* Trust Score Indicator (показываем если были переключения) */}
      {tabSwitchCount > 0 && (
        <div className={`trust-indicator ${trustScore < 70 ? 'low' : trustScore < 90 ? 'medium' : 'high'}`}>
          <span className="trust-label">🛡️ Trust Score:</span>
          <span className="trust-value">{trustScore}</span>
          {tabSwitchCount > 1 && (
            <span className="switch-count">({tabSwitchCount} переключений)</span>
          )}
        </div>
      )}

      {/* Minimal Header */}
      <header className="interview-header-minimal">
        <div className="header-left">
          <h1>VibeCode</h1>
          <div className="task-pills">
            {tasks.map((task, index) => (
              <button
                key={index}
                className={`task-pill ${index === currentTaskIndex ? 'active' : ''} ${task.status === 'completed' ? 'completed' : ''}`}
                onClick={() => switchToTask(index)}
              >
                {task.status === 'completed' ? '✓' : index + 1}
              </button>
            ))}
          </div>
        </div>
        
        <div className="header-right">
          <span className="score-display">
            {currentTask.actual_score || 0}/{currentTask.max_score} pts
          </span>
          <button 
            className="btn-sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title="Настройки и подсказки"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* Sidebar Panel */}
      <div className={`sidebar-panel ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>Панель управления</h3>
          <button className="btn-close-sidebar" onClick={() => setSidebarOpen(false)}>✕</button>
        </div>
        
        <div className="sidebar-content">
          {/* Task Info */}
          <div className="sidebar-section">
            <h4>📋 Задача {currentTaskIndex + 1}</h4>
            <div className="sidebar-meta">
              <span className={`difficulty-tag ${currentTask.difficulty}`}>
                {currentTask.difficulty === 'easy' ? '🟢 Лёгкая' : 
                 currentTask.difficulty === 'medium' ? '🟡 Средняя' : '🔴 Сложная'}
              </span>
              <span className="category-tag">{currentTask.category}</span>
            </div>
          </div>

          {/* Generation Info */}
          {generationMeta && (
            <div className="sidebar-section">
              <h4>🤖 Подбор задачи</h4>
              <p className="sidebar-text">{generationMeta.selection_reason || 'Задача подобрана под ваш уровень'}</p>
            </div>
          )}

          {/* Hints */}
          <div className="sidebar-section">
            <h4>💡 Подсказки</h4>
            {currentHints.length > 0 ? (
              <div className="hints-list">
                {currentHints.map((hint, i) => (
                  <div key={i} className="hint-item">
                    <span className="hint-badge">{hint.level}</span>
                    <p>{hint.hint_content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="hint-buttons-sidebar">
                <button onClick={() => requestHint('light')} disabled={hintLoading}>
                  🟢 Лёгкая (-10)
                </button>
                <button onClick={() => requestHint('medium')} disabled={hintLoading}>
                  🟡 Средняя (-20)
                </button>
                <button onClick={() => requestHint('heavy')} disabled={hintLoading}>
                  🔴 Сильная (-35)
                </button>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="sidebar-section">
            <h4>⚡ Действия</h4>
            <div className="sidebar-actions">
              {currentTask.status !== 'completed' && tasks.length < 3 && (
                <button className="btn-skip" onClick={skipTask} disabled={generatingTask}>
                  ⏭️ Пропустить задачу
                </button>
              )}
              <button className="btn-questions" onClick={goToQuestions}>
                📚 К теории →
              </button>
            </div>
          </div>

          {/* Trust Score */}
          {tabSwitchCount > 0 && (
            <div className="sidebar-section">
              <h4>🛡️ Trust Score</h4>
              <div className={`trust-display ${trustScore < 70 ? 'low' : trustScore < 90 ? 'medium' : 'high'}`}>
                <span className="trust-value-big">{trustScore}</span>
                <span className="trust-label-small">/100</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Overlay */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      {/* Main Layout - Clean 3-column */}
      <div className="interview-layout-clean">
        {/* Left Panel - Task Description */}
        <div className="task-panel-clean">
          <div className="task-header-clean">
            <h2>{currentTask.title}</h2>
            <span className={`difficulty-pill ${currentTask.difficulty}`}>
              {currentTask.difficulty === 'easy' ? '🟢' : currentTask.difficulty === 'medium' ? '🟡' : '🔴'}
            </span>
          </div>
          
          <div className="task-description-clean">
            {currentTask.description}
          </div>

          {/* Test Examples - Compact */}
          {currentTask.visible_tests && currentTask.visible_tests.length > 0 && (
            <div className="test-examples-clean">
              <h4>Примеры:</h4>
              {currentTask.visible_tests.slice(0, 2).map((test: any, i: number) => (
                <div key={i} className="test-example-clean">
                  <code>Вход: {JSON.stringify(test.input)}</code>
                  <code>Выход: {JSON.stringify(test.expected_output)}</code>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Center Panel - Code Editor */}
        <div className="code-panel-clean">
          <div className="editor-header-clean">
            <span>Python 3</span>
            <button className="btn-run-clean" onClick={submitCode} disabled={submitLoading}>
              {submitLoading ? '⏳' : '▶️'} {submitLoading ? 'Выполняется...' : 'Запустить'}
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
              }}
            />
          </div>
          
          {/* Compact Result */}
          {result && (
            <div className={`result-bar ${result.error_message ? 'error' : result.passed_visible === result.total_visible ? 'success' : 'partial'}`}>
              <span className="result-icon">
                {result.error_message ? '❌' : result.passed_visible === result.total_visible ? '✅' : '⚠️'}
              </span>
              <span className="result-text">
                {result.error_message ? 'Ошибка' : `Тесты: ${result.passed_visible}/${result.total_visible}`}
              </span>
              {result.execution_time_ms && <span className="result-time">{result.execution_time_ms.toFixed(0)}ms</span>}
            </div>
          )}

          {/* Next Task Button - show when tests passed */}
          {result && result.passed_visible > 0 && tasks.length < 3 && (
            <button 
              className="btn-next-task-clean"
              onClick={() => generateNextTask()}
              disabled={generatingTask}
            >
              {generatingTask ? '⏳ Генерация...' : '→ Следующая задача'}
            </button>
          )}
        </div>

        {/* Right Panel - Chat */}
        <div className="chat-panel-clean">
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
              <button 
                className={`voice-btn ${isRecording ? 'recording' : ''} ${isTranscribing ? 'transcribing' : ''}`}
                onClick={toggleRecording}
                disabled={isTranscribing || chatLoading}
                title={isRecording ? 'Остановить запись' : 'Голосовой ввод'}
              >
                {isTranscribing ? '⏳' : isRecording ? '⏹️' : '🎤'}
              </button>
              <input
                type="text"
                placeholder={isRecording ? '🔴 Говорите...' : isTranscribing ? 'Распознавание...' : 'Задайте вопрос или нажмите 🎤'}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isRecording || isTranscribing}
              />
              <button onClick={sendMessage} disabled={chatLoading || isRecording || isTranscribing || !chatInput.trim()}>
                📤
              </button>
            </div>
        </div>
      </div>
    </div>
  )
}

export default InterviewPage

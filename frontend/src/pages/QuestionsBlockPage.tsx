import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { questionBlockAPI, interviewAPI } from '../api/client'
import '../styles/questions-block.css'

interface Question {
  answer_id: number
  question_order: number
  total_questions: number
  question_text: string
  category: string
  difficulty: string
  question_type: string
  status: string
  shown_at: string | null
}

interface BlockStatus {
  block_id: number
  status: string
  total_questions: number
  current_index: number
  total_answered: number
  total_skipped: number
  total_correct: number | null
  average_score: number | null
  category_scores: Record<string, number> | null
  difficulty_scores: Record<string, number> | null
}

function QuestionsBlockPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  
  const [interview, setInterview] = useState<any>(null)
  const [blockId, setBlockId] = useState<number | null>(null)
  const [blockStatus, setBlockStatus] = useState<BlockStatus | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [skipping, setSkipping] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)
  const [showResult, setShowResult] = useState(false)
  
  // Timer state
  const [elapsedTime, setElapsedTime] = useState(0)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const questionStartRef = useRef<number>(Date.now())

  // Start timer when question is shown
  const startTimer = useCallback(() => {
    questionStartRef.current = Date.now()
    setElapsedTime(0)
    
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }
    
    timerRef.current = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - questionStartRef.current) / 1000))
    }, 1000)
  }, [])

  // Stop timer
  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Load interview info
  useEffect(() => {
    const loadInterview = async () => {
      try {
        const data = await interviewAPI.getInterview(Number(interviewId))
        setInterview(data)
      } catch (error) {
        console.error('Failed to load interview:', error)
      }
    }
    loadInterview()
  }, [interviewId])

  // Initialize or load block
  useEffect(() => {
    const initBlock = async () => {
      setLoading(true)
      try {
        // Try to get existing block
        try {
          const existingBlock = await questionBlockAPI.getBlockByInterview(Number(interviewId))
          setBlockId(existingBlock.block_id)
          setBlockStatus(existingBlock)
          
          if (existingBlock.status === 'completed') {
            navigate(`/result/${interviewId}`)
            return
          }
          
          // Load current question
          await loadCurrentQuestion(existingBlock.block_id)
        } catch {
          // No existing block, create new one
          const newBlock = await questionBlockAPI.startBlock(Number(interviewId), 20)
          setBlockId(newBlock.block_id)
          
          // Load block status
          const status = await questionBlockAPI.getBlockStatus(newBlock.block_id)
          setBlockStatus(status)
          
          // Load first question
          await loadCurrentQuestion(newBlock.block_id)
        }
      } catch (error) {
        console.error('Failed to init block:', error)
      } finally {
        setLoading(false)
      }
    }
    
    initBlock()
    
    return () => stopTimer()
  }, [interviewId, navigate, stopTimer])

  // Load current question
  const loadCurrentQuestion = async (bid: number) => {
    try {
      const question = await questionBlockAPI.getCurrentQuestion(bid)
      
      if (question.status === 'completed') {
        navigate(`/result/${interviewId}`)
        return
      }
      
      setCurrentQuestion(question)
      setAnswer('')
      setShowResult(false)
      setLastResult(null)
      startTimer()
    } catch (error) {
      console.error('Failed to load question:', error)
    }
  }

  // Submit answer
  const handleSubmit = async () => {
    if (!currentQuestion || !answer.trim() || submitting) return
    
    setSubmitting(true)
    stopTimer()
    
    try {
      const result = await questionBlockAPI.submitAnswer(currentQuestion.answer_id, answer)
      setLastResult(result)
      setShowResult(true)
      
      // Update block status
      if (blockId) {
        const status = await questionBlockAPI.getBlockStatus(blockId)
        setBlockStatus(status)
      }
      
      // Check if block completed
      if (result.block_completed) {
        setTimeout(() => {
          navigate(`/result/${interviewId}`)
        }, 2000)
      }
    } catch (error) {
      console.error('Failed to submit answer:', error)
    } finally {
      setSubmitting(false)
    }
  }

  // Skip question
  const handleSkip = async () => {
    if (!currentQuestion || skipping || submitting) return
    
    const answerId = currentQuestion.answer_id
    
    setSkipping(true)
    stopTimer()
    // Clear current question immediately to prevent double-skip
    setCurrentQuestion(null)
    
    try {
      const result = await questionBlockAPI.skipQuestion(answerId)
      
      // Update block status
      if (blockId) {
        const status = await questionBlockAPI.getBlockStatus(blockId)
        setBlockStatus(status)
      }
      
      // Check if block completed
      if (result.block_completed) {
        navigate(`/result/${interviewId}`)
        return
      }
      
      // Load next question
      await loadCurrentQuestion(blockId!)
    } catch (error) {
      console.error('Failed to skip question:', error)
      // Reload current question on error
      if (blockId) {
        await loadCurrentQuestion(blockId)
      }
    } finally {
      setSkipping(false)
    }
  }

  // Go to next question after viewing result
  const handleNext = async () => {
    if (!blockId) return
    
    if (lastResult?.block_completed) {
      navigate(`/result/${interviewId}`)
      return
    }
    
    await loadCurrentQuestion(blockId)
  }

  // Retry current question (score halved)
  const handleRetry = async () => {
    if (!lastResult?.answer_id) return
    
    setSubmitting(true)
    
    try {
      const retryResult = await questionBlockAPI.retryQuestion(lastResult.answer_id)
      
      // Update current question with retry info
      setCurrentQuestion({
        answer_id: retryResult.answer_id,
        question_order: retryResult.question_order,
        total_questions: blockStatus?.total_questions || 20,
        question_text: retryResult.question_text,
        category: retryResult.category,
        difficulty: retryResult.difficulty,
        question_type: retryResult.question_type,
        status: 'pending',
        shown_at: new Date().toISOString()
      })
      
      // Update block status
      if (blockId) {
        const status = await questionBlockAPI.getBlockStatus(blockId)
        setBlockStatus(status)
      }
      
      // Reset state for retry
      setAnswer('')
      setShowResult(false)
      setLastResult({ ...lastResult, score_multiplier: retryResult.score_multiplier })
      startTimer()
      
    } catch (error) {
      console.error('Failed to retry question:', error)
    } finally {
      setSubmitting(false)
    }
  }

  // Get difficulty badge class
  const getDifficultyClass = (difficulty: string): string => {
    switch (difficulty) {
      case 'easy': return 'difficulty-easy'
      case 'medium': return 'difficulty-medium'
      case 'hard': return 'difficulty-hard'
      default: return ''
    }
  }

  // Get difficulty label
  const getDifficultyLabel = (difficulty: string): string => {
    switch (difficulty) {
      case 'easy': return '🟢 Лёгкий'
      case 'medium': return '🟡 Средний'
      case 'hard': return '🔴 Сложный'
      default: return difficulty
    }
  }

  // Get score color class
  const getScoreClass = (score: number | null): string => {
    if (score === null) return ''
    if (score >= 70) return 'score-good'
    if (score >= 40) return 'score-medium'
    return 'score-poor'
  }

  if (loading) {
    return (
      <div className="questions-block-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Загрузка вопросов...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="questions-block-page">
      {/* Header */}
      <header className="qb-header">
        <div className="header-left">
          <h1>VibeCode</h1>
          <span className="divider">|</span>
          <span className="stage-label">Часть 2: Теория</span>
        </div>
        
        <div className="header-center">
          {interview && (
            <>
              <span className="direction-badge">{interview.direction}</span>
              <span className="level-badge">{interview.selected_level}</span>
            </>
          )}
        </div>
        
        <div className="header-right">
          <div className="timer">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{formatTime(elapsedTime)}</span>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="progress-section">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${blockStatus ? (blockStatus.current_index / blockStatus.total_questions) * 100 : 0}%` }}
          ></div>
        </div>
        <div className="progress-stats">
          <span className="progress-text">
            Вопрос {currentQuestion?.question_order || 0} из {blockStatus?.total_questions || 20}
          </span>
          <span className="stats-text">
            ✅ {blockStatus?.total_answered || 0} отвечено
            {blockStatus?.total_skipped ? ` | ⏭️ ${blockStatus.total_skipped} пропущено` : ''}
          </span>
        </div>
      </div>

      {/* Main Content */}
      <main className="qb-main">
        {showResult && lastResult ? (
          /* Result View */
          <div className="result-card">
            <div className="result-header">
              <h2>Результат</h2>
              <div className={`score-badge ${getScoreClass(lastResult.score)}`}>
                {lastResult.score !== null ? `${Math.round(lastResult.score)}%` : '—'}
              </div>
            </div>
            
            <div className="result-body">
              {lastResult.is_correct ? (
                <div className="result-status success">
                  <span className="icon">✅</span>
                  <span>Правильно!</span>
                </div>
              ) : (
                <div className="result-status error">
                  <span className="icon">❌</span>
                  <span>Неправильно</span>
                </div>
              )}
              
              {lastResult.feedback && (
                <div className="feedback-section">
                  <h4>Обратная связь:</h4>
                  <p>{lastResult.feedback}</p>
                </div>
              )}
              
              <div className="time-spent">
                <span>⏱️ Время ответа:</span>
                <strong>{lastResult.response_time_seconds ? formatTime(Math.round(lastResult.response_time_seconds)) : '—'}</strong>
              </div>
            </div>
            
            {/* Retry info */}
            {lastResult.score_multiplier && lastResult.score_multiplier < 1 && (
              <div className="retry-info">
                <span>⚠️ Попытка {lastResult.attempt_number || 1} — максимум {Math.round((lastResult.score_multiplier || 1) * 100)}% баллов</span>
              </div>
            )}
            
            <div className="result-actions">
              {!lastResult.block_completed && lastResult.can_retry && (
                <button 
                  className="btn-retry"
                  onClick={handleRetry}
                  disabled={submitting}
                >
                  🔄 Переответить ({Math.round((lastResult.score_multiplier || 1) * 50)}% макс.)
                </button>
              )}
              
              {lastResult.block_completed ? (
                <button className="btn-primary btn-large" onClick={() => navigate(`/result/${interviewId}`)}>
                  Перейти к результатам →
                </button>
              ) : (
                <button className="btn-primary btn-large" onClick={handleNext}>
                  Следующий вопрос →
                </button>
              )}
            </div>
          </div>
        ) : (skipping || submitting) ? (
          /* Loading next question */
          <div className="question-card loading-card">
            <div className="loading-question">
              <div className="loading-spinner"></div>
              <p>Загрузка следующего вопроса...</p>
            </div>
          </div>
        ) : currentQuestion ? (
          /* Question View */
          <div className="question-card">
            <div className="question-header">
              <div className="question-meta">
                <span className={`difficulty-badge ${getDifficultyClass(currentQuestion.difficulty)}`}>
                  {getDifficultyLabel(currentQuestion.difficulty)}
                </span>
                <span className="category-badge">{currentQuestion.category}</span>
                <span className="type-badge">
                  {currentQuestion.question_type === 'theory' ? '📚 Теория' : '💻 Код'}
                </span>
              </div>
              <div className="question-number">
                #{currentQuestion.question_order}
              </div>
            </div>
            
            <div className="question-body">
              <h3 className="question-text">{currentQuestion.question_text}</h3>
            </div>
            
            <div className="answer-section">
              <label htmlFor="answer">Ваш ответ:</label>
              <textarea
                id="answer"
                className="answer-input"
                placeholder="Введите ваш ответ здесь..."
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={6}
                disabled={submitting || skipping}
              />
            </div>
            
            <div className="question-actions">
              <button 
                className="btn-skip"
                onClick={handleSkip}
                disabled={submitting || skipping}
              >
                {skipping ? 'Пропуск...' : '⏭️ Пропустить'}
              </button>
              
              <button 
                className="btn-primary btn-submit"
                onClick={handleSubmit}
                disabled={!answer.trim() || submitting || skipping}
              >
                {submitting ? 'Отправка...' : 'Ответить →'}
              </button>
            </div>
          </div>
        ) : (
          <div className="no-question">
            <p>Вопросы закончились</p>
            <button className="btn-primary" onClick={() => navigate(`/result/${interviewId}`)}>
              Перейти к результатам
            </button>
          </div>
        )}

        {/* Side Stats */}
        <aside className="stats-sidebar">
          <div className="stats-card">
            <h4>📊 Статистика</h4>
            
            <div className="stat-item">
              <span className="stat-label">Отвечено:</span>
              <span className="stat-value">{blockStatus?.total_answered || 0}</span>
            </div>
            
            <div className="stat-item">
              <span className="stat-label">Пропущено:</span>
              <span className="stat-value">{blockStatus?.total_skipped || 0}</span>
            </div>
            
            <div className="stat-item">
              <span className="stat-label">Правильных:</span>
              <span className="stat-value correct">{blockStatus?.total_correct || 0}</span>
            </div>
            
            {blockStatus?.average_score !== null && blockStatus?.average_score !== undefined && (
              <div className="stat-item">
                <span className="stat-label">Средний балл:</span>
                <span className={`stat-value ${getScoreClass(blockStatus.average_score)}`}>
                  {Math.round(blockStatus.average_score)}%
                </span>
              </div>
            )}
          </div>
          
          {blockStatus?.category_scores && Object.keys(blockStatus.category_scores).length > 0 && (
            <div className="stats-card">
              <h4>📚 По категориям</h4>
              {Object.entries(blockStatus.category_scores).map(([cat, score]) => (
                <div className="stat-item" key={cat}>
                  <span className="stat-label">{cat}:</span>
                  <span className={`stat-value ${getScoreClass(score)}`}>{Math.round(score)}%</span>
                </div>
              ))}
            </div>
          )}
          
          <div className="info-card">
            <h4>ℹ️ Правила</h4>
            <ul>
              <li>Вернуться к вопросу нельзя</li>
              <li>Пропуск = 0 баллов</li>
              <li>Время ответа учитывается</li>
            </ul>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default QuestionsBlockPage


// пидормот

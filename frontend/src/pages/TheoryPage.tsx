import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { interviewAPI } from '../api/client'
import '../styles/theory.css'

interface TheoryQuestion {
  id: number
  question_order: number
  question_type: string
  question_text: string
  related_task_id?: number
  category?: string
  difficulty?: string
  total_answered: number
  max_questions: number
}

interface Evaluation {
  score: number
  feedback: string
  correctness?: number
  completeness?: number
}

function TheoryPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()

  const [interview, setInterview] = useState<any>(null)
  const [currentQuestion, setCurrentQuestion] = useState<TheoryQuestion | null>(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [lastEvaluation, setLastEvaluation] = useState<Evaluation | null>(null)
  const [answeredQuestions, setAnsweredQuestions] = useState<any[]>([])
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    loadInterview()
    loadNextQuestion()
    loadAnsweredQuestions()
  }, [interviewId])

  const loadInterview = async () => {
    try {
      const data = await interviewAPI.getInterviewV2(Number(interviewId))
      setInterview(data)
      
      if (data.current_stage === 'coding') {
        navigate(`/interview/${interviewId}`)
      } else if (data.current_stage === 'completed') {
        navigate(`/result/${interviewId}`)
      }
    } catch (error) {
      console.error('Failed to load interview:', error)
    }
  }

  const loadNextQuestion = async () => {
    setLoading(true)
    try {
      const question = await interviewAPI.getNextQuestion(Number(interviewId))
      if (question) {
        setCurrentQuestion(question)
        setAnswer('')
        setLastEvaluation(null)
      } else {
        // No more questions - interview complete
        setIsComplete(true)
      }
    } catch (error) {
      console.error('Failed to load question:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAnsweredQuestions = async () => {
    try {
      const answers = await interviewAPI.getTheoryAnswers(Number(interviewId))
      setAnsweredQuestions(answers.filter((a: any) => a.status === 'answered' || a.status === 'skipped'))
    } catch (error) {
      console.error('Failed to load answers:', error)
    }
  }

  const submitAnswer = async () => {
    if (!currentQuestion || !answer.trim()) return

    setSubmitting(true)
    try {
      const evaluation = await interviewAPI.submitTheoryAnswer({
        answer_id: currentQuestion.id,
        answer_text: answer
      })
      
      setLastEvaluation(evaluation)
      await loadAnsweredQuestions()
      
      // Wait a bit to show feedback, then load next question
      setTimeout(() => {
        loadNextQuestion()
      }, 2000)
    } catch (error: any) {
      console.error('Failed to submit answer:', error)
      alert(`Ошибка: ${error.response?.data?.detail || error.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const skipQuestion = async () => {
    if (!currentQuestion) return

    setSubmitting(true)
    try {
      await interviewAPI.submitTheoryAnswer({
        answer_id: currentQuestion.id,
        answer_text: 'ПРОПУСК'
      })
      
      await loadAnsweredQuestions()
      loadNextQuestion()
    } catch (error: any) {
      console.error('Failed to skip question:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const completeInterview = async () => {
    try {
      const scores = await interviewAPI.completeInterviewV2(Number(interviewId))
      console.log('Final scores:', scores)
      navigate(`/result/${interviewId}`)
    } catch (error: any) {
      console.error('Failed to complete interview:', error)
      alert(`Ошибка: ${error.response?.data?.detail || error.message}`)
    }
  }

  const getQuestionTypeLabel = (type: string) => {
    switch (type) {
      case 'solution_algorithm':
        return '🧠 Алгоритм решения'
      case 'solution_complexity':
        return '📊 Асимптотика'
      case 'theory':
        return '📚 Теория'
      default:
        return '❓ Вопрос'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'excellent'
    if (score >= 60) return 'good'
    if (score >= 40) return 'average'
    return 'poor'
  }

  if (!interview) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Загрузка...</p>
      </div>
    )
  }

  // Calculate progress
  const totalAnswered = answeredQuestions.length
  const maxQuestions = currentQuestion?.max_questions || 25
  const progressPercent = Math.min(100, (totalAnswered / maxQuestions) * 100)

  // Calculate average score
  const scoredAnswers = answeredQuestions.filter(a => a.score !== null && a.status === 'answered')
  const avgScore = scoredAnswers.length > 0
    ? Math.round(scoredAnswers.reduce((sum, a) => sum + a.score, 0) / scoredAnswers.length)
    : 0

  return (
    <div className="theory-container">
      {/* Header */}
      <header className="theory-header">
        <div className="header-left">
          <h1>VibeCode</h1>
          <span className="header-divider">|</span>
          <span className="stage-label">Этап 2: Теоретические вопросы</span>
        </div>

        <div className="header-center">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progressPercent}%` }}></div>
          </div>
          <span className="progress-text">
            Вопрос {totalAnswered + 1} из {maxQuestions}
          </span>
        </div>

        <div className="header-right">
          <div className="avg-score">
            <span>Средний балл:</span>
            <strong className={getScoreColor(avgScore)}>{avgScore}%</strong>
          </div>
        </div>
      </header>

      {/* Stage Indicator */}
      <div className="stage-indicator">
        <div className="stage completed">
          <span className="stage-number">✓</span>
          <span className="stage-name">Задачи</span>
        </div>
        <div className="stage-connector completed"></div>
        <div className="stage active">
          <span className="stage-number">2</span>
          <span className="stage-name">Вопросы</span>
        </div>
        <div className="stage-connector"></div>
        <div className="stage">
          <span className="stage-number">3</span>
          <span className="stage-name">Результат</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="theory-content">
        {isComplete ? (
          <div className="complete-section">
            <div className="complete-icon">🎉</div>
            <h2>Собеседование завершено!</h2>
            <p>Вы ответили на все вопросы. Нажмите кнопку ниже, чтобы получить результаты.</p>
            
            <div className="stats-summary">
              <div className="stat-card">
                <span className="stat-value">{totalAnswered}</span>
                <span className="stat-label">Вопросов отвечено</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{avgScore}%</span>
                <span className="stat-label">Средний балл</span>
              </div>
            </div>

            <button className="btn-complete" onClick={completeInterview}>
              Получить результаты →
            </button>
          </div>
        ) : loading ? (
          <div className="loading-section">
            <div className="loading-spinner"></div>
            <p>Загрузка вопроса...</p>
          </div>
        ) : currentQuestion ? (
          <div className="question-section">
            {/* Question Card */}
            <div className="question-card">
              <div className="question-header">
                <span className="question-type">
                  {getQuestionTypeLabel(currentQuestion.question_type)}
                </span>
                <span className="question-number">
                  Вопрос #{currentQuestion.question_order}
                </span>
              </div>

              <div className="question-text">
                {currentQuestion.question_text}
              </div>

              {currentQuestion.category && (
                <div className="question-meta">
                  <span className="category-badge">{currentQuestion.category}</span>
                  {currentQuestion.difficulty && (
                    <span className={`difficulty-badge ${currentQuestion.difficulty}`}>
                      {currentQuestion.difficulty}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Answer Section */}
            <div className="answer-section">
              <h3>Ваш ответ:</h3>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Введите ваш ответ здесь..."
                rows={6}
                disabled={submitting}
              />

              <div className="answer-actions">
                <button
                  className="btn-skip"
                  onClick={skipQuestion}
                  disabled={submitting}
                >
                  Пропустить
                </button>
                <button
                  className="btn-submit"
                  onClick={submitAnswer}
                  disabled={submitting || !answer.trim()}
                >
                  {submitting ? 'Проверка...' : 'Отправить ответ'}
                </button>
              </div>
            </div>

            {/* Last Evaluation */}
            {lastEvaluation && (
              <div className={`evaluation-card ${getScoreColor(lastEvaluation.score)}`}>
                <div className="evaluation-header">
                  <span className="evaluation-score">
                    {lastEvaluation.score}%
                  </span>
                  <span className="evaluation-label">
                    {lastEvaluation.score >= 80 ? '🎯 Отлично!' :
                     lastEvaluation.score >= 60 ? '👍 Хорошо' :
                     lastEvaluation.score >= 40 ? '📖 Неплохо' : '💪 Нужно подтянуть'}
                  </span>
                </div>
                <div className="evaluation-feedback">
                  {lastEvaluation.feedback}
                </div>
              </div>
            )}
          </div>
        ) : null}

        {/* Answered Questions History */}
        {answeredQuestions.length > 0 && (
          <div className="history-section">
            <h3>📋 История ответов</h3>
            <div className="history-list">
              {answeredQuestions.slice(-5).reverse().map((qa, i) => (
                <div key={i} className={`history-item ${qa.status === 'skipped' ? 'skipped' : getScoreColor(qa.score || 0)}`}>
                  <span className="history-question">
                    {qa.question_text?.substring(0, 60)}...
                  </span>
                  <span className="history-score">
                    {qa.status === 'skipped' ? '⏭️ Пропущен' : `${qa.score}%`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TheoryPage


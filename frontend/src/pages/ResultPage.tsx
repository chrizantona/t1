import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { interviewAPI, questionBlockAPI } from '../api/client'
import '../styles/result.css'

interface SkillScore {
  score: number
  comment: string
}

interface SkillAssessment {
  algorithms: SkillScore
  architecture: SkillScore
  clean_code: SkillScore
  debugging: SkillScore
  communication: SkillScore
  next_grade_tips: string[]
}

interface FinalReport {
  interview: any
  tasks: any[]
  skill_assessment: SkillAssessment
  total_hints_used: number
  total_submissions: number
}

// Форматирование грейда
const formatGrade = (grade: string | null | undefined): string => {
  if (!grade) return 'Не определён'
  const gradeMap: Record<string, string> = {
    'intern': 'Intern (Стажёр)',
    'junior': 'Junior',
    'junior_plus': 'Junior+',
    'junior+': 'Junior+',
    'middle': 'Middle',
    'middle_plus': 'Middle+',
    'middle+': 'Middle+',
    'senior': 'Senior',
    'senior_plus': 'Senior+',
  }
  return gradeMap[grade.toLowerCase()] || grade
}

const getGradeColor = (grade: string | null | undefined): string => {
  if (!grade) return '#8C8C8C'
  const g = grade.toLowerCase()
  if (g.includes('senior')) return '#722ED1'
  if (g.includes('middle')) return '#1890FF'
  if (g.includes('junior')) return '#52C41A'
  return '#FA8C16'
}

interface QuestionBlockStats {
  block_id: number
  interview_id: number
  status: string
  summary: {
    total_questions: number
    answered: number
    skipped: number
    correct: number
    average_score: number
    average_time_seconds: number
  }
  category_scores: Record<string, number>
  difficulty_scores: Record<string, number>
}

function ResultPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  
  const [report, setReport] = useState<FinalReport | null>(null)
  const [questionBlockStats, setQuestionBlockStats] = useState<QuestionBlockStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadReport()
  }, [interviewId])

  const loadReport = async () => {
    try {
      setLoading(true)
      const data = await interviewAPI.getFinalReport(Number(interviewId))
      setReport(data)
      
      // Try to load question block statistics
      try {
        const qbStats = await questionBlockAPI.getStatistics(Number(interviewId))
        if (qbStats && !qbStats.error) {
          setQuestionBlockStats(qbStats)
        }
      } catch {
        // Question block may not exist, that's ok
      }
    } catch (err: any) {
      console.error('Failed to load report:', err)
      setError('Не удалось загрузить отчёт')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>⏳ Генерация отчёта...</p>
        <p className="loading-subtitle">Анализируем ваше решение</p>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="error-screen">
        <h2>❌ Ошибка</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/')}>На главную</button>
      </div>
    )
  }

  const { interview, tasks, skill_assessment } = report
  
  // Calculate average score
  const avgScore = (
    skill_assessment.algorithms.score +
    skill_assessment.architecture.score +
    skill_assessment.clean_code.score +
    skill_assessment.debugging.score +
    skill_assessment.communication.score
  ) / 5

  // Calculate stats
  const completedTasks = tasks.filter(t => t.status === 'completed').length
  const totalScore = tasks.reduce((sum, t) => sum + (t.actual_score || 0), 0)
  const maxPossibleScore = tasks.length * 100
  const scorePercentage = maxPossibleScore > 0 ? (totalScore / maxPossibleScore * 100) : 0

  return (
    <div className="result-container">
      {/* Header */}
      <header className="result-header">
        <div className="result-header-content">
          <h1>🎉 Интервью завершено!</h1>
          <p className="result-subtitle">
            Кандидат: <strong>{interview.candidate_name || 'Без имени'}</strong>
          </p>
          <p className="result-meta">
            {interview.direction} • {interview.selected_level}
          </p>
        </div>

        <div className="result-summary">
          <div className="summary-card">
            <div className="summary-icon">🎯</div>
            <div className="summary-value">{avgScore.toFixed(1)}</div>
            <div className="summary-label">Средняя оценка</div>
          </div>
          
          <div className="summary-card">
            <div className="summary-icon">📊</div>
            <div className="summary-value">{scorePercentage.toFixed(0)}%</div>
            <div className="summary-label">Процент выполнения</div>
          </div>
          
          <div className="summary-card">
            <div className="summary-icon">✅</div>
            <div className="summary-value">{completedTasks}/{tasks.length}</div>
            <div className="summary-label">Задач решено</div>
          </div>
          
          <div className="summary-card grade-card">
            <div className="summary-icon">🏆</div>
            <div className="summary-value" style={{ color: getGradeColor(interview.overall_grade) }}>
              {formatGrade(interview.overall_grade)}
            </div>
            <div className="summary-label">Итоговый грейд</div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="result-content">
        {/* Skill Radar */}
        <section className="skill-radar-section">
          <h2>📊 Оценка навыков</h2>
          
          <div className="radar-container">
            <svg viewBox="0 0 400 400" className="radar-chart">
              {/* Radar grid */}
              {[20, 40, 60, 80, 100].map((level) => {
                const size = (level / 100) * 150
                return (
                  <circle
                    key={level}
                    cx="200"
                    cy="200"
                    r={size}
                    fill="none"
                    stroke="var(--color-border)"
                    strokeWidth="1"
                  />
                )
              })}
              
              {/* Axes */}
              {[0, 72, 144, 216, 288].map((angle, index) => {
                const rad = (angle - 90) * Math.PI / 180
                const x = 200 + Math.cos(rad) * 150
                const y = 200 + Math.sin(rad) * 150
                return (
                  <line
                    key={angle}
                    x1="200"
                    y1="200"
                    x2={x}
                    y2={y}
                    stroke="var(--color-border)"
                    strokeWidth="1"
                  />
                )
              })}
              
              {/* Data polygon */}
              <polygon
                points={[
                  skill_assessment.algorithms.score,
                  skill_assessment.architecture.score,
                  skill_assessment.clean_code.score,
                  skill_assessment.debugging.score,
                  skill_assessment.communication.score
                ].map((score, index) => {
                  const angle = index * 72 - 90
                  const rad = angle * Math.PI / 180
                  const distance = (score / 100) * 150
                  const x = 200 + Math.cos(rad) * distance
                  const y = 200 + Math.sin(rad) * distance
                  return `${x},${y}`
                }).join(' ')}
                fill="rgba(0, 173, 255, 0.3)"
                stroke="var(--color-primary)"
                strokeWidth="3"
              />
              
              {/* Labels */}
              <text x="200" y="35" textAnchor="middle" fill="var(--color-text-primary)" fontSize="14" fontWeight="600">
                Алгоритмы
              </text>
              <text x="350" y="165" textAnchor="start" fill="var(--color-text-primary)" fontSize="14" fontWeight="600">
                Архитектура
              </text>
              <text x="300" y="345" textAnchor="middle" fill="var(--color-text-primary)" fontSize="14" fontWeight="600">
                Clean Code
              </text>
              <text x="100" y="345" textAnchor="middle" fill="var(--color-text-primary)" fontSize="14" fontWeight="600">
                Debugging
              </text>
              <text x="50" y="165" textAnchor="end" fill="var(--color-text-primary)" fontSize="14" fontWeight="600">
                Коммуникация
              </text>
            </svg>
          </div>

          <div className="skill-details">
            <div className="skill-item">
              <div className="skill-name">🧮 Алгоритмы</div>
              <div className="skill-score">{skill_assessment.algorithms.score}/100</div>
              <div className="skill-comment">{skill_assessment.algorithms.comment}</div>
            </div>
            
            <div className="skill-item">
              <div className="skill-name">🏗️ Архитектура</div>
              <div className="skill-score">{skill_assessment.architecture.score}/100</div>
              <div className="skill-comment">{skill_assessment.architecture.comment}</div>
            </div>
            
            <div className="skill-item">
              <div className="skill-name">✨ Clean Code</div>
              <div className="skill-score">{skill_assessment.clean_code.score}/100</div>
              <div className="skill-comment">{skill_assessment.clean_code.comment}</div>
            </div>
            
            <div className="skill-item">
              <div className="skill-name">🐛 Debugging</div>
              <div className="skill-score">{skill_assessment.debugging.score}/100</div>
              <div className="skill-comment">{skill_assessment.debugging.comment}</div>
            </div>
            
            <div className="skill-item">
              <div className="skill-name">💬 Коммуникация</div>
              <div className="skill-score">{skill_assessment.communication.score}/100</div>
              <div className="skill-comment">{skill_assessment.communication.comment}</div>
            </div>
          </div>
        </section>

        {/* Tasks Overview */}
        <section className="tasks-overview-section">
          <h2>📝 Выполненные задачи</h2>
          
          <div className="tasks-grid">
            {tasks.map((task, index) => (
              <div key={task.id} className="task-card">
                <div className="task-card-header">
                  <span className="task-number">#{index + 1}</span>
                  <span className={`task-status ${task.status}`}>
                    {task.status === 'completed' ? '✅' : '⏳'}
                  </span>
                </div>
                
                <h3>{task.title}</h3>
                
                <div className="task-card-meta">
                  <span className={`difficulty-badge ${task.difficulty}`}>
                    {task.difficulty}
                  </span>
                  <span className="category-badge">{task.category}</span>
                </div>
                
                <div className="task-card-score">
                  <span>Балл:</span>
                  <strong>{task.actual_score ? task.actual_score.toFixed(1) : '0'} / {task.max_score}</strong>
                </div>
                
                {task.submissions && task.submissions.length > 0 && (
                  <div className="task-card-stats">
                    <span>Попыток: {task.submissions.length}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Recommendations */}
        <section className="recommendations-section">
          <h2>🚀 Рекомендации для роста</h2>
          
          <div className="tips-list">
            {skill_assessment.next_grade_tips.map((tip, index) => (
              <div key={index} className="tip-card">
                <div className="tip-number">{index + 1}</div>
                <div className="tip-content">{tip}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Question Block Statistics */}
        {questionBlockStats && questionBlockStats.summary && (
          <section className="questions-block-section">
            <h2>📚 Блок теоретических вопросов</h2>
            
            <div className="qb-summary">
              <div className="qb-stat-card">
                <div className="qb-stat-icon">✅</div>
                <div className="qb-stat-value">{questionBlockStats.summary.answered}</div>
                <div className="qb-stat-label">Отвечено</div>
              </div>
              
              <div className="qb-stat-card">
                <div className="qb-stat-icon">⏭️</div>
                <div className="qb-stat-value">{questionBlockStats.summary.skipped}</div>
                <div className="qb-stat-label">Пропущено</div>
              </div>
              
              <div className="qb-stat-card">
                <div className="qb-stat-icon">🎯</div>
                <div className="qb-stat-value">{questionBlockStats.summary.correct}</div>
                <div className="qb-stat-label">Правильных</div>
              </div>
              
              <div className="qb-stat-card">
                <div className="qb-stat-icon">📊</div>
                <div className="qb-stat-value">{questionBlockStats.summary.average_score.toFixed(0)}%</div>
                <div className="qb-stat-label">Средний балл</div>
              </div>
              
              <div className="qb-stat-card">
                <div className="qb-stat-icon">⏱️</div>
                <div className="qb-stat-value">{Math.round(questionBlockStats.summary.average_time_seconds)}с</div>
                <div className="qb-stat-label">Среднее время</div>
              </div>
            </div>
            
            {/* Category breakdown */}
            {Object.keys(questionBlockStats.category_scores).length > 0 && (
              <div className="qb-breakdown">
                <h3>Результаты по категориям</h3>
                <div className="category-bars">
                  {Object.entries(questionBlockStats.category_scores).map(([category, score]) => (
                    <div className="category-bar-item" key={category}>
                      <div className="category-bar-label">
                        <span className="category-name">{category}</span>
                        <span className="category-score">{Math.round(score)}%</span>
                      </div>
                      <div className="category-bar-container">
                        <div 
                          className="category-bar-fill"
                          style={{ 
                            width: `${score}%`,
                            backgroundColor: score >= 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444'
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Difficulty breakdown */}
            {Object.keys(questionBlockStats.difficulty_scores).length > 0 && (
              <div className="qb-breakdown">
                <h3>Результаты по сложности</h3>
                <div className="difficulty-stats">
                  {Object.entries(questionBlockStats.difficulty_scores).map(([difficulty, score]) => (
                    <div className="difficulty-stat-item" key={difficulty}>
                      <span className={`difficulty-label ${difficulty}`}>
                        {difficulty === 'easy' ? '🟢 Лёгкие' : difficulty === 'medium' ? '🟡 Средние' : '🔴 Сложные'}
                      </span>
                      <span className={`difficulty-score ${
                        score >= 70 ? 'good' : score >= 40 ? 'medium' : 'poor'
                      }`}>
                        {Math.round(score)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Trust Score */}
        {interview.trust_score !== null && interview.trust_score !== undefined && (
          <section className="trust-score-section">
            <h2>🔒 Trust Score</h2>
            
            <div className="trust-score-display">
              <div className={`trust-score-value ${
                interview.trust_score >= 80 ? 'high' : 
                interview.trust_score >= 50 ? 'medium' : 'low'
              }`}>
                {interview.trust_score.toFixed(0)}%
              </div>
              
              <p className="trust-score-description">
                {interview.trust_score >= 80 
                  ? '✅ Высокий уровень доверия - результаты достоверны'
                  : interview.trust_score >= 50
                  ? '⚠️ Средний уровень доверия - есть подозрительная активность'
                  : '❌ Низкий уровень доверия - возможное использование AI'
                }
              </p>
            </div>
          </section>
        )}

        {/* Statistics */}
        <section className="stats-section">
          <h2>📈 Статистика</h2>
          
          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-icon">💡</div>
              <div className="stat-value">{report.total_hints_used}</div>
              <div className="stat-label">Подсказок использовано</div>
            </div>
            
            <div className="stat-box">
              <div className="stat-icon">📤</div>
              <div className="stat-value">{report.total_submissions}</div>
              <div className="stat-label">Отправок кода</div>
            </div>
            
            <div className="stat-box">
              <div className="stat-icon">⏱️</div>
              <div className="stat-value">
                {interview.completed_at && interview.created_at 
                  ? Math.round((new Date(interview.completed_at).getTime() - new Date(interview.created_at).getTime()) / 60000)
                  : 'N/A'
                }
              </div>
              <div className="stat-label">Минут на интервью</div>
            </div>
            
            <div className="stat-box">
              <div className="stat-icon">🎯</div>
              <div className="stat-value">{totalScore.toFixed(0)}</div>
              <div className="stat-label">Общий балл</div>
            </div>
          </div>
        </section>

        {/* Actions */}
        <div className="result-actions">
          <button 
            className="btn-primary"
            onClick={() => navigate('/')}
          >
            🏠 На главную
          </button>
          <button 
            className="btn-secondary"
            onClick={() => window.print()}
          >
            🖨️ Распечатать отчёт
          </button>
        </div>
      </div>
    </div>
  )
}

export default ResultPage

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interviewAPI, resumeAPI } from '../api/client'

function LandingPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [selectedLevel, setSelectedLevel] = useState('middle')
  const [selectedDirection, setSelectedDirection] = useState('backend')
  const [cvText, setCvText] = useState('')
  const [suggestion, setSuggestion] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const analyzeCV = async () => {
    if (!cvText.trim()) return
    
    setLoading(true)
    try {
      const result = await resumeAPI.analyzeCV(cvText)
      setSuggestion(result)
      setSelectedLevel(result.suggested_level)
      setSelectedDirection(result.suggested_direction)
    } catch (error) {
      console.error('CV analysis failed:', error)
      alert('Не удалось проанализировать резюме')
    } finally {
      setLoading(false)
    }
  }

  const startInterview = async () => {
    setLoading(true)
    try {
      const interview = await interviewAPI.startInterview({
        candidate_name: name || undefined,
        candidate_email: email || undefined,
        selected_level: selectedLevel,
        direction: selectedDirection,
        cv_text: cvText || undefined,
      })
      navigate(`/interview/${interview.id}`)
    } catch (error) {
      console.error('Failed to start interview:', error)
      alert('Не удалось начать интервью')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '60px 40px', maxWidth: '900px', margin: '0 auto', background: 'white' }}>
      <div style={{ textAlign: 'center', marginBottom: '60px' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '16px', color: 'var(--color-text-primary)' }}>VibeCode</h1>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '400', color: 'var(--color-text-blue)' }}>
          AI-платформа для технических собеседований
        </h2>
        <p style={{ fontSize: '1.1rem', color: 'var(--color-text-light)', marginTop: '16px' }}>
          Powered by T1 SciBox LLM
        </p>
      </div>

      <div className="card" style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '1.25rem', marginBottom: '24px', color: 'var(--color-text-blue)' }}>
          Информация о кандидате
        </h3>
        
        <input
          type="text"
          placeholder="Имя (опционально)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ width: '100%', marginBottom: '16px' }}
        />
        
        <input
          type="email"
          placeholder="Email (опционально)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      <div className="card card-blue" style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', color: 'var(--color-primary)' }}>
          🤖 CV-based Level Suggestion
        </h3>
        <p className="light" style={{ marginBottom: '24px', fontSize: '0.95rem' }}>
          Загрузите резюме, и AI порекомендует оптимальный уровень
        </p>
        
        <textarea
          placeholder="Вставьте текст резюме здесь..."
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
          rows={6}
          style={{ width: '100%', marginBottom: '16px', fontFamily: 'monospace', background: 'white' }}
        />
        
        <button onClick={analyzeCV} disabled={loading || !cvText.trim()}>
          {loading ? '⏳ Анализ...' : '✨ Проанализировать резюме'}
        </button>
        
        {suggestion && (
          <div className="card" style={{ marginTop: '24px', background: 'white', border: '2px solid var(--color-primary)' }}>
            <h3 style={{ marginBottom: '16px', color: 'var(--color-primary)', fontSize: '1.1rem' }}>
              💡 Рекомендация AI
            </h3>
            <div style={{ display: 'grid', gap: '12px' }}>
              <p><strong style={{ color: 'var(--color-text-blue)' }}>Уровень:</strong> <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{suggestion.suggested_level}</span></p>
              <p><strong style={{ color: 'var(--color-text-blue)' }}>Направление:</strong> {suggestion.suggested_direction}</p>
              {suggestion.years_of_experience && (
                <p><strong style={{ color: 'var(--color-text-blue)' }}>Опыт:</strong> {suggestion.years_of_experience} лет</p>
              )}
              {suggestion.key_technologies.length > 0 && (
                <p><strong style={{ color: 'var(--color-text-blue)' }}>Технологии:</strong> {suggestion.key_technologies.join(', ')}</p>
              )}
              <p style={{ marginTop: '8px', padding: '12px', background: 'var(--color-bg-light)', borderRadius: '8px', fontSize: '0.95rem' }}>
                {suggestion.reasoning}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{ marginBottom: '40px' }}>
        <h3 style={{ fontSize: '1.25rem', marginBottom: '24px', color: 'var(--color-text-blue)' }}>
          Выбор уровня и направления
        </h3>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '12px', color: 'var(--color-text-grey)', fontWeight: 600 }}>
            Уровень:
          </label>
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            style={{ width: '100%' }}
          >
            <option value="junior">Junior</option>
            <option value="middle">Middle</option>
            <option value="middle+">Middle+</option>
            <option value="senior">Senior</option>
          </select>
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '12px', color: 'var(--color-text-grey)', fontWeight: 600 }}>
            Направление:
          </label>
          <select
            value={selectedDirection}
            onChange={(e) => setSelectedDirection(e.target.value)}
            style={{ width: '100%' }}
          >
            <option value="backend">Backend</option>
            <option value="frontend">Frontend</option>
            <option value="algorithms">Algorithms</option>
            <option value="fullstack">Fullstack</option>
          </select>
        </div>
      </div>

      <button
        onClick={startInterview}
        disabled={loading}
        style={{ width: '100%', padding: '18px', fontSize: '1.2rem', fontWeight: 700 }}
      >
        {loading ? '⏳ Запуск...' : '🚀 Начать интервью'}
      </button>
    </div>
  )
}

export default LandingPage


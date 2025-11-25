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
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>VibeCode</h1>
      <p style={{ fontSize: '1.2rem', color: '#888', marginBottom: '40px' }}>
        AI-платформа для технических собеседований
      </p>

      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>Информация о кандидате</h2>
        
        <input
          type="text"
          placeholder="Имя (опционально)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ width: '100%', padding: '12px', marginBottom: '15px', fontSize: '1rem', borderRadius: '8px', border: '1px solid #333' }}
        />
        
        <input
          type="email"
          placeholder="Email (опционально)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%', padding: '12px', marginBottom: '15px', fontSize: '1rem', borderRadius: '8px', border: '1px solid #333' }}
        />
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>
          Загрузить резюме (CV-based Level Suggestion)
        </h2>
        
        <textarea
          placeholder="Вставьте текст резюме здесь..."
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
          rows={6}
          style={{ width: '100%', padding: '12px', marginBottom: '15px', fontSize: '1rem', borderRadius: '8px', border: '1px solid #333', fontFamily: 'monospace' }}
        />
        
        <button onClick={analyzeCV} disabled={loading || !cvText.trim()}>
          {loading ? 'Анализ...' : 'Проанализировать резюме'}
        </button>
        
        {suggestion && (
          <div style={{ marginTop: '20px', padding: '20px', background: '#1a1a1a', borderRadius: '8px', border: '1px solid #333' }}>
            <h3 style={{ marginBottom: '10px' }}>Рекомендация AI</h3>
            <p><strong>Уровень:</strong> {suggestion.suggested_level}</p>
            <p><strong>Направление:</strong> {suggestion.suggested_direction}</p>
            {suggestion.years_of_experience && (
              <p><strong>Опыт:</strong> {suggestion.years_of_experience} лет</p>
            )}
            {suggestion.key_technologies.length > 0 && (
              <p><strong>Технологии:</strong> {suggestion.key_technologies.join(', ')}</p>
            )}
            <p style={{ marginTop: '10px', color: '#888' }}>{suggestion.reasoning}</p>
          </div>
        )}
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>Выбор уровня и направления</h2>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>Уровень:</label>
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            style={{ width: '100%', padding: '12px', fontSize: '1rem', borderRadius: '8px', border: '1px solid #333', background: '#1a1a1a' }}
          >
            <option value="junior">Junior</option>
            <option value="middle">Middle</option>
            <option value="middle+">Middle+</option>
            <option value="senior">Senior</option>
          </select>
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>Направление:</label>
          <select
            value={selectedDirection}
            onChange={(e) => setSelectedDirection(e.target.value)}
            style={{ width: '100%', padding: '12px', fontSize: '1rem', borderRadius: '8px', border: '1px solid #333', background: '#1a1a1a' }}
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
        style={{ width: '100%', padding: '16px', fontSize: '1.2rem', background: '#646cff', color: 'white', border: 'none' }}
      >
        {loading ? 'Запуск...' : 'Начать интервью'}
      </button>
    </div>
  )
}

export default LandingPage


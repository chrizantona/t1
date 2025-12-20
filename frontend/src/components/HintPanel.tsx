import { useState } from 'react'
import { interviewAPI } from '../api/client'

interface HintPanelProps {
  taskId: number
  currentCode: string
  onHintReceived: () => void
}

function HintPanel({ taskId, currentCode, onHintReceived }: HintPanelProps) {
  const [hint, setHint] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const requestHint = async (level: string) => {
    setLoading(true)
    try {
      const response = await interviewAPI.requestHint({
        task_id: taskId,
        hint_level: level,
        current_code: currentCode,
      })
      setHint(response)
      onHintReceived()
    } catch (error) {
      console.error('Failed to get hint:', error)
      alert('Ошибка при получении подсказки')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px', background: '#1a1a1a', borderTop: '1px solid #333' }}>
      <h3 style={{ marginBottom: '15px' }}>Подсказки (Hint Economy)</h3>
      
      <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
        <button
          onClick={() => requestHint('light')}
          disabled={loading}
          style={{ flex: 1, background: '#22c55e' }}
        >
          Лёгкая (-10%)
        </button>
        <button
          onClick={() => requestHint('medium')}
          disabled={loading}
          style={{ flex: 1, background: '#f59e0b' }}
        >
          Средняя (-20%)
        </button>
        <button
          onClick={() => requestHint('heavy')}
          disabled={loading}
          style={{ flex: 1, background: '#ef4444' }}
        >
          Жёсткая (-35%)
        </button>
      </div>

      {hint && (
        <div style={{ padding: '15px', background: '#242424', borderRadius: '8px', border: '1px solid #333' }}>
          <div style={{ marginBottom: '10px', color: '#f59e0b' }}>
            ⚠️ Штраф: -{hint.score_penalty}%. Новый максимум: {hint.new_max_score}/100
          </div>
          <div style={{ lineHeight: '1.6' }}>{hint.hint_content}</div>
        </div>
      )}
    </div>
  )
}

export default HintPanel


// пидормот

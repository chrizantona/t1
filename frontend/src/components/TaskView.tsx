import { useState } from 'react'
import IdeEditor from './IdeEditor'
import HintPanel from './HintPanel'
import { interviewAPI } from '../api/client'

interface TaskViewProps {
  task: any
  interviewId: number
  onTaskComplete: () => void
}

function TaskView({ task, interviewId, onTaskComplete }: TaskViewProps) {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [showHints, setShowHints] = useState(false)

  const submitCode = async () => {
    setLoading(true)
    try {
      const submission = await interviewAPI.submitCode({
        task_id: task.id,
        code,
        language,
      })
      setResult(submission)
      
      // Check if all tests passed
      if (submission.passed_visible === submission.total_visible && 
          submission.passed_hidden === submission.total_hidden) {
        setTimeout(() => {
          if (confirm('Все тесты пройдены! Перейти к следующей задаче?')) {
            onTaskComplete()
          }
        }, 1000)
      }
    } catch (error) {
      console.error('Submission failed:', error)
      alert('Ошибка при отправке кода')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Task Description */}
      <div style={{ padding: '20px', borderBottom: '1px solid #333', maxHeight: '200px', overflowY: 'auto' }}>
        <h2 style={{ fontSize: '1.3rem', marginBottom: '10px' }}>{task.title}</h2>
        <p style={{ color: '#ccc', lineHeight: '1.6' }}>{task.description}</p>
        
        {/* Visible Tests */}
        <div style={{ marginTop: '15px' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Примеры:</h3>
          {task.visible_tests.map((test: any, index: number) => (
            <div key={index} style={{ marginBottom: '8px', fontSize: '0.9rem', color: '#888' }}>
              <code>Вход: {JSON.stringify(test.input)} → Выход: {JSON.stringify(test.expected_output)}</code>
            </div>
          ))}
        </div>
        
        <div style={{ marginTop: '10px', fontSize: '0.9rem' }}>
          <span style={{ color: '#888' }}>Макс. балл:</span> <strong>{task.max_score}/100</strong>
        </div>
      </div>

      {/* Code Editor */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '10px 20px', background: '#1a1a1a', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #333', background: '#242424' }}
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
          </select>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setShowHints(!showHints)}>
              {showHints ? 'Скрыть подсказки' : 'Подсказки'}
            </button>
            <button
              onClick={submitCode}
              disabled={loading || !code.trim()}
              style={{ background: '#22c55e', color: 'white', border: 'none' }}
            >
              {loading ? 'Проверка...' : 'Отправить'}
            </button>
          </div>
        </div>
        
        <IdeEditor code={code} onChange={setCode} language={language} />
      </div>

      {/* Results */}
      {result && (
        <div style={{ padding: '20px', background: '#1a1a1a', borderTop: '1px solid #333' }}>
          <h3 style={{ marginBottom: '10px' }}>Результаты:</h3>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div>
              <span style={{ color: '#888' }}>Видимые тесты:</span>{' '}
              <span style={{ color: result.passed_visible === result.total_visible ? '#22c55e' : '#ef4444' }}>
                {result.passed_visible}/{result.total_visible}
              </span>
            </div>
            <div>
              <span style={{ color: '#888' }}>Скрытые тесты:</span>{' '}
              <span style={{ color: result.passed_hidden === result.total_hidden ? '#22c55e' : '#ef4444' }}>
                {result.passed_hidden}/{result.total_hidden}
              </span>
            </div>
            {result.execution_time_ms && (
              <div>
                <span style={{ color: '#888' }}>Время:</span> {result.execution_time_ms}ms
              </div>
            )}
          </div>
          {result.error_message && (
            <div style={{ marginTop: '10px', padding: '10px', background: '#ef4444', color: 'white', borderRadius: '4px' }}>
              {result.error_message}
            </div>
          )}
        </div>
      )}

      {/* Hints Panel */}
      {showHints && (
        <HintPanel taskId={task.id} currentCode={code} onHintReceived={() => {}} />
      )}
    </div>
  )
}

export default TaskView


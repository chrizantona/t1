import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { interviewAPI } from '../api/client'
import TaskView from '../components/TaskView'
import ChatPanel from '../components/ChatPanel'

function InterviewPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  const [interview, setInterview] = useState<any>(null)
  const [tasks, setTasks] = useState<any[]>([])
  const [currentTaskIndex, setCurrentTaskIndex] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInterview()
    loadTasks()
  }, [interviewId])

  const loadInterview = async () => {
    try {
      const data = await interviewAPI.getInterview(Number(interviewId))
      setInterview(data)
    } catch (error) {
      console.error('Failed to load interview:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTasks = async () => {
    try {
      const data = await interviewAPI.getTasks(Number(interviewId))
      setTasks(data)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    }
  }

  const completeInterview = async () => {
    try {
      await interviewAPI.completeInterview(Number(interviewId))
      navigate(`/result/${interviewId}`)
    } catch (error) {
      console.error('Failed to complete interview:', error)
      alert('Ошибка при завершении интервью')
    }
  }

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>
  }

  const currentTask = tasks[currentTaskIndex]

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Left side - Task and Code Editor */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #333' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #333' }}>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '10px' }}>
            Интервью: {interview?.direction} ({interview?.selected_level})
          </h1>
          <p style={{ color: '#888' }}>
            Задача {currentTaskIndex + 1} из {tasks.length}
          </p>
        </div>
        
        {currentTask ? (
          <TaskView
            task={currentTask}
            interviewId={Number(interviewId)}
            onTaskComplete={() => {
              if (currentTaskIndex < tasks.length - 1) {
                setCurrentTaskIndex(currentTaskIndex + 1)
              }
            }}
          />
        ) : (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <h2>Все задачи выполнены!</h2>
            <button onClick={completeInterview} style={{ marginTop: '20px' }}>
              Завершить интервью
            </button>
          </div>
        )}
      </div>

      {/* Right side - Chat Panel */}
      <div style={{ width: '400px', display: 'flex', flexDirection: 'column' }}>
        <ChatPanel
          interviewId={Number(interviewId)}
          taskId={currentTask?.id}
        />
      </div>
    </div>
  )
}

export default InterviewPage


import { useState, useEffect, useRef } from 'react'
import { interviewAPI } from '../api/client'

interface ChatPanelProps {
  interviewId: number
  taskId?: number
}

function ChatPanel({ interviewId, taskId }: ChatPanelProps) {
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await interviewAPI.sendMessage({
        interview_id: interviewId,
        content: input,
        task_id: taskId,
      })
      setMessages((prev) => [...prev, response])
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Ошибка при отправке сообщения' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '20px', borderBottom: '1px solid #333' }}>
        <h2 style={{ fontSize: '1.3rem' }}>AI Интервьюер</h2>
        <p style={{ fontSize: '0.9rem', color: '#888' }}>
          Задавайте вопросы о задаче, подходе и сложности
        </p>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
        {messages.length === 0 && (
          <div style={{ color: '#888', textAlign: 'center', marginTop: '40px' }}>
            Начните диалог с AI интервьюером
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: '15px',
              padding: '12px',
              borderRadius: '8px',
              background: msg.role === 'user' ? '#3b82f6' : '#1a1a1a',
              border: msg.role === 'assistant' ? '1px solid #333' : 'none',
            }}
          >
            <div style={{ fontSize: '0.85rem', color: '#888', marginBottom: '5px' }}>
              {msg.role === 'user' ? 'Вы' : 'AI Интервьюер'}
            </div>
            <div style={{ lineHeight: '1.5' }}>{msg.content}</div>
          </div>
        ))}
        
        {loading && (
          <div style={{ padding: '12px', color: '#888' }}>AI думает...</div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '20px', borderTop: '1px solid #333' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Напишите сообщение..."
          rows={3}
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #333',
            background: '#1a1a1a',
            color: 'white',
            fontSize: '1rem',
            resize: 'none',
            marginBottom: '10px',
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          style={{ width: '100%' }}
        >
          Отправить
        </button>
      </div>
    </div>
  )
}

export default ChatPanel


// пидормот

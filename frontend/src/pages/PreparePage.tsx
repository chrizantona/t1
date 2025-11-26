import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import '../styles/prepare.css'

function PreparePage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const navigate = useNavigate()
  const [countdown, setCountdown] = useState(10)
  const [phase, setPhase] = useState<'ready' | 'countdown' | 'go'>('ready')

  useEffect(() => {
    // Start countdown after a brief moment
    const startTimer = setTimeout(() => {
      setPhase('countdown')
    }, 500)

    return () => clearTimeout(startTimer)
  }, [])

  useEffect(() => {
    if (phase !== 'countdown') return

    if (countdown <= 0) {
      setPhase('go')
      // Navigate to interview after "GO!" animation
      setTimeout(() => {
        navigate(`/interview/${interviewId}`)
      }, 1000)
      return
    }

    const timer = setInterval(() => {
      setCountdown(prev => prev - 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [countdown, phase, interviewId, navigate])

  return (
    <div className="prepare-page">
      <div className="prepare-background">
        <div className="bg-circle bg-circle-1"></div>
        <div className="bg-circle bg-circle-2"></div>
        <div className="bg-circle bg-circle-3"></div>
      </div>

      <div className="prepare-content">
        <div className="logo-section">
          <span className="logo-icon">+</span>
          <span className="logo-text">VibeCode</span>
        </div>

        {phase === 'ready' && (
          <div className="ready-section">
            <h1>Подготовка...</h1>
          </div>
        )}

        {phase === 'countdown' && (
          <div className="countdown-section">
            <h1 className="prepare-title">Приготовьтесь</h1>
            <p className="prepare-subtitle">Собеседование начнётся через</p>
            
            <div className="countdown-container">
              <div className={`countdown-number ${countdown <= 3 ? 'urgent' : ''}`}>
                {countdown}
              </div>
              <div className="countdown-ring">
                <svg viewBox="0 0 100 100">
                  <circle 
                    className="countdown-ring-bg" 
                    cx="50" cy="50" r="45" 
                  />
                  <circle 
                    className="countdown-ring-progress" 
                    cx="50" cy="50" r="45"
                    style={{
                      strokeDasharray: `${2 * Math.PI * 45}`,
                      strokeDashoffset: `${2 * Math.PI * 45 * (1 - countdown / 10)}`
                    }}
                  />
                </svg>
              </div>
            </div>

            <div className="tips-section">
              <div className="tip">
                <span className="tip-icon">🎯</span>
                <span>Сосредоточьтесь на задаче</span>
              </div>
              <div className="tip">
                <span className="tip-icon">⏱️</span>
                <span>Время учитывается</span>
              </div>
              <div className="tip">
                <span className="tip-icon">💡</span>
                <span>Подсказки доступны</span>
              </div>
            </div>
          </div>
        )}

        {phase === 'go' && (
          <div className="go-section">
            <h1 className="go-text">ПОЕХАЛИ!</h1>
            <div className="go-icon">🚀</div>
          </div>
        )}
      </div>

      <div className="prepare-footer">
        <p>Удачи на собеседовании!</p>
      </div>
    </div>
  )
}

export default PreparePage


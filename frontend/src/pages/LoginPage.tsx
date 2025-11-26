import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI, setAuthToken } from '../api/client'
import '../styles/login.css'

function LoginPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [role, setRole] = useState<'candidate' | 'admin'>('candidate')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      let response
      if (mode === 'login') {
        response = await authAPI.login(email, password)
      } else {
        response = await authAPI.register({
          email,
          password,
          full_name: fullName || undefined,
          role
        })
      }

      setAuthToken(response.access_token)
      localStorage.setItem('vibecode_user', JSON.stringify(response))

      // Redirect based on role
      if (response.role === 'admin') {
        navigate('/admin')
      } else {
        navigate('/landing') // Candidate goes to interview start page
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка авторизации')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = async (demoRole: 'candidate' | 'admin') => {
    setLoading(true)
    setError('')

    try {
      const response = demoRole === 'admin' 
        ? await authAPI.demoAdmin()
        : await authAPI.demoCandidate()

      setAuthToken(response.access_token)
      localStorage.setItem('vibecode_user', JSON.stringify(response))

      if (response.role === 'admin') {
        navigate('/admin')
      } else {
        navigate('/landing') // Candidate goes to interview start page
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка демо-входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🚀 VibeCode</h1>
          <p>AI-powered technical interviews</p>
        </div>

        {/* Demo buttons */}
        <div className="demo-section">
          <p className="demo-label">Быстрый вход для демо:</p>
          <div className="demo-buttons">
            <button 
              className="demo-btn candidate"
              onClick={() => handleDemoLogin('candidate')}
              disabled={loading}
            >
              👤 Войти как кандидат
            </button>
            <button 
              className="demo-btn admin"
              onClick={() => handleDemoLogin('admin')}
              disabled={loading}
            >
              👔 Войти как рекрутер
            </button>
          </div>
        </div>

        <div className="divider">
          <span>или</span>
        </div>

        {/* Mode toggle */}
        <div className="mode-toggle">
          <button 
            className={mode === 'login' ? 'active' : ''}
            onClick={() => setMode('login')}
          >
            Вход
          </button>
          <button 
            className={mode === 'register' ? 'active' : ''}
            onClick={() => setMode('register')}
          >
            Регистрация
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {mode === 'register' && (
            <>
              <div className="form-group">
                <label>Имя</label>
                <input
                  type="text"
                  placeholder="Ваше имя"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Роль</label>
                <div className="role-select">
                  <button 
                    type="button"
                    className={role === 'candidate' ? 'active' : ''}
                    onClick={() => setRole('candidate')}
                  >
                    👤 Кандидат
                  </button>
                  <button 
                    type="button"
                    className={role === 'admin' ? 'active' : ''}
                    onClick={() => setRole('admin')}
                  >
                    👔 Рекрутер
                  </button>
                </div>
              </div>
            </>
          )}

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Пароль</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Загрузка...' : mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage


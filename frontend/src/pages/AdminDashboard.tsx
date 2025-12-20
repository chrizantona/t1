import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminAPI, vacancyAPI, setAuthToken } from '../api/client'
import '../styles/dashboard.css'

// Предустановленные скиллы по направлениям
const SKILLS_BY_DIRECTION: Record<string, { id: string; name: string }[]> = {
  backend: [
    { id: 'python', name: 'Python' },
    { id: 'go', name: 'Go' },
    { id: 'java', name: 'Java' },
    { id: 'nodejs', name: 'Node.js' },
    { id: 'sql', name: 'SQL' },
    { id: 'postgresql', name: 'PostgreSQL' },
    { id: 'redis', name: 'Redis' },
    { id: 'docker', name: 'Docker' },
    { id: 'kubernetes', name: 'Kubernetes' },
    { id: 'git', name: 'Git' },
    { id: 'rest_api', name: 'REST API' },
    { id: 'graphql', name: 'GraphQL' },
    { id: 'kafka', name: 'Kafka' },
    { id: 'rabbitmq', name: 'RabbitMQ' },
  ],
  frontend: [
    { id: 'javascript', name: 'JavaScript' },
    { id: 'typescript', name: 'TypeScript' },
    { id: 'react', name: 'React' },
    { id: 'vue', name: 'Vue.js' },
    { id: 'angular', name: 'Angular' },
    { id: 'html_css', name: 'HTML/CSS' },
    { id: 'sass', name: 'SASS/SCSS' },
    { id: 'webpack', name: 'Webpack' },
    { id: 'git', name: 'Git' },
    { id: 'testing', name: 'Testing (Jest)' },
    { id: 'nextjs', name: 'Next.js' },
  ],
  ml: [
    { id: 'python', name: 'Python' },
    { id: 'pytorch', name: 'PyTorch' },
    { id: 'tensorflow', name: 'TensorFlow' },
    { id: 'pandas', name: 'Pandas' },
    { id: 'numpy', name: 'NumPy' },
    { id: 'sklearn', name: 'Scikit-learn' },
    { id: 'sql', name: 'SQL' },
    { id: 'docker', name: 'Docker' },
    { id: 'mlops', name: 'MLOps' },
    { id: 'cv', name: 'Computer Vision' },
    { id: 'nlp', name: 'NLP' },
    { id: 'statistics', name: 'Statistics' },
  ],
  data: [
    { id: 'python', name: 'Python' },
    { id: 'sql', name: 'SQL' },
    { id: 'postgresql', name: 'PostgreSQL' },
    { id: 'spark', name: 'Apache Spark' },
    { id: 'airflow', name: 'Apache Airflow' },
    { id: 'kafka', name: 'Kafka' },
    { id: 'pandas', name: 'Pandas' },
    { id: 'etl', name: 'ETL' },
    { id: 'dbt', name: 'dbt' },
    { id: 'clickhouse', name: 'ClickHouse' },
  ],
  devops: [
    { id: 'linux', name: 'Linux' },
    { id: 'docker', name: 'Docker' },
    { id: 'kubernetes', name: 'Kubernetes' },
    { id: 'terraform', name: 'Terraform' },
    { id: 'ansible', name: 'Ansible' },
    { id: 'aws', name: 'AWS' },
    { id: 'gcp', name: 'GCP' },
    { id: 'cicd', name: 'CI/CD' },
    { id: 'git', name: 'Git' },
    { id: 'monitoring', name: 'Monitoring' },
    { id: 'nginx', name: 'Nginx' },
  ],
  fullstack: [
    { id: 'javascript', name: 'JavaScript' },
    { id: 'typescript', name: 'TypeScript' },
    { id: 'python', name: 'Python' },
    { id: 'react', name: 'React' },
    { id: 'nodejs', name: 'Node.js' },
    { id: 'sql', name: 'SQL' },
    { id: 'postgresql', name: 'PostgreSQL' },
    { id: 'docker', name: 'Docker' },
    { id: 'git', name: 'Git' },
    { id: 'rest_api', name: 'REST API' },
  ],
}

interface SkillItem {
  skill_id: string
  skill_name: string
  required_level: number
  weight: number
  skill_type: string
  is_critical: boolean
}

interface VacancyForm {
  title: string
  description: string
  company: string
  direction: string
  grade_required: string
  skills: SkillItem[]
}

function AdminDashboard() {
  const navigate = useNavigate()
  const [vacancies, setVacancies] = useState<any[]>([])
  const [interviews, setInterviews] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'vacancies' | 'candidates'>('overview')
  
  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [editingVacancy, setEditingVacancy] = useState<any>(null)
  const [formData, setFormData] = useState<VacancyForm>({
    title: '',
    description: '',
    company: '',
    direction: 'backend',
    grade_required: 'middle',
    skills: []
  })
  const [saving, setSaving] = useState(false)

  // Get available skills for current direction
  const availableSkills = SKILLS_BY_DIRECTION[formData.direction] || []

  // Toggle skill selection
  const toggleSkill = (skillId: string, skillName: string) => {
    const exists = formData.skills.find(s => s.skill_id === skillId)
    if (exists) {
      setFormData({
        ...formData,
        skills: formData.skills.filter(s => s.skill_id !== skillId)
      })
    } else {
      setFormData({
        ...formData,
        skills: [...formData.skills, {
          skill_id: skillId,
          skill_name: skillName,
          required_level: 2,
          weight: 1.0,
          skill_type: 'technical',
          is_critical: false
        }]
      })
    }
  }

  // Toggle critical skill
  const toggleCritical = (skillId: string) => {
    setFormData({
      ...formData,
      skills: formData.skills.map(s => 
        s.skill_id === skillId ? { ...s, is_critical: !s.is_critical } : s
      )
    })
  }

  // Update skill level
  const updateSkillLevel = (skillId: string, level: number) => {
    setFormData({
      ...formData,
      skills: formData.skills.map(s => 
        s.skill_id === skillId ? { ...s, required_level: level } : s
      )
    })
  }

  useEffect(() => {
    const userData = localStorage.getItem('vibecode_user')
    if (userData) {
      setUser(JSON.parse(userData))
    }
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [vacData, interviewData, statsData] = await Promise.all([
        vacancyAPI.listVacancies(),
        adminAPI.listInterviews(),
        adminAPI.getStatistics()
      ])
      setVacancies(vacData)
      setInterviews(interviewData)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setAuthToken(null)
    localStorage.removeItem('vibecode_user')
    navigate('/login')
  }

  const viewReport = (interviewId: number) => {
    navigate(`/result/${interviewId}`)
  }

  const openCreateModal = () => {
    setEditingVacancy(null)
    setFormData({
      title: '',
      description: '',
      company: '',
      direction: 'backend',
      grade_required: 'middle',
      skills: []
    })
    setShowModal(true)
  }

  const openEditModal = async (vacancy: any) => {
    setEditingVacancy(vacancy)
    // Load full vacancy with skills
    try {
      const fullVacancy = await vacancyAPI.getVacancy(vacancy.id)
      setFormData({
        title: fullVacancy.title,
        description: fullVacancy.description || '',
        company: fullVacancy.company || '',
        direction: fullVacancy.direction,
        grade_required: fullVacancy.grade_required,
        skills: fullVacancy.skills || []
      })
    } catch (e) {
      setFormData({
        title: vacancy.title,
        description: vacancy.description || '',
        company: vacancy.company || '',
        direction: vacancy.direction,
        grade_required: vacancy.grade_required,
        skills: []
      })
    }
    setShowModal(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      if (editingVacancy) {
        await vacancyAPI.updateVacancy(editingVacancy.id, formData)
      } else {
        await vacancyAPI.createVacancy(formData)
      }
      setShowModal(false)
      await loadData()
    } catch (error) {
      console.error('Failed to save vacancy:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (vacancyId: string) => {
    if (!confirm('Удалить эту вакансию?')) return
    
    try {
      await vacancyAPI.deleteVacancy(vacancyId)
      await loadData()
    } catch (error) {
      console.error('Failed to delete vacancy:', error)
    }
  }

  return (
    <div className="dashboard-container admin">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>🚀 VibeCode</h1>
          <span className="role-badge admin">Рекрутер</span>
        </div>
        <div className="header-right">
          <span className="user-name">👔 {user?.full_name || user?.email}</span>
          <button className="logout-btn" onClick={handleLogout}>Выйти</button>
        </div>
      </header>

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          📊 Обзор
        </button>
        <button 
          className={activeTab === 'vacancies' ? 'active' : ''}
          onClick={() => setActiveTab('vacancies')}
        >
          📋 Вакансии
        </button>
        <button 
          className={activeTab === 'candidates' ? 'active' : ''}
          onClick={() => setActiveTab('candidates')}
        >
          👥 Кандидаты
        </button>
      </div>

      <main className="dashboard-main">
        {loading ? (
          <div className="loading">Загрузка данных...</div>
        ) : (
          <>
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="overview-section">
                <h2>📊 Статистика платформы</h2>
                
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-value">{stats?.total_interviews || 0}</span>
                    <span className="stat-label">Всего интервью</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{stats?.completed_interviews || 0}</span>
                    <span className="stat-label">Завершено</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{stats?.in_progress_interviews || 0}</span>
                    <span className="stat-label">В процессе</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{vacancies.length}</span>
                    <span className="stat-label">Вакансий</span>
                  </div>
                </div>

                {/* Recent interviews */}
                <div className="recent-section">
                  <h3>🕐 Последние интервью</h3>
                  {interviews.length === 0 ? (
                    <p className="empty-text">Пока нет интервью</p>
                  ) : (
                    interviews.slice(0, 5).map((interview) => (
                      <div key={interview.id} className="interview-row">
                        <div className="interview-info">
                          <span className="candidate-name">
                            {interview.candidate_name || 'Кандидат'}
                          </span>
                          <span className="interview-meta">
                            {interview.direction} • {interview.selected_level}
                          </span>
                        </div>
                        <div className="interview-status">
                          <span className={`status-badge ${interview.status}`}>
                            {interview.status === 'completed' ? '✅ Завершено' : '🔄 В процессе'}
                          </span>
                          {interview.overall_grade && (
                            <span className="grade-badge">{interview.overall_grade}</span>
                          )}
                        </div>
                        <button 
                          className="view-btn"
                          onClick={() => viewReport(interview.id)}
                        >
                          Открыть
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Vacancies Tab */}
            {activeTab === 'vacancies' && (
              <div className="vacancies-section">
                <div className="section-header">
                  <h2>📋 Управление вакансиями</h2>
                  <button className="create-btn" onClick={openCreateModal}>
                    + Создать вакансию
                  </button>
                </div>
                
                {vacancies.length === 0 ? (
                  <div className="empty-state">
                    <p>Пока нет вакансий</p>
                    <p className="hint">Создайте первую вакансию для начала работы</p>
                  </div>
                ) : (
                  <div className="vacancies-table">
                    <div className="table-header">
                      <span>Название</span>
                      <span>Трек</span>
                      <span>Уровень</span>
                      <span>Кандидатов</span>
                      <span>Действия</span>
                    </div>
                    {vacancies.map((vacancy) => (
                      <div key={vacancy.id} className="table-row">
                        <span className="vacancy-title">{vacancy.title}</span>
                        <span className="vacancy-track">{vacancy.direction}</span>
                        <span className={`level-badge ${vacancy.grade_required}`}>
                          {vacancy.grade_required}
                        </span>
                        <span className="candidates-count">
                          {interviews.filter(i => i.vacancy_id === vacancy.id).length}
                        </span>
                        <div className="actions">
                          <button 
                            className="action-btn edit"
                            onClick={() => openEditModal(vacancy)}
                            title="Редактировать"
                          >
                            ✏️
                          </button>
                          <button 
                            className="action-btn delete"
                            onClick={() => handleDelete(vacancy.id)}
                            title="Удалить"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Candidates Tab */}
            {activeTab === 'candidates' && (
              <div className="candidates-section">
                <h2>👥 Все кандидаты</h2>
                
                {interviews.length === 0 ? (
                  <div className="empty-state">
                    <p>Пока нет кандидатов</p>
                  </div>
                ) : (
                  <div className="candidates-table">
                    <div className="table-header">
                      <span>Кандидат</span>
                      <span>Направление</span>
                      <span>Уровень</span>
                      <span>Статус</span>
                      <span>Оценка</span>
                      <span>Trust</span>
                      <span>Действия</span>
                    </div>
                    {interviews.map((interview) => (
                      <div key={interview.id} className="table-row">
                        <span className="candidate-name">
                          {interview.candidate_name || `Кандидат #${interview.id}`}
                        </span>
                        <span>{interview.direction}</span>
                        <span className={`level-badge ${interview.selected_level}`}>
                          {interview.selected_level}
                        </span>
                        <span className={`status-badge ${interview.status}`}>
                          {interview.status === 'completed' ? 'Завершено' : 'В процессе'}
                        </span>
                        <span className="grade">
                          {interview.overall_grade || '-'}
                          {interview.overall_score && ` (${Math.round(interview.overall_score)})`}
                        </span>
                        <span className={`trust-score ${(interview.trust_score || 100) >= 80 ? 'high' : (interview.trust_score || 100) >= 50 ? 'medium' : 'low'}`}>
                          {Math.round(interview.trust_score || 100)}%
                        </span>
                        <button 
                          className="view-btn"
                          onClick={() => viewReport(interview.id)}
                        >
                          Отчёт
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>

      {/* Modal for create/edit vacancy */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{editingVacancy ? '✏️ Редактировать вакансию' : '➕ Новая вакансия'}</h2>
            
            <div className="form-group">
              <label>Название вакансии</label>
              <input
                type="text"
                placeholder="Backend Developer Middle"
                value={formData.title}
                onChange={e => setFormData({...formData, title: e.target.value})}
              />
            </div>

            <div className="form-group">
              <label>Описание</label>
              <textarea
                placeholder="Описание вакансии и требований..."
                value={formData.description}
                onChange={e => setFormData({...formData, description: e.target.value})}
                rows={4}
              />
            </div>

            <div className="form-group">
              <label>Компания</label>
              <input
                type="text"
                placeholder="T1 Digital"
                value={formData.company}
                onChange={e => setFormData({...formData, company: e.target.value})}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Направление</label>
                <select
                  value={formData.direction}
                  onChange={e => setFormData({...formData, direction: e.target.value, skills: []})}
                >
                  <option value="backend">Backend</option>
                  <option value="frontend">Frontend</option>
                  <option value="ml">ML / Data Science</option>
                  <option value="data">Data Engineering</option>
                  <option value="devops">DevOps</option>
                  <option value="fullstack">Fullstack</option>
                </select>
              </div>

              <div className="form-group">
                <label>Уровень</label>
                <select
                  value={formData.grade_required}
                  onChange={e => setFormData({...formData, grade_required: e.target.value})}
                >
                  <option value="intern">Intern</option>
                  <option value="junior">Junior</option>
                  <option value="middle">Middle</option>
                  <option value="senior">Senior</option>
                </select>
              </div>
            </div>

            {/* Skills Selection */}
            <div className="form-group">
              <label>Требуемые навыки</label>
              <div className="skills-grid">
                {availableSkills.map(skill => {
                  const selected = formData.skills.find(s => s.skill_id === skill.id)
                  return (
                    <div 
                      key={skill.id} 
                      className={`skill-chip ${selected ? 'selected' : ''} ${selected?.is_critical ? 'critical' : ''}`}
                      onClick={() => toggleSkill(skill.id, skill.name)}
                    >
                      <span className="skill-name">{skill.name}</span>
                      {selected && (
                        <span 
                          className="skill-critical"
                          onClick={(e) => { e.stopPropagation(); toggleCritical(skill.id); }}
                          title="Критический навык"
                        >
                          ⭐
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
              {formData.skills.length > 0 && (
                <div className="selected-skills-info">
                  Выбрано: {formData.skills.length} навыков
                  {formData.skills.filter(s => s.is_critical).length > 0 && (
                    <span> (⭐ {formData.skills.filter(s => s.is_critical).length} критических)</span>
                  )}
                </div>
              )}
            </div>

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowModal(false)}>
                Отмена
              </button>
              <button 
                className="btn-save" 
                onClick={handleSave}
                disabled={saving || !formData.title}
              >
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminDashboard

// пидормот

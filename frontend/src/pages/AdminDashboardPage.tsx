import { useState, useEffect } from 'react'
import { adminAPI } from '../api/client'

function AdminDashboardPage() {
  const [interviews, setInterviews] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [interviewsData, statsData] = await Promise.all([
        adminAPI.listInterviews(),
        adminAPI.getStatistics(),
      ])
      setInterviews(interviewsData)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load admin data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>Панель администратора</h1>
      <p style={{ color: '#888', marginBottom: '40px' }}>Управление интервью и статистика</p>

      {/* Statistics */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '40px' }}>
          <div style={{ padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
            <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>{stats.total_interviews}</div>
            <div style={{ color: '#888', fontSize: '1.2rem' }}>Всего интервью</div>
          </div>
          
          <div style={{ padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
            <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>{stats.completed_interviews}</div>
            <div style={{ color: '#888', fontSize: '1.2rem' }}>Завершено</div>
          </div>
          
          <div style={{ padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
            <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>{stats.in_progress}</div>
            <div style={{ color: '#888', fontSize: '1.2rem' }}>В процессе</div>
          </div>
        </div>
      )}

      {/* Interviews List */}
      <h2 style={{ fontSize: '1.8rem', marginBottom: '20px' }}>Список интервью</h2>
      <div style={{ background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #333' }}>
              <th style={{ padding: '15px', textAlign: 'left' }}>ID</th>
              <th style={{ padding: '15px', textAlign: 'left' }}>Кандидат</th>
              <th style={{ padding: '15px', textAlign: 'left' }}>Уровень</th>
              <th style={{ padding: '15px', textAlign: 'left' }}>Направление</th>
              <th style={{ padding: '15px', textAlign: 'left' }}>Статус</th>
              <th style={{ padding: '15px', textAlign: 'left' }}>Грейд</th>
              <th style={{ padding: '15px', textAlign: 'left' }}>Балл</th>
            </tr>
          </thead>
          <tbody>
            {interviews.map((interview) => (
              <tr key={interview.id} style={{ borderBottom: '1px solid #333' }}>
                <td style={{ padding: '15px' }}>{interview.id}</td>
                <td style={{ padding: '15px' }}>{interview.candidate_name || 'Аноним'}</td>
                <td style={{ padding: '15px' }}>{interview.selected_level}</td>
                <td style={{ padding: '15px' }}>{interview.direction}</td>
                <td style={{ padding: '15px' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    background: interview.status === 'completed' ? '#22c55e' : '#3b82f6',
                    color: 'white',
                    fontSize: '0.85rem'
                  }}>
                    {interview.status}
                  </span>
                </td>
                <td style={{ padding: '15px' }}>{interview.overall_grade || '-'}</td>
                <td style={{ padding: '15px' }}>{interview.overall_score?.toFixed(1) || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default AdminDashboardPage


// пидормот

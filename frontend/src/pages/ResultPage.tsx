import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { interviewAPI } from '../api/client'
import SkillRadarChart from '../components/SkillRadarChart'
import GradeProgressBar from '../components/GradeProgressBar'
import TrustScoreBadge from '../components/TrustScoreBadge'

function ResultPage() {
  const { interviewId } = useParams<{ interviewId: string }>()
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadReport()
  }, [interviewId])

  const loadReport = async () => {
    try {
      const data = await interviewAPI.getFinalReport(Number(interviewId))
      setReport(data)
    } catch (error) {
      console.error('Failed to load report:', error)
      alert('Ошибка при загрузке отчёта')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Генерация отчёта...</div>
  }

  if (!report) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Отчёт не найден</div>
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>Результаты интервью</h1>
      <p style={{ color: '#888', marginBottom: '40px' }}>
        {report.interview.candidate_name || 'Кандидат'} • {report.interview.direction} • {report.interview.selected_level}
      </p>

      {/* Overall Grade and Trust Score */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '40px' }}>
        <div style={{ flex: 1, padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '10px', color: '#888' }}>Финальный грейд</h2>
          <div style={{ fontSize: '3rem', fontWeight: 'bold' }}>
            {report.interview.overall_grade?.toUpperCase()}
          </div>
          <div style={{ fontSize: '1.5rem', color: '#888' }}>
            {report.interview.overall_score?.toFixed(1)}/100
          </div>
        </div>
        
        <div style={{ flex: 1, padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
          <TrustScoreBadge score={report.interview.trust_score} />
        </div>
      </div>

      {/* Grade Progress Bar */}
      <div style={{ marginBottom: '40px' }}>
        <GradeProgressBar score={report.interview.overall_score} />
      </div>

      {/* Skill Radar Chart */}
      {report.skill_assessment && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '1.8rem', marginBottom: '20px' }}>Карта навыков</h2>
          <SkillRadarChart assessment={report.skill_assessment} />
        </div>
      )}

      {/* Statistics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '40px' }}>
        <div style={{ padding: '20px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{report.tasks.length}</div>
          <div style={{ color: '#888' }}>Задач решено</div>
        </div>
        
        <div style={{ padding: '20px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{report.total_hints_used}</div>
          <div style={{ color: '#888' }}>Подсказок использовано</div>
        </div>
        
        <div style={{ padding: '20px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{report.total_submissions}</div>
          <div style={{ color: '#888' }}>Попыток отправки</div>
        </div>
      </div>

      {/* Next Steps */}
      {report.skill_assessment?.next_grade_tips && (
        <div style={{ padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>Рекомендации для роста</h2>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {report.skill_assessment.next_grade_tips.map((tip: string, index: number) => (
              <li key={index} style={{ padding: '10px 0', borderBottom: index < report.skill_assessment.next_grade_tips.length - 1 ? '1px solid #333' : 'none' }}>
                • {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ResultPage


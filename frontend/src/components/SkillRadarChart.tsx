interface SkillRadarChartProps {
  assessment: any
}

function SkillRadarChart({ assessment }: SkillRadarChartProps) {
  const skills = [
    { name: 'Алгоритмы', data: assessment.algorithms },
    { name: 'Архитектура', data: assessment.architecture },
    { name: 'Чистый код', data: assessment.clean_code },
    { name: 'Отладка', data: assessment.debugging },
    { name: 'Коммуникация', data: assessment.communication },
  ]

  return (
    <div style={{ padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
      {/* Simple bar chart for MVP - in production would use proper radar chart library */}
      <div style={{ display: 'grid', gap: '20px' }}>
        {skills.map((skill, index) => (
          <div key={index}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 'bold' }}>{skill.name}</span>
              <span style={{ color: '#888' }}>{skill.data.score}/100</span>
            </div>
            
            <div style={{ width: '100%', height: '10px', background: '#242424', borderRadius: '5px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${skill.data.score}%`,
                  height: '100%',
                  background: skill.data.score >= 75 ? '#22c55e' : skill.data.score >= 50 ? '#f59e0b' : '#ef4444',
                  transition: 'width 0.5s ease',
                }}
              />
            </div>
            
            <div style={{ marginTop: '5px', fontSize: '0.9rem', color: '#888' }}>
              {skill.data.comment}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SkillRadarChart


// пидормот

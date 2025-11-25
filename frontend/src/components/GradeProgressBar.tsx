interface GradeProgressBarProps {
  score: number
}

function GradeProgressBar({ score }: GradeProgressBarProps) {
  const grades = [
    { name: 'Junior', min: 0, max: 40 },
    { name: 'Junior+', min: 40, max: 55 },
    { name: 'Middle', min: 55, max: 70 },
    { name: 'Middle+', min: 70, max: 85 },
    { name: 'Senior', min: 85, max: 100 },
  ]

  const getCurrentGrade = () => {
    return grades.find((g) => score >= g.min && score < g.max) || grades[grades.length - 1]
  }

  const currentGrade = getCurrentGrade()
  const nextGrade = grades[grades.indexOf(currentGrade) + 1]

  return (
    <div style={{ padding: '30px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '20px' }}>Прогресс по грейдам</h2>
      
      {/* Progress bar */}
      <div style={{ position: 'relative', marginBottom: '40px' }}>
        <div style={{ width: '100%', height: '20px', background: '#242424', borderRadius: '10px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${score}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #3b82f6, #22c55e)',
              transition: 'width 1s ease',
            }}
          />
        </div>
        
        {/* Markers */}
        <div style={{ position: 'relative', marginTop: '10px', display: 'flex', justifyContent: 'space-between' }}>
          {grades.map((grade, index) => (
            <div key={index} style={{ textAlign: 'center', fontSize: '0.85rem' }}>
              <div style={{ color: score >= grade.min ? '#22c55e' : '#888' }}>{grade.name}</div>
              <div style={{ color: '#666' }}>{grade.min}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* Current status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '0.9rem', color: '#888', marginBottom: '5px' }}>Текущий грейд</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{currentGrade.name}</div>
        </div>
        
        {nextGrade && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.9rem', color: '#888', marginBottom: '5px' }}>До {nextGrade.name}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {(nextGrade.min - score).toFixed(0)} баллов
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default GradeProgressBar


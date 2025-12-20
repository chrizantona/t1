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
    <div className="card" style={{ padding: '32px' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '24px', color: 'var(--color-text-blue)' }}>
        📊 Прогресс по грейдам
      </h2>
      
      {/* Progress bar */}
      <div style={{ position: 'relative', marginBottom: '40px' }}>
        <div style={{ width: '100%', height: '24px', background: 'var(--color-bg-secondary)', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--color-border)' }}>
          <div
            style={{
              width: `${score}%`,
              height: '100%',
              background: 'linear-gradient(90deg, var(--color-primary-dark), var(--color-primary))',
              transition: 'width 1s ease',
              boxShadow: '0 2px 8px rgba(0, 173, 255, 0.3)',
            }}
          />
        </div>
        
        {/* Markers */}
        <div style={{ position: 'relative', marginTop: '16px', display: 'flex', justifyContent: 'space-between' }}>
          {grades.map((grade, index) => (
            <div key={index} style={{ textAlign: 'center', fontSize: '0.85rem' }}>
              <div style={{ 
                color: score >= grade.min ? 'var(--color-primary)' : 'var(--color-text-light)', 
                fontWeight: score >= grade.min ? 600 : 400 
              }}>
                {grade.name}
              </div>
              <div style={{ color: 'var(--color-text-light)', fontSize: '0.75rem', marginTop: '4px' }}>
                {grade.min}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Current status */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', padding: '24px', background: 'var(--color-bg-light)', borderRadius: '12px' }}>
        <div>
          <div style={{ fontSize: '0.9rem', color: 'var(--color-text-light)', marginBottom: '8px', fontWeight: 600 }}>
            Текущий грейд
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>
            {currentGrade.name}
          </div>
        </div>
        
        {nextGrade && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.9rem', color: 'var(--color-text-light)', marginBottom: '8px', fontWeight: 600 }}>
              До {nextGrade.name}
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: 'var(--color-secondary)' }}>
              {(nextGrade.min - score).toFixed(0)} баллов
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default GradeProgressBar


// пидормот

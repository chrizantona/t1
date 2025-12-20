interface TrustScoreBadgeProps {
  score: number
}

function TrustScoreBadge({ score }: TrustScoreBadgeProps) {
  const getColor = () => {
    if (score >= 90) return '#22c55e'
    if (score >= 70) return '#f59e0b'
    return '#ef4444'
  }

  const getLabel = () => {
    if (score >= 90) return 'Высокое доверие'
    if (score >= 70) return 'Среднее доверие'
    return 'Низкое доверие'
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.2rem', marginBottom: '10px', color: '#888' }}>Trust Score</h2>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ fontSize: '3rem', fontWeight: 'bold', color: getColor() }}>
          {score.toFixed(0)}
        </div>
        <div>
          <div style={{ fontSize: '1.5rem', marginBottom: '5px' }}>{getLabel()}</div>
          <div style={{ fontSize: '0.9rem', color: '#888' }}>
            Анализ подозрительных действий
          </div>
        </div>
      </div>

      {/* Progress circle or bar */}
      <div style={{ marginTop: '20px', width: '100%', height: '10px', background: '#242424', borderRadius: '5px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${score}%`,
            height: '100%',
            background: getColor(),
            transition: 'width 0.5s ease',
          }}
        />
      </div>
    </div>
  )
}

export default TrustScoreBadge


// пидормот

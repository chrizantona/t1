interface MetricsPanelProps {
  metrics: {
    tasksCompleted: number
    totalTasks: number
    hintsUsed: number
    averageScore: number
    timeSpent: number
  }
}

function MetricsPanel({ metrics }: MetricsPanelProps) {
  return (
    <div style={{ padding: '20px', background: '#1a1a1a', borderRadius: '12px', border: '1px solid #333' }}>
      <h3 style={{ marginBottom: '15px' }}>Метрики</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
        <div>
          <div style={{ fontSize: '0.85rem', color: '#888' }}>Задачи</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {metrics.tasksCompleted}/{metrics.totalTasks}
          </div>
        </div>
        
        <div>
          <div style={{ fontSize: '0.85rem', color: '#888' }}>Подсказки</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.hintsUsed}</div>
        </div>
        
        <div>
          <div style={{ fontSize: '0.85rem', color: '#888' }}>Средний балл</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{metrics.averageScore.toFixed(1)}</div>
        </div>
        
        <div>
          <div style={{ fontSize: '0.85rem', color: '#888' }}>Время</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {Math.floor(metrics.timeSpent / 60)}м
          </div>
        </div>
      </div>
    </div>
  )
}

export default MetricsPanel


// пидормот

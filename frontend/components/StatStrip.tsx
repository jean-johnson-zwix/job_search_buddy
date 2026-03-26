const ACCENT: Record<string, string> = {
  yellow:   'var(--yellow)',
  sage:     'var(--sage)',
  pink:     'var(--pink)',
  lavender: 'var(--lavender)',
}

interface Stat { label: string; value: string | number; accent: string }

export function StatStrip({ stats }: { stats: Stat[] }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${stats.length}, 1fr)`, gap: '10px', marginBottom: '20px' }}>
      {stats.map(s => (
        <div key={s.label} style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          padding: '14px 16px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
            background: ACCENT[s.accent] ?? 'var(--yellow)',
          }} />
          <div style={{
            fontSize: typeof s.value === 'string' && s.value.length > 6 ? '15px' : '26px',
            fontWeight: 300,
            color: ACCENT[s.accent] ?? 'var(--yellow)',
            lineHeight: 1,
          }}>
            {s.value}
          </div>
          <div style={{
            fontFamily: 'DM Mono, monospace',
            fontSize: '10px',
            color: 'var(--text-muted)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginTop: '5px',
          }}>
            {s.label}
          </div>
        </div>
      ))}
    </div>
  )
}

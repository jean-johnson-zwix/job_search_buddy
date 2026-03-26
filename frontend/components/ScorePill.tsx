function pillStyle(score: number) {
  if (score >= 75) return { color: 'var(--sage)',   bg: 'rgba(143,191,138,0.06)', border: 'rgba(143,191,138,0.2)'  }
  if (score >= 55) return { color: 'var(--yellow)', bg: 'rgba(245,230,66,0.06)',  border: 'rgba(245,230,66,0.2)'   }
  return              { color: 'var(--pink)',   bg: 'rgba(240,111,170,0.06)', border: 'rgba(240,111,170,0.2)'  }
}

export function ScorePill({ label, score }: { label: string; score: number }) {
  const s = pillStyle(score)
  return (
    <span style={{
      fontFamily: 'DM Mono, monospace', fontSize: '10px', letterSpacing: '0.04em',
      color: s.color, background: s.bg, border: `1px solid ${s.border}`,
      borderRadius: '3px', padding: '2px 9px',
    }}>
      {label}: {score}%
    </span>
  )
}

function ringStyle(score: number) {
  if (score >= 75) return { color: 'var(--sage)',   bg: 'rgba(143,191,138,0.06)', border: 'rgba(143,191,138,0.3)'  }
  if (score >= 55) return { color: 'var(--yellow)', bg: 'rgba(245,230,66,0.06)',  border: 'rgba(245,230,66,0.3)'   }
  return              { color: 'var(--pink)',   bg: 'rgba(240,111,170,0.06)', border: 'rgba(240,111,170,0.3)'  }
}

export function ScoreRing({ score }: { score: number }) {
  const s = ringStyle(score)
  return (
    <div style={{
      width: '52px', height: '52px', borderRadius: '50%', flexShrink: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      border: `1px solid ${s.border}`, background: s.bg,
    }}>
      <span style={{ fontFamily: 'Outfit, sans-serif', fontSize: '14px', fontWeight: 300, color: s.color, lineHeight: 1 }}>
        {score}%
      </span>
      <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: '1px' }}>
        skill
      </span>
    </div>
  )
}

const TIER: Record<string, { color: string; bg: string; border: string; label: string }> = {
  faang:   { color: 'var(--yellow)',   bg: 'rgba(245,230,66,0.06)',   border: 'rgba(245,230,66,0.25)',   label: 'FAANG'   },
  unicorn: { color: 'var(--lavender)', bg: 'rgba(168,153,230,0.06)',  border: 'rgba(168,153,230,0.25)',  label: 'Unicorn' },
  startup: { color: 'var(--sage)',     bg: 'rgba(143,191,138,0.06)',  border: 'rgba(143,191,138,0.25)',  label: 'Startup' },
}

export function TierBadge({ tier }: { tier: string }) {
  const t = TIER[tier?.toLowerCase()] ?? TIER.startup
  return (
    <span style={{
      fontFamily: 'DM Mono, monospace',
      fontSize: '10px',
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
      color: t.color,
      background: t.bg,
      border: `1px solid ${t.border}`,
      borderRadius: '3px',
      padding: '2px 8px',
    }}>
      {t.label}
    </span>
  )
}

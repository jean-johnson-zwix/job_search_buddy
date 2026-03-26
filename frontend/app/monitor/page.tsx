'use client'
import { useState, useEffect } from 'react'
import { StatStrip } from '@/components/StatStrip'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

const CARD_STYLE = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  borderRadius: '10px',
  padding: '16px',
}

const SECTION_LABEL = (color = 'var(--yellow)') => ({
  fontFamily: 'DM Mono, monospace',
  fontSize: '10px',
  letterSpacing: '0.12em',
  textTransform: 'uppercase' as const,
  color,
  marginBottom: '12px',
})

const TASK_COLOR: Record<string, string> = {
  job_skill_extraction:   '#f5e642',
  job_resume_match:       '#8fbf8a',
  resume_skill_extraction:'#a899e6',
  resume_condensation:    '#f06faa',
}

const PROVIDER_COLOR: Record<string, string> = {
  gemini:     '#f5e642',
  groq:       '#8fbf8a',
  openrouter: '#a899e6',
}

const TOOLTIP_STYLE = {
  background: 'var(--bg-surface)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
  fontFamily: 'DM Mono, monospace',
  fontSize: '11px',
  color: 'var(--cream)',
}

function formatTask(task: string) {
  return task.replace(/_/g, ' ')
}

export default function MonitorPage() {
  const [rows,    setRows]    = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/usage')
      .then(r => r.json())
      .then(d => { setRows(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  // Group by run_date
  const byDate: Record<string, any[]> = {}
  for (const row of rows) {
    if (!byDate[row.run_date]) byDate[row.run_date] = []
    byDate[row.run_date].push(row)
  }
  const dates = Object.keys(byDate).sort((a, b) => b.localeCompare(a))
  const latestRows = byDate[dates[0]] ?? []

  // Stats from latest run
  const totalCalls  = latestRows.reduce((s: number, r: any) => s + r.calls, 0)
  const totalTokens = latestRows.reduce((s: number, r: any) => s + r.total_tokens, 0)
  const providers   = [...new Set(latestRows.map((r: any) => r.provider))].join(', ')
  const runDays     = dates.length

  const stats = [
    { label: 'Runs tracked',   value: runDays,                           accent: 'yellow'   },
    { label: 'Calls today',    value: totalCalls || '—',                 accent: 'sage'     },
    { label: 'Tokens today',   value: totalTokens ? totalTokens.toLocaleString() : '—', accent: 'lavender' },
    { label: 'Provider',       value: providers || '—',                  accent: 'pink'     },
  ]

  // Chart: tokens per run date (last 14 days)
  const tokenTrend = dates.slice(0, 14).reverse().map(date => ({
    date: date.slice(5), // MM-DD
    tokens: byDate[date].reduce((s: number, r: any) => s + r.total_tokens, 0),
    calls:  byDate[date].reduce((s: number, r: any) => s + r.calls, 0),
  }))

  return (
    <div>
      <StatStrip stats={stats} />

      {loading && (
        <div style={{ textAlign: 'center', padding: '60px', fontFamily: 'DM Mono, monospace', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
          Loading usage data...
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(240,111,170,0.06)', border: '1px solid rgba(240,111,170,0.2)', borderRadius: '6px', padding: '12px', color: 'var(--pink)', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {!loading && !error && rows.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px', letterSpacing: '0.08em' }}>
          No usage data yet — run the pipeline first
        </div>
      )}

      {!loading && !error && rows.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* Token usage over time */}
          <div style={CARD_STYLE}>
            <div style={SECTION_LABEL()}>Token usage — last {tokenTrend.length} runs</div>
            <p style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontSize: '16px', color: 'var(--cream)', marginBottom: '16px' }}>
              Total tokens per pipeline run
            </p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={tokenTrend} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={(v: number) => v >= 1000 ? `${(v/1000).toFixed(1)}k` : String(v)} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => [v.toLocaleString(), 'tokens']} />
                <Bar dataKey="tokens" radius={[3, 3, 0, 0]}>
                  {tokenTrend.map((_, i) => (
                    <Cell key={i} fill="#f5e642" fillOpacity={i === tokenTrend.length - 1 ? 0.9 : 0.4} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Per-run breakdown */}
          {dates.map(date => {
            const runRows = byDate[date]
            const runTotal  = runRows.reduce((s: number, r: any) => s + r.total_tokens, 0)
            const runCalls  = runRows.reduce((s: number, r: any) => s + r.calls, 0)
            const isToday   = date === dates[0]
            return (
              <div key={date} style={{ ...CARD_STYLE, borderLeft: isToday ? '2px solid var(--yellow)' : '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div>
                    <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '11px', color: isToday ? 'var(--yellow)' : 'var(--sand)', letterSpacing: '0.06em' }}>
                      {date}
                    </span>
                    {isToday && (
                      <span style={{ marginLeft: '8px', fontFamily: 'DM Mono, monospace', fontSize: '9px', color: 'var(--bg-dark)', background: 'var(--yellow)', borderRadius: '2px', padding: '1px 6px', letterSpacing: '0.06em' }}>
                        LATEST
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '16px' }}>
                    <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>
                      {runCalls} calls
                    </span>
                    <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--lavender)' }}>
                      {runTotal.toLocaleString()} tokens
                    </span>
                  </div>
                </div>

                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {['Task', 'Provider / Model', 'Calls', 'Prompt', 'Completion', 'Total', 'Avg ms'].map(h => (
                        <th key={h} style={{ textAlign: 'left', padding: '4px 8px', fontFamily: 'DM Mono, monospace', fontSize: '9px', fontWeight: 400, color: 'var(--text-muted)', borderBottom: '1px solid var(--border)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {runRows.map((r: any) => {
                      const taskColor    = TASK_COLOR[r.task]    ?? 'var(--sand)'
                      const provColor    = PROVIDER_COLOR[r.provider] ?? 'var(--sand)'
                      return (
                        <tr key={r.task} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <td style={{ padding: '7px 8px' }}>
                            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: taskColor, background: `${taskColor}10`, border: `1px solid ${taskColor}30`, borderRadius: '3px', padding: '2px 7px', letterSpacing: '0.04em' }}>
                              {formatTask(r.task)}
                            </span>
                          </td>
                          <td style={{ padding: '7px 8px' }}>
                            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: provColor }}>{r.provider}</span>
                            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '9px', color: 'var(--text-muted)', marginLeft: '5px' }}>{r.model}</span>
                          </td>
                          <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '11px', color: 'var(--cream)' }}>{r.calls}</td>
                          <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-secondary)' }}>{r.prompt_tokens.toLocaleString()}</td>
                          <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-secondary)' }}>{r.completion_tokens.toLocaleString()}</td>
                          <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '11px', color: 'var(--lavender)' }}>{r.total_tokens.toLocaleString()}</td>
                          <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>{r.avg_duration_ms}ms</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )
          })}

        </div>
      )}
    </div>
  )
}

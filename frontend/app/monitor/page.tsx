'use client'
import { useState, useEffect } from 'react'
import { StatStrip } from '@/components/StatStrip'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
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
  cerebras:   '#f0a070',
  sambanova:  '#70c8f0',
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
  const [rows,       setRows]       = useState<any[]>([])
  const [errorRows,  setErrorRows]  = useState<any[]>([])
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/usage').then(r => r.json()),
      fetch('/api/errors').then(r => r.json()),
    ])
      .then(([usage, errs]) => {
        setRows(Array.isArray(usage) ? usage : [])
        setErrorRows(Array.isArray(errs) ? errs : [])
        setLoading(false)
      })
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
  const runDays     = dates.length

  // Errors grouped by date
  const errorsByDate: Record<string, any[]> = {}
  for (const e of errorRows) {
    if (!errorsByDate[e.run_date]) errorsByDate[e.run_date] = []
    errorsByDate[e.run_date].push(e)
  }
  const todayErrors = errorsByDate[dates[0]] ?? []

  const stats = [
    { label: 'Days tracked',   value: runDays,                                          accent: 'yellow'   },
    { label: 'Calls today',    value: totalCalls || '—',                                accent: 'sage'     },
    { label: 'Tokens today',   value: totalTokens ? totalTokens.toLocaleString() : '—', accent: 'lavender' },
    { label: 'Errors today',   value: todayErrors.length || '—',                        accent: 'pink'     },
  ]

  // Chart: tokens per day broken down by task (last 14 days)
  const ALL_TASKS = Object.keys(TASK_COLOR)
  const tokenTrend = dates.slice(0, 14).reverse().map(date => {
    const entry: Record<string, any> = { date: date.slice(5) }
    for (const row of byDate[date]) {
      entry[row.task] = (entry[row.task] ?? 0) + row.total_tokens
    }
    return entry
  })

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
            <div style={SECTION_LABEL()}>Token usage — last {tokenTrend.length} days</div>
            <p style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontSize: '16px', color: 'var(--cream)', marginBottom: '16px' }}>
              Tokens per task per day
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={tokenTrend} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={(v: number) => v >= 1000 ? `${(v/1000).toFixed(1)}k` : String(v)} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any, name: any) => [v.toLocaleString(), formatTask(String(name))]} />
                <Legend wrapperStyle={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-secondary)' }} formatter={formatTask} />
                {ALL_TASKS.map((task, i) => (
                  <Bar key={task} dataKey={task} stackId="a" fill={TASK_COLOR[task]} fillOpacity={0.85}
                    radius={i === ALL_TASKS.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Per-day breakdown */}
          {dates.map(date => {
            // Aggregate rows by (task, provider, model) so multiple same-day runs collapse into daily totals
            const aggMap: Record<string, any> = {}
            for (const r of byDate[date]) {
              const key = `${r.task}__${r.provider}__${r.model}`
              if (!aggMap[key]) {
                aggMap[key] = { ...r }
              } else {
                const prev     = aggMap[key]
                const newCalls = prev.calls + r.calls
                aggMap[key] = {
                  ...prev,
                  calls:             newCalls,
                  prompt_tokens:     prev.prompt_tokens     + r.prompt_tokens,
                  completion_tokens: prev.completion_tokens + r.completion_tokens,
                  total_tokens:      prev.total_tokens      + r.total_tokens,
                  avg_duration_ms:   Math.round(
                    (prev.avg_duration_ms * prev.calls + r.avg_duration_ms * r.calls) / newCalls
                  ),
                }
              }
            }
            const dailyRows = Object.values(aggMap)
            const dayTotal  = dailyRows.reduce((s: number, r: any) => s + r.total_tokens, 0)
            const dayCalls  = dailyRows.reduce((s: number, r: any) => s + r.calls, 0)
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
                        TODAY
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '16px' }}>
                    <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>
                      {dayCalls} calls
                    </span>
                    <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--lavender)' }}>
                      {dayTotal.toLocaleString()} tokens
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
                    {dailyRows.map((r: any) => {
                      const taskColor = TASK_COLOR[r.task]        ?? 'var(--sand)'
                      const provColor = PROVIDER_COLOR[r.provider] ?? 'var(--sand)'
                      return (
                        <tr key={`${r.task}__${r.provider}__${r.model}`} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
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

          {/* Pipeline errors */}
          {Object.keys(errorsByDate).length > 0 && (
            <div style={CARD_STYLE}>
              <div style={SECTION_LABEL('var(--pink)')}>Pipeline errors — last 30 days</div>
              {Object.entries(errorsByDate)
                .sort(([a], [b]) => b.localeCompare(a))
                .map(([date, errs]) => (
                  <div key={date} style={{ marginBottom: '16px' }}>
                    <div style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--sand)', letterSpacing: '0.06em', marginBottom: '6px' }}>
                      {date} · <span style={{ color: 'var(--pink)' }}>{errs.length} error{errs.length !== 1 ? 's' : ''}</span>
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          {['Node', 'Job', 'Error'].map(h => (
                            <th key={h} style={{ textAlign: 'left', padding: '4px 8px', fontFamily: 'DM Mono, monospace', fontSize: '9px', fontWeight: 400, color: 'var(--text-muted)', borderBottom: '1px solid var(--border)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {errs.map((e: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                            <td style={{ padding: '7px 8px', whiteSpace: 'nowrap' }}>
                              <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--pink)', background: 'rgba(240,111,170,0.08)', border: '1px solid rgba(240,111,170,0.2)', borderRadius: '3px', padding: '2px 7px' }}>
                                {e.node}
                              </span>
                            </td>
                            <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--sand)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {e.job_title ?? e.job_id ?? '—'}
                            </td>
                            <td style={{ padding: '7px 8px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                              {e.error}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
            </div>
          )}

        </div>
      )}
    </div>
  )
}

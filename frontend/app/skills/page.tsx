'use client'
import { useState, useEffect } from 'react'
import { StatStrip } from '@/components/StatStrip'
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend,
} from 'recharts'

const CHART_COLORS = [
  '#f5e642',  // yellow
  '#8fbf8a',  // sage
  '#f06faa',  // pink
  '#a899e6',  // lavender
  '#f5a142',  // orange
  '#42c9f5',  // cyan
  '#e6c499',  // peach
  '#99e6c9',  // mint
  '#e699a8',  // rose
  '#99c9e6',  // sky
  '#c9e699',  // lime
  '#c4a8e6',  // violet
]

const SECTION_LABEL = (color = 'var(--yellow)') => ({
  fontFamily: 'DM Mono, monospace',
  fontSize: '10px',
  letterSpacing: '0.12em',
  textTransform: 'uppercase' as const,
  color,
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  marginBottom: '6px',
})

const CARD_STYLE = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  borderRadius: '10px',
  padding: '16px',
}

const ROLES = ['All', 'SWE', 'ML', 'DevOps', 'Data']
const TIERS = ['All', 'faang', 'unicorn', 'startup']

export default function SkillsPage() {
  const [data,           setData]           = useState<any>(null)
  const [loading,        setLoading]        = useState(true)
  const [roleFilter,     setRoleFilter]     = useState('All')
  const [tierFilter,     setTierFilter]     = useState('All')
  const [selectedSkills, setSelectedSkills] = useState<string[]>([])

  useEffect(() => {
    const params = new URLSearchParams()
    if (roleFilter !== 'All') params.set('role_type',    roleFilter)
    if (tierFilter !== 'All') params.set('company_tier', tierFilter)
    setLoading(true)
    fetch(`/api/skills?${params}`)
      .then(r => r.json())
      .then(d => {
        setData(d)
        const topGaps = (d.gaps ?? []).filter((g: any) => g.status === 'gap').slice(0, 4).map((g: any) => g.skill)
        setSelectedSkills(topGaps)
        setLoading(false)
      })
  }, [roleFilter, tierFilter])

  const trendData = (() => {
    if (!data?.trends) return []
    const weeks: Record<string, any> = {}
    for (const r of data.trends) {
      if (!selectedSkills.includes(r.skill)) continue
      if (!weeks[r.week_start]) weeks[r.week_start] = { week: r.week_start.slice(5) }
      weeks[r.week_start][r.skill] = Math.round(r.pct_of_jobs * 100)
    }
    return Object.values(weeks).sort((a: any, b: any) => a.week.localeCompare(b.week))
  })()

  // Sum pct_of_jobs across all weeks per skill, then sort by total demand
  const trendTotals: Record<string, number> = {}
  for (const r of (data?.trends ?? [])) {
    trendTotals[r.skill] = (trendTotals[r.skill] ?? 0) + r.pct_of_jobs
  }
  const allTrendSkills = Object.entries(trendTotals)
    .sort(([, a], [, b]) => b - a)
    .map(([skill]) => skill) as string[]

  // Stable skill → color mapping so button and chart line always match.
  // Cover all trend skills first, then fill in any selected skills not in trend data
  // (e.g. gap skills pre-selected on load that may not appear in the trend window).
  const skillColor: Record<string, string> = {}
  allTrendSkills.forEach((skill, i) => {
    skillColor[skill] = CHART_COLORS[i % CHART_COLORS.length]
  })
  selectedSkills.forEach((skill, i) => {
    if (!skillColor[skill]) {
      skillColor[skill] = CHART_COLORS[(allTrendSkills.length + i) % CHART_COLORS.length]
    }
  })

  const SELECT_STYLE = {
    fontFamily: 'DM Mono, monospace',
    fontSize: '11px',
    border: '1px solid var(--border)',
    borderRadius: '4px',
    padding: '5px 10px',
    background: 'var(--bg-surface)',
    color: 'var(--sand)',
    cursor: 'pointer',
  }

  const TOOLTIP_STYLE = {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    borderRadius: '4px',
    fontFamily: 'DM Mono, monospace',
    fontSize: '11px',
    color: 'var(--cream)',
  }

  const stats = [
    { label: 'Jobs analyzed',    value: data?.topSkills?.[0]?.count ?? '—',                                    accent: 'yellow'   },
    { label: 'Skills you have',  value: data?.topSkills?.filter((s: any) => s.has_skill).length ?? '—',        accent: 'sage'     },
    { label: 'Skill gaps',       value: data?.gaps?.filter((g: any) => g.status === 'gap').length ?? '—',      accent: 'pink'     },
    { label: 'Fastest growing',  value: data?.trends ? allTrendSkills[0] ?? '—' : '—',                        accent: 'lavender' },
  ]

  return (
    <div>
      <StatStrip stats={stats} />

      {/* Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <select style={SELECT_STYLE} value={roleFilter} onChange={e => setRoleFilter(e.target.value)}>
          {ROLES.map(r => <option key={r} value={r}>{r === 'All' ? 'All roles' : r}</option>)}
        </select>
        <select style={SELECT_STYLE} value={tierFilter} onChange={e => setTierFilter(e.target.value)}>
          {TIERS.map(t => <option key={t} value={t}>{t === 'All' ? 'All tiers' : t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
        </select>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '60px', fontFamily: 'DM Mono, monospace', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
          Loading skills data...
        </div>
      )}

      {!loading && data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          {/* Section 1 — Top skills */}
          <div style={CARD_STYLE}>
            <div style={SECTION_LABEL()}>Top skills this week</div>
            <p style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontSize: '16px', fontWeight: 300, color: 'var(--cream)', marginBottom: '14px' }}>
              What the market wants
            </p>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-secondary)' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: 'var(--sage)' }} /> You have it
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-secondary)' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: 'var(--pink)' }} /> Gap
              </div>
            </div>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={data.topSkills} layout="vertical" margin={{ left: 90, right: 40, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v: number) => `${v}%`} tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="skill" tick={{ fontSize: 11, fontFamily: 'DM Mono, monospace', fill: 'var(--text-secondary)' }} width={85} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => [`${v}%`, 'Jobs requiring']} />
                <Bar dataKey="pct" radius={[0, 3, 3, 0]}>
                  {data.topSkills.map((entry: any, i: number) => (
                    <Cell key={i} fill={entry.has_skill ? '#8fbf8a' : '#f06faa'} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Section 2 — Trends */}
          <div style={CARD_STYLE}>
            <div style={SECTION_LABEL('var(--lavender)')}>Trends</div>
            <p style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontSize: '16px', fontWeight: 300, color: 'var(--cream)', marginBottom: '4px' }}>
              Skill demand over time
            </p>
            <p style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '12px' }}>
              last 8 weeks · select skills to compare
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '16px' }}>
              {allTrendSkills.slice(0, CHART_COLORS.length).map((skill) => {
                const color = skillColor[skill]
                const active = selectedSkills.includes(skill)
                return (
                  <button
                    key={skill}
                    onClick={() => setSelectedSkills(prev =>
                      prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]
                    )}
                    style={{
                      fontFamily: 'DM Mono, monospace', fontSize: '10px', letterSpacing: '0.04em',
                      padding: '2px 9px', borderRadius: '3px', cursor: 'pointer',
                      background: active ? color : 'transparent',
                      color:      active ? 'var(--bg-dark)' : 'var(--text-secondary)',
                      border:     `1px solid ${active ? color : 'var(--border)'}`,
                      transition: 'all 0.15s',
                    }}
                  >
                    {skill}
                  </button>
                )
              })}
            </div>
            {trendData.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', fontFamily: 'DM Mono, monospace', fontSize: '11px', color: 'var(--text-muted)' }}>
                No trend data yet — populates every Monday
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="week" tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v: number) => `${v}%`} tick={{ fontSize: 10, fontFamily: 'DM Mono, monospace', fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => `${v}%`} />
                  <Legend wrapperStyle={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-secondary)' }} />
                  {selectedSkills.map((skill) => (
                    <Line key={skill} type="monotone" dataKey={skill}
                      stroke={skillColor[skill]} strokeWidth={1.5}
                      dot={{ r: 3, fill: 'var(--bg-card)', stroke: skillColor[skill], strokeWidth: 1.5 }}
                      activeDot={{ r: 4 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Section 3 — Gap analysis */}
          <div style={CARD_STYLE}>
            <div style={SECTION_LABEL('var(--sage)')}>Gap analysis</div>
            <p style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic', fontSize: '16px', fontWeight: 300, color: 'var(--cream)', marginBottom: '4px' }}>
              Skills to develop
            </p>
            <p style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '14px' }}>
              required in more than 5% of jobs · skills you already have are excluded · adjacent = similar skill in your resume
            </p>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Skill', 'Market demand', 'Status'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '6px 8px', fontFamily: 'DM Mono, monospace', fontSize: '10px', fontWeight: 400, color: 'var(--text-muted)', borderBottom: '1px solid var(--border)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.gaps.map((g: any) => {
                  const tagStyle = g.status === 'have'
                    ? { color: 'var(--sage)',   bg: 'rgba(143,191,138,0.06)', border: 'rgba(143,191,138,0.2)', label: 'Have it'  }
                    : g.status === 'adjacent'
                    ? { color: 'var(--yellow)', bg: 'rgba(245,230,66,0.06)',  border: 'rgba(245,230,66,0.2)',  label: 'Adjacent' }
                    : { color: 'var(--pink)',   bg: 'rgba(240,111,170,0.06)', border: 'rgba(240,111,170,0.2)', label: 'Gap'      }
                  const barColor = g.status === 'gap' ? '#f06faa' : g.status === 'adjacent' ? '#f5e642' : '#8fbf8a'
                  return (
                    <tr key={g.skill} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '8px', fontSize: '13px', fontWeight: 400, color: 'var(--sand)' }}>{g.skill}</td>
                      <td style={{ padding: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: '80px', height: '4px', background: 'var(--bg-surface)', borderRadius: '2px', border: '1px solid var(--border)', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(g.pct, 100)}%`, height: '100%', background: barColor, borderRadius: '2px', opacity: 0.8 }} />
                          </div>
                          <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>{g.pct}%</span>
                        </div>
                      </td>
                      <td style={{ padding: '8px' }}>
                        <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', letterSpacing: '0.04em', color: tagStyle.color, background: tagStyle.bg, border: `1px solid ${tagStyle.border}`, borderRadius: '3px', padding: '2px 8px' }}>
                          {tagStyle.label}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

        </div>
      )}
    </div>
  )
}

'use client'
import { useState, useEffect, useCallback, useMemo } from 'react'
import { JobCard }   from '@/components/JobCard'
import { StatStrip } from '@/components/StatStrip'

type Tab    = 'to-apply' | 'applied'
type SortBy = 'skill' | 'role' | 'exp' | 'score' | 'date' | 'company'

const SORT_OPTIONS: { value: SortBy; label: string }[] = [
  { value: 'skill',   label: 'Skill fit'   },
  { value: 'role',    label: 'Role fit'    },
  { value: 'exp',     label: 'Exp fit'     },
  { value: 'score',   label: 'Final score' },
  { value: 'date',    label: 'Date posted' },
  { value: 'company', label: 'Company'     },
]

function sortFn(by: SortBy) {
  return (a: any, b: any) => {
    switch (by) {
      case 'skill':   return (b.skill_fit ?? 0)       - (a.skill_fit ?? 0)
      case 'role':    return (b.role_fit ?? 0)         - (a.role_fit ?? 0)
      case 'exp':     return (b.experience_fit ?? 0)   - (a.experience_fit ?? 0)
      case 'score':   return (b.final_score ?? 0)      - (a.final_score ?? 0)
      case 'date':    return new Date(b.jobs?.posted_at ?? 0).getTime() - new Date(a.jobs?.posted_at ?? 0).getTime()
      case 'company': return (a.jobs?.companies?.name ?? '').localeCompare(b.jobs?.companies?.name ?? '')
    }
  }
}

function applySearch(jobs: any[], q: string) {
  if (!q.trim()) return jobs
  const lower = q.toLowerCase()
  return jobs.filter(m =>
    m.jobs?.title?.toLowerCase().includes(lower)       ||
    m.jobs?.companies?.name?.toLowerCase().includes(lower) ||
    m.jobs?.location?.toLowerCase().includes(lower)
  )
}

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('to-apply')
  const [toApply,   setToApply]   = useState<any[]>([])
  const [applied,   setApplied]   = useState<any[]>([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)
  const [search,    setSearch]    = useState('')
  const [sortBy,    setSortBy]    = useState<SortBy>('skill')

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [r1, r2] = await Promise.all([fetch('/api/jobs'), fetch('/api/jobs/applied')])
      if (!r1.ok || !r2.ok) throw new Error('Failed to fetch jobs')
      const [ta, ap] = await Promise.all([r1.json(), r2.json()])
      setToApply(ta)
      setApplied(ap)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchJobs() }, [fetchJobs])

  const visibleToApply = useMemo(() =>
    applySearch([...toApply].sort(sortFn(sortBy)), search),
    [toApply, sortBy, search]
  )
  const visibleApplied = useMemo(() =>
    applySearch([...applied].sort(sortFn(sortBy)), search),
    [applied, sortBy, search]
  )

  const stats = [
    { label: 'Jobs today',  value: toApply.length + applied.length,                                accent: 'yellow'   },
    { label: 'To apply',    value: toApply.length,                                                  accent: 'sage'     },
    { label: 'In progress', value: applied.filter((m: any) => m.status === 'interviewing').length,  accent: 'lavender' },
    { label: 'Top match',   value: toApply[0] ? `${toApply[0].skill_fit}%` : '—',                  accent: 'pink'     },
  ]

  const TAB_STYLE = (active: boolean) => ({
    background: 'none',
    border: 'none',
    borderBottom: `2px solid ${active ? 'var(--yellow)' : 'transparent'}`,
    marginBottom: '-1px',
    fontFamily: 'DM Mono, monospace',
    fontSize: '11px',
    letterSpacing: '0.08em',
    textTransform: 'uppercase' as const,
    padding: '8px 16px',
    cursor: 'pointer',
    color: active ? 'var(--yellow)' : 'var(--text-muted)',
    transition: 'color 0.2s',
  })

  const CONTROL_BASE: React.CSSProperties = {
    background: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    borderRadius: '4px',
    fontFamily: 'DM Mono, monospace',
    fontSize: '11px',
    letterSpacing: '0.04em',
    color: 'var(--text-secondary)',
    padding: '4px 10px',
    height: '28px',
    outline: 'none',
  }

  const visible = activeTab === 'to-apply' ? visibleToApply : visibleApplied
  const total   = activeTab === 'to-apply' ? toApply.length : applied.length

  return (
    <div>
      <StatStrip stats={stats} />

      {/* Tabs + controls */}
      <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid var(--border)', marginBottom: '12px', gap: '8px' }}>
        <button style={TAB_STYLE(activeTab === 'to-apply')} onClick={() => setActiveTab('to-apply')}>
          To Apply
          <span style={{ marginLeft: '6px', fontSize: '10px', opacity: 0.5 }}>{toApply.length}</span>
        </button>
        <button style={TAB_STYLE(activeTab === 'applied')} onClick={() => setActiveTab('applied')}>
          Applied
          <span style={{ marginLeft: '6px', fontSize: '10px', opacity: 0.5 }}>{applied.length}</span>
        </button>

        <div style={{ flex: 1 }} />

        {/* Search */}
        <input
          type="text"
          placeholder="search title, company, location…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ ...CONTROL_BASE, width: '220px', paddingLeft: '10px' }}
        />

        {/* Sort */}
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value as SortBy)}
          style={{ ...CONTROL_BASE, cursor: 'pointer' }}
        >
          {SORT_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        {/* Refresh */}
        <button
          onClick={fetchJobs}
          style={{ ...CONTROL_BASE, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}
        >
          Refresh
        </button>
      </div>

      {/* Result count when filtering */}
      {search.trim() && !loading && (
        <div style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '10px' }}>
          {visible.length} of {total} jobs
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px', fontFamily: 'DM Mono, monospace', fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.08em' }}>
          Loading...
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(240,111,170,0.06)', border: '1px solid rgba(240,111,170,0.2)', borderRadius: '6px', padding: '12px', color: 'var(--pink)', fontSize: '13px' }}>
          {error}
        </div>
      )}

      {!loading && !error && activeTab === 'to-apply' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {visibleToApply.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px', letterSpacing: '0.08em' }}>
              {search.trim() ? 'No jobs match your search' : 'No new matches today — pipeline runs at 7am MST'}
            </div>
          ) : (
            visibleToApply.map((m, i) => (
              <JobCard
                key={m.job_id}
                match={m}
                rank={i + 1}
                tab="to-apply"
                onRemove={id => setToApply(prev => prev.filter((x: any) => x.job_id !== id))}
              />
            ))
          )}
        </div>
      )}

      {!loading && !error && activeTab === 'applied' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {visibleApplied.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px', letterSpacing: '0.08em' }}>
              {search.trim() ? 'No jobs match your search' : 'No applications tracked yet'}
            </div>
          ) : (
            visibleApplied.map((m, i) => (
              <JobCard
                key={m.job_id}
                match={m}
                rank={i + 1}
                tab="applied"
                onRemove={id => setApplied(prev => prev.filter((x: any) => x.job_id !== id))}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}

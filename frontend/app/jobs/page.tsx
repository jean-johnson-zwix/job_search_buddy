'use client'
import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
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
      case 'skill':   return (b.skill_fit ?? 0)     - (a.skill_fit ?? 0)
      case 'role':    return (b.role_fit ?? 0)       - (a.role_fit ?? 0)
      case 'exp':     return (b.experience_fit ?? 0) - (a.experience_fit ?? 0)
      case 'score':   return (b.final_score ?? 0)    - (a.final_score ?? 0)
      case 'date':    return new Date(b.jobs?.posted_at ?? 0).getTime() - new Date(a.jobs?.posted_at ?? 0).getTime()
      case 'company': return (a.jobs?.companies?.name ?? '').localeCompare(b.jobs?.companies?.name ?? '')
    }
  }
}

function applySearch(jobs: any[], q: string) {
  if (!q.trim()) return jobs
  const lower = q.toLowerCase()
  return jobs.filter(m =>
    m.jobs?.title?.toLowerCase().includes(lower)            ||
    m.jobs?.companies?.name?.toLowerCase().includes(lower)  ||
    m.jobs?.location?.toLowerCase().includes(lower)
  )
}

function stripHtml(html: string): string {
  if (!html) return ''
  const doc = new DOMParser().parseFromString(html, 'text/html')
  // Preserve line breaks from block elements before extracting text
  doc.querySelectorAll('p, li, br, h1, h2, h3, h4').forEach(el => {
    el.after(document.createTextNode('\n'))
  })
  return (doc.body.textContent ?? '').replace(/\n{3,}/g, '\n\n').trim()
}

function generateMarkdown(jobs: any[]): string {
  return jobs.map(m => {
    const job     = m.jobs ?? {}
    const company = job.companies ?? {}
    const posted  = job.posted_at
      ? new Date(job.posted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      : '—'
    const matched = (m.matched_skills ?? []).join(', ') || '—'
    const gaps    = (m.gap_skills    ?? []).join(', ') || '—'
    const flags   = (m.green_flags   ?? [])

    return [
      `# ${job.title ?? 'Unknown'} — ${company.name ?? 'Unknown'}`,
      '',
      `**Company:** ${company.name ?? '—'} (${(company.tier ?? '—').toUpperCase()})  `,
      `**Seniority:** ${job.seniority ?? '—'}  `,
      `**Location:** ${job.location ?? '—'}${job.remote ? ' · Remote' : ''}  `,
      `**Posted:** ${posted}  `,
      `**Apply:** ${job.apply_url ?? '—'}`,
      '',
      '---',
      '',
      '## Match Scores',
      '',
      '| Metric | Score |',
      '|--------|-------|',
      `| Skill Fit | ${m.skill_fit ?? 0}% |`,
      `| Role Fit | ${m.role_fit ?? 0}% |`,
      `| Experience Fit | ${m.experience_fit ?? 0}% |`,
      `| Final Score | ${m.final_score?.toFixed(3) ?? '—'} |`,
      '',
      '## AI Summary',
      '',
      m.summary ?? '—',
      '',
      '## Matched Skills',
      '',
      matched,
      '',
      '## Skill Gaps',
      '',
      gaps,
      ...(flags.length > 0 ? ['', '## Green Flags', '', ...flags.map((f: string) => `- ${f}`)] : []),
      '',
      '## Job Description',
      '',
      stripHtml(job.description ?? ''),
      '',
      '---',
    ].join('\n')
  }).join('\n\n')
}

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('to-apply')
  const [toApply,   setToApply]   = useState<any[]>([])
  const [applied,   setApplied]   = useState<any[]>([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)
  const [search,    setSearch]    = useState('')
  const [sortBy,    setSortBy]    = useState<SortBy>('skill')
  const [selected,  setSelected]  = useState<Set<string>>(new Set())

  const selectAllRef = useRef<HTMLInputElement>(null)

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

  const visible = activeTab === 'to-apply' ? visibleToApply : visibleApplied

  // Keep select-all checkbox in sync (checked / indeterminate)
  useEffect(() => {
    if (!selectAllRef.current) return
    const ids = visible.map((m: any) => m.job_id)
    const n   = ids.filter((id: string) => selected.has(id)).length
    selectAllRef.current.checked       = n > 0 && n === ids.length
    selectAllRef.current.indeterminate = n > 0 && n < ids.length
  }, [visible, selected])

  const toggleSelect = useCallback((jobId: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(jobId) ? next.delete(jobId) : next.add(jobId)
      return next
    })
  }, [])

  const toggleAll = useCallback(() => {
    const ids = visible.map((m: any) => m.job_id)
    const allChecked = ids.every((id: string) => selected.has(id))
    setSelected(prev => {
      const next = new Set(prev)
      allChecked
        ? ids.forEach((id: string) => next.delete(id))
        : ids.forEach((id: string) => next.add(id))
      return next
    })
  }, [visible, selected])

  const downloadMarkdown = useCallback(() => {
    const all = [...toApply, ...applied]
    const jobs = all.filter(m => selected.has(m.job_id))
    if (!jobs.length) return
    const md   = generateMarkdown(jobs)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `job-matches-${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }, [selected, toApply, applied])

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

  const selectedCount = selected.size

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

        {/* Select all */}
        {!loading && visible.length > 0 && (
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', userSelect: 'none', marginBottom: '4px' }}>
            <input
              ref={selectAllRef}
              type="checkbox"
              onChange={toggleAll}
              style={{ cursor: 'pointer', accentColor: 'var(--yellow)' }}
            />
            all
          </label>
        )}

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

        {/* Download */}
        {selectedCount > 0 && (
          <button
            onClick={downloadMarkdown}
            style={{ ...CONTROL_BASE, cursor: 'pointer', background: 'var(--yellow)', color: 'var(--bg-dark)', border: 'none', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '4px', whiteSpace: 'nowrap' }}
          >
            Download {selectedCount} job{selectedCount !== 1 ? 's' : ''}
          </button>
        )}

        {/* Refresh */}
        <button
          onClick={fetchJobs}
          style={{ ...CONTROL_BASE, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px' }}
        >
          Refresh
        </button>
      </div>

      {/* Result / selection hint */}
      {!loading && (search.trim() || selectedCount > 0) && (
        <div style={{ display: 'flex', gap: '16px', fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.06em', marginBottom: '10px' }}>
          {search.trim() && <span>{visible.length} of {activeTab === 'to-apply' ? toApply.length : applied.length} jobs</span>}
          {selectedCount > 0 && (
            <span>
              {selectedCount} selected ·{' '}
              <button onClick={() => setSelected(new Set())} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontFamily: 'inherit', fontSize: 'inherit', letterSpacing: 'inherit', textDecoration: 'underline', padding: 0 }}>
                clear
              </button>
            </span>
          )}
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
                selected={selected.has(m.job_id)}
                onToggle={toggleSelect}
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
                selected={selected.has(m.job_id)}
                onToggle={toggleSelect}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}

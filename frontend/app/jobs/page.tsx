'use client'
import { useState, useEffect, useCallback } from 'react'
import { JobCard }   from '@/components/JobCard'
import { StatStrip } from '@/components/StatStrip'

type Tab = 'to-apply' | 'applied'

export default function JobsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('to-apply')
  const [toApply,   setToApply]   = useState<any[]>([])
  const [applied,   setApplied]   = useState<any[]>([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)

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

  const stats = [
    { label: 'Jobs today',  value: toApply.length + applied.length,                                    accent: 'yellow'   },
    { label: 'To apply',    value: toApply.length,                                                     accent: 'sage'     },
    { label: 'In progress', value: applied.filter((m: any) => m.status === 'interviewing').length,     accent: 'lavender' },
    { label: 'Top match',   value: toApply[0] ? `${toApply[0].skill_fit}%` : '—',                     accent: 'pink'     },
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

  return (
    <div>
      <StatStrip stats={stats} />

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: '16px' }}>
        <button style={TAB_STYLE(activeTab === 'to-apply')} onClick={() => setActiveTab('to-apply')}>
          To Apply
          <span style={{ marginLeft: '6px', fontSize: '10px', opacity: 0.5 }}>{toApply.length}</span>
        </button>
        <button style={TAB_STYLE(activeTab === 'applied')} onClick={() => setActiveTab('applied')}>
          Applied
          <span style={{ marginLeft: '6px', fontSize: '10px', opacity: 0.5 }}>{applied.length}</span>
        </button>
        <div style={{ flex: 1 }} />
        <button
          onClick={fetchJobs}
          style={{
            background: 'none', border: '1px solid var(--border)', borderRadius: '4px',
            fontFamily: 'DM Mono, monospace', fontSize: '10px', letterSpacing: '0.06em',
            textTransform: 'uppercase', color: 'var(--text-muted)', cursor: 'pointer',
            padding: '4px 12px', marginBottom: '4px', alignSelf: 'center',
          }}
        >
          Refresh
        </button>
      </div>

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
          {toApply.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px', letterSpacing: '0.08em' }}>
              No new matches today — pipeline runs at 7am MST
            </div>
          ) : (
            toApply.map((m, i) => (
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
          {applied.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace', fontSize: '11px', letterSpacing: '0.08em' }}>
              No applications tracked yet
            </div>
          ) : (
            applied.map((m, i) => (
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

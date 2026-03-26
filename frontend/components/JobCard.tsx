'use client'
import { useState } from 'react'
import { TierBadge }       from './TierBadge'
import { ScoreRing }       from './ScoreRing'
import { ScorePill }       from './ScorePill'
import { StatusDropdown }  from './StatusDropdown'

type Status = 'new' | 'reviewing' | 'applied' | 'interviewing' | 'rejected' | 'ignored'

const TIER_ACCENT: Record<string, string> = {
  faang:   'var(--yellow)',
  unicorn: 'var(--lavender)',
  startup: 'var(--sage)',
}

const TO_APPLY_OPTIONS = [
  { value: 'new'       as Status, label: 'New'       },
  { value: 'reviewing' as Status, label: 'Reviewing' },
  { value: 'applied'   as Status, label: 'Applied'   },
  { value: 'ignored'   as Status, label: 'Ignore'    },
]

const APPLIED_OPTIONS = [
  { value: 'applied'      as Status, label: 'Applied'      },
  { value: 'interviewing' as Status, label: 'Interviewing' },
  { value: 'rejected'     as Status, label: 'Rejected'     },
]

interface Match {
  job_id:           string
  skill_fit:        number
  role_fit:         number
  experience_fit:   number
  final_score:      number
  status:           Status
  status_updated_at?: string
  matched_skills:   string[]
  gap_skills:       string[]
  green_flags:      string[]
  summary:          string
  jobs: {
    title:     string
    location:  string
    remote:    boolean
    apply_url: string
    posted_at: string
    seniority: string
    companies: { name: string; tier: string }
  }
}

interface Props {
  match:    Match
  rank:     number
  tab:      'to-apply' | 'applied'
  onRemove: (jobId: string) => void
}

export function JobCard({ match, rank, tab, onRemove }: Props) {
  const [status, setStatus] = useState<Status>(match.status)
  const job     = match.jobs
  const company = job.companies
  const tier    = company.tier?.toLowerCase() ?? 'startup'
  const accent  = TIER_ACCENT[tier] ?? 'var(--sage)'
  const posted  = job.posted_at
    ? new Date(job.posted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : '—'
  const appliedOn = match.status_updated_at
    ? new Date(match.status_updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : null

  const handleStatusChange = (jobId: string, newStatus: Status) => {
    setStatus(newStatus)
    if (tab === 'to-apply' && (newStatus === 'applied' || newStatus === 'ignored')) onRemove(jobId)
    if (tab === 'applied'  && !['applied','interviewing','rejected'].includes(newStatus)) onRemove(jobId)
  }

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderLeft: `2px solid ${accent}`,
      borderRadius: '10px',
      padding: '16px',
      transition: 'border-color 0.2s, transform 0.2s',
    }}
    onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-hover)')}
    onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', marginBottom: '10px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ marginBottom: '5px' }}>
            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.08em', marginRight: '6px' }}>
              {String(rank).padStart(2, '0')} —
            </span>
            <span style={{ fontSize: '14px', fontWeight: 400, color: 'var(--cream)' }}>
              {job.title}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '5px' }}>
            <span style={{ fontSize: '13px', fontWeight: 400, color: 'var(--sand)' }}>{company.name}</span>
            <TierBadge tier={tier} />
            <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>·</span>
            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>{job.seniority}</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>·</span>
            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>
              {job.location}{job.remote ? ' · Remote' : ''}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>·</span>
            <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)' }}>
              {appliedOn ? `Applied ${appliedOn}` : posted}
            </span>
          </div>
        </div>
        <ScoreRing score={match.skill_fit} />
      </div>

      {/* Scores */}
      {tab === 'to-apply' && (
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', marginBottom: '8px' }}>
          <ScorePill label="role" score={match.role_fit} />
          <ScorePill label="exp"  score={match.experience_fit} />
          <span style={{ fontFamily: 'DM Mono, monospace', fontSize: '10px', color: 'var(--text-muted)', alignSelf: 'center', letterSpacing: '0.04em' }}>
            final: {match.final_score?.toFixed(2)}
          </span>
        </div>
      )}

      {/* Flags */}
      <div style={{ marginBottom: '6px', display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
        {(match.green_flags ?? []).length > 0 && (
          <span style={{
            fontFamily: 'DM Mono, monospace', fontSize: '10px', letterSpacing: '0.04em',
            color: 'var(--sage)', background: 'rgba(143,191,138,0.06)',
            border: '1px solid rgba(143,191,138,0.2)', borderRadius: '3px', padding: '2px 8px',
          }}>
            ✓ {(match.green_flags ?? []).slice(0,3).join(' · ')}
          </span>
        )}
        {(match.gap_skills ?? []).length > 0 && (
          <span style={{
            fontFamily: 'DM Mono, monospace', fontSize: '10px', letterSpacing: '0.04em',
            color: 'var(--pink)', background: 'rgba(240,111,170,0.06)',
            border: '1px solid rgba(240,111,170,0.2)', borderRadius: '3px', padding: '2px 8px',
          }}>
            ⚠ {(match.gap_skills ?? []).slice(0,3).join(' · ')}
          </span>
        )}
      </div>

      {/* Summary */}
      {match.summary && (
        <p style={{
          fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic',
          borderLeft: '2px solid var(--border)', padding: '5px 10px',
          margin: '8px 0', background: 'var(--bg-surface)', borderRadius: '0 4px 4px 0',
        }}>
          {match.summary}
        </p>
      )}

      {/* Footer */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border)',
      }}>
        <StatusDropdown
          jobId={match.job_id}
          current={status}
          options={tab === 'to-apply' ? TO_APPLY_OPTIONS : APPLIED_OPTIONS}
          onChange={handleStatusChange}
        />
        {job.apply_url && (
          <a
            href={job.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontFamily: 'DM Mono, monospace', fontSize: '11px', fontWeight: 600,
              letterSpacing: '0.06em', textTransform: 'uppercase',
              background: 'var(--yellow)', color: 'var(--bg-dark)',
              border: 'none', padding: '6px 16px', borderRadius: '4px',
              textDecoration: 'none', cursor: 'pointer',
            }}
          >
            Apply →
          </a>
        )}
      </div>
    </div>
  )
}

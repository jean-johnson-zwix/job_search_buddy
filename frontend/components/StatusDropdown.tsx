'use client'
import { useState } from 'react'

type Status = 'new' | 'reviewing' | 'applied' | 'interviewing' | 'rejected' | 'ignored'

interface Props {
  jobId:    string
  current:  Status
  options:  { value: Status; label: string }[]
  onChange: (jobId: string, newStatus: Status) => void
}

export function StatusDropdown({ jobId, current, options, onChange }: Props) {
  const [loading, setLoading] = useState(false)

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = e.target.value as Status
    setLoading(true)
    try {
      await fetch('/api/jobs/status', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId, status: newStatus }),
      })
      onChange(jobId, newStatus)
    } finally {
      setLoading(false)
    }
  }

  return (
    <select
      value={current}
      onChange={handleChange}
      disabled={loading}
      style={{
        fontFamily: 'DM Mono, monospace',
        fontSize: '11px',
        letterSpacing: '0.04em',
        border: '1px solid var(--border)',
        borderRadius: '4px',
        padding: '5px 10px',
        background: 'var(--bg-surface)',
        color: 'var(--sand)',
        cursor: 'pointer',
        opacity: loading ? 0.5 : 1,
      }}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

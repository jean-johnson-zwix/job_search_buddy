import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

const VALID = ['new', 'reviewing', 'applied', 'interviewing', 'rejected', 'ignored']

export async function PATCH(request: Request) {
  const { job_id, status } = await request.json()

  if (!job_id || !status)
    return NextResponse.json({ error: 'job_id and status required' }, { status: 400 })

  if (!VALID.includes(status))
    return NextResponse.json({ error: `Invalid status` }, { status: 400 })

  const { error } = await supabase
    .from('resume_matches')
    .update({ status, status_updated_at: new Date().toISOString() })
    .eq('job_id', job_id)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ success: true })
}

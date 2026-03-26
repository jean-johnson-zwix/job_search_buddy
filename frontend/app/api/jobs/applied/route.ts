import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET() {
  const { data, error } = await supabase
    .from('resume_matches')
    .select(`
      job_id, skill_fit, role_fit, experience_fit,
      final_score, status, status_updated_at,
      matched_skills, gap_skills, summary,
      jobs (
        id, title, location, remote, apply_url,
        posted_at, role_type, seniority,
        companies ( name, tier )
      )
    `)
    .in('status', ['applied', 'interviewing', 'rejected'])
    .order('status_updated_at', { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

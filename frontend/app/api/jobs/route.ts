import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET() {
  const { data, error } = await supabase
    .from('resume_matches')
    .select(`
      job_id, skill_fit, role_fit, experience_fit,
      final_score, status, matched_skills, gap_skills,
      green_flags, red_flags, summary,
      jobs (
        id, title, location, remote, apply_url,
        posted_at, role_type, seniority,
        companies ( name, tier )
      )
    `)
    .in('status', ['new', 'reviewing'])
    .order('skill_fit',   { ascending: false, nullsFirst: false })
    .order('final_score', { ascending: false, nullsFirst: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

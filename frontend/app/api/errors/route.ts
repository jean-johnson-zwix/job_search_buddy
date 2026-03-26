import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET() {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10)

  const { data, error } = await supabase
    .from('pipeline_errors')
    .select('run_date, node, job_id, job_title, error, created_at')
    .gte('run_date', thirtyDaysAgo)
    .order('created_at', { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

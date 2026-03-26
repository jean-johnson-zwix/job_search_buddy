import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET() {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10)

  const { data, error } = await supabase
    .from('llm_usage')
    .select('run_date, task, provider, model, calls, prompt_tokens, completion_tokens, total_tokens, avg_duration_ms')
    .gte('run_date', thirtyDaysAgo)
    .order('run_date', { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

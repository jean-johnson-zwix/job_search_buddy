import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const role_type    = searchParams.get('role_type')
  const company_tier = searchParams.get('company_tier')

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()

  // 1. Top skills this week
  let q = supabase
    .from('job_skills')
    .select('skill, jobs!inner(role_type, first_seen_at, companies!inner(tier))')
    .eq('required', true)
    .gte('jobs.first_seen_at', sevenDaysAgo)

  if (role_type)    q = q.eq('jobs.role_type',      role_type)
  if (company_tier) q = q.eq('jobs.companies.tier', company_tier)

  const { data: rawSkills } = await q

  const counts: Record<string, number> = {}
  for (const r of rawSkills ?? []) counts[r.skill] = (counts[r.skill] ?? 0) + 1
  const total = Math.max(new Set((rawSkills ?? []).map((r: any) => r.job_id)).size, 1)

  const { data: cands } = await supabase.from('candidate_skills').select('name')
  const candSet = new Set((cands ?? []).map((s: any) => s.name.toLowerCase()))

  const topSkills = Object.entries(counts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 20)
    .map(([skill, count]) => ({
      skill,
      count,
      pct: Math.round((count / total) * 100),
      has_skill: candSet.has(skill.toLowerCase()),
    }))

  // 2. Trends (last 8 weeks)
  const eightWeeksAgo = new Date(Date.now() - 56 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  let tq = supabase
    .from('skill_trends')
    .select('skill, week_start, pct_of_jobs')
    .gte('week_start', eightWeeksAgo)
    .order('week_start', { ascending: true })
  if (role_type)    tq = tq.eq('role_type',    role_type)
  if (company_tier) tq = tq.eq('company_tier', company_tier)
  const { data: trends } = await tq

  // 3. Gap analysis (latest week)
  const { data: latestWeek } = await supabase
    .from('skill_trends').select('week_start')
    .order('week_start', { ascending: false }).limit(1)
  const weekStart = latestWeek?.[0]?.week_start

  let gq = supabase
    .from('skill_trends')
    .select('skill, pct_of_jobs')
    .eq('week_start', weekStart)
    .gt('pct_of_jobs', 0.05)
    .order('pct_of_jobs', { ascending: false })
  if (role_type)    gq = gq.eq('role_type',    role_type)
  if (company_tier) gq = gq.eq('company_tier', company_tier)
  const { data: gapData } = await gq

  const gaps = (gapData ?? []).map((row: any) => {
    const lower = row.skill.toLowerCase()
    const have  = candSet.has(lower)
    const adjacent = !have && [...candSet].some(cs => {
      const ct = new Set<string>(cs.split(/[\s\-_]+/))
      const rt = new Set<string>(lower.split(/[\s\-_]+/))
      return [...rt].some((t: string) => t.length > 2 && ct.has(t))
    })
    return { skill: row.skill, pct: Math.round(row.pct_of_jobs * 100), status: have ? 'have' : adjacent ? 'adjacent' : 'gap' }
  })

  return NextResponse.json({ topSkills, trends, gaps })
}

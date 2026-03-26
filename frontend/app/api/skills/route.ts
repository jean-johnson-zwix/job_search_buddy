import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

// Returns the ISO date string for the Monday of the week containing `dateStr`
function getWeekStart(dateStr: string): string {
  const d = new Date(dateStr)
  const day = d.getUTCDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setUTCDate(d.getUTCDate() + diff)
  return d.toISOString().slice(0, 10)
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const role_type    = searchParams.get('role_type')
  const company_tier = searchParams.get('company_tier')

  const sevenDaysAgo  = new Date(Date.now() - 7  * 24 * 60 * 60 * 1000).toISOString()
  const eightWeeksAgo = new Date(Date.now() - 56 * 24 * 60 * 60 * 1000).toISOString()

  // Candidate skills (shared across all three sections)
  const { data: cands } = await supabase.from('candidate_skills').select('name')
  const candSet = new Set((cands ?? []).map((s: any) => s.name.toLowerCase()))

  // ── 1. Top skills this week (last 7 days) ───────────────────────────────────
  let q = supabase
    .from('job_skills')
    .select('job_id, skill, jobs!inner(role_type, first_seen_at, companies!inner(tier))')
    .eq('required', true)
    .gte('jobs.first_seen_at', sevenDaysAgo)

  if (role_type)    q = q.eq('jobs.role_type',      role_type)
  if (company_tier) q = q.eq('jobs.companies.tier', company_tier)

  const { data: rawSkills } = await q

  const counts: Record<string, number> = {}
  for (const r of rawSkills ?? []) counts[r.skill] = (counts[r.skill] ?? 0) + 1
  const total = Math.max(new Set((rawSkills ?? []).map((r: any) => r.job_id)).size, 1)

  const topSkills = Object.entries(counts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 20)
    .map(([skill, count]) => ({
      skill,
      count,
      pct: Math.round((count / total) * 100),
      has_skill: candSet.has(skill.toLowerCase()),
    }))

  // ── 2. Trends (last 8 weeks, computed from job_skills) ──────────────────────
  let tq = supabase
    .from('job_skills')
    .select('job_id, skill, jobs!inner(role_type, first_seen_at, companies!inner(tier))')
    .eq('required', true)
    .gte('jobs.first_seen_at', eightWeeksAgo)

  if (role_type)    tq = tq.eq('jobs.role_type',      role_type)
  if (company_tier) tq = tq.eq('jobs.companies.tier', company_tier)

  const { data: trendRaw } = await tq

  // Group by week: count unique jobs and skill occurrences per week
  const weekJobIds: Record<string, Set<string>>         = {}
  const weekSkillCounts: Record<string, Record<string, number>> = {}

  for (const r of (trendRaw ?? []) as any[]) {
    if (!r.job_id || !r.jobs?.first_seen_at) continue
    const week = getWeekStart(r.jobs.first_seen_at)
    if (!weekJobIds[week])      weekJobIds[week]      = new Set()
    if (!weekSkillCounts[week]) weekSkillCounts[week] = {}
    weekJobIds[week].add(r.job_id)
    weekSkillCounts[week][r.skill] = (weekSkillCounts[week][r.skill] ?? 0) + 1
  }

  // Build flat trends array (same shape the frontend expects)
  const trends: { skill: string; week_start: string; pct_of_jobs: number }[] = []
  for (const [week, skillCounts] of Object.entries(weekSkillCounts)) {
    const jobCount = Math.max(weekJobIds[week].size, 1)
    for (const [skill, count] of Object.entries(skillCounts)) {
      trends.push({ skill, week_start: week, pct_of_jobs: count / jobCount })
    }
  }
  trends.sort((a, b) => a.week_start.localeCompare(b.week_start))

  // ── 3. Gap analysis (derived from top-skills counts, threshold > 5%) ─────────
  const gaps = Object.entries(counts)
    .map(([skill, count]) => {
      const pct   = Math.round((count / total) * 100)
      const lower = skill.toLowerCase()
      const have  = candSet.has(lower)
      const adjacent = !have && [...candSet].some(cs => {
        const ct = new Set<string>(cs.split(/[\s\-_]+/))
        const rt = new Set<string>(lower.split(/[\s\-_]+/))
        return [...rt].some((t: string) => t.length > 2 && ct.has(t))
      })
      return { skill, pct, status: have ? 'have' : adjacent ? 'adjacent' : 'gap' }
    })
    .filter(g => g.pct > 5 && g.status !== 'have')
    .sort((a, b) => b.pct - a.pct)

  return NextResponse.json({ topSkills, trends, gaps })
}

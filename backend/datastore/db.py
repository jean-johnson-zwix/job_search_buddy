import logging
import os
from datetime import date, datetime, timezone
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client

def get_all_companies() -> list[dict]:
    db = get_client()
    res = db.table("companies").select("*").execute()
    return res.data or []

def upsert_job(job: dict) -> None:
    db = get_client()
    db.table("jobs").upsert(
        {
            "id":             job["id"],
            "company_id":     job["company_id"],
            "title":          job["title"],
            "role_type":      job.get("role_type"),
            "seniority":      job.get("seniority"),
            "years_required": job.get("years_required"),
            "location":       job.get("location", ""),
            "remote":         job.get("remote", False),
            "description":    job.get("description", ""),
            "apply_url":      job.get("apply_url", ""),
            "posted_at":      _dt_str(job.get("posted_at")),
            "last_seen_at":   _now_str(),
        },
        on_conflict="id",
        ignore_duplicates=False,
    ).execute()

def get_existing_job_ids(job_ids: list[str]) -> set[str]:
    if not job_ids:
        return set()
    db = get_client()
    res = (
        db.table("jobs")
        .select("id")
        .in_("id", job_ids)
        .execute()
    )
    return {row["id"] for row in (res.data or [])}

def upsert_skills(job_id: str, skills: list[dict]) -> None:
    db = get_client()
    db.table("job_skills").delete().eq("job_id", job_id).execute()
    rows = [
        {
            "job_id":   job_id,
            "skill":    s["name"],
            "category": s.get("category", "other"),
            "required": s.get("required", True),
        }
        for s in skills
    ]
    if rows:
        db.table("job_skills").insert(rows).execute()


def get_job_skills(job_id: str) -> list[dict]:
    """Load stored skills for a known job — avoids re-extraction."""
    db = get_client()
    res = (
        db.table("job_skills")
        .select("skill, category, required")
        .eq("job_id", job_id)
        .execute()
    )
    return [
        {"name": r["skill"], "category": r["category"], "required": r["required"]}
        for r in (res.data or [])
    ]

def get_candidate_skills() -> list[dict]:
    """Returns all rows from candidate_skills table."""
    db = get_client()
    res = db.table("candidate_skills").select("*").execute()
    return res.data or []


def get_candidate_profile(key: str) -> str | None:
    """Returns the value for a given key from candidate_profile."""
    db = get_client()
    res = (
        db.table("candidate_profile")
        .select("value")
        .eq("key", key)
        .execute()
    )
    return res.data[0]["value"] if res.data else None

def upsert_resume_match(
    job_id: str,
    skill_fit: int,
    role_fit: int,
    experience_fit: int,
    matched_skills: list[str],
    gap_skills: list[str],
    green_flags: list[str],
    red_flags: list[str],
    summary: str,
    final_score: float,
    run_date: Optional[date] = None,
) -> None:
    db = get_client()
    db.table("resume_matches").upsert(
        {
            "job_id":          job_id,
            "skill_fit":       skill_fit,
            "role_fit":        role_fit,
            "experience_fit":  experience_fit,
            "matched_skills":  matched_skills,
            "gap_skills":      gap_skills,
            "green_flags":     green_flags,
            "red_flags":       red_flags,
            "summary":         summary,
            "final_score":     final_score,
            "run_date":        str(run_date or date.today()),
        },
        on_conflict="job_id,run_date",
    ).execute()


def get_processed_job_ids(run_date: Optional[date] = None) -> set[str]:
    db = get_client()
    today = str(run_date or date.today())
    res = (
        db.table("resume_matches")
        .select("job_id")
        .eq("run_date", today)
        .execute()
    )
    return {row["job_id"] for row in (res.data or [])}


def update_job_status(job_id: str, status: str, notes: str = None) -> None:
    db = get_client()
    payload = {
        "status": status,
        "status_updated_at": _now_str(),
    }
    if notes is not None:
        payload["notes"] = notes
    db.table("resume_matches").update(payload).eq("job_id", job_id).execute()


def get_applied_jobs(limit: int = 100) -> list[dict]:
    db = get_client()
    res = (
        db.table("resume_matches")
        .select(
            "status, status_updated_at, notes, final_score, "
            "jobs(id, title, apply_url, companies(name, tier))"
        )
        .in_("status", ["applied", "interviewing", "rejected"])
        .order("status_updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def get_top_matches(limit: int = 15, run_date: Optional[date] = None, max_per_company: int = 3) -> list[dict]:
    from collections import defaultdict
    db = get_client()
    today = str(run_date or date.today())
    res = (
        db.table("resume_matches")
        .select(
            "final_score, skill_fit, role_fit, experience_fit, "
            "matched_skills, gap_skills, green_flags, red_flags, summary, "
            "jobs(id, title, location, remote, apply_url, posted_at, "
            "role_type, seniority, description, "
            "companies(id, name, tier))"
        )
        .eq("run_date", today)
        .in_("status", ["new", "reviewing"])
        .order("final_score", desc=True)
        .limit(limit * max_per_company)
        .execute()
    )
    rows = res.data or []
    company_counts: defaultdict[str, int] = defaultdict(int)
    capped = []
    for match in rows:
        company_id = ((match.get("jobs") or {}).get("companies") or {}).get("id")
        if company_id is not None and company_counts[company_id] >= max_per_company:
            continue
        if company_id is not None:
            company_counts[company_id] += 1
        capped.append(match)
        if len(capped) >= limit:
            break
    return capped

def _dt_str(dt) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(dt)

def _now_str() -> str:
    return datetime.now(timezone.utc).isoformat()

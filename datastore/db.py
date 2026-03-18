
import os
import logging
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
            "id":           job["id"],
            "company_id":   job["company_id"],
            "title":        job["title"],
            "role_type":    job.get("role_type"),
            "seniority":    job.get("seniority"),
            "location":     job.get("location", ""),
            "remote":       job.get("remote", False),
            "description":  job.get("description", ""),
            "apply_url":    job.get("apply_url", ""),
            "posted_at":    _dt_str(job.get("posted_at")),
            "last_seen_at": _now_str(),
        },
        on_conflict="id",
        ignore_duplicates=False,
    ).execute()


def upsert_skills(job_id: str, skills: list[dict]) -> None:
    db = get_client()
    # delete existing
    db.table("job_skills").delete().eq("job_id", job_id).execute()
    # insert fresh
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


def upsert_resume_match(
    job_id: str,
    match_pct: int,
    matched_skills: list[str],
    gap_skills: list[str],
    final_score: float,
    run_date: Optional[date] = None,
) -> None:
    db = get_client()
    db.table("resume_matches").upsert(
        {
            "job_id":         job_id,
            "match_pct":      match_pct,
            "matched_skills": matched_skills,
            "gap_skills":     gap_skills,
            "final_score":    final_score,
            "run_date":       str(run_date or date.today()),
        },
        on_conflict="job_id,run_date",
    ).execute()


def get_top_matches(limit: int = 15, run_date: Optional[date] = None) -> list[dict]:
    db = get_client()
    today = str(run_date or date.today())

    res = (
        db.table("resume_matches")
        .select(
            "final_score, match_pct, matched_skills, gap_skills, "
            "jobs(id, title, location, remote, apply_url, posted_at, role_type, seniority, description, "
            "companies(name, tier))"
        )
        .eq("run_date", today)
        .order("final_score", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


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

def get_processed_job_ids(run_date=None) -> set[str]:
    from datetime import date
    db = get_client()
    today = str(run_date or date.today())
    res = (
        db.table("resume_matches")
        .select("job_id")
        .eq("run_date", today)
        .execute()
    )
    return {row["job_id"] for row in (res.data or [])}
 
 
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

import httpx
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ENGINEERING_DEPT_PATTERNS = [
    r"^engineering$",
    r"^software",
    r"^data",
    r"^machine learning",
    r"^ai",
    r"^infrastructure",
    r"^platform",
    r"^security",
    r"^research",
    r"^product engineering",
    r"^tech",
    r"^it"
]

def _is_engineering_dept(name: str) -> bool:
    n = name.lower().strip()
    return any(re.search(p, n) for p in ENGINEERING_DEPT_PATTERNS)

def _get(url: str, timeout: int = 15) -> Optional[dict | list]:
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None

def fetch_greenhouse(slug: str) -> list[dict]:
    # Fetch all departments
    dept_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/departments"
    dept_data = _get(dept_url)
    print (dept_data)
    return [] 
    eng_dept_ids = []
    if dept_data and "departments" in dept_data:
        for dept in dept_data["departments"]:
            if _is_engineering_dept(dept.get("name", "")):
                eng_dept_ids.append(dept["id"])
                logger.info(
                    f"  Greenhouse [{slug}]: "
                    f"using dept '{dept['name']}' (id={dept['id']})"
                )
    # Fetch jobs per engineering department if departments available
    if eng_dept_ids:
        all_jobs = []
        for dept_id in eng_dept_ids:
            url = (
                f"https://boards-api.greenhouse.io/v1/boards/{slug}"
                f"/departments/{dept_id}"
            )
            data = _get(url)
            if data and "jobs" in data:
                all_jobs.extend(data["jobs"])
        logger.info(
            f"  Greenhouse [{slug}]: "
            f"{len(all_jobs)} jobs from {len(eng_dept_ids)} engineering dept(s)"
        )
        return [_parse_gh_job(j) for j in all_jobs]
    # Else fetch all content
    logger.warning(
        f"  Greenhouse [{slug}]: no engineering dept found, "
        f"fetching all (title filter will apply)"
    )
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    data = _get(url)
    if not data or "jobs" not in data:
        return []
    return [_parse_gh_job(j) for j in data["jobs"]]

def _parse_gh_job(j: dict) -> dict:
    location = _gh_location(j)
    return {
        "id":          f"gh_{j['id']}",
        "title":       j.get("title", ""),
        "location":    location,
        "remote":      _is_remote(j.get("title", ""), location),
        "description": _strip_html(j.get("content", "")),
        "apply_url":   j.get("absolute_url", ""),
        "posted_at":   _parse_iso(j.get("updated_at")),
    }

def _gh_location(j: dict) -> str:
    locs = j.get("offices", [])
    if locs:
        return locs[0].get("name", "")
    loc = j.get("location", {})
    return loc.get("name", "") if isinstance(loc, dict) else ""

def fetch_lever(slug: str) -> list[dict]:

    target_teams = ["Engineering", "Data", "Machine Learning", "AI", "Platform", "Software", "IT"]
    location_filter = "&location=United+States"
    all_jobs = []
    seen_ids = set()

    for team in target_teams:
        import urllib.parse
        encoded = urllib.parse.quote(team)
        url = (
            f"https://api.lever.co/v0/postings/{slug}"
            f"?mode=json&limit=200&team={encoded}{location_filter}"
        )
        data = _get(url)
        postings = data if isinstance(data, list) else (data or {}).get("data", [])
        for j in postings:
            if j["id"] not in seen_ids:
                seen_ids.add(j["id"])
                all_jobs.append(_parse_lever_job(j))
 
    if all_jobs:
        logger.info(f"  Lever [{slug}]: {len(all_jobs)} jobs (team-filtered)")
        return all_jobs
    
    # fallback to get all jobs
    logger.warning(f"  Lever [{slug}]: team filter returned nothing, fetching all")
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=200{location_filter}"
    data = _get(url)
    postings = data if isinstance(data, list) else (data or {}).get("data", [])
    logger.info(f"  Lever [{slug}]: {len(postings)} jobs (unfiltered)")
    return [_parse_lever_job(j) for j in postings]

def _parse_lever_job(j: dict) -> dict:
    location = j.get("categories", {}).get("location", "")
    return {
        "id":          f"lv_{j['id']}",
        "title":       j.get("text", ""),
        "location":    location,
        "remote":      _is_remote(j.get("text", ""), location),
        "description": _lever_description(j),
        "apply_url":   j.get("hostedUrl", ""),
        "posted_at":   _parse_epoch_ms(j.get("createdAt")),
    }

def _lever_description(j: dict) -> str:
    parts = []
    for section in j.get("descriptionBody", {}).get("content", []):
        for node in section.get("content", []):
            text = node.get("text", "")
            if text:
                parts.append(text)
    if not parts:
        parts.append(j.get("descriptionPlain", ""))
    return " ".join(parts)


def fetch_ashby(slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    data = _get(url)
    if not data or "jobPostings" not in data:
        logger.warning(f"Ashby: no jobs found for {slug}")
        return []

    jobs = []
    for j in data["jobPostings"]:
        location = j.get("locationName", "")
        jobs.append({
            "id":          f"ab_{j['id']}",
            "title":       j.get("title", ""),
            "location":    location,
            "remote":      j.get("isRemote", False) or _is_remote(j.get("title", ""), location),
            "description": j.get("descriptionPlain", j.get("descriptionHtml", "")),
            "apply_url":   j.get("jobUrl", ""),
            "posted_at":   _parse_iso(j.get("publishedAt")),
        })
    logger.info(f"  Ashby [{slug}]: {len(jobs)} jobs (unfiltered — title filter next)")
    return jobs

def fetch_jobs_for_company(ats: str, slug: str) -> list[dict]:
    fetchers = {
        "greenhouse": fetch_greenhouse,
        "lever":      fetch_lever,
        "ashby":      fetch_ashby,
    }
    fn = fetchers.get(ats)
    if not fn:
        logger.error(f"Unknown ATS: {ats}")
        return []
    return fn(slug)

def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def _parse_epoch_ms(ms: Optional[int]) -> Optional[datetime]:
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except Exception:
        return None

def _is_remote(title: str, location: str) -> bool:
    text = f"{title} {location}".lower()
    return any(w in text for w in ["remote", "anywhere", "distributed", "work from home"])


import re
def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

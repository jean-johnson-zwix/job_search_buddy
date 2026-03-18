import httpx
import logging
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

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
    
    candidate_job_ids: set[int] = set()
    if dept_data and "departments" in dept_data:
        for dept in dept_data["departments"]:
            for job_stub in dept.get("jobs", []):
                loc = (job_stub.get("location") or {}).get("name", "")
                if _is_us_location_str(loc):
                    candidate_job_ids.add(job_stub["id"])
    logger.info(f"Greenhouse [{slug}]: {len(candidate_job_ids)} US candidate jobs")

    # Fetch Job Descriptions
    jobs_data = _get(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    )
    if not jobs_data or "jobs" not in jobs_data:
        return []
 
    all_jobs = jobs_data["jobs"]
    if candidate_job_ids:
        filtered = [j for j in all_jobs if j["id"] in candidate_job_ids]
    else:
        filtered = all_jobs
 
    logger.info(
        f"  Greenhouse [{slug}]: {len(all_jobs)} total → {len(filtered)} after eng+US filter"
    )
    return [_parse_gh_job(j) for j in filtered]

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

def fetch_ashby(slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    data = _get(url)
    if not data or "jobs" not in data:
        logger.warning(f"Ashby: no jobs found for {slug}")
        return []
    jobs = []
    for j in data["jobs"]:
        # skip unlisted
        if not j.get("isListed", True):
            continue
        # get location
        address = j.get("address", {}) or {}
        postal = address.get("postalAddress", {}) or {}
        country = postal.get("addressCountry", "")
        location_str = j.get("location", "")
        # filter based on location
        if country:
            if country not in ("United States", "US", "USA"):
                continue
        else:
            if not _is_us_location_str(location_str):
                continue
        jobs.append({
            "id":          f"ab_{j['id']}",
            "title":       j.get("title", ""),
            "location":    location_str,
            "remote":      j.get("isRemote", False) or _is_remote(j.get("title", ""), location_str),
            "description": j.get("descriptionPlain", j.get("descriptionHtml", "")),
            "apply_url":   j.get("jobUrl", ""),
            "posted_at":   _parse_iso(j.get("publishedAt")),
        })
    logger.info(f"  Ashby [{slug}]: {len(jobs)} jobs (unfiltered — title filter next)")
    return jobs

def fetch_jobs_for_company(ats: str, slug: str) -> list[dict]:
    fetchers = {
        "greenhouse": fetch_greenhouse,
        "ashby":      fetch_ashby,
    }
    fn = fetchers.get(ats)
    if not fn:
        logger.error(f"Unknown ATS: {ats}")
        return []
    return fn(slug)

US_SIGNALS = [
    r"\bUS\b", r"\bU\.S\b", r"United States",
    r"\bremote\b", r"\banywhere\b",
    r"\bSF\b", r"\bSEA\b", r"\bNYC\b", r"\bNY\b", r"\bCHI\b",
    r"\bATL\b", r"\bDC\b", r"\bLA\b",
    r"San Francisco", r"Seattle", r"New York", r"Chicago",
    r"Atlanta", r"Austin", r"Boston", r"Denver", r"Washington",
    r"California", r"Texas", r"Hawaii",
    r"\bNA\b", r"North America",
]
 
NON_US_SIGNALS = [
    r"Dublin", r"London", r"Bengaluru", r"Bangalore", r"Toronto",
    r"Singapore", r"Tokyo", r"Sydney", r"Melbourne", r"Paris",
    r"Berlin", r"Munich", r"Amsterdam", r"Barcelona", r"Madrid",
    r"Stockholm", r"Luxembourg", r"Bucharest", r"Romania",
    r"Mexico City", r"Mexico\b", r"CDMX",
    r"\bCanada\b", r"\bIndia\b", r"\bIreland\b", r"\bUK\b",
    r"\bGermany\b", r"\bFrance\b", r"\bSpain\b", r"\bJapan\b",
    r"\bAustralia\b", r"\bBrazil\b",
    r"\bEMEA\b", r"\bAPAC\b", r"\bLATAM\b",
]
 
_UNKNOWN_EXACT = {"", "n/a", "na", "location", "null", "tbd", "remote-us/ca"}

def _is_us_location_str(location: str) -> bool:
    if not location:
        return True
    stripped = location.strip().lower()
    if stripped in _UNKNOWN_EXACT:
        return True
    for pat in NON_US_SIGNALS:
        if re.search(pat, location, re.IGNORECASE):
            return False
    for pat in US_SIGNALS:
        if re.search(pat, location, re.IGNORECASE):
            return True
    return True

def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def _is_remote(title: str, location: str) -> bool:
    text = f"{title} {location}".lower()
    return any(w in text for w in ["remote", "anywhere", "distributed", "work from home"])

def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

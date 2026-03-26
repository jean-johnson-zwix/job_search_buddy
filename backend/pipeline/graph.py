import logging
import time

from langgraph.graph import StateGraph, END

# nodes
from datastore import db
from intelligence.llm import get_usage_log, reset_usage_log
from ingestion.job_retriever import fetch_jobs_for_company
from ingestion.job_filter import filter_jobs
from intelligence.resume_parser import run_resume_parser
from intelligence.job_analyzer import extract_skills_from_jobs, match_resume_to_job
from intelligence.score import compute_final_score
from delivery.email import send_daily_digest
from utils.logging import log_methods

# state
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

DELAY_SEC = 4  # avoid RQM limits

#node 1: load resume + extract skills
@log_methods
def node_resume_extraction(state: PipelineState) -> dict:
    logger.info("NODE 1 - RESUME EXTRACTION")
    reset_usage_log()
    try:
        success = run_resume_parser(force=False) # only if modified
        logger.info(f"Resume {'parsed' if success else 'loaded from database'}")
    except Exception as e:
        logger.error(f"Resume extraction failed: {e}. Fallback - loading from database")
    return {}

# node 2: node_data_loader
@log_methods
def node_data_loader(state: PipelineState) -> dict:
    logger.info("NODE 2 - DATA LOADER")
    #load all companies
    companies = db.get_all_companies()
    logger.info(f"Loaded {len(companies)} companies")
    #load resume skills
    candidate_skills = [s["name"] for s in db.get_candidate_skills()]
    logger.info(f"Loaded {len(candidate_skills)} skills from resume")
    #load jobs already scored (skipped)
    already_scored = db.get_processed_job_ids()
    logger.info(f"Found {len(already_scored)} jobs is already scored today")
    return {
        "companies":             companies,
        "candidate_skills": candidate_skills,
        "already_scored":        already_scored,
        # Initialize accumulators
        "new_jobs":              [],
        "known_jobs":            [],
        "extracted_jobs":        [],
        "matched_jobs":          [],
        "stats":  {"fetched": 0, "new": 0, "known": 0,
                   "extracted": 0, "matched": 0, "skipped": 0},
        "errors": [],
    }

# node 3: node_job_ingestion
@log_methods
def node_job_ingestion(state: PipelineState) -> dict:
    logger.info("NODE 3 - JOB INGESTION")
    all_new, all_known = [], []
    for company in state["companies"]:
        logger.info(f"Retrieving jobs for {company['name']} ({company['ats']})")
        try:
            raw_jobs = fetch_jobs_for_company(company["ats"], company["slug"])
        except Exception as e:
            logger.error(f"Job Ingestion failed for {company['name']}: {e}")
            continue
        if not raw_jobs:
            logger.info("no new jobs")
            continue
        # filter jobs based on location, title, freshness, and sponsorship
        relevant = filter_jobs(raw_jobs, company["name"])
        if not relevant:
            continue
        # tag jobs with company metadata
        for job in relevant:
            job["company_id"] = company["id"]
            job["company_tier"] = company["tier"]
        # split into new and known job lists
        raw_ids = [j["id"] for j in relevant]
        existing_ids = db.get_existing_job_ids(raw_ids)
        new = [j for j in relevant if j["id"] not in existing_ids]
        known = [j for j in relevant if j["id"] in existing_ids]
        logger.info(f"found new jobs ({len(new)}) and known jobs ({len(known)})")
        all_new.extend(new)
        all_known.extend(known)
    total = len(all_new) + len(all_known)
    logger.info(f"Total: {total} ({len(all_new)} new, {len(all_known)} known)")
    return {
        "new_jobs":   all_new,
        "known_jobs": all_known,
        "stats": {**state.get("stats"),
                  "fetched": total,
                  "new":     len(all_new),
                  "known":   len(all_known)},
    }

# conditional_edge: after jobs are loaded
def router_post_job_ingestion(state: PipelineState) -> dict:
    logger.info("CONDITIONAL NODE - CHECK FOR NEW JOBS")
    total = len(state.get("new_jobs", [])) + len(state.get("known_jobs", []))
    if total > 0:
        return "continue"
    logger.info("No jobs fetched — skipping to email")
    return "skip_to_email"

# node 4: node_job_extraction
@log_methods
def node_job_extraction(state: PipelineState) -> dict:
    logger.info("NODE 4 - JOB EXTRACTION")
    extracted = []
    errors    = list(state["errors"])
    call_count = 0

    # cap new jobs via MAX_NEW_JOBS env var (useful for first runs)
    import os
    max_new = int(os.getenv("MAX_NEW_JOBS", 0)) or None
    new_jobs = state["new_jobs"][:max_new] if max_new else state["new_jobs"]
    if max_new and len(state["new_jobs"]) > max_new:
        logger.warning(f"MAX_NEW_JOBS={max_new}: capping {len(state['new_jobs'])} → {max_new} new jobs")

    # new jobs - extract skills via llm
    for job in new_jobs:
        try:
            result = extract_skills_from_jobs(
                job["title"],
                job.get("description", "")
            )
            call_count += 1
            logger.info("Sleeping %ss (rate limit)", DELAY_SEC)
            time.sleep(DELAY_SEC)

            if result:
                job["role_type"]      = result.get("role_type", "Other")
                job["seniority"]      = result.get("seniority", "Unknown")
                job["years_required"] = result.get("years_required")
                job["skills"]         = result.get("skills", [])
            else:
                job["role_type"]      = "Other"
                job["seniority"]      = "Unknown"
                job["years_required"] = None
                job["skills"]         = []
            db.upsert_job(job)
            db.upsert_skills(job["id"], job["skills"])
            extracted.append(job)
        except Exception as e:
            logger.error(f"  Extract failed '{job['title']}': {e}")
            errors.append({"job_id": job["id"], "node": "extract", "error": str(e)})

    # known jobs — load skills from DB
    for job in state["known_jobs"]:
        try:
            job["skills"] = db.get_job_skills(job["id"])
            db.upsert_job(job)
            extracted.append(job)
        except Exception as e:
            logger.error(f"  DB load failed '{job['title']}': {e}")
            errors.append({"job_id": job["id"], "node": "extract_known", "error": str(e)})

    logger.info(f"Skills extracted of new jobs: {call_count} · "
                f"Known jobs loaded: {len(state['known_jobs'])} · "
                f"Total: {len(extracted)}")

    return {
        "extracted_jobs": extracted,
        "errors":         errors,
        "stats": {**state.get("stats", {}), "extracted": call_count},
    }

@log_methods
def node_job_match(state: PipelineState) -> dict:
    logger.info("NODE 5 - JOB MATCHING")
    matched   = []
    errors    = list(state["errors"])
    skipped   = 0

    for job in state["extracted_jobs"]:
        # Skip if already scored today
        if job["id"] in state["already_scored"]:
            skipped += 1
            continue

        try:
            result = match_resume_to_job(
                job["title"],
                job.get("description", ""),
            )
            logger.info("Sleeping %ss (rate limit)", DELAY_SEC)
            time.sleep(DELAY_SEC)

            if not result:
                logger.warning(f"match_resume_to_job returned None for '{job['title']}'")
                continue

            final_score = compute_final_score(
                skill_fit=result.get("skill_fit", 0),
                role_fit=result.get("role_fit", 0),
                experience_fit=result.get("experience_fit", 0),
                posted_at=job.get("posted_at"),
                company_tier=job.get("company_tier", "startup"),
            )

            db.upsert_resume_match(
                job_id=job["id"],
                skill_fit=result.get("skill_fit", 0),
                role_fit=result.get("role_fit", 0),
                experience_fit=result.get("experience_fit", 0),
                matched_skills=result.get("matched_skills", []),
                gap_skills=result.get("gap_skills", []),
                green_flags=result.get("green_flags", []),
                red_flags=result.get("red_flags", []),
                summary=result.get("summary", ""),
                final_score=final_score,
            )

            job["final_score"] = final_score
            matched.append(job)

        except Exception as e:
            logger.error(f"  Match failed '{job['title']}': {e}")
            errors.append({"job_id": job["id"], "node": "smart_match", "error": str(e)})

    logger.info(f"Scored: {len(matched)} jobs | Skipped: {skipped} jobs")

    return {
        "matched_jobs": matched,
        "errors":       errors,
        "stats": {**state.get("stats", {}),
          "matched": len(matched),
          "skipped": state.get("stats", {}).get("skipped", 0) + skipped},
    }

@log_methods
def node_emailer(state: PipelineState) -> dict:
    logger.info("NODE 6 - EMAIL SENDER")
    try:
        db.save_llm_usage(get_usage_log())
    except Exception as e:
        logger.error(f"  LLM usage save failed: {e}")
    try:
        send_daily_digest()
    except Exception as e:
        logger.error(f"  Email failed: {e}")
    # Final summary log
    s = state.get("stats", {})
    e = state.get("errors", [])
    logger.info(
        "Pipeline complete — "
        f"fetched:{s.get('fetched',0)} "
        f"new:{s.get('new',0)} "
        f"extracted:{s.get('extracted',0)} "
        f"matched:{s.get('matched',0)} "
        f"skipped:{s.get('skipped',0)} "
        f"errors:{len(e)}"
    )
    if e:
        for err in e:
            logger.warning(f"  [{err['node']}] {err['job_id']} — {err['error']}")
    return {}

# build the graph
@log_methods
def build_pipeline():
    graph = StateGraph(PipelineState)
    # register nodes
    graph.add_node("resume_extraction",node_resume_extraction)
    graph.add_node("data_loader",node_data_loader)
    graph.add_node("job_ingestion",node_job_ingestion)
    graph.add_node("job_extraction",node_job_extraction)
    graph.add_node("job_matcher",node_job_match)
    graph.add_node("emailer",node_emailer)
    # set entry point
    graph.set_entry_point("resume_extraction")
    # wire edges
    graph.add_edge("resume_extraction", "data_loader")
    graph.add_edge("data_loader", "job_ingestion")
    # add conditional edge after jobs are ingested
    graph.add_conditional_edges(
        "job_ingestion", 
        router_post_job_ingestion, 
        {
            "continue":"job_extraction",
            "skip_to_email":"emailer"
    })
    graph.add_edge("job_extraction","job_matcher")
    graph.add_edge("job_matcher","emailer")
    graph.add_edge("emailer",END)
    return graph.compile()













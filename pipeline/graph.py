import logging
import time

from langgraph.graph import StateGraph, END

# nodes
from datastore import db
from ingestion.job_retriever import fetch_jobs_for_company
from ingestion.job_filter import filter_jobs
from intelligence.resume_parser import run_resume_parser
from intelligence.job_analyzer import extract_skills_from_jobs, match_resume_to_job
from delivery.email import send_daily_digest

# state
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

DELAY_SEC=4 # avoid RQM limits

#node 1: load resume + extract skills
def node_resume_extraction(state: PipelineState) -> dict:
    logger.info("NODE 1 - RESUME EXTRACTION")
    try:
        success = run_resume_parser(force=False) # only if modified
        logger.info(f"Resume {'parsed' if success else 'loaded from database'}")
    except Exception as e:
        logger.error(f"Resume extraction failed: {e}. Fallback - loading from database")
    return {}

# node 2: node_data_loader
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
        "candidate_skill_names": candidate_skills,
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
        # filter jobs based on location + title
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
        "stats": {**state["stats"],
                  "fetched": total,
                  "new":     len(all_new),
                  "known":   len(all_known)},
    }










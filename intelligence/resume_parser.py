import logging
import os
import json
from datetime import datetime, timezone

from supabase import create_client
from .llm import call_llm
from .llm_config import RESUME_SKILL_EXTRACTION, RESUME_CONDENSATION
from intelligence.prompts import (
    RESUME_SKILL_EXTRACTION_SYSTEM,
    RESUME_CONDENSATION_SYSTEM,
)
from ingestion.resume_reader import get_resume, get_resume_modified_time

logger = logging.getLogger(__name__)

def needs_reparse() -> bool:

    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    row = (
        db.table("candidate_profile")
        .select("value")
        .eq("key", "last_parsed_at")
        .execute()
    )
    if not row.data:
        logger.info("Resume: no last_parsed_at found:  first run")
        return True

    last_parsed = row.data[0]["value"]
    modified    = get_resume_modified_time()
    changed     = modified > last_parsed
    logger.info(
        f"Resume: last_parsed={last_parsed[:19]}  "
        f"drive_modified={modified[:19]}  "
        f"→ {'CHANGED' if changed else 'unchanged'}"
    )
    return changed


def run_resume_parser(force: bool = False) -> bool:
    if not force and not needs_reparse():
        logger.info("Resume unchanged:  skipping re-parse")
        return False

    logger.info("Parsing resume...")
    resume_text = get_resume()
    logger.info(f"  Resume fetched ({len(resume_text)} chars)")

    # LLM Call 1:  skill extraction
    logger.info("LLM Call 1: extracting resume skills...")
    raw_response = call_llm(
        task=RESUME_SKILL_EXTRACTION,
        system_prompt=RESUME_SKILL_EXTRACTION_SYSTEM,
        user_prompt=resume_text,
    )
    raw_list = json.loads(raw_response)["skills"]
    skills   = list(dict.fromkeys(raw_list))
    logger.info(f"  Extracted {len(skills)} skills")

    # LLM Call 2:  condense resume
    logger.info("  LLM Call 2: condensing resume...")
    condensed = call_llm(
        task=RESUME_CONDENSATION,
        system_prompt=RESUME_CONDENSATION_SYSTEM,
        user_prompt=resume_text,
    )
    logger.info(f"  Condensed from {len(resume_text)} chars to {len(condensed)} chars")

    # Store to Supabase
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    skill_rows = [{"name": s} for s in skills]
    db.table("candidate_skills").upsert(skill_rows, on_conflict="name").execute()
    logger.info(f"  Stored {len(skill_rows)} candidate skills")

    now = datetime.now(timezone.utc).isoformat()
    db.table("candidate_profile").upsert(
        [
            {"key": "condensed_resume", "value": condensed},
            {"key": "last_parsed_at",   "value": now},
        ],
        on_conflict="key",
    ).execute()
    logger.info("  Stored condensed_resume and last_parsed_at")

    return True

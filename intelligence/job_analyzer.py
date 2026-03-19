import json
import logging
import re

from intelligence.prompts import (
    JOB_SKILL_EXTRACTION_SYSTEM,
    JOB_SKILL_EXTRACTION_USER,
    JOB_RESUME_MATCH_SYSTEM_TEMPLATE,
)
from intelligence.llm import call_llm
from intelligence.llm_config import JOB_SKILL_EXTRACTION, JOB_RESUME_MATCH

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e} — raw: {text[:200]}")
        return None


def extract_skills_from_jobs(title: str, description: str) -> dict | None:
    user = JOB_SKILL_EXTRACTION_USER.format(
        title=title,
        description=description[:4000],
    )
    try:
        print(f"SYSTEM_PROMPT\n{JOB_SKILL_EXTRACTION_SYSTEM}\nUSER PROMPT\n{user}")
        raw = call_llm(
            task=JOB_SKILL_EXTRACTION,
            system_prompt=JOB_SKILL_EXTRACTION_SYSTEM,
            user_prompt=user,
        )
        return _parse_json(raw)
    except Exception as e:
        logger.warning(f"failed to extract skills for for '{title}': {e}")
        return None


def match_resume_to_jobs(title: str, description: str, system_prompt: str) -> dict | None:
    user = JOB_RESUME_MATCH_SYSTEM_TEMPLATE.format(
        title=title,
        description=description[:2500],
    )
    try:
        raw = call_llm(
            task=JOB_RESUME_MATCH,
            system_prompt=system_prompt,
            user_prompt=user,
        )
        return _parse_json(raw)
    except Exception as e:
        logger.warning(f"smart_match failed for '{title}': {e}")
        return None
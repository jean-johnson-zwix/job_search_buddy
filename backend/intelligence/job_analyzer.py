import json
import logging
import re

from intelligence.prompts import (
    JOB_SKILL_EXTRACTION_SYSTEM,
    JOB_SKILL_EXTRACTION_USER,
    JOB_RESUME_MATCH_SYSTEM,
    JOB_RESUME_MATCH_USER
)
from intelligence.llm import call_llm
from intelligence.llm_config import JOB_SKILL_EXTRACTION, JOB_RESUME_MATCH

logger = logging.getLogger(__name__)


def _parse_json(text: str) -> dict | None:
    text = text.strip()
    # strip reasoning model thinking blocks (<think>...</think>)
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()

    # try marker extraction first (prompt-based JSON, works across all providers)
    marker_match = re.search(r"---JSON_START---\s*([\s\S]*?)\s*---JSON_END---", text)
    if marker_match:
        text = marker_match.group(1).strip()
    else:
        # fall back: strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Strip trailing junk after the last valid JSON delimiter
        trimmed = re.sub(r'[^"}\]]*$', '', text).strip()
        # Iteratively try closure sequences from simplest to most complete
        for closure in ['"', '"]', '"}', '"]}', '" ]}', '"} }']:
            try:
                result = json.loads(trimmed + closure)
                logger.warning("JSON truncation recovered (closure=%r) — skills may be incomplete", closure)
                return result
            except json.JSONDecodeError:
                continue
        logger.warning(f"JSON parse failed: {e} — raw: {text[:200]}")
        return None


def extract_skills_from_jobs(title: str, description: str) -> dict | None:
    user = JOB_SKILL_EXTRACTION_USER.format(
        title=title,
        description=description[:4000],
    )
    try:
        raw = call_llm(
            task=JOB_SKILL_EXTRACTION,
            system_prompt=JOB_SKILL_EXTRACTION_SYSTEM,
            user_prompt=user,
        )
        return _parse_json(raw)
    except Exception as e:
        logger.warning(f"failed to extract skills for for '{title}': {e}")
        return None


def match_resume_to_job(title: str, description: str) -> dict | None:
    user = JOB_RESUME_MATCH_USER.format(
        title=title,
        description=description[:4000],
    )
    try:
        raw = call_llm(
            task=JOB_RESUME_MATCH,
            system_prompt=JOB_RESUME_MATCH_SYSTEM,
            user_prompt=user,
        )
        return _parse_json(raw)
    except Exception as e:
        logger.warning(f"smart_match failed for '{title}': {e}")
        return None
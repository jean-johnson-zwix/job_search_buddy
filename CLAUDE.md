# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the pipeline

```bash
# Activate the virtual environment first
source venv/Scripts/activate   # Windows bash
# or: venv\Scripts\activate.bat  (cmd)

# Run the full pipeline
python main.py
```

There are no tests or linting tools configured. `pipeline/test_graph.py` is empty.

## Environment setup

Copy `.env` with the following keys (all required):
- `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY` — LLM providers
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — database
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `RESEND_TO_EMAIL` — email delivery
- Google OAuth credentials are read from `resources/credentials.json`

Database schema is in `migrations/001_init.sql`.

## Architecture

The pipeline is a **LangGraph `StateGraph`** defined entirely in `pipeline/graph.py`. All 6 nodes are functions in that file; `pipeline/state.py` defines the `PipelineState` TypedDict that flows between them.

**Node sequence:**
```
resume_extraction → data_loader → job_ingestion
                                        ↓ (conditional)
                          [jobs found] → job_extraction → job_matcher → emailer
                          [no jobs]   ──────────────────────────────→ emailer
```

**Key design decisions:**

- **New vs. known jobs split** (`node_job_ingestion`): jobs already in the DB are "known" (skills loaded from DB); only "new" jobs make LLM calls in `node_job_extraction`. This avoids redundant extraction.
- **Already-scored deduplication** (`node_job_match`): `already_scored` is a set of job IDs scored today, loaded in `node_data_loader`. The matcher skips these entirely.
- **4-second delay between LLM calls** (`DELAY_SEC = 4`): hardcoded in `graph.py` to avoid rate limits.
- **LLM fallback chain**: all LLM calls go through `intelligence/llm.py`, which retries with fallback providers per task config in `intelligence/llm_config.py`. Primary provider is Gemini; fallbacks are Groq then OpenRouter models.
- **Final score formula** (`intelligence/score.py`): `(skill_fit×0.5 + role_fit×0.3 + exp_fit×0.2)/100 × 0.50 + recency × 0.30 + tier_weight × 0.12`. Company tier ("faang", "unicorn", "startup") and posting recency both influence the final score independent of LLM match quality.

**Module responsibilities:**
- `ingestion/` — HTTP fetching from Greenhouse/Ashby ATS APIs + title/location filtering
- `intelligence/` — all LLM interactions: resume parsing, job skill extraction, resume↔job matching, scoring
- `datastore/db.py` — all Supabase reads/writes; single module, no ORM
- `delivery/email.py` — builds HTML digest and sends via Resend; also generates Claude.ai prompts embedded in the email for resume tailoring
- `utils/auth.py` — Google OAuth flow for Drive access (resume source)

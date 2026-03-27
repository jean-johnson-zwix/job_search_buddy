# Job Search Buddy — Backend

An automated job search pipeline that scrapes engineering roles from company ATS boards, scores them against your resume using LLMs, and delivers a ranked daily digest to your inbox.

---

## Features

- **ATS ingestion** — Fetches live job postings from Greenhouse and Ashby APIs across 50+ companies
- **Multi-stage filtering** — Drops non-US locations, irrelevant/senior titles, stale postings (> 30 days), and roles that explicitly deny visa sponsorship
- **Resume parsing** — Reads your resume from Google Drive, extracts skills and a condensed candidate profile via LLM; re-parses only when the file changes
- **Skill extraction** — For each new job, extracts role type, seniority, years required, and required skills via LLM; known jobs reload from the database to avoid redundant calls
- **Match scoring** — Scores each job against your candidate profile on three dimensions: skill fit, role fit, and experience fit
- **Final ranking** — Combines LLM scores with posting recency and company tier (FAANG / unicorn / startup) into a single `final_score`
- **Daily email digest** — Sends an HTML-formatted email with top matches, per-company capped at 3, plus embedded Claude.ai prompts for resume tailoring
- **LLM fallback chain** — Cerebras is the primary provider; falls back through SambaNova → Groq → OpenRouter → Gemini per task
- **Usage tracking** — Every pipeline run logs token counts and latency per task, provider, and model to the database

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph` |
| LLM providers | Cerebras (primary), SambaNova, Groq, OpenRouter, Gemini |
| Database | Supabase (PostgreSQL) |
| ATS APIs | Greenhouse Boards API, Ashby Posting API |
| Resume source | Google Drive (via OAuth) |
| Email delivery | [Resend](https://resend.com) |
| HTTP client | httpx |
| Runtime | Python 3.11+ |

---

## LLM Models

All LLM calls go through `intelligence/llm.py`, which tries providers in order and moves to the next fallback on any non-retryable error (429, 4xx).

| Task | Primary | Fallback 1 | Fallback 2 | Fallback 3 |
|---|---|---|---|---|
| `resume_skill_extraction` | Cerebras / Qwen-3-235B | Groq / Llama-3.3-70B | SambaNova / Llama-4-Maverick | Gemini Flash Lite |
| `resume_condensation` | Cerebras / Llama-3.1-8B | Groq / Qwen3-32B | Gemini Flash Lite | — |
| `job_skill_extraction` | Cerebras / Qwen-3-235B | SambaNova / Qwen3-32B | Groq / Llama-3.3-70B | Gemini Flash Lite |
| `job_resume_match` | Cerebras / Qwen-3-235B | Groq / Llama-3.3-70B | OpenRouter / DeepSeek-R1 | Gemini Flash Lite |

**Why Cerebras primary?** Sub-second inference on large models with generous free-tier rate limits — ideal for bulk extraction tasks (60–100 jobs per run).

**Why the fallback order?** SambaNova and Groq have higher rate limits than OpenRouter for the model sizes used. Gemini is last because it uses a different API format and is the most reliable but slowest.

---

## Project Structure

```
backend/
├── main.py                  # Entry point — builds and invokes the pipeline
├── pipeline/
│   ├── graph.py             # LangGraph StateGraph: all 6 nodes wired together
│   └── state.py             # PipelineState TypedDict
├── ingestion/
│   ├── job_retriever.py     # HTTP fetchers for Greenhouse + Ashby APIs
│   ├── job_filter.py        # Location, title, freshness, sponsorship filters
│   └── resume_reader.py     # Google Drive resume reader
├── intelligence/
│   ├── resume_parser.py     # Resume → skills + condensed profile (LLM)
│   ├── job_analyzer.py      # Job → skill extraction + resume match (LLM)
│   ├── score.py             # Final score formula
│   ├── llm.py               # LLM client with provider fallback
│   ├── llm_config.py        # Per-task model/provider configuration
│   └── prompts.py           # All LLM prompt templates
├── datastore/
│   └── db.py                # All Supabase reads and writes
├── delivery/
│   └── email.py             # HTML digest builder + Resend sender
├── utils/
│   ├── auth.py              # Google OAuth flow (one-time setup)
│   └── logging.py           # log_methods decorator
├── migrations/              # SQL schema and seed files (001–007)
├── scripts/
│   └── verify_slugs.py      # Validate ATS slugs are live
└── resources/
    └── credentials.json     # Google OAuth credentials (not committed)
```

---

## Pipeline Flow

```
resume_extraction → data_loader → job_ingestion
                                       ↓ (conditional)
                         [jobs found] → job_extraction → job_matcher → emailer
                         [no jobs]   ──────────────────────────────→ emailer
```

**Node responsibilities:**

| Node | What it does |
|---|---|
| `resume_extraction` | Parses resume from Google Drive; skips if file unchanged |
| `data_loader` | Loads companies, candidate skills, and already-scored job IDs from DB |
| `job_ingestion` | Fetches jobs from each company's ATS, applies all filters, splits into new vs. known |
| `job_extraction` | Extracts skills via LLM for new jobs; loads skills from DB for known jobs (bulk query) |
| `job_matcher` | Scores each job against the candidate profile; skips already-scored jobs |
| `emailer` | Sends daily digest; saves LLM usage and pipeline errors to DB |

---

## Environment Setup

Copy `.env.example` to `.env` and fill in all values:

```
CEREBRAS_API_KEY=
SAMBANOVA_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
GEMINI_API_KEY=

SUPABASE_URL=
SUPABASE_KEY=

RESEND_API_KEY=
RESEND_FROM_EMAIL=
RESEND_TO_EMAIL=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
```

Google OAuth credentials are read from `resources/credentials.json`. Run `utils/auth.py` once to generate the refresh token.

---

## Database Schema

Migrations live in `migrations/` and must be applied in order via the Supabase SQL editor.

| Migration | Description |
|---|---|
| `001_init.sql` | Core tables: `companies`, `jobs`, `job_skills`, `candidate_skills`, `resume_matches` |
| `002_add_status.sql` | Application status tracking on `resume_matches` |
| `003_seed_companies.sql` | Initial company seed data |
| `004_llm_usage.sql` | `llm_usage` table for per-task token tracking |
| `005_pipeline_errors.sql` | `pipeline_errors` table |
| `006_add_companies.sql` | Expanded company list (50+ companies) |
| `007_llm_usage_by_provider.sql` | Widens unique constraint to `(run_date, task, provider, model)` so fallback providers get separate rows |

---

## Commands

All commands must be run from the `backend/` directory.

```bash
cd backend

# Activate virtual environment
source venv/Scripts/activate      # Windows bash
# or: venv\Scripts\activate.bat   # cmd

# Install dependencies
pip install -r requirements.txt

# Apply database schema
# Run migrations 001–007 in order via the Supabase dashboard

# Verify company ATS slugs are live before seeding
python scripts/verify_slugs.py

# Run the full pipeline
python main.py
```

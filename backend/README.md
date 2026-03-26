# Job Search Buddy — Backend

An automated job search pipeline that scrapes engineering roles from company ATS boards, scores them against your resume using LLMs, and delivers a ranked daily digest to your inbox.

---

## Features

- **ATS ingestion** — Fetches live job postings from Greenhouse and Ashby APIs across a configurable list of companies
- **Multi-stage filtering** — Drops non-US locations, irrelevant/senior titles, stale postings (> 30 days), and roles that explicitly deny visa sponsorship
- **Resume parsing** — Reads your resume from Google Drive, extracts skills and a condensed candidate profile via LLM; re-parses only when the file changes
- **Skill extraction** — For each new job, extracts role type, seniority, years required, and required skills via LLM; known jobs reload from the database to avoid redundant calls
- **Match scoring** — Scores each job against your candidate profile on three dimensions: skill fit, role fit, and experience fit
- **Final ranking** — Combines LLM scores with posting recency and company tier (FAANG / unicorn / startup) into a single `final_score`
- **Daily email digest** — Sends an HTML-formatted email with top matches, per-company capped at 3, plus embedded Claude.ai prompts for resume tailoring
- **LLM fallback chain** — Primary provider is Gemini; falls back to Groq then OpenRouter models on failure

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph` |
| LLM providers | Gemini (primary), Groq, OpenRouter |
| Database | Supabase (PostgreSQL) |
| ATS APIs | Greenhouse Boards API, Ashby Posting API |
| Resume source | Google Drive (via OAuth) |
| Email delivery | [Resend](https://resend.com) |
| HTTP client | httpx |
| Runtime | Python 3.11+ |

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
├── migrations/              # SQL schema and seed files
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
| `job_extraction` | Extracts skills via LLM for new jobs; loads skills from DB for known jobs |
| `job_matcher` | Scores each job against the candidate profile; skips already-scored jobs |
| `emailer` | Sends daily digest; logs pipeline summary |

---

## Environment Setup

Copy `.env.example` to `.env` and fill in all values:

```
GEMINI_API_KEY=
OPENROUTER_API_KEY=
GROQ_API_KEY=

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

RESEND_API_KEY=
RESEND_FROM_EMAIL=
RESEND_TO_EMAIL=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
```

Google OAuth credentials are read from `resources/credentials.json`. Run `utils/auth.py` once to generate the refresh token.

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
# Run migrations/001_init.sql → 002 → 003 in order via the Supabase dashboard or psql

# Seed companies (destructive — clears existing data)
# Run migrations/003_seed_companies.sql via Supabase dashboard or psql

# Verify company ATS slugs are live before seeding
python scripts/verify_slugs.py

# Run the full pipeline
python main.py
```

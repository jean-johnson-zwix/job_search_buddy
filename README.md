# Job Search Buddy

An automated job search system that fetches engineering roles daily, scores them against your resume using LLMs, and delivers a ranked digest to your inbox — with a dashboard to track applications and analyze skill trends.

---

## What it does

1. **Fetches** new job postings every morning from Greenhouse and Ashby ATS boards across a curated list of companies
2. **Filters** out non-US roles, irrelevant titles (sales, HR, design, director-level), stale postings, and jobs that deny visa sponsorship
3. **Scores** each job against your resume on skill fit, role fit, and experience fit using Gemini AI
4. **Ranks** results by a composite score that also factors in posting recency and company tier (FAANG / unicorn / startup)
5. **Emails** a daily HTML digest of top matches with embedded resume-tailoring prompts
6. **Tracks** applications through a dashboard — from new match to interviewing

---

## Pipeline Flow

```
resume_extraction → data_loader → job_ingestion
                                        ↓
                          [new jobs found] → job_extraction → job_matcher → emailer
                          [no new jobs]   ──────────────────────────────→ emailer
```

| Node | What it does |
|---|---|
| `resume_extraction` | Pulls resume from Google Drive, extracts skills via LLM (skips if unchanged) |
| `data_loader` | Loads companies, candidate skills, and already-scored job IDs from DB |
| `job_ingestion` | Fetches from each company's ATS, filters, splits new vs. known |
| `job_extraction` | LLM skill extraction for new jobs; DB lookup for known jobs |
| `job_matcher` | Scores each job against candidate profile; skips already-scored |
| `emailer` | Sends digest, saves LLM usage stats to DB |

---

## Dashboard Pages

| Route | Description |
|---|---|
| `/jobs` | Ranked job matches — "To Apply" and "Applied" tabs. Update status inline. |
| `/skills` | Top skills in demand this week, 8-week trend chart, gap analysis vs. your resume |
| `/monitor` | LLM usage per pipeline run — calls, tokens, provider, avg latency |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Pipeline orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) StateGraph |
| LLM (primary) | Gemini Flash Lite |
| LLM (fallbacks) | Groq → OpenRouter |
| Database | Supabase (PostgreSQL) |
| ATS sources | Greenhouse Boards API, Ashby Posting API |
| Resume source | Google Docs (via OAuth) |
| Email delivery | [Resend](https://resend.com) |
| Dashboard | Next.js 16, TypeScript, Recharts |
| Hosting | GitHub Actions (pipeline) + Vercel (dashboard) |

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in:

```
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=

SUPABASE_URL=
SUPABASE_KEY=

RESEND_API_KEY=
DIGEST_EMAIL_FROM=
DIGEST_EMAIL_TO=

RESUME_DOC_ID=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=

MAX_NEW_JOBS=30    # cap for first run; set to 0 after
```

Run migrations in order via the Supabase SQL editor:
```
migrations/001_init.sql
migrations/002_add_status.sql
migrations/003_seed_companies.sql
migrations/004_llm_usage.sql
```

Run the pipeline:
```bash
python main.py
```

### Frontend

```bash
cd frontend
npm install
```

Create `.env.local`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

```bash
npm run dev   # http://localhost:3000
```

### GitHub Actions (daily schedule)

Add these repository secrets in Settings → Secrets:

```
GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY
SUPABASE_URL, SUPABASE_KEY
RESEND_API_KEY, DIGEST_EMAIL_FROM, DIGEST_EMAIL_TO
RESUME_DOC_ID, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
```

The pipeline runs automatically at **7am MST** daily. Trigger manually from the Actions tab.

---
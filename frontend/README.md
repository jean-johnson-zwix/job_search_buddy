# Job Search Buddy — Dashboard

Next.js frontend for the Job Search Buddy pipeline. Runs locally against Supabase.

---

## Pages

| Route | Description |
|---|---|
| `/jobs` | Ranked job matches — "To Apply" and "Applied" tabs. Search, sort, multi-select, download as markdown. |
| `/skills` | Top skills in market demand, 8-week trend chart, gap analysis vs. your resume skills. |
| `/monitor` | LLM token usage per task and provider per day, pipeline error logs. |

---

## Setup

```bash
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

---

## Tech Stack

- Next.js 16 App Router, React 19, TypeScript
- Recharts (bar + line charts)
- Supabase JS client (direct DB queries from API routes)
- DM Mono + Georgia — no UI component library

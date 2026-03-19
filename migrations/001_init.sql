create table if not exists companies (
  id          serial primary key,
  name        text not null,
  slug        text not null,        -- ATS identifier e.g. "stripe"
  ats         text not null,        -- "greenhouse" | "lever" | "ashby"
  tier        text not null,        -- "faang" | "unicorn" | "startup"
  created_at  timestamptz default now()
);

create table if not exists jobs (
  id              text primary key,  -- ATS job id (stable across runs)
  company_id      int references companies(id),
  title           text not null,
  role_type       text,              -- "SWE" | "ML" | "DevOps" | "Data" | "Other"
  seniority       text,              -- "Junior" | "Mid" | "Senior" | "Staff"
  years_required  int,               -- minimum years extracted by Prompt A
  location        text,
  remote          boolean default false,
  description     text,
  apply_url       text,
  posted_at       timestamptz,
  first_seen_at   timestamptz default now(),
  last_seen_at    timestamptz default now()
);

create table if not exists job_skills (
  id          serial primary key,
  job_id      text references jobs(id) on delete cascade,
  skill       text not null,
  category    text,                  -- "language" | "framework" | "cloud" | "tool" | "concept"
  required    boolean default true,
  created_at  timestamptz default now()
);

create table if not exists candidate_skills (
  name        text primary key,
  updated_at  timestamptz default now()
);

-- One-time resume parser output: key/value store
-- Keys: "condensed_resume", "last_parsed_at"
create table if not exists candidate_profile (
  key        text primary key,
  value      text,
  updated_at timestamptz default now()
);

-- Daily resume match scores
create table if not exists resume_matches (
  id              serial primary key,
  job_id          text references jobs(id) on delete cascade,
  skill_fit       int,               -- LLM score 0-100
  role_fit        int,               -- LLM score 0-100
  experience_fit  int,               -- LLM score 0-100
  matched_skills  text[],
  gap_skills      text[],
  green_flags     jsonb default '[]',
  red_flags       jsonb default '[]',
  summary         text,
  final_score     float,             -- weighted ranking score
  run_date        date default current_date,
  created_at      timestamptz default now(),
  unique(job_id, run_date)
);

-- Weekly aggregated skill trends (populated by a separate aggregation step)
create table if not exists skill_trends (
  id            serial primary key,
  skill         text not null,
  role_type     text,
  company_tier  text,
  week_start    date not null,
  job_count     int default 0,
  pct_of_jobs   float default 0,
  created_at    timestamptz default now(),
  unique(skill, role_type, company_tier, week_start)
);

-- Indexes
create index if not exists idx_jobs_posted_at        on jobs(posted_at desc);
create index if not exists idx_jobs_role_type        on jobs(role_type);
create index if not exists idx_job_skills_skill      on job_skills(skill);
create index if not exists idx_job_skills_job_id     on job_skills(job_id);
create index if not exists idx_skill_trends_week     on skill_trends(week_start desc);
create index if not exists idx_resume_matches_date   on resume_matches(run_date desc, final_score desc);
create index if not exists idx_candidate_skills_name on candidate_skills(name);

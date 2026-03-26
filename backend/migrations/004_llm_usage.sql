create table if not exists llm_usage (
  id               bigint generated always as identity primary key,
  run_date         date        not null,
  task             text        not null,
  provider         text        not null,
  model            text        not null,
  calls            int         not null default 0,
  prompt_tokens    int         not null default 0,
  completion_tokens int        not null default 0,
  total_tokens     int         not null default 0,
  avg_duration_ms  float,
  created_at       timestamptz not null default now(),
  unique (run_date, task)
);

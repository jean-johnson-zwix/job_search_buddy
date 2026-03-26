create table if not exists pipeline_errors (
  id         bigint generated always as identity primary key,
  run_date   date        not null,
  node       text        not null,
  job_id     text,
  job_title  text,
  error      text        not null,
  created_at timestamptz not null default now()
);

create index if not exists pipeline_errors_run_date_idx on pipeline_errors (run_date);

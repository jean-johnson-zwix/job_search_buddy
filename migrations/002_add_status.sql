alter table resume_matches
  add column status text not null default 'new',
  add column status_updated_at timestamptz,
  add column notes text;

alter table resume_matches
  add constraint resume_matches_status_check
  check (status in ('new', 'reviewing', 'applied', 'interviewing', 'rejected', 'ignored'));

create index if not exists idx_resume_matches_status on resume_matches(status);

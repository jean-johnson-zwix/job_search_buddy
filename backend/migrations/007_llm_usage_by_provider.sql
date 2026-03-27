-- Widen the llm_usage unique constraint to include provider and model.
-- Previously (run_date, task) meant all fallback-provider calls were silently
-- collapsed into one row under whichever provider appeared first.
-- Now each (run_date, task, provider, model) combination gets its own row.

alter table llm_usage
  drop constraint llm_usage_run_date_task_key;

alter table llm_usage
  add constraint llm_usage_run_date_task_provider_model_key
  unique (run_date, task, provider, model);

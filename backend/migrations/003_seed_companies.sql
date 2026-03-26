-- Seed file for tracked companies
-- WARNING: truncates all dependent data. Run only on a fresh or dev database.
truncate table resume_matches restart identity cascade;
truncate table job_skills restart identity cascade;
truncate table jobs restart identity cascade;
truncate table companies restart identity cascade;

-- FAANG tier — Greenhouse
insert into companies (name, slug, ats, tier) values
  ('Stripe',      'stripe',      'greenhouse', 'faang'),
  ('Airbnb',      'airbnb',      'greenhouse', 'faang'),
  ('Lyft',        'lyft',        'greenhouse', 'faang'),
  ('Dropbox',     'dropbox',     'greenhouse', 'faang'),
  ('Reddit',      'reddit',      'greenhouse', 'faang'),
  ('Robinhood',   'robinhood',   'greenhouse', 'faang'),
  ('Cloudflare',  'cloudflare',  'greenhouse', 'faang'),
  ('Databricks',  'databricks',  'greenhouse', 'faang'),
  ('Coinbase',    'coinbase',    'greenhouse', 'faang');

-- Unicorn tier — Greenhouse
-- Removed (404 — wrong slug or moved ATS): Notion, OpenAI, Plaid, Ramp, Rippling, Confluent, Miro, Deel
insert into companies (name, slug, ats, tier) values
  ('Anthropic',   'anthropic',   'greenhouse', 'unicorn'),
  ('Brex',        'brex',        'greenhouse', 'unicorn'),
  ('Datadog',     'datadog',     'greenhouse', 'unicorn'),
  ('Asana',       'asana',       'greenhouse', 'unicorn'),
  ('Grammarly',   'grammarly',   'greenhouse', 'unicorn'),
  ('Scale AI',    'scaleai',     'greenhouse', 'unicorn'),
  ('Chime',       'chime',       'greenhouse', 'unicorn'),
  ('Gusto',       'gusto',       'greenhouse', 'unicorn'),
  ('Airtable',    'airtable',    'greenhouse', 'unicorn');

-- Unicorn tier — Ashby
insert into companies (name, slug, ats, tier) values
  ('Vercel',      'vercel',      'ashby', 'unicorn'),
  ('Linear',      'linear',      'ashby', 'unicorn'),
  ('Retool',      'retool',      'ashby', 'unicorn'),
  ('Replit',      'replit',      'ashby', 'unicorn'),
  ('Mercury',     'mercury',     'ashby', 'unicorn'),
  ('Perplexity',  'perplexity',  'ashby', 'unicorn');

-- Startup tier — Ashby
insert into companies (name, slug, ats, tier) values
  ('Raycast',     'raycast',     'ashby', 'startup'),
  ('Posthog',     'posthog',     'ashby', 'startup'),
  ('Supabase',    'supabase',    'ashby', 'startup');

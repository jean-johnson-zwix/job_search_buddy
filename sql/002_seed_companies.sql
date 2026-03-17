-- Seed companies
-- Run after 001_init.sql
-- Add / remove companies to control your dataset

insert into companies (name, slug, ats, tier) values
  -- ── Greenhouse companies ──────────────────────────────────────────────
  ('Stripe',          'stripe',           'greenhouse', 'unicorn'),
  ('Figma',           'figma',            'greenhouse', 'unicorn'),
  ('Airbnb',          'airbnb',           'greenhouse', 'faang'),
  ('Dropbox',         'dropbox',          'greenhouse', 'unicorn'),
  ('Coinbase',        'coinbase',         'greenhouse', 'unicorn'),
  ('Robinhood',       'robinhood',        'greenhouse', 'unicorn'),
  ('Brex',            'brex',             'greenhouse', 'unicorn'),
  ('Databricks',      'databricks',       'greenhouse', 'unicorn'),
  ('Confluent',       'confluent',        'greenhouse', 'unicorn'),
  ('Scale AI',        'scaleai',          'greenhouse', 'unicorn'),

  -- ── Lever companies ──────────────────────────────────────────────────
  ('Netflix',         'netflix',          'lever',      'faang'),
  ('Reddit',          'reddit',           'lever',      'unicorn'),
  ('Lyft',            'lyft',             'lever',      'unicorn'),
  ('Instacart',       'instacart',        'lever',      'unicorn'),
  ('Twilio',          'twilio',           'lever',      'unicorn'),
  ('PagerDuty',       'pagerduty',        'lever',      'unicorn'),
  ('Carta',           'carta',            'lever',      'unicorn'),

  -- ── Ashby companies ──────────────────────────────────────────────────
  ('Notion',          'notion',           'ashby',      'unicorn'),
  ('Linear',          'linear',           'ashby',      'startup'),
  ('Ramp',            'ramp',             'ashby',      'unicorn'),
  ('Plaid',           'plaid',            'ashby',      'unicorn'),
  ('Retool',          'retool',           'ashby',      'startup'),
  ('Vercel',          'vercel',           'ashby',      'startup'),
  ('Supabase',        'supabase',         'ashby',      'startup'),
  ('Anthropic',       'anthropic',        'ashby',      'unicorn'),
  ('Mistral AI',      'mistral',          'ashby',      'startup'),
  ('Perplexity',      'perplexity-ai',    'ashby',      'startup')

on conflict do nothing;

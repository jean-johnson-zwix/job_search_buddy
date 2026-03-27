-- Migration 006: fix Vercel ATS, recover previously-failed companies, add 23 new companies

-- Add unique constraint on slug so future upserts are safe
ALTER TABLE companies ADD CONSTRAINT companies_slug_unique UNIQUE (slug);

-- ─── CORRECTION: Vercel was tracked under Ashby (0 jobs). Move to Greenhouse (79 jobs). ───
UPDATE companies SET ats = 'greenhouse' WHERE slug = 'vercel' AND ats = 'ashby';

-- ─── RECOVERED: previously failed — correct ATS/slug now confirmed ───
INSERT INTO companies (name, slug, ats, tier) VALUES
  ('OpenAI',       'openai',               'ashby',      'faang'),    -- moved from Greenhouse to Ashby
  ('Notion',       'notion',               'ashby',      'unicorn'),  -- moved from Greenhouse to Ashby
  ('Ramp',         'ramp',                 'ashby',      'unicorn'),
  ('Confluent',    'confluent',            'ashby',      'unicorn'),
  ('Deel',         'deel',                 'ashby',      'unicorn'),
  ('Miro',         'realtimeboardglobal',  'greenhouse', 'unicorn')   -- slug is not "miro"
ON CONFLICT (slug) DO NOTHING;

-- ─── NEW: FAANG tier ───
INSERT INTO companies (name, slug, ats, tier) VALUES
  ('DoorDash',     'doordashusa', 'greenhouse', 'faang'),   -- slug is not "doordash"
  ('MongoDB',      'mongodb',     'greenhouse', 'faang'),
  ('Twilio',       'twilio',      'greenhouse', 'faang'),
  ('Okta',         'okta',        'greenhouse', 'faang'),
  ('Snowflake',    'snowflake',   'ashby',      'faang')
ON CONFLICT (slug) DO NOTHING;

-- ─── NEW: Unicorn tier — Greenhouse ───
INSERT INTO companies (name, slug, ats, tier) VALUES
  ('Figma',        'figma',       'greenhouse', 'unicorn'),
  ('Duolingo',     'duolingo',    'greenhouse', 'unicorn'),
  ('Instacart',    'instacart',   'greenhouse', 'unicorn'),
  ('PagerDuty',    'pagerduty',   'greenhouse', 'unicorn'),
  ('Affirm',       'affirm',      'greenhouse', 'unicorn'),
  ('Together AI',  'togetherai',  'greenhouse', 'unicorn')
ON CONFLICT (slug) DO NOTHING;

-- ─── NEW: Unicorn tier — Ashby ───
INSERT INTO companies (name, slug, ats, tier) VALUES
  ('Cursor',       'cursor',      'ashby', 'unicorn'),
  ('Cohere',       'cohere',      'ashby', 'unicorn'),
  ('Anyscale',     'anyscale',    'ashby', 'unicorn'),
  ('ElevenLabs',   'elevenlabs',  'ashby', 'unicorn'),
  ('Character.AI', 'character',   'ashby', 'unicorn')
ON CONFLICT (slug) DO NOTHING;

-- ─── NEW: Startup tier — Greenhouse ───
INSERT INTO companies (name, slug, ats, tier) VALUES
  ('Warp Terminal', 'warp',      'greenhouse', 'startup'),
  ('Descript',      'descript',  'greenhouse', 'startup')
ON CONFLICT (slug) DO NOTHING;

-- ─── NEW: Startup tier — Ashby ───
INSERT INTO companies (name, slug, ats, tier) VALUES
  ('Modal',        'modal',      'ashby', 'startup'),
  ('LangChain',    'langchain',  'ashby', 'startup'),
  ('Cognition',    'cognition',  'ashby', 'startup'),
  ('Harvey',       'harvey',     'ashby', 'startup'),
  ('Writer',       'writer',     'ashby', 'startup')
ON CONFLICT (slug) DO NOTHING;

-- Threads Reposts → Ideas Pipeline
-- Run this in Supabase SQL Editor

CREATE TABLE reposts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  threads_post_id TEXT UNIQUE NOT NULL,
  original_author TEXT NOT NULL,
  original_content TEXT NOT NULL,
  reposted_at    TIMESTAMPTZ NOT NULL,
  scraped_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ideas (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repost_id       UUID REFERENCES reposts(id) ON DELETE CASCADE,
  content         TEXT NOT NULL,
  edited_content  TEXT,
  extended_thoughts JSONB DEFAULT '[]'::jsonb,
  category        TEXT,
  status          TEXT DEFAULT 'pending'
                  CHECK (status IN ('pending', 'approved', 'deleted')),
  reviewed_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE categories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ideas_status_idx     ON ideas(status);
CREATE INDEX ideas_category_idx   ON ideas(category);
CREATE INDEX ideas_created_at_idx ON ideas(created_at DESC);

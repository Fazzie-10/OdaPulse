-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    source TEXT,
    source_type TEXT DEFAULT 'rss',
    tags TEXT[] DEFAULT '{}',
    gist TEXT,
    published_at TIMESTAMPTZ,
    discovered_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS interest_tags TEXT[] DEFAULT '{"Politics", "Economy/Finance", "Security/Conflict", "Diaspora Policy", "Tech/Innovation", "Culture/Sports", "Health/Education"}';
ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS delivery_time TEXT DEFAULT '08:00';
ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS delivery_frequency TEXT DEFAULT 'daily';
ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS delivery_channel TEXT DEFAULT 'telegram';
ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS last_digest_sent TIMESTAMPTZ;

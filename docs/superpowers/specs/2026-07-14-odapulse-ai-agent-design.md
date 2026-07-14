# OdaPulse 2.0 — AI-Powered Nigerian News Agent

## Overview

Transform OdaPulse from an RSS broadcaster into an AI agent that tracks Nigeria-related news across diaspora and international media, generates personalized AI summaries, and delivers them via Telegram or email on a per-user schedule.

## Architecture

```
RSS feeds (30s poll) ─┐
                       ├──→ Dedup → AI tag + gist → Store → Match user topics
GDELT API (15min) ────┘                                      ↓
                                                        Compose digest
                                                        (7 days, by day)
                                                             ↓
                                                   Telegram / Email at
                                                   user's chosen time
```

### Components

| Module | Responsibility |
|--------|---------------|
| `bot.py` | Telegram commands, job queue, button handlers |
| `feeds.py` | RSS config + parallel async fetching with ETags |
| `gdelt_search.py` | GDELT DOC 2.0 API wrapper for diaspora news discovery |
| `ai_service.py` | Gemini 3 Flash: article tagging, gisting, digest composition |
| `scheduler.py` | Per-user digest scheduler (runs hourly, checks who's due) |
| `emailer.py` | Resend API for email digest delivery |
| `db.py` | Supabase: articles table + extended subscriber prefs |
| `notifier.py` | Telegram/email message formatting |
| `config.py` | Environment variable management |
| `landing/` | Static HTML landing page hosted on Railway |

## Pipeline

### Discovery Layer
- **RSS:** Existing 6 feeds, upgraded to parallel async + ETags, polled every 30s
- **GDELT:** Query `Nigeria` from `sourcecountry:US|GB|CA` every 15 minutes
- Results merged, deduplicated by URL, fed into AI pipeline

### AI Processing (per new article)
1. Fetch full text (trafilatura or readability)
2. Gemini 3 Flash: assign topic tags from predefined list
3. Gemini 3 Flash: write 1-2 sentence gist
4. Store in `articles` table

### User Matching
- Users pick interest tags from: Politics, Economy/Finance, Security/Conflict, Diaspora Policy, Tech/Innovation, Culture/Sports, Health/Education
- On digest time: pull articles since last digest matching user's tags

### Digest Composition
- **Daily:** articles from past 24h matching user interests
- **Weekly:** full 7-day summary, broken down by day, matching user interests
- Gemini 3 Flash composes ~500-word summary from stored gists
- If no matching articles → send "Nothing new today/week" message

### Delivery
- **Telegram:** via existing bot infra
- **Email:** via Resend API with HTML template
- Scheduled per user: pick hour + frequency (daily/weekly) + channel

## Database Changes

```sql
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  url TEXT UNIQUE,
  title TEXT,
  source TEXT,
  source_type TEXT,     -- "rss" or "gdelt"
  tags TEXT[],          -- ["Politics", "Security"]
  gist TEXT,            -- AI-generated summary
  published_at TIMESTAMPTZ,
  discovered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extended subscriber preferences
-- Delivery time (default 08:00)
-- Delivery frequency (daily/weekly, default daily)
-- Delivery channel (telegram/email/both, default telegram)
-- Email address
-- Interest tags array
-- Last digest sent timestamp
```

## Topic Tags

Politics | Economy/Finance | Security/Conflict | Diaspora Policy | Tech/Innovation | Culture/Sports | Health/Education

## Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Hosting | Railway (replaces Render) | $1/mo |
| Database | Supabase (existing) | Free |
| AI | Gemini 3 Flash API (free tier) | $0 |
| Discovery | GDELT DOC 2.0 API | $0 |
| News Sources | RSS + GDELT | $0 |
| Email | Resend (free tier) | $0 |
| Bot | python-telegram-bot | $0 |

## Build Order

1. Fix RSS speed (parallel async, ETags)
2. GDELT discovery layer
3. AI tagging + summarization pipeline
4. User preferences + scheduler
5. Email delivery via Resend
6. Static HTML landing page
7. Migrate Render → Railway + README + AGENTS.md

## API Keys Required

- Telegram Bot Token ✅ (existing)
- Supabase URL + Key ✅ (existing)
- Gemini API Key ❌ (get from aistudio.google.com)
- Resend API Key ❌ (get from resend.com)
- Railway Account ❌ (github sign in, $1/mo minimum)
- GDELT — no key needed

## Error Handling

- Failed GDELT queries: retry 3x with exponential backoff, skip cycle if all fail
- AI service failure: skip tagging for that article, retry next cycle
- Email failure (bounce, invalid): log, notify user via Telegram
- Scheduler: if user's digest fails, retry next hour, max 3 attempts
- Nothing new: send polite "no news today" message, don't leave users wondering

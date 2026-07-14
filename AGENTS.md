# OdaPulse — AI Agent Instructions

## Overview
OdaPulse is a Telegram bot + AI agent that tracks Nigerian news across local and diaspora media, generates AI summaries, and delivers personalized digests.

## Tech Stack
- Python 3.10+, python-telegram-bot, feedparser, gdeltdoc, google-genai, resend
- Supabase (PostgreSQL), Railway (hosting)

## Key Conventions
- All async functions use `asyncio` + `httpx` or native async SDKs
- AI tagging uses Gemini 2.0 Flash model
- Supabase is the single source of truth
- Tests go in `tests/`, one file per module
- Run `pytest tests/ -v` before committing

## Running Locally
```bash
pip install -r requirements.txt
python bot.py
```

## Deployment (Railway)
1. Push to GitHub
2. Connect repo on Railway
3. Set env vars (see .env.example)
4. Done — Railway detects Procfile

## Project Structure
| File | Purpose |
|------|---------|
| bot.py | Entry point, commands, job queue |
| feeds.py | RSS fetching (async parallel) |
| gdelt_search.py | GDELT diaspora news discovery |
| ai_service.py | Gemini tagging + digest composition |
| scheduler.py | Per-user digest scheduling |
| emailer.py | Resend email delivery |
| db.py | Supabase CRUD |
| notifier.py | Message formatting (Telegram + email) |
| config.py | Environment variable management |
| landing/ | Static HTML page |
| migration.sql | SQL to run in Supabase SQL Editor |

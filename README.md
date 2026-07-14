# 📰 OdaPulse — AI-Powered Nigerian News Agent

A Telegram bot + AI agent that tracks Nigerian news across local and diaspora media, generates AI summaries, and delivers personalized digests to your Telegram or email — on your schedule.

## Architecture

| Module | Responsibility |
|--------|---------------|
| `bot.py` | Entry point, command handlers, job queue |
| `feeds.py` | RSS fetching (async parallel) |
| `gdelt_search.py` | GDELT diaspora news discovery |
| `ai_service.py` | Gemini tagging + digest composition |
| `scheduler.py` | Per-user digest scheduling |
| `emailer.py` | Resend email delivery |
| `db.py` | Supabase CRUD |
| `notifier.py` | Message formatting (Telegram + email) |
| `config.py` | Environment variable management |
| `landing/` | Static HTML page |

## Pipeline

```
RSS feeds (30s) + GDELT API (15min)
         ↓
    Dedup + AI tag & gist
         ↓
    Store in Supabase
         ↓
    Match user interests → Compose digest
         ↓
    Deliver via Telegram / Email
```

## News Sources

**Nigerian 🇳🇬** — Punch, Daily Trust, HumAngle, Sahara Reporters
**International 🌍** — BBC World, ProPublica
**Diaspora 🌐** — Discovered via GDELT (US, UK, Canadian media covering Nigeria)

## Track Topics

Politics | Economy/Finance | Security/Conflict | Diaspora Policy | Tech/Innovation | Culture/Sports | Health/Education

---

## Setup

### 1. API Keys Needed

| Service | Where To Get |
|---------|-------------|
| Telegram Bot Token | [@BotFather](https://t.me/botfather) |
| Supabase URL + Key | [supabase.com](https://supabase.com) (your project settings) |
| Gemini API Key | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| Resend API Key | [resend.com](https://resend.com) → Sign up → API Keys |
| GDELT | No key needed (free API) |

### 2. Supabase Database

Run `migration.sql` in your Supabase SQL Editor to create the required tables.

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in all credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon/public key |
| `GEMINI_KEY` | Your Gemini API key |
| `RESEND_KEY` | Your Resend API key |
| `POLL_INTERVAL` | Feed check interval in seconds (default: 60) |
| `GDELT_INTERVAL` | GDELT query interval in seconds (default: 900) |

### 4. Install & Run Locally

```bash
pip install -r requirements.txt
python bot.py
```

---

## Deploy to Railway

1. Push this repo to GitHub
2. Connect the repo on [Railway](https://railway.app)
3. Railway auto-detects the `Procfile` — no extra config needed
4. Set all 6 environment variables in Railway's dashboard
5. Deploy — Railway keeps the bot running 24/7 with no sleep

---

## User Commands

| Command | Description |
|---------|-------------|
| `/start` | Subscribe to news updates |
| `/stop` | Unsubscribe from updates |
| `/settings` | Configure sources, topics, delivery time, channel, frequency |
| `/email your@email.com` | Set your email for digest delivery |
| `/digest` | Request an immediate digest |
| `/help` | Show all commands |

---

## License

MIT

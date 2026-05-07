# 📰 Pinnacle DaaS — Telegram RSS News Bot

A real-time Telegram bot that polls Nigerian and international RSS feeds every 60 seconds and broadcasts new articles to subscribed users.

## Architecture

| Module | Responsibility |
|---|---|
| `bot.py` | Entry point, command handlers, job queue |
| `feeds.py` | RSS feed configuration & parsing |
| `db.py` | Supabase persistence (deduplication + subscriptions) |
| `notifier.py` | Telegram message formatting (HTML) |
| `config.py` | Environment variable management |

## News Sources

**Nigerian 🇳🇬** — Punch, Daily Trust, HumAngle, Sahara Reporters  
**International 🌍** — BBC World, ProPublica

---

## Setup

### 1. Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a display name (e.g. "Pinnacle DaaS News") and a username (must end in `bot`, e.g. `PinnacleDaaSBot`)
4. BotFather replies with your **bot token** — copy it

### 2. Supabase

Create a free project at [supabase.com](https://supabase.com) and run this SQL in the SQL Editor:

```sql
CREATE TABLE seen_articles (
    url TEXT PRIMARY KEY,
    seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE subscribers (
    user_id BIGINT PRIMARY KEY
);
```

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon/public key |

### 4. Install & Run Locally

```bash
pip install -r requirements.txt
python bot.py
```

---

## Deploy to Railway

1. Push this repo to GitHub
2. Create a new project on [railway.app](https://railway.app)
3. Connect your GitHub repository
4. Add the three environment variables (`BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY`)
5. Railway auto-detects `requirements.txt` and starts the bot

> Railway's free tier keeps long-running Python processes alive 24/7 — ideal for polling bots.

---

## User Commands

| Command | Description |
|---|---|
| `/start` | Subscribe to news updates |
| `/stop` | Unsubscribe from updates |
| `/help` | Show available commands and sources |

---

## License

MIT

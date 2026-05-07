# 📰 OdaPulse — Telegram RSS News Bot

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
3. Choose a display name (e.g. "OdaPulse News") and a username (must end in `bot`, e.g. `OdaPulseBot`)
4. BotFather replies with your **bot token** — copy it

### 2. Supabase

Create a free project at [supabase.com](https://supabase.com) and run this SQL in the SQL Editor:

```sql
CREATE TABLE seen_articles (
    url TEXT PRIMARY KEY,
    seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE subscribers (
    user_id BIGINT PRIMARY KEY,
    preferences JSONB DEFAULT '{"sources": ["PUNCH", "DAILY TRUST", "HUMANGLE", "SAHARA REPORTERS", "BBC WORLD", "PROPUBLICA"]}'
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

## Deploy to Render (Free Tier)

Render's free tier requires apps to be "Web Services" and puts them to sleep after 15 minutes of inactivity. We've added a background `keep_alive` web server to the bot to handle this!

1. Push this repo to GitHub
2. Create a new **Web Service** on [Render.com](https://render.com)
3. Connect your GitHub repository
4. Set the **Build Command** to: `pip install -r requirements.txt`
5. Set the **Start Command** to: `python bot.py`
6. Add the three environment variables (`BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY`) in the Environment tab
7. Click **Deploy Web Service**

> **IMPORTANT:** Render will still put the bot to sleep after 15 minutes. To keep it running 24/7, copy the Render URL it gives you (e.g. `odapulse-bot-xxx.onrender.com`) and add it as an HTTP Monitor on [UptimeRobot.com](https://uptimerobot.com) to ping it every 10 minutes.

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

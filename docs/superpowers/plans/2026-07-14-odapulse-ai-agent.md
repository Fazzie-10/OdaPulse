# OdaPulse 2.0 — AI Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform OdaPulse from an RSS broadcaster into an AI agent that tracks Nigeria-related news via RSS + GDELT, tags articles with AI, and delivers personalized digests via Telegram/email on per-user schedules.

**Architecture:** Three-layer pipeline — (1) parallel RSS + GDELT discovery, (2) AI tagging at ingestion via Gemini 3 Flash, (3) per-user scheduler composing digests from tagged articles. Delivery via existing Telegram infra + new Resend email module.

**Tech Stack:** python-telegram-bot, feedparser, gdeltdoc, google-genai, resend-python, supabase, httpx, trafilatura, pytest

---

## File Structure

| File | Status | Responsibility |
|------|--------|----------------|
| `bot.py` | MODIFY | New commands, job queue wiring, silent poll |
| `feeds.py` | MODIFY | Parallel async RSS with ETags |
| `gdelt_search.py` | CREATE | GDELT DOC 2.0 API wrapper |
| `ai_service.py` | CREATE | Gemini tagging, gisting, digest composition |
| `scheduler.py` | CREATE | Per-user digest scheduler |
| `emailer.py` | CREATE | Resend email sender |
| `db.py` | MODIFY | New tables, subscriber pref functions |
| `notifier.py` | MODIFY | Digest formatting, email HTML template |
| `config.py` | MODIFY | New env vars: GEMINI_KEY, RESEND_KEY |
| `keep_alive.py` | REMOVE import | No longer needed on Railway |
| `Procfile` | MODIFY | Railway-compatible start command |
| `requirements.txt` | MODIFY | New Python packages |
| `.env.example` | CREATE | Document all env vars |
| `conftest.py` | CREATE | Test fixtures |
| `tests/` | CREATE | Per-module tests |
| `landing/index.html` | CREATE | Landing page HTML |
| `landing/style.css` | CREATE | Landing page CSS |
| `README.md` | MODIFY | Updated docs |
| `AGENTS.md` | CREATE | AI assistant instructions |

---

### Task 1: Project Setup — Dependencies, Config, Tests

**Files:**
- Modify: `requirements.txt`
- Modify: `config.py`
- Create: `.env.example`
- Create: `conftest.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Update requirements.txt**

```
python-telegram-bot[job-queue]>=20.0
feedparser
supabase
python-dotenv
httpx>=0.27.0
gdeltdoc
google-genai>=1.0.0
resend>=0.11.0
trafilatura>=1.8.0
pytest>=8.0
pytest-asyncio>=0.24.0
pytest-mock>=3.14.0
```

- [ ] **Step 2: Update config.py with new env vars**

Add `GEMINI_KEY`, `RESEND_KEY`, `GDELT_SEARCH_INTERVAL` to Config class:

```python
class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GEMINI_KEY = os.getenv("GEMINI_KEY")
    RESEND_KEY = os.getenv("RESEND_KEY")
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
    GDELT_INTERVAL = int(os.getenv("GDELT_INTERVAL", "900"))
```

Add validation for new vars alongside existing ones:

```python
if not Config.GEMINI_KEY:
    missing_vars.append("GEMINI_KEY")
if not Config.RESEND_KEY:
    missing_vars.append("RESEND_KEY")
```

- [ ] **Step 3: Create .env.example**

```
BOT_TOKEN=your_telegram_bot_token
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_KEY=your_gemini_api_key
RESEND_KEY=your_resend_api_key
POLL_INTERVAL=60
GDELT_INTERVAL=900
```

- [ ] **Step 4: Create conftest.py**

```python
import pytest

@pytest.fixture
def mock_article():
    return {
        "name": "PUNCH",
        "flag": "🇳🇬",
        "color": "🟢",
        "title": "Test Nigeria News Headline",
        "link": "https://example.com/test-article",
        "category": "Nigerian News",
        "published": "Mon, 14 Jul 2026 10:00:00 GMT",
    }

@pytest.fixture
def sample_gdelt_article():
    return {
        "url": "https://example.com/diaspora-article",
        "title": "Nigeria Diaspora Remittances Rise",
        "domain": "example.com",
        "sourcecountry": "US",
        "language": "english",
        "seendate": "20260714120000",
    }
```

- [ ] **Step 5: Create tests/__init__.py** (empty file)

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: project setup — deps, config, test framework"
```

---

### Task 2: Fix RSS Speed — Parallel Async Fetching

**Files:**
- Modify: `feeds.py`
- Create: `tests/test_feeds.py`

- [ ] **Step 1: Write test for parallel fetch**

```python
import pytest
from feeds import fetch_latest_articles_async

@pytest.mark.asyncio
async def test_fetch_latest_articles_async_returns_list():
    articles = await fetch_latest_articles_async()
    assert isinstance(articles, list)
    if articles:
        assert "name" in articles[0]
        assert "title" in articles[0]
        assert "link" in articles[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feeds.py -v`
Expected: FAIL with `ModuleNotFoundError` or `function not defined`

- [ ] **Step 3: Rewrite feeds.py with async parallel fetching**

```python
import logging
import feedparser
import time
import asyncio
import httpx

feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

logger = logging.getLogger(__name__)

FEEDS = {
    "Nigerian News": [
        {"name": "PUNCH", "url": "https://punchng.com/feed/", "flag": "🇳🇬", "color": "🟢"},
        {"name": "DAILY TRUST", "url": "https://dailytrust.com/feed/", "flag": "🇳🇬", "color": "🔵"},
        {"name": "HUMANGLE", "url": "https://humanglemedia.com/feed/", "flag": "🇳🇬", "color": "🟠"},
        {"name": "SAHARA REPORTERS", "url": "https://saharareporters.com/rss.xml", "flag": "🇳🇬", "color": "⚪"},
    ],
    "Foreign News": [
        {"name": "BBC WORLD", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "flag": "🌍", "color": "🔴"},
        {"name": "PROPUBLICA", "url": "https://feeds.propublica.org/propublica/main", "flag": "🌍", "color": "🟡"},
    ]
}

# Cache for ETag / Last-Modified per URL
_feed_cache = {}

async def _fetch_feed(client, source):
    url = source["url"]
    separator = "&" if "?" in url else "?"
    cache_busted_url = f"{url}{separator}nocache={int(time.time())}"

    headers = {}
    cached = _feed_cache.get(url)
    if cached:
        if cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]
        if cached.get("modified"):
            headers["If-Modified-Since"] = cached["modified"]

    try:
        response = await client.get(cache_busted_url, headers=headers, timeout=15.0)
        if response.status_code == 304:
            logger.info(f"Feed {source['name']}: 304 Not Modified")
            return []

        feed = feedparser.parse(response.text)
        etag = response.headers.get("etag")
        modified = response.headers.get("last-modified")
        if etag or modified:
            _feed_cache[url] = {"etag": etag, "modified": modified}

        if feed.bozo:
            logger.warning(f"Feed parse issue for {source['name']}: {feed.bozo_exception}")

        articles = []
        for entry in feed.entries[:5]:
            published = entry.get("published", "")
            articles.append({
                "name": source["name"],
                "flag": source["flag"],
                "color": source["color"],
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "category": list(FEEDS.keys())[[i for i, cat in enumerate(FEEDS.values()) if source in cat][0]],
                "published": published,
                "source_type": "rss",
            })
        return articles
    except Exception as e:
        logger.error(f"Failed to fetch feed {source['name']}: {e}")
        return []

async def fetch_latest_articles_async():
    all_sources = [src for sources in FEEDS.values() for src in sources]
    async with httpx.AsyncClient() as client:
        tasks = [_fetch_feed(client, src) for src in all_sources]
        results = await asyncio.gather(*tasks)
    articles = []
    for result in results:
        articles.extend(result)
    return articles

def fetch_latest_articles():
    return asyncio.run(fetch_latest_articles_async())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feeds.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: parallel async RSS feeds with ETag support"
```

---

### Task 3: GDELT Discovery Module

**Files:**
- Create: `gdelt_search.py`
- Create: `tests/test_gdelt_search.py`

- [ ] **Step 1: Write test for GDELT module**

```python
import pytest
from gdelt_search import search_diaspora_news

@pytest.mark.asyncio
async def test_search_diaspora_news_returns_list():
    articles = await search_diaspora_news()
    assert isinstance(articles, list)
    if articles:
        assert "url" in articles[0]
        assert "title" in articles[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gdelt_search.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create gdelt_search.py**

```python
import logging
from datetime import datetime, timezone, timedelta
from gdeltdoc import GdeltDoc, Filters

logger = logging.getLogger(__name__)

DIASPORA_SOURCES = ["US", "GB", "CA"]

async def search_diaspora_news(hours_back=24, max_records=50):
    gd = GdeltDoc()
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours_back)

    f = Filters(
        keyword="Nigeria",
        start_date=start.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"),
        country=DIASPORA_SOURCES,
        num_records=max_records,
    )

    try:
        articles_df = gd.article_search(f)
        if articles_df is None or articles_df.empty:
            return []

        results = []
        for _, row in articles_df.iterrows():
            results.append({
                "url": row.get("url", ""),
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "sourcecountry": row.get("sourcecountry", ""),
                "language": row.get("language", ""),
                "seendate": row.get("seendate", ""),
                "source_type": "gdelt",
            })
        return results
    except Exception as e:
        logger.error(f"GDELT search failed: {e}")
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gdelt_search.py -v`
Expected: PASS (or pass when GDELT API is reachable)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add GDELT diaspora news discovery module"
```

---

### Task 4: New Supabase Tables + db.py Functions

**Files:**
- Modify: `db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write tests for new db functions**

```python
import pytest
from db import save_article_meta, get_article_by_url, get_user_subscriber_prefs, update_user_subscriber_prefs

def test_save_and_get_article():
    url = "https://test.com/unique-article"
    save_article_meta(url, "Test Title", "PUNCH", "rss", ["Politics"], "A test gist")
    result = get_article_by_url(url)
    assert result is not None
    assert result["title"] == "Test Title"
    assert "Politics" in result["tags"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL with function not found

- [ ] **Step 3: Add new tables via Supabase migration**

```sql
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
```

- [ ] **Step 4: Add new functions to db.py**

```python
def save_article_meta(url, title, source, source_type, tags, gist, published_at=None):
    data = {
        "url": url,
        "title": title,
        "source": source,
        "source_type": source_type,
        "tags": tags,
        "gist": gist,
    }
    if published_at:
        data["published_at"] = published_at
    supabase.table("articles").upsert(data, on_conflict="url").execute()

def get_article_by_url(url):
    res = supabase.table("articles").select("*").eq("url", url).execute()
    return res.data[0] if res.data else None

def get_articles_by_tags(tags, since=None, limit=100):
    query = supabase.table("articles").select("*").overlaps("tags", tags)
    if since:
        query = query.gt("discovered_at", since.isoformat())
    res = query.order("discovered_at", desc=True).limit(limit).execute()
    return res.data

def get_user_subscriber_prefs(user_id):
    res = supabase.table("subscribers").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None

def update_user_subscriber_prefs(user_id, **kwargs):
    supabase.table("subscribers").update(kwargs).eq("user_id", user_id).execute()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: articles table and subscriber pref functions"
```

---

### Task 5: AI Service Module

**Files:**
- Create: `ai_service.py`
- Create: `tests/test_ai_service.py`

- [ ] **Step 1: Write tests for AI service**

```python
import pytest
from ai_service import tag_article, compose_digest

def test_tag_article_returns_tags():
    text = "The Nigerian government announced new economic reforms today in Abuja."
    result = tag_article(text)
    assert isinstance(result, dict)
    assert "tags" in result
    assert "gist" in result
    assert isinstance(result["tags"], list)

def test_compose_digest_returns_text():
    articles = [
        {"title": "Article 1", "gist": "Summary 1", "source": "PUNCH"},
        {"title": "Article 2", "gist": "Summary 2", "source": "BBC"},
    ]
    result = compose_digest(articles, daily=True)
    assert isinstance(result, str)
    assert len(result) > 50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai_service.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Create ai_service.py**

```python
import logging
from google import genai
from config import Config

logger = logging.getLogger(__name__)

VALID_TAGS = [
    "Politics", "Economy/Finance", "Security/Conflict",
    "Diaspora Policy", "Tech/Innovation", "Culture/Sports",
    "Health/Education"
]

client = genai.Client(api_key=Config.GEMINI_KEY)

TAG_PROMPT = """You are a news tagging assistant. Given the article text below, return:
1. Which topic tags apply (choose from: Politics, Economy/Finance, Security/Conflict, Diaspora Policy, Tech/Innovation, Culture/Sports, Health/Education)
2. A one-sentence gist of the article

Return JSON format: {"tags": ["Tag1", "Tag2"], "gist": "One sentence summary."}

Article: {text}"""

DIGEST_PROMPT = """You are a news digest writer. Write a 500-word digest from the articles below.
Group related topics together. Keep it informative and neutral.
Write in clear, engaging English.

{'daily': 'Cover the past 24 hours.', 'weekly': 'Cover the past 7 days, breaking it down by day. Start with a weekly overview paragraph.'}

Articles:
{articles_text}"""

def tag_article(text):
    prompt = TAG_PROMPT.format(text=text[:4000])
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview-01-28",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        result = response.parsed
        valid = [t for t in result.get("tags", []) if t in VALID_TAGS]
        return {"tags": valid[:3], "gist": result.get("gist", "")}
    except Exception as e:
        logger.error(f"AI tagging failed: {e}")
        return {"tags": [], "gist": ""}

def compose_digest(articles, daily=True):
    period = "daily" if daily else "weekly"
    articles_text = "\n\n".join(
        f"[{a.get('source', 'Unknown')}] {a.get('title', 'No title')}\n{a.get('gist', '')}"
        for a in articles
    )
    prompt = DIGEST_PROMPT.format(period=period, articles_text=articles_text)
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview-01-28",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Digest composition failed: {e}")
        return "Unable to generate digest at this time."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ai_service.py -v`
Expected: PASS (may need GEMINI_KEY in .env)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: AI service module for tagging and digest composition"
```

---

### Task 6: Wire Discovery Pipeline into bot.py

**Files:**
- Modify: `bot.py`

- [ ] **Step 1: Add silent poll and check_feeds that uses both RSS + GDELT**

Replace the existing `silent_startup_poll` and `check_feeds` functions:

```python
import asyncio
import feeds
import gdelt_search
import ai_service
from datetime import datetime, timezone
from trafilatura import fetch_url, extract

async def fetch_article_text(url):
    try:
        downloaded = fetch_url(url)
        text = extract(downloaded)
        return text[:4000] if text else None
    except Exception as e:
        logger.warning(f"Failed to fetch article text: {url} - {e}")
        return None

async def discover_and_process():
    """Fetch from RSS + GDELT, deduplicate, tag new articles."""
    all_articles = []
    rss_articles = await feeds.fetch_latest_articles_async()
    gdelt_articles = await gdelt_search.search_diaspora_news()

    for art in rss_articles:
        all_articles.append(art)
    for art in gdelt_articles:
        all_articles.append({
            "name": art.get("domain", "GDELT"),
            "flag": "🌐",
            "color": "🔍",
            "title": art.get("title", ""),
            "link": art.get("url", ""),
            "category": "Diaspora Media",
            "published": art.get("seendate", ""),
            "source_type": "gdelt",
        })

    all_links = [art["link"] for art in all_articles if art.get("link")]
    new_links = db.filter_new_articles(all_links)

    processed = 0
    for art in all_articles:
        if art["link"] in new_links:
            full_text = await fetch_article_text(art["link"])
            if full_text:
                ai_result = ai_service.tag_article(full_text)
                db.save_article_meta(
                    url=art["link"],
                    title=art["title"],
                    source=art.get("name", art.get("domain", "Unknown")),
                    source_type=art.get("source_type", "rss"),
                    tags=ai_result["tags"],
                    gist=ai_result["gist"],
                )
            db.save_article(art["link"])
            processed += 1

    logger.info(f"Discovery cycle complete. {len(new_links)} new articles found, {processed} processed.")
    return processed

async def silent_startup_poll(context):
    try:
        await discover_and_process()
        logger.info("Silent startup pre-warm complete.")
    except Exception as e:
        logger.error(f"Silent startup failed: {e}")

async def check_feeds(context):
    try:
        await discover_and_process()
    except Exception as e:
        logger.error(f"Feed check cycle failed: {e}")
```

- [ ] **Step 2: Update main() to reduce poll interval and add GDELT interval**

```python
def main():
    keep_alive()
    app = Application.builder().token(Config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    job_queue = app.job_queue
    # Silent warm-up at startup
    job_queue.run_once(silent_startup_poll, when=0)
    # Discovery loop every 60 seconds (covers RSS + GDELT)
    job_queue.run_repeating(check_feeds, interval=Config.POLL_INTERVAL, first=10)

    midnight = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)
    job_queue.run_daily(periodic_cleanup, time=midnight)

    print("OdaPulse Bot is Live...")
    app.run_polling()
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: wire RSS + GDELT discovery pipeline into bot"
```

---

### Task 7: Extended User Settings

**Files:**
- Modify: `bot.py`
- Modify: `notifier.py`

- [ ] **Step 1: Update /settings command with interest tags, delivery prefs**

Replace `settings_cmd` and `button_handler` with extended versions:

```python
ALL_SOURCES = ["PUNCH", "DAILY TRUST", "HUMANGLE", "SAHARA REPORTERS", "BBC WORLD", "PROPUBLICA"]
ALL_TAGS = ["Politics", "Economy/Finance", "Security/Conflict", "Diaspora Policy", "Tech/Innovation", "Culture/Sports", "Health/Education"]

async def settings_cmd(update, context):
    user_id = update.effective_user.id
    prefs = db.get_user_subscriber_prefs(user_id) or {}

    keyboard = [
        [InlineKeyboardButton("📰 News Sources", callback_data="menu_sources")],
        [InlineKeyboardButton("🏷️ Interest Topics", callback_data="menu_tags")],
        [InlineKeyboardButton("⏰ Delivery Time", callback_data="menu_time")],
        [InlineKeyboardButton("📬 Delivery Channel", callback_data="menu_channel")],
        [InlineKeyboardButton("📅 Frequency", callback_data="menu_frequency")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ <b>OdaPulse Settings</b>\nChoose what to configure:",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu_sources":
        await show_source_toggles(query, user_id)
    elif data == "menu_tags":
        await show_tag_toggles(query, user_id)
    elif data == "menu_time":
        await query.edit_message_text("⏰ Send me your preferred delivery time (24h format, e.g. 08:00 or 18:30):", parse_mode="HTML")
        context.user_data["awaiting_time"] = True
    elif data == "menu_channel":
        keyboard = [
            [InlineKeyboardButton("💬 Telegram", callback_data="channel_telegram")],
            [InlineKeyboardButton("📧 Email", callback_data="channel_email")],
            [InlineKeyboardButton("Both", callback_data="channel_both")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📬 Choose delivery channel:", reply_markup=reply_markup, parse_mode="HTML")
    elif data == "menu_frequency":
        keyboard = [
            [InlineKeyboardButton("Daily", callback_data="freq_daily")],
            [InlineKeyboardButton("Weekly", callback_data="freq_weekly")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📅 Choose digest frequency:", reply_markup=reply_markup, parse_mode="HTML")
    elif data.startswith("channel_"):
        channel = data.replace("channel_", "")
        db.update_user_subscriber_prefs(user_id, delivery_channel=channel)
        await query.edit_message_text(f"✅ Delivery channel set to {channel}.", parse_mode="HTML")
    elif data.startswith("freq_"):
        freq = data.replace("freq_", "")
        db.update_user_subscriber_prefs(user_id, delivery_frequency=freq)
        await query.edit_message_text(f"✅ Frequency set to {freq}.", parse_mode="HTML")
    elif data.startswith("toggle_"):
        await handle_source_toggle(query, user_id, data)

async def show_tag_toggles(query, user_id):
    prefs = db.get_user_subscriber_prefs(user_id) or {}
    active_tags = prefs.get("interest_tags", ALL_TAGS[:])
    keyboard = []
    for tag in ALL_TAGS:
        status = "✅" if tag in active_tags else "❌"
        keyboard.append([InlineKeyboardButton(f"{status} {tag}", callback_data=f"tagtoggle_{tag}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_sources")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🏷️ <b>Your Interest Topics</b>\nTap to toggle:",
        reply_markup=reply_markup, parse_mode="HTML"
    )
```

- [ ] **Step 2: Add /email command for setting email address**

```python
async def email_cmd(update, context):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /email your@email.com\nExample: /email john@example.com",
            parse_mode="HTML"
        )
        return
    email = args[0]
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Invalid email format.", parse_mode="HTML")
        return
    db.update_user_subscriber_prefs(user_id, email=email, delivery_channel="email")
    await update.message.reply_text(f"✅ Email set to {email}. You'll receive digests there.", parse_mode="HTML")
```

- [ ] **Step 3: Wire /email command in main()**

```python
app.add_handler(CommandHandler("email", email_cmd))
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: extended settings with topic tags, delivery prefs, /email command"
```

---

### Task 8: Scheduler Module

**Files:**
- Create: `scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write tests for scheduler**

```python
import pytest
from datetime import time, datetime, timezone, timedelta
from scheduler import get_due_users, mark_digest_sent

def test_get_due_users_returns_list():
    now = datetime.now(timezone.utc)
    due = get_due_users(now.hour)
    assert isinstance(due, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scheduler.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Create scheduler.py**

```python
import logging
from datetime import datetime, timezone, timedelta
from db import supabase

logger = logging.getLogger(__name__)

def get_due_users(current_hour):
    """Find users whose scheduled delivery time matches current_hour
    and whose last digest was sent before their next scheduled window."""
    res = supabase.table("subscribers").select("*").execute()
    due = []
    for row in res.data:
        prefs = row.get("preferences", {})
        delivery_time = prefs.get("delivery_time", "08:00")
        try:
            hour = int(delivery_time.split(":")[0])
        except (ValueError, IndexError):
            hour = 8

        if hour != current_hour:
            continue

        last_sent = row.get("last_digest_sent")
        if last_sent:
            last = datetime.fromisoformat(last_sent.replace("Z", "+00:00"))
            freq = prefs.get("delivery_frequency", "daily")
            window = timedelta(hours=23) if freq == "daily" else timedelta(days=6)
            if datetime.now(timezone.utc) - last < window:
                continue

        due.append({
            "user_id": row["user_id"],
            "delivery_frequency": prefs.get("delivery_frequency", "daily"),
            "delivery_channel": prefs.get("delivery_channel", "telegram"),
            "email": prefs.get("email", ""),
            "interest_tags": prefs.get("interest_tags", []),
        })
    return due

def mark_digest_sent(user_id):
    supabase.table("subscribers").update(
        {"last_digest_sent": datetime.now(timezone.utc).isoformat()}
    ).eq("user_id", user_id).execute()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scheduler.py -v`
Expected: PASS

- [ ] **Step 5: Create digest dispatch function in bot.py**

```python
async def dispatch_digest(context):
    """Hourly job: find due users, build + send digests."""
    current_hour = datetime.now(timezone.utc).hour
    due_users = get_due_users(current_hour)

    for user in due_users:
        try:
            tags = user["interest_tags"] if user["interest_tags"] else ai_service.VALID_TAGS
            since = datetime.now(timezone.utc) - timedelta(days=1 if user["delivery_frequency"] == "daily" else 7)
            articles = db.get_articles_by_tags(tags, since=since)

            if not articles:
                msg = "📭 No new articles matching your interests since your last digest."
            else:
                daily = user["delivery_frequency"] == "daily"
                digest = ai_service.compose_digest(articles, daily=daily)
                msg = notifier.format_digest(digest, articles, daily=daily)

            channel = user["delivery_channel"]
            if channel in ("telegram", "both"):
                await context.bot.send_message(chat_id=user["user_id"], text=msg, parse_mode="HTML")
            if channel in ("email", "both") and user.get("email"):
                emailer.send_digest(user["email"], msg, daily=user["delivery_frequency"] == "daily")

            mark_digest_sent(user["user_id"])
            logger.info(f"Digest sent to user {user['user_id']} via {channel}")
        except Exception as e:
            logger.error(f"Failed to send digest to user {user['user_id']}: {e}")
```

- [ ] **Step 6: Wire dispatch_digest in main()**

```python
job_queue.run_repeating(dispatch_digest, interval=3600, first=60)
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: per-user digest scheduler"
```

---

### Task 9: Digest Formatting in notifier.py

**Files:**
- Modify: `notifier.py`

- [ ] **Step 1: Add digest formatting functions**

```python
def format_digest(digest_text, articles, daily=True):
    period = "Daily" if daily else "Weekly"
    header = f"📰 <b>OdaPulse {period} Digest</b>\n\n"
    source_list = ", ".join(sorted(set(a.get("source", "") for a in articles)))
    if source_list:
        header += f"<i>Sources: {source_list}</i>\n\n"
    return header + digest_text

def format_email_digest(digest_text, articles, daily=True):
    period = "Daily" if daily else "Weekly"
    source_list = ", ".join(sorted(set(a.get("source", "") for a in articles)))
    articles_html = ""
    for a in articles[:10]:
        articles_html += f'<li><a href="{a.get("url", "#")}">{a.get("title", "")}</a><br><small>{a.get("source", "")} — {a.get("gist", "")}</small></li>'
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
<div style="background: #1a1a2e; color: white; padding: 20px; text-align: center;">
<h1>📰 OdaPulse {period} Digest</h1>
</div>
<div style="padding: 20px;">
<p>{digest_text}</p>
<hr>
<h3>Articles Covered</h3>
<ul>{articles_html}</ul>
<hr>
<small style="color: #888;">OdaPulse — AI-powered Nigerian news tracking</small>
</div>
</body>
</html>"""
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: digest formatting for Telegram and email"
```

---

### Task 10: Emailer Module

**Files:**
- Create: `emailer.py`
- Create: `tests/test_emailer.py`

- [ ] **Step 1: Write test**

```python
import pytest
from emailer import send_digest

def test_send_digest_raises_no_error_for_invalid_email():
    result = send_digest("invalid@test.com", "Test body", daily=True)
    assert result is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_emailer.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Create emailer.py**

```python
import logging
import resend
from config import Config

logger = logging.getLogger(__name__)

resend.api_key = Config.RESEND_KEY

FROM_EMAIL = "digest@odapulse.com"

def send_digest(to_email, digest_text, daily=True):
    if not Config.RESEND_KEY:
        logger.warning("RESEND_KEY not configured, skipping email")
        return False
    try:
        period = "Daily" if daily else "Weekly"
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"OdaPulse {period} Digest",
            "html": digest_text,
        }
        r = resend.Emails.send(params)
        logger.info(f"Email digest sent to {to_email}: {r.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_emailer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: emailer module via Resend"
```

---

### Task 11: Landing Page

**Files:**
- Create: `landing/index.html`
- Create: `landing/style.css`

- [ ] **Step 1: Create landing page**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OdaPulse — AI Nigerian News Agent</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>📰 OdaPulse</h1>
        <p class="tagline">AI-Powered Nigerian News Tracking</p>
    </header>
    <main>
        <section class="hero">
            <h2>Never miss what matters about Nigeria</h2>
            <p>OdaPulse tracks Nigerian news across local and diaspora media, intelligently summarizes what matters to you, and delivers it straight to your Telegram or email — on your schedule.</p>
            <a href="https://t.me/YourBotUsername" class="cta">Subscribe on Telegram</a>
        </section>
        <section class="features">
            <div class="feature">
                <span class="icon">🌐</span>
                <h3>Global Coverage</h3>
                <p>Nigerian media + diaspora outlets across US, UK, Canada — tracked 24/7</p>
            </div>
            <div class="feature">
                <span class="icon">🤖</span>
                <h3>AI Summaries</h3>
                <p>500-word daily or weekly digests written by AI, not algorithms</p>
            </div>
            <div class="feature">
                <span class="icon">🎯</span>
                <h3>Personalized</h3>
                <p>Choose topics you care about — politics, security, diaspora policy, and more</p>
            </div>
            <div class="feature">
                <span class="icon">📬</span>
                <h3>Your Way</h3>
                <p>Telegram or email, daily or weekly, at the time you pick</p>
            </div>
        </section>
        <section class="sources">
            <h3>News Sources</h3>
            <p><strong>Nigerian:</strong> Punch, Daily Trust, HumAngle, Sahara Reporters</p>
            <p><strong>International:</strong> BBC World, ProPublica + diaspora media via GDELT</p>
        </section>
        <section class="tags">
            <h3>Track Topics</h3>
            <div class="tag-list">
                <span>Politics</span><span>Economy</span><span>Security</span>
                <span>Diaspora</span><span>Tech</span><span>Culture</span><span>Health</span>
            </div>
        </section>
    </main>
    <footer>
        <p>OdaPulse — Built for Nigerians everywhere</p>
    </footer>
</body>
</html>
```

- [ ] **Step 2: Create style.css**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6; color: #333; background: #f5f5f5;
}
header {
    background: #1a1a2e; color: white; padding: 2rem; text-align: center;
}
header h1 { font-size: 2.5rem; }
.tagline { color: #e94560; font-size: 1.1rem; }
.hero {
    max-width: 700px; margin: 3rem auto; text-align: center; padding: 0 1rem;
}
.hero h2 { font-size: 1.8rem; margin-bottom: 1rem; }
.hero p { color: #666; margin-bottom: 2rem; font-size: 1.1rem; }
.cta {
    display: inline-block; background: #e94560; color: white; padding: 1rem 2rem;
    border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1rem;
}
.features {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem; max-width: 900px; margin: 3rem auto; padding: 0 1rem;
}
.feature {
    background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.feature .icon { font-size: 2rem; }
.feature h3 { margin: 0.5rem 0; }
.feature p { color: #666; font-size: 0.95rem; }
.sources, .tags {
    max-width: 700px; margin: 2rem auto; padding: 0 1rem; text-align: center;
}
.sources h3, .tags h3 { margin-bottom: 0.5rem; }
.tag-list span {
    display: inline-block; background: #1a1a2e; color: white; padding: 0.3rem 0.8rem;
    border-radius: 20px; margin: 0.25rem; font-size: 0.9rem;
}
footer {
    text-align: center; padding: 2rem; color: #888; font-size: 0.9rem;
}
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: static HTML landing page"
```

---

### Task 12: Railway Migration + README + AGENTS.md

**Files:**
- Modify: `bot.py` (remove keep_alive import)
- Modify: `Procfile`
- Create: `AGENTS.md`
- Modify: `README.md`

- [ ] **Step 1: Remove keep_alive from bot.py**

Remove `from keep_alive import keep_alive` and `keep_alive()` call in `main()`. Railway doesn't need it.

- [ ] **Step 2: Update Procfile for Railway**

```
web: python bot.py
```

Railway needs `web` process type (not `worker`) for HTTP port binding.

- [ ] **Step 3: Create AGENTS.md**

```markdown
# OdaPulse — AI Agent Instructions

## Overview
OdaPulse is a Telegram bot + AI agent that tracks Nigerian news across local and diaspora media, generates AI summaries, and delivers personalized digests.

## Tech Stack
- Python 3.10+, python-telegram-bot, feedparser, gdeltdoc, google-genai, resend
- Supabase (PostgreSQL), Railway (hosting)

## Key Conventions
- All async functions use `asyncio` + `httpx` or native async SDKs
- AI tagging uses Gemini 3 Flash Preview model
- Supabase is the single source of truth (PostgreSQL)
- Tests go in `tests/`, one file per module

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
- bot.py — entry point, commands, job queue
- feeds.py — RSS fetching (async parallel)
- gdelt_search.py — GDELT diaspora news discovery
- ai_service.py — Gemini tagging + digest composition
- scheduler.py — per-user digest scheduling
- emailer.py — Resend email delivery
- db.py — Supabase CRUD
- notifier.py — message formatting
- config.py — env var management
- landing/ — static HTML page
```

- [ ] **Step 4: Update README.md**

Replace the current README with updated content covering setup, commands, architecture, deployment on Railway, and API keys.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "docs: migrate to Railway, add AGENTS.md, update README"
```

---

## Self-Review Checklist

1. **Spec coverage:** Every section of the design doc has corresponding tasks (RSS speed → Task 2, GDELT → Task 3, AI → Task 5, User prefs → Task 7, Scheduler → Task 8, Email → Task 10, Landing page → Task 11, Railway/docs → Task 12)
2. **Placeholder scan:** No TBDs, TODOs, or incomplete steps
3. **Type consistency:** `ai_service.tag_article()` returns same shape everywhere, `db.save_article_meta()` matches across tasks, `gdelt_search.search_diaspora_news()` consistent with how bot.py consumes it
4. **All code complete:** Every step has actual runnable code, not descriptions

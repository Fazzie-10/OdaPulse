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

_feeds_cache = {}

_source_to_category = {}
for cat, sources in FEEDS.items():
    for src in sources:
        _source_to_category[src["name"]] = cat

async def _fetch_feed(client, source):
    url = source["url"]
    separator = "&" if "?" in url else "?"
    cache_busted_url = f"{url}{separator}nocache={int(time.time())}"

    headers = {}
    cached = _feeds_cache.get(url)
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
            _feeds_cache[url] = {"etag": etag, "modified": modified}

        if feed.bozo:
            logger.warning(f"Feed parse issue for {source['name']}: {feed.bozo_exception}")

        category = _source_to_category.get(source["name"], "Other")
        articles = []
        for entry in feed.entries[:5]:
            published = entry.get("published", "")
            articles.append({
                "name": source["name"],
                "flag": source["flag"],
                "color": source["color"],
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "category": category,
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

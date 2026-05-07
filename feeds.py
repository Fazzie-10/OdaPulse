import logging
import feedparser
import time

# Set a standard browser User-Agent to prevent 403 Forbidden errors and CDNs treating it as a bot
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

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

def fetch_latest_articles():
    """Fetch the top 5 entries from each configured RSS feed."""
    all_news = []
    for category, sources in FEEDS.items():
        for source in sources:
            try:
                # Add cache-busting query parameter to force fresh results from CDNs
                url = source['url']
                separator = '&' if '?' in url else '?'
                cache_busted_url = f"{url}{separator}nocache={int(time.time())}"
                
                feed = feedparser.parse(cache_busted_url)
                if feed.bozo:
                    logger.warning(f"Feed parse issue for {source['name']}: {feed.bozo_exception}")
                for entry in feed.entries[:5]:  # Check top 5
                    # Extract publish time if available
                    published = entry.get('published', '')
                    all_news.append({
                        "name": source['name'],
                        "flag": source['flag'],
                        "color": source['color'],
                        "title": entry.get('title', 'No title'),
                        "link": entry.get('link', ''),
                        "category": category,
                        "published": published,
                    })
            except Exception as e:
                logger.error(f"Failed to fetch feed {source['name']}: {e}")
                continue
    return all_news

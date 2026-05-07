import logging
from datetime import datetime, timedelta, timezone
from supabase import create_client
from config import Config

logger = logging.getLogger(__name__)

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


def filter_new_articles(urls):
    """Check which URLs have NOT been seen before — in a single DB call.

    Returns a set of URLs that are new (not in the seen_articles table).
    """
    if not urls:
        return set()
    res = supabase.table("seen_articles").select("url").in_("url", urls).execute()
    seen = {row['url'] for row in res.data}
    return set(urls) - seen


def save_article(url):
    """Mark an article URL as seen, with a timestamp for future cleanup."""
    supabase.table("seen_articles").insert({
        "url": url,
        "seen_at": datetime.now(timezone.utc).isoformat()
    }).execute()


def cleanup_old_articles(days=7):
    """Delete seen articles older than N days to prevent unbounded table growth."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        supabase.table("seen_articles").delete().lt("seen_at", cutoff).execute()
        logger.info(f"Cleaned up seen_articles older than {days} days")
    except Exception as e:
        logger.warning(f"Cleanup failed (table may not have seen_at column yet): {e}")


def add_subscriber(user_id):
    """Add or update a subscriber by their Telegram user ID."""
    supabase.table("subscribers").upsert({"user_id": user_id}).execute()


def remove_subscriber(user_id):
    """Remove a subscriber by their Telegram user ID."""
    supabase.table("subscribers").delete().eq("user_id", user_id).execute()


def get_subscribers():
    """Retrieve all subscribed user IDs."""
    res = supabase.table("subscribers").select("user_id").execute()
    return [row['user_id'] for row in res.data]

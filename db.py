import logging
from datetime import datetime, timedelta, timezone
from supabase import create_client
from config import Config

logger = logging.getLogger(__name__)

supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

DEFAULT_PREFS = {
    "sources": ["PUNCH", "DAILY TRUST", "HUMANGLE", "SAHARA REPORTERS", "BBC WORLD", "PROPUBLICA"]
}

def filter_new_articles(urls):
    """Check which URLs have NOT been seen before — in a single DB call."""
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
    """Add a new subscriber if they don't already exist."""
    res = supabase.table("subscribers").select("user_id").eq("user_id", user_id).execute()
    if len(res.data) == 0:
        supabase.table("subscribers").insert({"user_id": user_id, "preferences": DEFAULT_PREFS}).execute()

def remove_subscriber(user_id):
    """Remove a subscriber by their Telegram user ID."""
    supabase.table("subscribers").delete().eq("user_id", user_id).execute()

def update_user_prefs(user_id, sources_list):
    """Update a user's chosen news sources."""
    prefs = {"sources": sources_list}
    supabase.table("subscribers").update({"preferences": prefs}).eq("user_id", user_id).execute()

def get_subscribers_with_prefs():
    """Retrieve all subscribers and their active source preferences."""
    res = supabase.table("subscribers").select("user_id, preferences").execute()
    subs = {}
    for row in res.data:
        prefs = row.get("preferences")
        if prefs is None:
            prefs = DEFAULT_PREFS
        subs[row['user_id']] = prefs.get("sources", DEFAULT_PREFS["sources"])
    return subs

def get_user_prefs(user_id):
    """Get a specific user's active sources."""
    res = supabase.table("subscribers").select("preferences").eq("user_id", user_id).execute()
    if len(res.data) > 0:
        prefs = res.data[0].get("preferences")
        if prefs is None:
            prefs = DEFAULT_PREFS
        return prefs.get("sources", DEFAULT_PREFS["sources"])
    return []

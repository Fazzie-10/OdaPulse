import html
from datetime import datetime
from email.utils import parsedate_to_datetime


def _parse_publish_time(published_str):
    """Try to parse the RSS publish time, fall back to current time."""
    if published_str:
        try:
            return parsedate_to_datetime(published_str)
        except Exception:
            pass
    return datetime.now()


def format_message(article):
    """Format an article into a styled Telegram message using HTML.

    Uses HTML parse mode instead of Markdown to avoid crashes
    when headlines contain *, _, [, or other special characters.
    """
    pub_time = _parse_publish_time(article.get('published', ''))
    time_str = pub_time.strftime("%I:%M %p | %b %d, %Y")

    # HTML-escape the title to prevent parse errors from special characters
    safe_title = html.escape(article['title'])
    safe_link = html.escape(article['link'])

    return (
        f"{article['color']} [{article['name']}] {article['flag']}📰\n"
        f"<b>{safe_title}</b>\n\n"
        f"🕐 {time_str}\n"
        f"🔗 <a href=\"{safe_link}\">Read more →</a>"
    )

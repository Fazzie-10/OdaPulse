import html
from datetime import datetime
from email.utils import parsedate_to_datetime


def _parse_publish_time(published_str):
    if published_str:
        try:
            return parsedate_to_datetime(published_str)
        except Exception:
            pass
    return datetime.now()


def format_message(article):
    pub_time = _parse_publish_time(article.get('published', ''))
    time_str = pub_time.strftime("%I:%M %p | %b %d, %Y")

    safe_title = html.escape(article['title'])
    safe_link = html.escape(article['link'])

    return (
        f"{article['color']} [{article['name']}] {article['flag']}📰\n"
        f"<b>{safe_title}</b>\n\n"
        f"🕐 {time_str}\n"
        f"🔗 <a href=\"{safe_link}\">Read more →</a>"
    )


def format_digest(digest_text, articles, daily=True):
    period = "Daily" if daily else "Weekly"
    source_list = ", ".join(sorted(set(a.get("source", "") for a in articles)))
    header = f"📰 <b>OdaPulse {period} Digest</b>\n\n"
    if source_list:
        header += f"<i>Sources: {source_list}</i>\n\n"
    return header + digest_text


def format_email_digest(digest_text, articles, daily=True):
    period = "Daily" if daily else "Weekly"
    source_list = ", ".join(sorted(set(a.get("source", "") for a in articles)))
    articles_html = ""
    for a in articles[:10]:
        safe_url = html.escape(a.get("url", "#"))
        safe_title = html.escape(a.get("title", ""))
        safe_source = html.escape(a.get("source", ""))
        safe_gist = html.escape(a.get("gist", ""))
        articles_html += f'<li><a href="{safe_url}">{safe_title}</a><br><small>{safe_source} — {safe_gist}</small></li>'
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

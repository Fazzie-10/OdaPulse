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

Return JSON format: {{"tags": ["Tag1", "Tag2"], "gist": "One sentence summary."}}

Article: {text}"""

DIGEST_PROMPT = """You are a news digest writer. Write a 500-word digest from the articles below.
Group related topics together. Keep it informative and neutral.
Write in clear, engaging English.

{period_label}

Articles:
{articles_text}"""

def tag_article(text):
    prompt = TAG_PROMPT.format(text=text[:4000])
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
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
    try:
        period_label = "Cover the past 24 hours." if daily else "Cover the past 7 days, breaking it down by day. Start with a weekly overview paragraph."
        articles_text = "\n\n".join(
            f"[{a.get('source', 'Unknown')}] {a.get('title', 'No title')}\n{a.get('gist', '')}"
            for a in articles
        )
        prompt = DIGEST_PROMPT.format(period_label=period_label, articles_text=articles_text)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Digest composition failed: {e}")
        lines = [f"• {a.get('title', 'No title')} — {a.get('source', 'Unknown')}" for a in articles]
        return f"Here's your {period} roundup of Nigeria-related news:\n\n" + "\n".join(lines)

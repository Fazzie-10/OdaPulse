import asyncio
import logging
import traceback
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
        articles_df = await asyncio.to_thread(gd.article_search, f)
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
        logger.error(f"GDELT search failed: {traceback.format_exc()}")
        return []

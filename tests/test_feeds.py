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

import pytest
from gdelt_search import search_diaspora_news

@pytest.mark.asyncio
async def test_search_diaspora_news_returns_list():
    articles = await search_diaspora_news()
    assert isinstance(articles, list)
    if articles:
        assert "url" in articles[0]
        assert "title" in articles[0]

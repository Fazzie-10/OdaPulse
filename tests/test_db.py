import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_supabase():
    with patch("db.supabase") as mock:
        mock.table.return_value.select.return_value.execute.return_value.data = []
        yield mock

def test_save_article_meta_upserts(mock_supabase):
    from db import save_article_meta
    save_article_meta(
        url="https://test.com/article",
        title="Test Title",
        source="PUNCH",
        source_type="rss",
        tags=["Politics"],
        gist="A test gist",
    )
    mock_supabase.table.assert_called_with("articles")
    mock_supabase.table.return_value.upsert.assert_called_once()

def test_get_article_by_url_returns_none_when_missing(mock_supabase):
    from db import get_article_by_url
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    result = get_article_by_url("https://test.com/missing")
    assert result is None

def test_get_article_by_url_returns_article_when_found(mock_supabase):
    from db import get_article_by_url
    mock_data = [{"url": "https://test.com/art", "title": "Test"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_data
    result = get_article_by_url("https://test.com/art")
    assert result == mock_data[0]

def test_get_articles_by_tags_returns_list(mock_supabase):
    from db import get_articles_by_tags
    mock_supabase.table.return_value.select.return_value.gt.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    result = get_articles_by_tags(["Politics"])
    assert isinstance(result, list)

def test_update_user_subscriber_prefs_calls_update(mock_supabase):
    from db import update_user_subscriber_prefs
    update_user_subscriber_prefs(user_id=12345, email="test@example.com")
    mock_supabase.table.assert_called_with("subscribers")
    mock_supabase.table.return_value.update.assert_called_once()

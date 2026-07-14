import pytest

@pytest.fixture
def mock_article():
    return {
        "name": "PUNCH",
        "flag": "🇳🇬",
        "color": "🟢",
        "title": "Test Nigeria News Headline",
        "link": "https://example.com/test-article",
        "category": "Nigerian News",
        "published": "Mon, 14 Jul 2026 10:00:00 GMT",
    }

@pytest.fixture
def sample_gdelt_article():
    return {
        "url": "https://example.com/diaspora-article",
        "title": "Nigeria Diaspora Remittances Rise",
        "domain": "example.com",
        "sourcecountry": "US",
        "language": "english",
        "seendate": "20260714120000",
    }

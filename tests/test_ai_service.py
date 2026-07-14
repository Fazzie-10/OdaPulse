import pytest
from unittest.mock import patch, MagicMock
from ai_service import VALID_TAGS

@pytest.fixture
def mock_genai():
    with patch("ai_service.client") as mock:
        yield mock

def test_valid_tags_defined():
    assert len(VALID_TAGS) > 0
    assert "Politics" in VALID_TAGS

def test_tag_article_returns_dict_on_failure(mock_genai):
    mock_genai.models.generate_content.side_effect = Exception("API error")
    from ai_service import tag_article
    result = tag_article("Some article text")
    assert isinstance(result, dict)
    assert "tags" in result
    assert "gist" in result

def test_compose_digest_returns_string_on_failure(mock_genai):
    mock_genai.models.generate_content.side_effect = Exception("API error")
    from ai_service import compose_digest
    result = compose_digest([{"title": "Test", "gist": "Gist", "source": "BBC"}], daily=True)
    assert isinstance(result, str)
    assert "Unable to generate" in result

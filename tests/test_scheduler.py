import pytest
from unittest.mock import patch

@pytest.fixture
def mock_supabase():
    with patch("scheduler.supabase") as mock:
        yield mock

def test_get_due_users_returns_list(mock_supabase):
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = []
    from scheduler import get_due_users
    result = get_due_users(8)
    assert isinstance(result, list)

def test_get_due_users_filters_by_hour(mock_supabase):
    mock_data = [
        {"user_id": 1, "delivery_time": "08:00", "delivery_frequency": "daily",
         "last_digest_sent": None, "email": "", "interest_tags": []},
        {"user_id": 2, "delivery_time": "14:00", "delivery_frequency": "daily",
         "last_digest_sent": None, "email": "", "interest_tags": []},
    ]
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = mock_data
    from scheduler import get_due_users
    result = get_due_users(8)
    assert len(result) == 1
    assert result[0]["user_id"] == 1

import pytest
from unittest.mock import patch

def test_send_digest_returns_false_without_key():
    with patch("emailer.Config.RESEND_KEY", "placeholder_get_from_resend"):
        from emailer import send_digest
        result = send_digest("test@example.com", "<p>Test body</p>", daily=True)
        assert result is False

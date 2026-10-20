"""
Test KC-06: Error handling: API timeout returns retry-able error.

TDD Phase: RED -> GREEN
"""
import pytest
from unittest.mock import patch, MagicMock
import httpx


class TestClientTimeout:
    """Tests for timeout error handling."""

    def test_timeout_raises_retryable_error(self):
        """KC-06a: API timeout raises TimeoutError with retryable=True."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import TimeoutError

        with patch('httpx.Client.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Connection timed out")

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(TimeoutError) as exc_info:
                client.authenticate()

            assert exc_info.value.retryable is True
            assert "timed out" in str(exc_info.value).lower()

    def test_connect_timeout_is_retryable(self):
        """KC-06b: Connection timeout is also retryable."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import TimeoutError

        with patch('httpx.Client.post') as mock_post:
            mock_post.side_effect = httpx.ConnectTimeout("Connect timeout")

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(TimeoutError) as exc_info:
                client.create_story(project_id=1, title="Test", column_id=1)

            assert exc_info.value.retryable is True

    def test_read_timeout_is_retryable(self):
        """KC-06c: Read timeout is also retryable."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import TimeoutError

        with patch('httpx.Client.post') as mock_post:
            mock_post.side_effect = httpx.ReadTimeout("Read timeout")

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(TimeoutError) as exc_info:
                client.list_stories(project_id=1)

            assert exc_info.value.retryable is True

    def test_timeout_error_code_is_408(self):
        """KC-06d: TimeoutError has HTTP 408 code."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import TimeoutError

        with patch('httpx.Client.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(TimeoutError) as exc_info:
                client.authenticate()

            assert exc_info.value.code == 408

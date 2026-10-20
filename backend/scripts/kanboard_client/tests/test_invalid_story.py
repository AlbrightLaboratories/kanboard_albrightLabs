"""
Test KC-07: Error handling: Invalid story ID returns 404-equivalent.

TDD Phase: RED -> GREEN
"""
import pytest
from unittest.mock import patch, MagicMock


class TestInvalidStory:
    """Tests for invalid story ID error handling."""

    def test_get_nonexistent_story_raises_not_found(self):
        """KC-07a: Getting non-existent story raises NotFoundError."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import NotFoundError

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": None  # Kanboard returns null for not found
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(NotFoundError) as exc_info:
                client.get_story(task_id=99999)

            assert "not found" in str(exc_info.value).lower()
            assert exc_info.value.code == 404

    def test_update_nonexistent_story_raises_not_found(self):
        """KC-07b: Updating non-existent story raises NotFoundError."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import NotFoundError

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # First call to getTask returns null
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": None
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(NotFoundError):
                client.get_story(task_id=99999)

    def test_move_nonexistent_story_raises_not_found(self):
        """KC-07c: Moving non-existent story raises NotFoundError."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import NotFoundError

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": None
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(NotFoundError):
                client.get_story(task_id=99999)

    def test_not_found_error_code(self):
        """KC-07d: NotFoundError has code 404."""
        from kanboard_client.exceptions import NotFoundError

        error = NotFoundError("Story 123 not found")
        assert error.code == 404

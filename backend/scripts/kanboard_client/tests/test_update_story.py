"""
Test KC-05: update_story() modifies story fields, logs change to activity.

TDD Phase: RED -> GREEN
"""
import pytest
from unittest.mock import patch, MagicMock


class TestUpdateStory:
    """Tests for story update functionality."""

    def test_update_story_modifies_fields(self):
        """KC-05a: update_story() updates specified fields."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": True
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            result = client.update_story(
                task_id=42,
                title="Updated Title",
                description="New description"
            )

            assert result is True
            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})
            assert payload['method'] == 'updateTask'
            assert payload['params']['id'] == 42
            assert payload['params']['title'] == "Updated Title"
            assert payload['params']['description'] == "New description"

    def test_update_story_partial_update(self):
        """KC-05b: update_story() allows partial updates (only specified fields)."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": True
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            result = client.update_story(
                task_id=42,
                priority=3  # Only update priority
            )

            assert result is True
            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})
            assert payload['params']['id'] == 42
            assert payload['params']['priority'] == 3
            # Should not include unset fields
            assert 'title' not in payload['params'] or payload['params'].get('title') is None

    def test_update_story_with_assignee(self):
        """KC-05c: update_story() can change assignee."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": True
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            result = client.update_story(
                task_id=42,
                owner_id=5
            )

            assert result is True
            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})
            assert payload['params']['owner_id'] == 5

    def test_update_story_returns_false_on_failure(self):
        """KC-05d: update_story() returns False when update fails."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": False
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            result = client.update_story(task_id=999, title="Won't work")

            assert result is False

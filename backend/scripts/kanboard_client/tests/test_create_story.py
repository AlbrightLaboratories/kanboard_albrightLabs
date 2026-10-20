"""
Test KC-02: create_story() creates story in Backlog, returns story ID.

TDD Phase: RED -> GREEN
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCreateStory:
    """Tests for story creation functionality."""

    def test_create_story_returns_story_id(self):
        """KC-02a: create_story() returns the new story ID."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": 42  # New story ID
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            story_id = client.create_story(
                project_id=1,
                title="New Story",
                description="Story description",
                column_id=1  # Backlog
            )

            assert story_id == 42

    def test_create_story_sends_correct_payload(self):
        """KC-02b: create_story() sends proper JSON-RPC payload."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": 123
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            client.create_story(
                project_id=5,
                title="Test Story",
                description="Description here",
                column_id=1  # Backlog column
            )

            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})

            assert payload['method'] == 'createTask'
            assert payload['params']['project_id'] == 5
            assert payload['params']['title'] == 'Test Story'
            assert payload['params']['description'] == 'Description here'
            assert payload['params']['column_id'] == 1

    def test_create_story_defaults_to_backlog(self):
        """KC-02c: create_story() defaults to first column (Backlog) if not specified."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            # First call returns columns, second creates task
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = [
                # getColumns response
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": [
                        {"id": 10, "title": "Backlog", "position": 1},
                        {"id": 11, "title": "In Progress", "position": 2}
                    ]
                },
                # createTask response
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": 99
                }
            ]
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            story_id = client.create_story(
                project_id=1,
                title="Story without column"
            )

            assert story_id == 99
            # Should have fetched columns first
            calls = mock_post.call_args_list
            assert len(calls) == 2

    def test_create_story_with_optional_fields(self):
        """KC-02d: create_story() supports optional fields like assignee, priority."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": 200
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            story_id = client.create_story(
                project_id=1,
                title="Story with options",
                description="Full description",
                column_id=1,
                owner_id=5,  # Assignee
                priority=2,
                tags=["bug", "urgent"]
            )

            assert story_id == 200
            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})

            assert payload['params']['owner_id'] == 5
            assert payload['params']['priority'] == 2
            assert payload['params']['tags'] == ["bug", "urgent"]

    def test_create_story_handles_api_error(self):
        """KC-02e: create_story() raises KanboardError on API failure."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import KanboardError

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32602,
                    "message": "Invalid project_id"
                }
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(KanboardError) as exc_info:
                client.create_story(
                    project_id=999,  # Invalid
                    title="Story"
                )

            assert "Invalid project_id" in str(exc_info.value)

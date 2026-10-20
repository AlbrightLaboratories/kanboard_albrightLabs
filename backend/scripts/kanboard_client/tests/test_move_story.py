"""
Test KC-03: move_story() moves story between columns, validates column exists.

TDD Phase: RED -> GREEN
"""
import pytest
from unittest.mock import patch, MagicMock


class TestMoveStory:
    """Tests for story movement functionality."""

    def test_move_story_to_valid_column(self):
        """KC-03a: move_story() moves story to specified column."""
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

            result = client.move_story(
                task_id=42,
                column_id=5
            )

            assert result is True
            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})
            assert payload['method'] == 'moveTaskPosition'
            assert payload['params']['task_id'] == 42
            assert payload['params']['column_id'] == 5

    def test_move_story_validates_column_exists(self):
        """KC-03b: move_story() validates target column exists."""
        from kanboard_client.client import KanboardClient
        from kanboard_client.exceptions import NotFoundError

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # getColumns returns valid columns, but moveTask fails
            mock_response.json.side_effect = [
                # getColumns response - column 999 not in list
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": [
                        {"id": 1, "title": "Backlog"},
                        {"id": 2, "title": "In Progress"}
                    ]
                }
            ]
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            with pytest.raises(NotFoundError) as exc_info:
                client.move_story(
                    task_id=42,
                    column_id=999,  # Invalid column
                    project_id=1,
                    validate=True
                )

            assert "Column 999 not found" in str(exc_info.value)

    def test_move_story_with_position(self):
        """KC-03c: move_story() supports position within column."""
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

            result = client.move_story(
                task_id=42,
                column_id=5,
                position=1  # Top of column
            )

            assert result is True
            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json', {})
            assert payload['params']['position'] == 1

    def test_move_story_returns_false_on_failure(self):
        """KC-03d: move_story() returns False when move fails."""
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

            result = client.move_story(task_id=42, column_id=5)

            assert result is False

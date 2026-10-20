"""
Test KC-04: list_stories() returns stories filtered by column/project/assignee.

TDD Phase: RED -> GREEN
"""
import pytest
from unittest.mock import patch, MagicMock


class TestListStories:
    """Tests for story listing functionality."""

    def test_list_stories_by_project(self):
        """KC-04a: list_stories() returns all stories in a project."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": [
                    {"id": 1, "title": "Story 1", "column_id": 1},
                    {"id": 2, "title": "Story 2", "column_id": 2},
                    {"id": 3, "title": "Story 3", "column_id": 1}
                ]
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            stories = client.list_stories(project_id=1)

            assert len(stories) == 3
            assert stories[0]["title"] == "Story 1"

    def test_list_stories_by_column(self):
        """KC-04b: list_stories() filters by column_id."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": [
                    {"id": 1, "title": "Story 1", "column_id": 1},
                    {"id": 3, "title": "Story 3", "column_id": 1}
                ]
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            stories = client.list_stories(project_id=1, column_id=1)

            assert len(stories) == 2
            for story in stories:
                assert story["column_id"] == 1

    def test_list_stories_by_assignee(self):
        """KC-04c: list_stories() filters by owner_id (assignee)."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": [
                    {"id": 5, "title": "My Story", "owner_id": 10}
                ]
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            stories = client.list_stories(project_id=1, owner_id=10)

            assert len(stories) == 1
            assert stories[0]["owner_id"] == 10

    def test_list_stories_empty_result(self):
        """KC-04d: list_stories() returns empty list when no matches."""
        from kanboard_client.client import KanboardClient

        with patch('httpx.Client.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": []
            }
            mock_post.return_value = mock_response

            client = KanboardClient(
                url="http://kanboard.local/jsonrpc.php",
                username="admin",
                api_token="test-token"
            )

            stories = client.list_stories(project_id=999)

            assert stories == []

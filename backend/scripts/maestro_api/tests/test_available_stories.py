"""
Test MA-03: GET /stories/available returns only unblocked, unclaimed stories.
"""
import pytest
from fastapi.testclient import TestClient


class TestAvailableStories:
    """Tests for available stories endpoint."""

    def test_returns_unblocked_stories(self):
        """MA-03a: Returns stories that are not blocked."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Add test stories
        maestro.add_story(1, {"title": "Story 1", "blocked": False, "claimed": False})
        maestro.add_story(2, {"title": "Story 2", "blocked": True, "claimed": False})

        response = client.get("/stories/available")
        assert response.status_code == 200

        stories = response.json()
        story_ids = [s["id"] for s in stories]
        assert 1 in story_ids
        assert 2 not in story_ids  # Blocked

    def test_excludes_claimed_stories(self):
        """MA-03b: Does not return already claimed stories."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        maestro.add_story(3, {"title": "Story 3", "blocked": False, "claimed": False})
        maestro.add_story(4, {"title": "Story 4", "blocked": False, "claimed": True})

        response = client.get("/stories/available")
        stories = response.json()
        story_ids = [s["id"] for s in stories]

        assert 3 in story_ids
        assert 4 not in story_ids  # Already claimed

    def test_empty_when_none_available(self):
        """MA-03c: Returns empty list when no stories available."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()
        maestro.clear_stories()

        response = client.get("/stories/available")
        assert response.status_code == 200
        assert response.json() == []

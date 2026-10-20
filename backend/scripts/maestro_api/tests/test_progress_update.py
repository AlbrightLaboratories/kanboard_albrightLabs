"""
Test MA-06: POST /stories/{id}/progress updates progress %, broadcasts via WebSocket.
"""
import pytest
from fastapi.testclient import TestClient


class TestProgressUpdate:
    """Tests for progress update endpoint."""

    def test_updates_progress_percentage(self):
        """MA-06a: Progress update stores percentage."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Setup
        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]
        maestro.add_story(30, {"title": "Progress test", "blocked": False, "claimed": False})
        client.post("/stories/30/claim", json={"agent_id": agent_id})

        # Update progress
        response = client.post("/stories/30/progress", json={
            "agent_id": agent_id,
            "progress": 50,
            "message": "Halfway done"
        })

        assert response.status_code == 200

        story = maestro.get_story(30)
        assert story["progress"] == 50

    def test_progress_includes_message(self):
        """MA-06b: Progress update stores message."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]
        maestro.add_story(31, {"title": "Message test", "blocked": False, "claimed": False})
        client.post("/stories/31/claim", json={"agent_id": agent_id})

        client.post("/stories/31/progress", json={
            "agent_id": agent_id,
            "progress": 75,
            "message": "Running tests"
        })

        story = maestro.get_story(31)
        assert story["progress_message"] == "Running tests"

    def test_only_assigned_agent_can_update(self):
        """MA-06c: Only assigned agent can update progress."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg1 = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        reg2 = client.post("/agents/register", json={"agent_type": "gemini", "capabilities": []})
        agent1 = reg1.json()["agent_id"]
        agent2 = reg2.json()["agent_id"]

        maestro.add_story(32, {"title": "Owner test", "blocked": False, "claimed": False})
        client.post("/stories/32/claim", json={"agent_id": agent1})

        # Wrong agent tries to update
        response = client.post("/stories/32/progress", json={
            "agent_id": agent2,
            "progress": 50
        })

        assert response.status_code == 403  # Forbidden

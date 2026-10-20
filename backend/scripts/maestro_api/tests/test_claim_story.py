"""
Test MA-04: POST /stories/{id}/claim assigns story to agent, prevents double-claim.
"""
import pytest
from fastapi.testclient import TestClient


class TestClaimStory:
    """Tests for story claiming endpoint."""

    def test_claim_assigns_story_to_agent(self):
        """MA-04a: Claiming assigns story to the agent."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Register agent
        reg = client.post("/agents/register", json={
            "agent_type": "claude",
            "capabilities": []
        })
        agent_id = reg.json()["agent_id"]

        # Add story
        maestro.add_story(10, {"title": "Claimable", "blocked": False, "claimed": False})

        # Claim it
        response = client.post(f"/stories/10/claim", json={"agent_id": agent_id})
        assert response.status_code == 200
        assert response.json()["claimed"] is True

        # Verify assignment
        story = maestro.get_story(10)
        assert story["assigned_agent"] == agent_id

    def test_prevents_double_claim(self):
        """MA-04b: Cannot claim already claimed story."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Register two agents
        reg1 = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        reg2 = client.post("/agents/register", json={"agent_type": "gemini", "capabilities": []})
        agent1 = reg1.json()["agent_id"]
        agent2 = reg2.json()["agent_id"]

        # Add story
        maestro.add_story(11, {"title": "Single claim", "blocked": False, "claimed": False})

        # First claim succeeds
        resp1 = client.post("/stories/11/claim", json={"agent_id": agent1})
        assert resp1.status_code == 200

        # Second claim fails
        resp2 = client.post("/stories/11/claim", json={"agent_id": agent2})
        assert resp2.status_code == 409  # Conflict

    def test_cannot_claim_blocked_story(self):
        """MA-04c: Cannot claim a blocked story."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        maestro.add_story(12, {"title": "Blocked", "blocked": True, "claimed": False})

        response = client.post("/stories/12/claim", json={"agent_id": agent_id})
        assert response.status_code == 400  # Bad request - blocked

    def test_claim_updates_agent_status(self):
        """MA-04d: Claiming story updates agent status to 'working'."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        maestro.add_story(13, {"title": "Work", "blocked": False, "claimed": False})

        client.post("/stories/13/claim", json={"agent_id": agent_id})

        details = client.get(f"/agents/{agent_id}")
        assert details.json()["status"] == "working"

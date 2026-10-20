"""
Test MA-08: Agent timeout: agents with no heartbeat >5min marked stale.
"""
import pytest
from fastapi.testclient import TestClient
import time


class TestAgentTimeout:
    """Tests for agent timeout/staleness detection."""

    def test_agent_marked_stale_after_timeout(self):
        """MA-08a: Agent without heartbeat is marked stale."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Register agent
        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        # Simulate timeout (set last_seen in past)
        maestro.set_agent_last_seen(agent_id, time.time() - 301)  # 5min + 1sec ago

        # Check staleness
        maestro.check_stale_agents(timeout_seconds=300)

        details = client.get(f"/agents/{agent_id}")
        assert details.json()["status"] == "stale"

    def test_active_agent_not_marked_stale(self):
        """MA-08b: Agent with recent heartbeat stays active."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        # Send heartbeat
        client.get(f"/agents/{agent_id}/heartbeat")

        # Check staleness
        maestro.check_stale_agents(timeout_seconds=300)

        details = client.get(f"/agents/{agent_id}")
        assert details.json()["status"] != "stale"

    def test_stale_agent_releases_claimed_stories(self):
        """MA-08c: Stale agent's claimed stories become available."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        maestro.add_story(40, {"title": "Stale test", "blocked": False, "claimed": False})
        client.post("/stories/40/claim", json={"agent_id": agent_id})

        # Verify claimed
        assert maestro.get_story(40)["claimed"] is True

        # Timeout the agent
        maestro.set_agent_last_seen(agent_id, time.time() - 301)
        maestro.check_stale_agents(timeout_seconds=300)

        # Story should be released
        assert maestro.get_story(40)["claimed"] is False

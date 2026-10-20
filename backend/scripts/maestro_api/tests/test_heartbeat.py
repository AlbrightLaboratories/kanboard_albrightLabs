"""
Test MA-02: GET /agents/{id}/heartbeat updates last_seen, returns agent status.
"""
import pytest
from fastapi.testclient import TestClient
import time


class TestHeartbeat:
    """Tests for agent heartbeat endpoint."""

    def test_heartbeat_updates_last_seen(self):
        """MA-02a: Heartbeat updates last_seen timestamp."""
        from maestro_api.server import app

        client = TestClient(app)

        # Register agent
        reg = client.post("/agents/register", json={
            "agent_type": "claude",
            "capabilities": []
        })
        agent_id = reg.json()["agent_id"]

        # Get initial last_seen
        details1 = client.get(f"/agents/{agent_id}")
        last_seen1 = details1.json()["last_seen"]

        # Small delay
        time.sleep(0.01)

        # Send heartbeat
        response = client.get(f"/agents/{agent_id}/heartbeat")
        assert response.status_code == 200

        # Check last_seen updated
        details2 = client.get(f"/agents/{agent_id}")
        last_seen2 = details2.json()["last_seen"]
        assert last_seen2 >= last_seen1

    def test_heartbeat_returns_status(self):
        """MA-02b: Heartbeat returns current agent status."""
        from maestro_api.server import app

        client = TestClient(app)

        reg = client.post("/agents/register", json={
            "agent_type": "claude",
            "capabilities": []
        })
        agent_id = reg.json()["agent_id"]

        response = client.get(f"/agents/{agent_id}/heartbeat")
        data = response.json()

        assert "status" in data
        assert data["status"] == "idle"

    def test_heartbeat_unknown_agent_404(self):
        """MA-02c: Heartbeat for unknown agent returns 404."""
        from maestro_api.server import app

        client = TestClient(app)

        response = client.get("/agents/nonexistent-id/heartbeat")
        assert response.status_code == 404

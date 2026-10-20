"""
Test MA-09: Rate limiting: >100 req/min per agent returns 429.
"""
import pytest
from fastapi.testclient import TestClient


class TestRateLimit:
    """Tests for rate limiting."""

    def test_rate_limit_exceeded_returns_429(self):
        """MA-09a: Exceeding rate limit returns 429 Too Many Requests."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Register agent
        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        # Simulate exceeding rate limit
        maestro.set_request_count(agent_id, 101)

        # Next request should fail
        response = client.get(f"/agents/{agent_id}/heartbeat")
        assert response.status_code == 429

    def test_under_limit_succeeds(self):
        """MA-09b: Requests under rate limit succeed."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        # Under limit
        maestro.set_request_count(agent_id, 50)

        response = client.get(f"/agents/{agent_id}/heartbeat")
        assert response.status_code == 200

    def test_rate_limit_resets_after_window(self):
        """MA-09c: Rate limit resets after time window."""
        from maestro_api.server import app, get_maestro
        import time

        client = TestClient(app)
        maestro = get_maestro()

        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        # Set high count but old window
        maestro.set_request_count(agent_id, 101, window_start=time.time() - 61)

        # Should reset and succeed
        response = client.get(f"/agents/{agent_id}/heartbeat")
        assert response.status_code == 200

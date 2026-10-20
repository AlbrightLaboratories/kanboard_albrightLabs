"""
Test MA-01: POST /agents/register registers agent, returns agent_id.
"""
import pytest
from fastapi.testclient import TestClient


class TestAgentRegister:
    """Tests for agent registration endpoint."""

    def test_register_agent_returns_agent_id(self):
        """MA-01a: POST /agents/register returns new agent_id."""
        from maestro_api.server import app

        client = TestClient(app)

        response = client.post("/agents/register", json={
            "agent_type": "claude",
            "capabilities": ["code_generation", "test_execution"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert data["agent_id"] is not None

    def test_register_agent_stores_agent_type(self):
        """MA-01b: Registered agent stores type correctly."""
        from maestro_api.server import app

        client = TestClient(app)

        response = client.post("/agents/register", json={
            "agent_type": "gemini",
            "capabilities": ["code_review"]
        })

        assert response.status_code == 200
        agent_id = response.json()["agent_id"]

        # Get agent details
        details = client.get(f"/agents/{agent_id}")
        assert details.status_code == 200
        assert details.json()["agent_type"] == "gemini"

    def test_register_agent_with_name(self):
        """MA-01c: Agent can register with custom name."""
        from maestro_api.server import app

        client = TestClient(app)

        response = client.post("/agents/register", json={
            "agent_type": "custom",
            "name": "my-local-llm",
            "capabilities": ["code_generation"]
        })

        assert response.status_code == 200
        agent_id = response.json()["agent_id"]

        details = client.get(f"/agents/{agent_id}")
        assert details.json()["name"] == "my-local-llm"

    def test_register_agent_sets_status_idle(self):
        """MA-01d: New agent status is 'idle'."""
        from maestro_api.server import app

        client = TestClient(app)

        response = client.post("/agents/register", json={
            "agent_type": "claude",
            "capabilities": []
        })

        agent_id = response.json()["agent_id"]
        details = client.get(f"/agents/{agent_id}")
        assert details.json()["status"] == "idle"

"""
Test MA-07: WebSocket /stream delivers real-time messages to connected agents.
"""
import pytest
from fastapi.testclient import TestClient


def drain_pending_messages(maestro) -> None:
    """Drain any pending messages from the queue."""
    while maestro.pop_message() is not None:
        pass


class TestWebSocketStream:
    """Tests for WebSocket message streaming."""

    def test_websocket_connects(self):
        """MA-07a: WebSocket connection establishes successfully."""
        from maestro_api.server import app

        client = TestClient(app)

        with client.websocket_connect("/stream") as ws:
            # Connection established
            assert ws is not None

    def test_websocket_receives_messages(self):
        """MA-07b: Connected client receives broadcast messages."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Clear any stale messages from previous tests
        drain_pending_messages(maestro)

        with client.websocket_connect("/stream") as ws:
            # Trigger a broadcast
            maestro.broadcast({"type": "test", "data": "hello"})

            # Receive message
            data = ws.receive_json()
            assert data["type"] == "test"
            assert data["data"] == "hello"

    def test_websocket_agent_specific_messages(self):
        """MA-07c: Agent can subscribe to specific message types."""
        from maestro_api.server import app, get_maestro

        client = TestClient(app)
        maestro = get_maestro()

        # Clear any stale messages from previous tests
        drain_pending_messages(maestro)

        # Register agent
        reg = client.post("/agents/register", json={"agent_type": "claude", "capabilities": []})
        agent_id = reg.json()["agent_id"]

        with client.websocket_connect(f"/stream?agent_id={agent_id}") as ws:
            # Send agent-specific message
            maestro.send_to_agent(agent_id, {"type": "task", "story_id": 1})

            data = ws.receive_json()
            assert data["type"] == "task"
            assert data["story_id"] == 1

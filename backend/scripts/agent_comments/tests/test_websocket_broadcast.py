"""
Test AIC-08: WebSocket broadcasts agent responses in real-time
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from ..websocket_broadcaster import (
    WebSocketHub,
    WebSocketMessage,
    MessageType,
    broadcast_agent_response,
    broadcast_execution_status,
    broadcast_comment_added,
    get_hub,
)


@pytest.fixture
def hub():
    """Fresh WebSocket hub for tests."""
    return WebSocketHub()


@pytest.fixture
def mock_connection():
    """Mock WebSocket connection."""
    conn = AsyncMock()
    conn.send = AsyncMock()
    return conn


class TestWebSocketHub:
    """Tests for WebSocketHub class."""

    @pytest.mark.asyncio
    async def test_subscribe_to_story(self, hub, mock_connection):
        """Connection can subscribe to specific story."""
        await hub.subscribe(mock_connection, story_id="123")

        assert mock_connection in hub._story_connections.get("123", set())
        assert "123" in hub._connection_stories.get(mock_connection, set())

    @pytest.mark.asyncio
    async def test_subscribe_global(self, hub, mock_connection):
        """Connection can subscribe globally."""
        await hub.subscribe(mock_connection, story_id=None)

        assert mock_connection in hub._global_connections

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_from_all(self, hub, mock_connection):
        """Unsubscribe removes connection from all stories."""
        await hub.subscribe(mock_connection, story_id="123")
        await hub.subscribe(mock_connection, story_id="456")
        await hub.unsubscribe(mock_connection)

        assert mock_connection not in hub._story_connections.get("123", set())
        assert mock_connection not in hub._story_connections.get("456", set())
        assert mock_connection not in hub._connection_stories

    @pytest.mark.asyncio
    async def test_broadcast_to_story_subscribers(self, hub, mock_connection):
        """Broadcast reaches story subscribers."""
        await hub.subscribe(mock_connection, story_id="123")

        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            story_id="123",
            payload={"test": "data"},
        )

        count = await hub.broadcast(message)

        assert count == 1
        mock_connection.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_global_subscribers(self, hub, mock_connection):
        """Broadcast reaches global subscribers."""
        await hub.subscribe(mock_connection, story_id=None)

        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            story_id="123",
            payload={"test": "data"},
        )

        count = await hub.broadcast(message)

        assert count == 1
        mock_connection.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_skips_unsubscribed(self, hub, mock_connection):
        """Broadcast doesn't reach connections for other stories."""
        await hub.subscribe(mock_connection, story_id="456")  # Different story

        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            story_id="123",  # Different story
            payload={"test": "data"},
        )

        count = await hub.broadcast(message)

        assert count == 0
        mock_connection.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_handles_closed_connection(self, hub):
        """Broadcast handles closed connections gracefully."""
        bad_conn = AsyncMock()
        bad_conn.send = AsyncMock(side_effect=Exception("Connection closed"))

        await hub.subscribe(bad_conn, story_id="123")

        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            story_id="123",
            payload={},
        )

        # Should not raise
        count = await hub.broadcast(message)
        assert count == 0


class TestWebSocketMessage:
    """Tests for WebSocketMessage class."""

    def test_to_json(self):
        """Message serializes to JSON."""
        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            story_id="123",
            payload={"agent_id": "claude-001"},
        )

        json_str = message.to_json()

        assert "agent_response" in json_str
        assert "123" in json_str
        assert "claude-001" in json_str

    def test_auto_timestamp(self):
        """Timestamp is set automatically."""
        message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            story_id="123",
            payload={},
        )

        assert message.timestamp != ""
        assert "T" in message.timestamp  # ISO format


class TestBroadcastHelpers:
    """Tests for broadcast helper functions."""

    @pytest.mark.asyncio
    async def test_broadcast_agent_response(self):
        """broadcast_agent_response sends correct message."""
        # Reset singleton and use fresh hub
        import backend.scripts.agent_comments.websocket_broadcaster as ws_mod
        original_hub = ws_mod._hub
        ws_mod._hub = None

        hub = get_hub()
        mock_conn = AsyncMock()
        await hub.subscribe(mock_conn, story_id="123")

        count = await broadcast_agent_response(
            story_id="123",
            agent_id="claude-001",
            agent_name="Claude",
            comment_id="c1",
            content="Here is my response...",
            has_execution_request=True,
        )

        assert count >= 1
        mock_conn.send.assert_called()
        ws_mod._hub = original_hub

    @pytest.mark.asyncio
    async def test_broadcast_execution_status(self):
        """broadcast_execution_status sends correct message."""
        import backend.scripts.agent_comments.websocket_broadcaster as ws_mod
        original_hub = ws_mod._hub
        ws_mod._hub = None

        hub = get_hub()
        mock_conn = AsyncMock()
        await hub.subscribe(mock_conn, story_id="123")

        count = await broadcast_execution_status(
            story_id="123",
            execution_id="exec-123",
            status="passed",
            details={"exit_code": 0},
        )

        assert count >= 1
        mock_conn.send.assert_called()
        ws_mod._hub = original_hub

    @pytest.mark.asyncio
    async def test_broadcast_comment_added(self):
        """broadcast_comment_added sends correct message."""
        import backend.scripts.agent_comments.websocket_broadcaster as ws_mod
        original_hub = ws_mod._hub
        ws_mod._hub = None

        hub = get_hub()
        mock_conn = AsyncMock()
        await hub.subscribe(mock_conn, story_id="123")

        count = await broadcast_comment_added(
            story_id="123",
            comment_id="c1",
            author="user1",
            is_agent=False,
        )

        assert count >= 1
        mock_conn.send.assert_called()
        ws_mod._hub = original_hub

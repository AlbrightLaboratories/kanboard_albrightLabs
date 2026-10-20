"""
WebSocket Broadcaster - Broadcasts agent responses in real-time

Implements AIC-08: WebSocket broadcasts agent responses in real-time
"""

from dataclasses import dataclass
from typing import Dict, Any, Set, Optional
from datetime import datetime, timezone
import json
import asyncio


@dataclass
class WebSocketMessage:
    """Message to broadcast via WebSocket."""
    type: str
    story_id: str
    payload: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "type": self.type,
            "story_id": self.story_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })


# Message types
class MessageType:
    AGENT_RESPONSE = "agent_response"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_APPROVED = "execution_approved"
    EXECUTION_REJECTED = "execution_rejected"
    COMMENT_ADDED = "comment_added"


class WebSocketHub:
    """
    Hub for managing WebSocket connections and broadcasting.

    Tracks connections per story for targeted broadcasting.
    """

    def __init__(self):
        # Map of story_id -> set of connections
        self._story_connections: Dict[str, Set[Any]] = {}
        # Map of connection -> subscribed stories
        self._connection_stories: Dict[Any, Set[str]] = {}
        # Global connections (receive all messages)
        self._global_connections: Set[Any] = set()

    async def subscribe(
        self,
        connection: Any,
        story_id: Optional[str] = None,
    ) -> None:
        """
        Subscribe a connection to story updates.

        Args:
            connection: WebSocket connection
            story_id: Specific story to subscribe to, or None for global
        """
        if story_id:
            if story_id not in self._story_connections:
                self._story_connections[story_id] = set()
            self._story_connections[story_id].add(connection)

            if connection not in self._connection_stories:
                self._connection_stories[connection] = set()
            self._connection_stories[connection].add(story_id)
        else:
            self._global_connections.add(connection)

    async def unsubscribe(self, connection: Any) -> None:
        """
        Unsubscribe a connection from all stories.

        Args:
            connection: WebSocket connection to remove
        """
        # Remove from global
        self._global_connections.discard(connection)

        # Remove from story subscriptions
        if connection in self._connection_stories:
            for story_id in self._connection_stories[connection]:
                if story_id in self._story_connections:
                    self._story_connections[story_id].discard(connection)
            del self._connection_stories[connection]

    async def broadcast(self, message: WebSocketMessage) -> int:
        """
        Broadcast message to relevant connections.

        Args:
            message: Message to broadcast

        Returns:
            Number of connections reached
        """
        connections_reached = 0
        json_message = message.to_json()

        # Get connections for this story
        story_connections = self._story_connections.get(message.story_id, set())

        # Combine with global connections
        all_connections = story_connections | self._global_connections

        # Send to all
        for connection in all_connections:
            try:
                await connection.send(json_message)
                connections_reached += 1
            except Exception:
                # Connection closed, will be cleaned up
                pass

        return connections_reached


# Singleton hub instance
_hub: Optional[WebSocketHub] = None


def get_hub() -> WebSocketHub:
    """Get the singleton WebSocket hub."""
    global _hub
    if _hub is None:
        _hub = WebSocketHub()
    return _hub


async def broadcast_agent_response(
    story_id: str,
    agent_id: str,
    agent_name: str,
    comment_id: str,
    content: str,
    has_execution_request: bool = False,
) -> int:
    """
    Broadcast an agent response via WebSocket.

    Args:
        story_id: Story the response is for
        agent_id: ID of responding agent
        agent_name: Name of responding agent
        comment_id: ID of the new comment
        content: Response content (truncated for broadcast)
        has_execution_request: Whether response has execution request

    Returns:
        Number of connections reached
    """
    hub = get_hub()

    message = WebSocketMessage(
        type=MessageType.AGENT_RESPONSE,
        story_id=story_id,
        payload={
            "agent_id": agent_id,
            "agent_name": agent_name,
            "comment_id": comment_id,
            "content_preview": content[:200],  # Preview only
            "has_execution_request": has_execution_request,
        },
    )

    return await hub.broadcast(message)


async def broadcast_execution_status(
    story_id: str,
    execution_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Broadcast execution status update.

    Args:
        story_id: Story ID
        execution_id: Execution request ID
        status: New status
        details: Additional details

    Returns:
        Number of connections reached
    """
    hub = get_hub()

    message_type = {
        "running": MessageType.EXECUTION_STARTED,
        "passed": MessageType.EXECUTION_COMPLETED,
        "failed": MessageType.EXECUTION_COMPLETED,
        "approved": MessageType.EXECUTION_APPROVED,
        "rejected": MessageType.EXECUTION_REJECTED,
    }.get(status, MessageType.EXECUTION_COMPLETED)

    message = WebSocketMessage(
        type=message_type,
        story_id=story_id,
        payload={
            "execution_id": execution_id,
            "status": status,
            **(details or {}),
        },
    )

    return await hub.broadcast(message)


async def broadcast_comment_added(
    story_id: str,
    comment_id: str,
    author: str,
    is_agent: bool = False,
) -> int:
    """
    Broadcast that a new comment was added.

    Args:
        story_id: Story ID
        comment_id: New comment ID
        author: Comment author
        is_agent: Whether from an agent

    Returns:
        Number of connections reached
    """
    hub = get_hub()

    message = WebSocketMessage(
        type=MessageType.COMMENT_ADDED,
        story_id=story_id,
        payload={
            "comment_id": comment_id,
            "author": author,
            "is_agent": is_agent,
        },
    )

    return await hub.broadcast(message)

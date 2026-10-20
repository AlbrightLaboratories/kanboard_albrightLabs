"""
Agent Registry

Manages AI agent registration, heartbeats, and status tracking.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional


class AgentRegistry:
    """Registry for AI agents."""

    def __init__(self):
        """Initialize empty registry."""
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._request_counts: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        agent_type: str,
        capabilities: List[str],
        name: Optional[str] = None
    ) -> str:
        """
        Register a new agent.

        Returns:
            New agent ID
        """
        agent_id = str(uuid.uuid4())
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "name": name or f"{agent_type}-{agent_id[:8]}",
            "capabilities": capabilities,
            "status": "idle",
            "last_seen": time.time(),
            "current_story": None
        }
        self._request_counts[agent_id] = {
            "count": 0,
            "window_start": time.time()
        }
        return agent_id

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def exists(self, agent_id: str) -> bool:
        """Check if agent exists."""
        return agent_id in self._agents

    def heartbeat(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Update agent heartbeat.

        Returns:
            Agent status info or None if not found
        """
        if agent_id not in self._agents:
            return None

        self._agents[agent_id]["last_seen"] = time.time()
        return {
            "status": self._agents[agent_id]["status"],
            "current_story": self._agents[agent_id]["current_story"]
        }

    def set_status(self, agent_id: str, status: str) -> None:
        """Set agent status."""
        if agent_id in self._agents:
            self._agents[agent_id]["status"] = status

    def set_current_story(self, agent_id: str, story_id: Optional[int]) -> None:
        """Set agent's current story."""
        if agent_id in self._agents:
            self._agents[agent_id]["current_story"] = story_id

    def set_last_seen(self, agent_id: str, timestamp: float) -> None:
        """Set last_seen timestamp (for testing)."""
        if agent_id in self._agents:
            self._agents[agent_id]["last_seen"] = timestamp

    def check_stale(self, timeout_seconds: int = 300) -> List[str]:
        """
        Check for stale agents and mark them.

        Returns:
            List of agent IDs that became stale
        """
        now = time.time()
        stale = []

        for agent_id, agent in self._agents.items():
            if agent["status"] != "stale":
                if now - agent["last_seen"] > timeout_seconds:
                    agent["status"] = "stale"
                    stale.append(agent_id)

        return stale

    def get_request_count(self, agent_id: str) -> int:
        """Get current request count for agent."""
        if agent_id not in self._request_counts:
            return 0
        return self._request_counts[agent_id]["count"]

    def increment_request_count(self, agent_id: str) -> int:
        """Increment and return request count."""
        if agent_id not in self._request_counts:
            self._request_counts[agent_id] = {
                "count": 0,
                "window_start": time.time()
            }

        # Check if window needs reset (1 minute)
        if time.time() - self._request_counts[agent_id]["window_start"] > 60:
            self._request_counts[agent_id] = {
                "count": 0,
                "window_start": time.time()
            }

        self._request_counts[agent_id]["count"] += 1
        return self._request_counts[agent_id]["count"]

    def set_request_count(
        self,
        agent_id: str,
        count: int,
        window_start: Optional[float] = None
    ) -> None:
        """Set request count (for testing)."""
        self._request_counts[agent_id] = {
            "count": count,
            "window_start": window_start or time.time()
        }

    def is_rate_limited(self, agent_id: str, limit: int = 100) -> bool:
        """Check if agent is rate limited."""
        if agent_id not in self._request_counts:
            return False

        rc = self._request_counts[agent_id]

        # Reset if window expired
        if time.time() - rc["window_start"] > 60:
            self._request_counts[agent_id] = {
                "count": 0,
                "window_start": time.time()
            }
            return False

        return rc["count"] > limit

"""
Story Claims

Manages story claiming, availability, and progress tracking.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class StoryClaims:
    """Manages story claims and availability."""

    def __init__(self):
        """Initialize empty store."""
        self._stories: Dict[int, Dict[str, Any]] = {}

    def add_story(self, story_id: int, data: Dict[str, Any]) -> None:
        """Add or update a story."""
        self._stories[story_id] = {
            "id": story_id,
            **data,
            "progress": data.get("progress", 0),
            "progress_message": data.get("progress_message", ""),
            "assigned_agent": data.get("assigned_agent"),
        }

    def get_story(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get story by ID."""
        return self._stories.get(story_id)

    def clear_stories(self) -> None:
        """Clear all stories."""
        self._stories.clear()

    def get_available(self) -> List[Dict[str, Any]]:
        """Get all available (unblocked, unclaimed) stories."""
        return [
            story for story in self._stories.values()
            if not story.get("blocked", False) and not story.get("claimed", False)
        ]

    def claim(self, story_id: int, agent_id: str) -> bool:
        """
        Claim a story for an agent.

        Returns:
            True if claim succeeded, False otherwise
        """
        story = self._stories.get(story_id)
        if not story:
            return False

        if story.get("blocked", False):
            return False

        if story.get("claimed", False):
            return False

        story["claimed"] = True
        story["assigned_agent"] = agent_id
        return True

    def release(self, story_id: int) -> None:
        """Release a claimed story."""
        story = self._stories.get(story_id)
        if story:
            story["claimed"] = False
            story["assigned_agent"] = None

    def update_progress(
        self,
        story_id: int,
        progress: int,
        message: str = ""
    ) -> bool:
        """
        Update story progress.

        Returns:
            True if updated, False if story not found
        """
        story = self._stories.get(story_id)
        if not story:
            return False

        story["progress"] = progress
        story["progress_message"] = message
        return True

    def get_agent_stories(self, agent_id: str) -> List[int]:
        """Get all story IDs claimed by an agent."""
        return [
            story["id"] for story in self._stories.values()
            if story.get("assigned_agent") == agent_id
        ]

    def release_agent_stories(self, agent_id: str) -> List[int]:
        """Release all stories claimed by an agent."""
        released = []
        for story_id in self.get_agent_stories(agent_id):
            self.release(story_id)
            released.append(story_id)
        return released

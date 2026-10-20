"""
Base Skill

Abstract base class for all mandatory skills.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillResult:
    """Result of a skill execution."""
    skill_name: str
    status: str  # "passed", "failed", "pending"
    output: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
    executed_at: Optional[float] = None
    agent_id: Optional[str] = None
    story_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "skill_name": self.skill_name,
            "status": self.status,
            "output": self.output,
            "failure_reason": self.failure_reason,
            "executed_at": self.executed_at,
            "agent_id": self.agent_id,
            "story_id": self.story_id
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillResult":
        """Create from dictionary."""
        return cls(
            skill_name=data["skill_name"],
            status=data["status"],
            output=data.get("output", {}),
            failure_reason=data.get("failure_reason"),
            executed_at=data.get("executed_at"),
            agent_id=data.get("agent_id"),
            story_id=data.get("story_id")
        )


class BaseSkill(ABC):
    """Abstract base class for mandatory skills."""

    # Skill name used for identification
    name: str = "base"

    def __init__(self):
        """Initialize skill."""
        self._results: Dict[int, SkillResult] = {}  # story_id -> result

    @abstractmethod
    def execute(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Execute the skill for a story.

        Args:
            story_id: Story being processed
            story_data: Story details (title, description, etc.)
            agent_id: Agent executing the skill
            **kwargs: Additional skill-specific parameters

        Returns:
            SkillResult with status and output
        """
        pass

    def get_result(self, story_id: int) -> Optional[SkillResult]:
        """Get the result for a story."""
        return self._results.get(story_id)

    def is_complete(self, story_id: int) -> bool:
        """Check if skill completed for story."""
        result = self._results.get(story_id)
        return result is not None and result.status == "passed"

    def clear_result(self, story_id: int) -> None:
        """Clear result for a story (for retry)."""
        if story_id in self._results:
            del self._results[story_id]

    def _create_result(
        self,
        story_id: int,
        status: str,
        output: Dict[str, Any] = None,
        failure_reason: str = None,
        agent_id: str = None
    ) -> SkillResult:
        """Create and store a skill result."""
        result = SkillResult(
            skill_name=self.name,
            status=status,
            output=output or {},
            failure_reason=failure_reason,
            executed_at=time.time(),
            agent_id=agent_id,
            story_id=story_id
        )
        self._results[story_id] = result
        return result

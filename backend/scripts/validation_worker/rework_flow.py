"""
Rework Flow

Handles failed validations by moving stories back for rework.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .result_handler import ValidationResult


@dataclass
class ReworkAction:
    """Action taken for a rework."""

    story_id: int
    status: str  # pending, completed, failed
    from_column: str = "Validation"
    to_column: str = "In Progress"
    comment_added: bool = False
    failure_reasons: List[str] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.failure_reasons is None:
            self.failure_reasons = []


class ReworkFlow:
    """Manages the rework flow for failed validations."""

    def __init__(self, kanboard_client: Optional[Any] = None) -> None:
        """
        Initialize rework flow handler.

        Args:
            kanboard_client: Optional Kanboard API client
        """
        self.kanboard_client = kanboard_client
        self._rework_history: Dict[int, List[ReworkAction]] = {}

    def handle_failed_validation(
        self,
        story_id: int,
        result: ValidationResult
    ) -> ReworkAction:
        """
        Handle a failed validation by moving story back to In Progress.

        Args:
            story_id: Story ID
            result: Failed validation result

        Returns:
            ReworkAction with action taken
        """
        action = ReworkAction(
            story_id=story_id,
            status="pending",
            failure_reasons=result.failure_reasons
        )

        # Move story back to In Progress
        if self.kanboard_client:
            try:
                self.kanboard_client.move_story(
                    story_id=story_id,
                    column="In Progress"
                )
                action.status = "completed"
            except Exception as e:
                action.status = "failed"
                action.error = str(e)

        # Add failure comment to story
        comment_result = self.add_failure_comment(story_id, result)
        action.comment_added = comment_result

        # Record in history
        if story_id not in self._rework_history:
            self._rework_history[story_id] = []
        self._rework_history[story_id].append(action)

        return action

    def add_failure_comment(
        self,
        story_id: int,
        result: ValidationResult
    ) -> bool:
        """
        Add failure comment to story for agent to read.

        Args:
            story_id: Story ID
            result: Validation result with failure details

        Returns:
            True if comment added successfully
        """
        if not self.kanboard_client:
            return False

        # Build rework comment
        comment = self._build_rework_comment(result)

        try:
            self.kanboard_client.add_comment(
                story_id=story_id,
                content=comment
            )
            return True
        except Exception:
            return False

    def _build_rework_comment(self, result: ValidationResult) -> str:
        """Build a detailed rework comment for agents."""
        comment = "## REWORK REQUIRED\n\n"
        comment += "Validation failed. Story moved back to In Progress.\n\n"

        comment += "### Failure Reasons\n\n"
        for i, reason in enumerate(result.failure_reasons, 1):
            comment += f"{i}. {reason}\n"

        if result.modularity_issues:
            comment += "\n### Modularity Issues\n\n"
            for issue in result.modularity_issues:
                comment += f"- {issue}\n"

        comment += "\n### Test Summary\n\n"
        comment += f"| Metric | Value |\n"
        comment += f"|--------|-------|\n"
        comment += f"| Tests Passed | {result.tests_passed} |\n"
        comment += f"| Tests Failed | {result.tests_failed} |\n"
        comment += f"| Coverage | {result.coverage_percentage:.1f}% |\n"

        if result.failure_log:
            comment += "\n### Failure Details\n\n"
            comment += "```\n"
            # Truncate long logs
            log = result.failure_log
            if len(log) > 3000:
                log = log[:3000] + "\n... (truncated)"
            comment += log
            comment += "\n```\n"

        comment += "\n### Next Steps\n\n"
        comment += "1. Review the failure reasons above\n"
        comment += "2. Fix the identified issues\n"
        comment += "3. Re-run TDD skill to verify fixes\n"
        comment += "4. Submit for validation again\n"

        if result.workflow_run_url:
            comment += f"\n[View Full Workflow Run]({result.workflow_run_url})\n"

        return comment

    def get_rework_count(self, story_id: int) -> int:
        """Get number of times a story has been reworked."""
        return len(self._rework_history.get(story_id, []))

    def get_rework_history(self, story_id: int) -> List[ReworkAction]:
        """Get full rework history for a story."""
        return self._rework_history.get(story_id, [])

    def get_latest_failure_reasons(
        self,
        story_id: int
    ) -> List[str]:
        """
        Get failure reasons from most recent rework.

        Args:
            story_id: Story ID

        Returns:
            List of failure reasons
        """
        history = self._rework_history.get(story_id, [])
        if history:
            return history[-1].failure_reasons
        return []

    def clear_history(self, story_id: Optional[int] = None) -> None:
        """
        Clear rework history.

        Args:
            story_id: Optional story ID (clears all if None)
        """
        if story_id:
            self._rework_history.pop(story_id, None)
        else:
            self._rework_history.clear()

    def is_story_being_reworked(self, story_id: int) -> bool:
        """
        Check if a story is currently being reworked.

        Args:
            story_id: Story ID

        Returns:
            True if story has rework history
        """
        return story_id in self._rework_history and len(self._rework_history[story_id]) > 0

    def should_escalate(
        self,
        story_id: int,
        max_reworks: int = 3
    ) -> bool:
        """
        Check if story should be escalated due to too many reworks.

        Args:
            story_id: Story ID
            max_reworks: Maximum allowed reworks before escalation

        Returns:
            True if rework count exceeds threshold
        """
        return self.get_rework_count(story_id) >= max_reworks

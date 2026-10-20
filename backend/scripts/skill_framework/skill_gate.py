"""
Skill Gate

Blocks column transitions if required skills are not complete.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .skill_runner import SkillRunner


class SkillGate:
    """Enforces skill completion before column transitions."""

    # Required skills to move from In Progress to Validation
    IN_PROGRESS_TO_VALIDATION = ["plan", "design-a-prd", "tdd"]

    # Required skills to move from Validation to Done
    VALIDATION_TO_DONE = ["prove-it", "release-it"]

    def __init__(self, skill_runner: SkillRunner) -> None:
        """
        Initialize skill gate.

        Args:
            skill_runner: SkillRunner instance for checking skill status
        """
        self._runner = skill_runner

    def can_transition(
        self,
        story_id: int,
        from_column: str,
        to_column: str
    ) -> Tuple[bool, List[str]]:
        """
        Check if a story can transition between columns.

        Args:
            story_id: Story ID
            from_column: Current column name
            to_column: Target column name

        Returns:
            Tuple of (can_transition, list of blocking skills)
        """
        # Normalize column names
        from_col = from_column.lower().replace(" ", "_").replace("-", "_")
        to_col = to_column.lower().replace(" ", "_").replace("-", "_")

        # Check In Progress -> Validation transition
        if from_col == "in_progress" and to_col == "validation":
            return self._check_skills_complete(
                story_id,
                self.IN_PROGRESS_TO_VALIDATION
            )

        # Check Validation -> Done transition
        if from_col == "validation" and to_col == "done":
            return self._check_skills_complete(
                story_id,
                self.VALIDATION_TO_DONE
            )

        # All other transitions are allowed
        return True, []

    def _check_skills_complete(
        self,
        story_id: int,
        required_skills: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if all required skills are complete.

        Args:
            story_id: Story ID
            required_skills: List of required skill names

        Returns:
            Tuple of (all_complete, list of incomplete skills)
        """
        incomplete = []

        for skill_name in required_skills:
            status = self._runner.get_skill_status(story_id, skill_name)
            if status != "passed":
                incomplete.append(skill_name)

        return len(incomplete) == 0, incomplete

    def get_required_skills(
        self,
        from_column: str,
        to_column: str
    ) -> List[str]:
        """
        Get the list of required skills for a transition.

        Args:
            from_column: Current column name
            to_column: Target column name

        Returns:
            List of required skill names (empty if no requirements)
        """
        from_col = from_column.lower().replace(" ", "_").replace("-", "_")
        to_col = to_column.lower().replace(" ", "_").replace("-", "_")

        if from_col == "in_progress" and to_col == "validation":
            return self.IN_PROGRESS_TO_VALIDATION.copy()

        if from_col == "validation" and to_col == "done":
            return self.VALIDATION_TO_DONE.copy()

        return []

    def get_skill_progress(
        self,
        story_id: int,
        phase: str
    ) -> Dict[str, Any]:
        """
        Get progress for all skills in a phase.

        Args:
            story_id: Story ID
            phase: "in_progress" or "validation"

        Returns:
            Dict with skill statuses and completion percentage
        """
        if phase == "in_progress":
            skills = self.IN_PROGRESS_TO_VALIDATION
        elif phase == "validation":
            skills = self.VALIDATION_TO_DONE
        else:
            return {"error": f"Unknown phase: {phase}"}

        statuses = {}
        completed = 0

        for skill_name in skills:
            status = self._runner.get_skill_status(story_id, skill_name)
            statuses[skill_name] = status or "pending"
            if status == "passed":
                completed += 1

        return {
            "skills": statuses,
            "completed": completed,
            "total": len(skills),
            "percentage": (completed / len(skills)) * 100 if skills else 0,
            "all_complete": completed == len(skills)
        }

    def block_transition(
        self,
        story_id: int,
        from_column: str,
        to_column: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check transition and return blocking info if blocked.

        Args:
            story_id: Story ID
            from_column: Current column
            to_column: Target column

        Returns:
            None if allowed, or dict with blocking details
        """
        can_move, incomplete = self.can_transition(story_id, from_column, to_column)

        if can_move:
            return None

        return {
            "blocked": True,
            "from_column": from_column,
            "to_column": to_column,
            "incomplete_skills": incomplete,
            "message": f"Cannot move to {to_column}. Complete these skills first: {', '.join(incomplete)}"
        }

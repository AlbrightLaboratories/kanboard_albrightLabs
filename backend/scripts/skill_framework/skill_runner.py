"""
Skill Runner

Executes skills in order with proper sequencing and output tracking.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Type

from .skills.base_skill import BaseSkill, SkillResult
from .skills.plan_skill import PlanSkill
from .skills.prd_skill import PRDSkill
from .skills.tdd_skill import TDDSkill
from .skills.prove_it_skill import ProveItSkill
from .skills.release_it_skill import ReleaseItSkill


class SkillRunner:
    """Executes mandatory skills in order."""

    # Skill execution order for In Progress phase
    IN_PROGRESS_SKILLS = ["plan", "design-a-prd", "tdd"]

    # Skill execution order for Validation phase
    VALIDATION_SKILLS = ["prove-it", "release-it"]

    def __init__(self) -> None:
        """Initialize skill runner with all available skills."""
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_outputs: Dict[int, Dict[str, SkillResult]] = {}

        # Register all skills
        self._register_skill(PlanSkill())
        self._register_skill(PRDSkill())
        self._register_skill(TDDSkill())
        self._register_skill(ProveItSkill())
        self._register_skill(ReleaseItSkill())

    def _register_skill(self, skill: BaseSkill) -> None:
        """Register a skill by its name."""
        self._skills[skill.name] = skill

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self._skills.get(skill_name)

    def list_skills(self) -> List[str]:
        """List all registered skill names."""
        return list(self._skills.keys())

    def execute(
        self,
        skill_name: str,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Execute a single skill.

        Args:
            skill_name: Name of the skill to execute
            story_id: Story ID
            story_data: Story data dict
            agent_id: Optional agent ID
            **kwargs: Additional arguments for the skill

        Returns:
            SkillResult with execution outcome
        """
        skill = self._skills.get(skill_name)
        if not skill:
            result = SkillResult(
                skill_name=skill_name,
                status="failed",
                failure_reason=f"Unknown skill: {skill_name}",
                story_id=story_id,
                executed_at=time.time(),
                agent_id=agent_id
            )
        else:
            result = skill.execute(story_id, story_data, agent_id, **kwargs)

        # Store output for retrieval (even for unknown skills)
        if story_id not in self._skill_outputs:
            self._skill_outputs[story_id] = {}
        self._skill_outputs[story_id][skill_name] = result

        return result

    def execute_phase(
        self,
        phase: str,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> List[SkillResult]:
        """
        Execute all skills for a phase in order.

        Args:
            phase: "in_progress" or "validation"
            story_id: Story ID
            story_data: Story data dict
            agent_id: Optional agent ID
            **kwargs: Additional arguments

        Returns:
            List of SkillResult for each skill executed
        """
        if phase == "in_progress":
            skill_names = self.IN_PROGRESS_SKILLS
        elif phase == "validation":
            skill_names = self.VALIDATION_SKILLS
        else:
            return [SkillResult(
                skill_name="phase",
                status="failed",
                failure_reason=f"Unknown phase: {phase}",
                story_id=story_id,
                executed_at=time.time(),
                agent_id=agent_id
            )]

        results = []
        for skill_name in skill_names:
            result = self.execute(skill_name, story_id, story_data, agent_id, **kwargs)
            results.append(result)

            # Stop on failure
            if result.status == "failed":
                break

        return results

    def get_skill_output(
        self,
        story_id: int,
        skill_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get stored skill output.

        Args:
            story_id: Story ID
            skill_name: Optional skill name (returns all if None)

        Returns:
            SkillResult or dict of all results, or None if not found
        """
        story_outputs = self._skill_outputs.get(story_id)
        if not story_outputs:
            return None

        if skill_name:
            result = story_outputs.get(skill_name)
            return result.output if result else None

        # Return all outputs for the story
        return {name: result.output for name, result in story_outputs.items()}

    def get_skill_status(
        self,
        story_id: int,
        skill_name: str
    ) -> Optional[str]:
        """
        Get status of a specific skill execution.

        Args:
            story_id: Story ID
            skill_name: Skill name

        Returns:
            Status string or None if not executed
        """
        story_outputs = self._skill_outputs.get(story_id)
        if not story_outputs:
            return None

        result = story_outputs.get(skill_name)
        return result.status if result else None

    def clear_outputs(self, story_id: Optional[int] = None) -> None:
        """
        Clear stored outputs.

        Args:
            story_id: Optional story ID (clears all if None)
        """
        if story_id:
            self._skill_outputs.pop(story_id, None)
        else:
            self._skill_outputs.clear()

    def retry_skill(
        self,
        skill_name: str,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Retry a failed skill execution.

        Same as execute() but semantically indicates a retry.
        """
        return self.execute(skill_name, story_id, story_data, agent_id, **kwargs)

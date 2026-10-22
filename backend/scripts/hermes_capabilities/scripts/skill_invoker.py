"""
SkillInvoker - Invoke Claude skills for story execution.

Skills pipeline: plan → design-a-prd → tdd → prove-it → release-it

Each skill execution is persisted to hermes-memory for recovery.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class SkillName(Enum):
    """Available Claude skills for story execution."""
    PLAN = "plan"
    DESIGN_PRD = "design-a-prd"
    TDD = "tdd"
    PROVE_IT = "prove-it"
    RELEASE_IT = "release-it"


@dataclass
class SkillResult:
    """Result from a skill invocation."""
    skill: SkillName
    success: bool
    output: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class SkillState:
    """Persistent state for skill pipeline execution."""
    story_id: int
    current_skill: Optional[SkillName] = None
    completed_skills: List[SkillName] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    failure_count: int = 0


class SkillInvoker:
    """
    Invoke Claude skills for autonomous story execution.

    Orchestrates the full skill pipeline with state persistence.
    """

    # Skill execution order
    PIPELINE_ORDER = [
        SkillName.PLAN,
        SkillName.DESIGN_PRD,
        SkillName.TDD,
        SkillName.PROVE_IT,
        SkillName.RELEASE_IT,
    ]

    def __init__(
        self,
        hermes_memory_url: Optional[str] = None,
        skill_timeout_s: float = 300.0,
    ):
        """
        Initialize SkillInvoker.

        Args:
            hermes_memory_url: URL of hermes-memory service for state persistence
            skill_timeout_s: Timeout for skill execution
        """
        self.hermes_memory_url = hermes_memory_url or os.getenv(
            "HERMES_MEMORY_URL",
            "http://hermes-memory.hermes-tools.svc.cluster.local:8080"
        )
        self._timeout_s = skill_timeout_s
        self._states: Dict[int, SkillState] = {}

    async def invoke_plan(self, story_context: Dict[str, Any]) -> SkillResult:
        """
        Invoke /plan skill.

        Args:
            story_context: Story details including title, description, ACs

        Returns:
            SkillResult with plan steps
        """
        result = await self._execute_skill(SkillName.PLAN, story_context)
        await self._save_state(SkillState(
            story_id=story_context["story_id"],
            current_skill=SkillName.PLAN,
            outputs={"plan": result.output},
        ))
        return result

    async def invoke_design_prd(self, story_context: Dict[str, Any]) -> SkillResult:
        """
        Invoke /design-a-prd skill.

        Args:
            story_context: Story details

        Returns:
            SkillResult with modules and ACs
        """
        result = await self._execute_skill(SkillName.DESIGN_PRD, story_context)
        await self._update_state(story_context["story_id"], SkillName.DESIGN_PRD, result)
        return result

    async def invoke_tdd(self, story_context: Dict[str, Any]) -> SkillResult:
        """
        Invoke /tdd skill.

        Args:
            story_context: Story details

        Returns:
            SkillResult with test status
        """
        result = await self._execute_skill(SkillName.TDD, story_context)
        await self._update_state(story_context["story_id"], SkillName.TDD, result)
        return result

    async def invoke_prove_it(self, story_context: Dict[str, Any]) -> SkillResult:
        """
        Invoke /prove-it skill.

        Args:
            story_context: Story details

        Returns:
            SkillResult with coverage and test results
        """
        result = await self._execute_skill(SkillName.PROVE_IT, story_context)
        await self._update_state(story_context["story_id"], SkillName.PROVE_IT, result)
        return result

    async def invoke_release_it(self, story_context: Dict[str, Any]) -> SkillResult:
        """
        Invoke /release-it skill.

        Args:
            story_context: Story details

        Returns:
            SkillResult with version and TOC link
        """
        result = await self._execute_skill(SkillName.RELEASE_IT, story_context)
        await self._update_state(story_context["story_id"], SkillName.RELEASE_IT, result)
        return result

    async def run_pipeline(
        self,
        story_context: Dict[str, Any],
        resume_from: Optional[SkillName] = None,
    ) -> List[SkillResult]:
        """
        Run the full skill pipeline.

        Args:
            story_context: Story details
            resume_from: Optional skill to resume from (skips earlier skills)

        Returns:
            List of SkillResults for each skill
        """
        results = []
        start_idx = 0

        if resume_from:
            try:
                start_idx = self.PIPELINE_ORDER.index(resume_from)
            except ValueError:
                pass

        for skill in self.PIPELINE_ORDER[start_idx:]:
            result = await self._execute_skill(skill, story_context)
            results.append(result)

            if not result.success:
                logger.warning(f"Pipeline stopped at {skill.value}: {result.error}")
                break

            await self._update_state(story_context["story_id"], skill, result)

        return results

    async def get_state(self, story_id: int) -> Optional[SkillState]:
        """
        Get current skill state for a story.

        Args:
            story_id: Story ID

        Returns:
            SkillState or None
        """
        # Check local cache
        if story_id in self._states:
            return self._states[story_id]

        # Load from memory
        return await self._load_state(story_id)

    def needs_rework(self, result: SkillResult) -> bool:
        """Check if a skill result requires rework."""
        return not result.success

    def build_rework_context(
        self,
        story_context: Dict[str, Any],
        failed_result: SkillResult,
    ) -> Dict[str, Any]:
        """
        Build context for rework loop after failure.

        Args:
            story_context: Original story context
            failed_result: The failed skill result

        Returns:
            Context dict with failure details
        """
        return {
            **story_context,
            "failed_skill": failed_result.skill,
            "failure_reason": failed_result.error or "Unknown error",
            "previous_output": failed_result.output,
            "rework": True,
        }

    async def _execute_skill(
        self,
        skill: SkillName,
        context: Dict[str, Any],
    ) -> SkillResult:
        """
        Execute a skill with the given context.

        This is the core execution method that would call the actual
        skill implementation (via Claude Code, MCP, or direct execution).
        """
        logger.info(f"Executing skill: {skill.value} for story {context.get('story_id')}")

        # In production, this would call the skill framework
        # For now, return a placeholder result
        return SkillResult(
            skill=skill,
            success=True,
            output={"executed": True, "skill": skill.value},
        )

    async def _save_state(self, state: SkillState) -> None:
        """Save skill state to hermes-memory."""
        self._states[state.story_id] = state

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{self.hermes_memory_url}/memories",
                    json={
                        "task_id": state.story_id,
                        "type": "skill_state",
                        "content": {
                            "current_skill": state.current_skill.value if state.current_skill else None,
                            "completed_skills": [s.value for s in state.completed_skills],
                            "outputs": state.outputs,
                            "failure_count": state.failure_count,
                        },
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to save state to hermes-memory: {e}")

    async def _load_state(self, story_id: int) -> Optional[SkillState]:
        """Load skill state from hermes-memory."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(
                    f"{self.hermes_memory_url}/memories",
                    params={"task_id": story_id, "type": "skill_state"},
                )

                if r.status_code != 200:
                    return None

                data = r.json()
                if not data.get("memories"):
                    return None

                latest = data["memories"][-1]["content"]
                return SkillState(
                    story_id=story_id,
                    current_skill=SkillName(latest["current_skill"]) if latest.get("current_skill") else None,
                    completed_skills=[SkillName(s) for s in latest.get("completed_skills", [])],
                    outputs=latest.get("outputs", {}),
                    failure_count=latest.get("failure_count", 0),
                )

        except Exception as e:
            logger.warning(f"Failed to load state from hermes-memory: {e}")
            return None

    async def _update_state(
        self,
        story_id: int,
        skill: SkillName,
        result: SkillResult,
    ) -> None:
        """Update state after skill execution."""
        state = self._states.get(story_id) or SkillState(story_id=story_id)

        if result.success:
            state.current_skill = skill
            if skill not in state.completed_skills:
                state.completed_skills.append(skill)
            state.outputs[skill.value] = result.output
        else:
            state.failure_count += 1

        await self._save_state(state)

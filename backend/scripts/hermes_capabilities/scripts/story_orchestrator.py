"""
StoryOrchestrator - Autonomous story execution with lifecycle management.

Handles:
- Claiming stories from Kanboard
- Running the skill pipeline
- Moving stories through columns (Backlog → In Progress → Validation → Done)
- Posting progress comments
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from .skill_invoker import SkillInvoker, SkillResult, SkillName

logger = logging.getLogger(__name__)


class StoryLifecycle(Enum):
    """Kanboard column states for story lifecycle."""
    BACKLOG = "Backlog"
    IN_PROGRESS = "In Progress"
    VALIDATION = "Validation"
    DONE = "Done"


@dataclass
class ExecutionResult:
    """Result of story execution."""
    success: bool
    story_id: int
    skills_completed: int
    final_column: StoryLifecycle
    error: Optional[str] = None


class StoryOrchestrator:
    """
    Orchestrate autonomous story execution.

    Claims stories, runs skill pipeline, moves through lifecycle.
    """

    def __init__(
        self,
        kanboard_url: Optional[str] = None,
        kanboard_token: Optional[str] = None,
    ):
        """
        Initialize StoryOrchestrator.

        Args:
            kanboard_url: Kanboard JSON-RPC API URL
            kanboard_token: Kanboard API token
        """
        self.kanboard_url = kanboard_url or os.getenv(
            "KANBOARD_URL",
            "http://kanboard.hr-project-tracking.svc.cluster.local/jsonrpc.php"
        )
        self._token = kanboard_token or os.getenv("KANBOARD_API_TOKEN", "")
        self._skill_invoker = SkillInvoker()

    async def execute_story(self, story: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a story autonomously.

        1. Claim the story
        2. Run skill pipeline
        3. Move to Done on success

        Args:
            story: Story dict with id, title, description, etc.

        Returns:
            ExecutionResult with success status and details
        """
        story_id = story["id"]
        logger.info(f"Starting execution of story {story_id}: {story.get('title')}")

        # Step 1: Claim the story
        claimed = await self._claim_story(story)
        if not claimed:
            return ExecutionResult(
                success=False,
                story_id=story_id,
                skills_completed=0,
                final_column=StoryLifecycle.BACKLOG,
                error="Failed to claim story",
            )

        # Step 2: Run skill pipeline
        results = await self._run_skill_pipeline(story)

        # Count successful skills
        skills_completed = sum(1 for r in results if r.success)

        # Check if all skills passed
        all_passed = all(r.success for r in results)

        # Post progress comments for each result
        for result in results:
            await self._on_skill_complete(story, result)

        # Step 3: Move to Done if all passed
        if all_passed and len(results) == 5:
            await self._on_tdd_complete(story)  # Move to Validation after TDD
            await self._move_to_done(story)
            return ExecutionResult(
                success=True,
                story_id=story_id,
                skills_completed=skills_completed,
                final_column=StoryLifecycle.DONE,
            )

        # Failed somewhere
        failed_skill = next((r for r in results if not r.success), None)
        return ExecutionResult(
            success=False,
            story_id=story_id,
            skills_completed=skills_completed,
            final_column=StoryLifecycle.IN_PROGRESS,
            error=failed_skill.error if failed_skill else "Unknown error",
        )

    async def _claim_story(self, story: Dict[str, Any]) -> bool:
        """
        Claim a story and move to In Progress.

        Args:
            story: Story dict

        Returns:
            True if claimed successfully
        """
        story_id = story["id"]
        logger.info(f"Claiming story {story_id}")

        try:
            await self._move_story(story_id, StoryLifecycle.IN_PROGRESS)
            return True
        except Exception as e:
            logger.error(f"Failed to claim story {story_id}: {e}")
            return False

    async def _run_skill_pipeline(
        self,
        story: Dict[str, Any],
    ) -> List[SkillResult]:
        """
        Run the full skill pipeline for a story.

        Args:
            story: Story dict

        Returns:
            List of SkillResults
        """
        context = {
            "story_id": story["id"],
            "title": story.get("title", ""),
            "description": story.get("description", ""),
            "repo": story.get("repo", ""),
            "branch": story.get("branch", ""),
            "acceptance_criteria": story.get("acceptance_criteria", []),
        }

        return await self._skill_invoker.run_pipeline(context)

    async def _on_tdd_complete(self, story: Dict[str, Any]) -> None:
        """Move story to Validation after TDD completes."""
        await self._move_story(story["id"], StoryLifecycle.VALIDATION)

    async def _move_to_done(self, story: Dict[str, Any]) -> None:
        """Move story to Done column."""
        await self._move_story(story["id"], StoryLifecycle.DONE)

    async def _move_story(
        self,
        story_id: int,
        column: StoryLifecycle,
    ) -> None:
        """
        Move a story to a specific column.

        Args:
            story_id: Story ID
            column: Target column
        """
        logger.info(f"Moving story {story_id} to {column.value}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "moveTaskToColumn",
                    "id": 1,
                    "params": {
                        "task_id": story_id,
                        "column_name": column.value,
                    },
                }

                await client.post(
                    self.kanboard_url,
                    json=payload,
                    auth=("jsonrpc", self._token),
                )

        except Exception as e:
            logger.error(f"Failed to move story {story_id}: {e}")

    async def _on_skill_complete(
        self,
        story: Dict[str, Any],
        result: SkillResult,
    ) -> None:
        """
        Handle skill completion - post progress comment.

        Args:
            story: Story dict
            result: Skill result
        """
        skill_name = result.skill.value

        if result.success:
            comment = f"/{skill_name} completed successfully."
            if result.output:
                comment += f" Output: {result.output}"
        else:
            comment = f"/{skill_name} failed: {result.error or 'Unknown error'}"

        await self._post_comment(story["id"], comment)

    async def _post_comment(
        self,
        story_id: int,
        comment: str,
    ) -> None:
        """
        Post a comment to a story.

        Args:
            story_id: Story ID
            comment: Comment text
        """
        logger.info(f"Posting comment to story {story_id}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "createComment",
                    "id": 1,
                    "params": {
                        "task_id": story_id,
                        "content": comment,
                    },
                }

                await client.post(
                    self.kanboard_url,
                    json=payload,
                    auth=("jsonrpc", self._token),
                )

        except Exception as e:
            logger.warning(f"Failed to post comment to story {story_id}: {e}")

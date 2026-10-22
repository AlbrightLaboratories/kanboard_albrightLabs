"""
Tests for StoryOrchestrator - HC-19 to HC-22.

TDD: Write failing tests first.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from scripts.hermes_capabilities.scripts.story_orchestrator import (
    StoryOrchestrator,
    StoryLifecycle,
)
from scripts.hermes_capabilities.scripts.skill_invoker import (
    SkillResult,
    SkillName,
)


class TestStoryOrchestrator:
    """Tests for StoryOrchestrator managing story lifecycle."""

    @pytest.fixture
    def orchestrator(self) -> StoryOrchestrator:
        return StoryOrchestrator()

    @pytest.fixture
    def story(self) -> dict:
        return {
            "id": 17,
            "title": "Implement user auth",
            "description": "Add OAuth2 login flow",
            "column": "Backlog",
            "repo": "kanboard_albrightLabs",
            "branch": "feat/user-auth",
        }

    # HC-19: StoryOrchestrator claims story and runs pipeline
    @pytest.mark.asyncio
    async def test_claim_and_run_pipeline(self, orchestrator, story):
        """HC-19: StoryOrchestrator claims story, runs skill pipeline, moves to Done."""
        with patch.object(orchestrator, "_claim_story", new_callable=AsyncMock) as mock_claim:
            mock_claim.return_value = True

            with patch.object(orchestrator, "_run_skill_pipeline", new_callable=AsyncMock) as mock_pipeline:
                mock_pipeline.return_value = [
                    SkillResult(skill=SkillName.PLAN, success=True, output={}),
                    SkillResult(skill=SkillName.DESIGN_PRD, success=True, output={}),
                    SkillResult(skill=SkillName.TDD, success=True, output={}),
                    SkillResult(skill=SkillName.PROVE_IT, success=True, output={}),
                    SkillResult(skill=SkillName.RELEASE_IT, success=True, output={}),
                ]

                with patch.object(orchestrator, "_move_to_done", new_callable=AsyncMock) as mock_done:
                    result = await orchestrator.execute_story(story)

                    mock_claim.assert_called_once()
                    mock_pipeline.assert_called_once()
                    mock_done.assert_called_once()
                    assert result.success is True

    @pytest.mark.asyncio
    async def test_claim_fails_returns_error(self, orchestrator, story):
        """HC-19: Claim failure returns error."""
        with patch.object(orchestrator, "_claim_story", new_callable=AsyncMock) as mock_claim:
            mock_claim.return_value = False

            result = await orchestrator.execute_story(story)

            assert result.success is False
            assert "claim" in result.error.lower()

    # HC-20: E2E story work
    @pytest.mark.asyncio
    async def test_hermes_mention_triggers_full_pipeline(self, orchestrator, story):
        """HC-20: @hermes claim and work on story runs full skill pipeline."""
        with patch.object(orchestrator, "_claim_story", new_callable=AsyncMock) as mock_claim:
            mock_claim.return_value = True

            with patch.object(orchestrator, "_run_skill_pipeline", new_callable=AsyncMock) as mock_pipeline:
                all_success = [
                    SkillResult(skill=s, success=True, output={})
                    for s in [SkillName.PLAN, SkillName.DESIGN_PRD, SkillName.TDD,
                              SkillName.PROVE_IT, SkillName.RELEASE_IT]
                ]
                mock_pipeline.return_value = all_success

                with patch.object(orchestrator, "_move_to_done", new_callable=AsyncMock):
                    result = await orchestrator.execute_story(story)

                    # All 5 skills should have run
                    assert result.skills_completed == 5

    # HC-21: Story lifecycle Backlog → In Progress → Validation → Done
    @pytest.mark.asyncio
    async def test_lifecycle_backlog_to_in_progress(self, orchestrator, story):
        """HC-21: Story moves from Backlog to In Progress on claim."""
        with patch.object(orchestrator, "_move_story", new_callable=AsyncMock) as mock_move:
            await orchestrator._claim_story(story)

            mock_move.assert_called_with(story["id"], StoryLifecycle.IN_PROGRESS)

    @pytest.mark.asyncio
    async def test_lifecycle_in_progress_to_validation(self, orchestrator, story):
        """HC-21: Story moves to Validation after TDD completes."""
        story["column"] = "In Progress"

        with patch.object(orchestrator, "_move_story", new_callable=AsyncMock) as mock_move:
            await orchestrator._on_tdd_complete(story)

            mock_move.assert_called_with(story["id"], StoryLifecycle.VALIDATION)

    @pytest.mark.asyncio
    async def test_lifecycle_validation_to_done(self, orchestrator, story):
        """HC-21: Story moves to Done after release-it."""
        story["column"] = "Validation"

        with patch.object(orchestrator, "_move_story", new_callable=AsyncMock) as mock_move:
            await orchestrator._move_to_done(story)

            mock_move.assert_called_with(story["id"], StoryLifecycle.DONE)

    @pytest.mark.asyncio
    async def test_full_lifecycle_autonomous(self, orchestrator, story):
        """HC-21: Full autonomous lifecycle Backlog → Done."""
        lifecycle_moves = []

        async def track_move(story_id, column):
            lifecycle_moves.append(column)

        with patch.object(orchestrator, "_move_story", new_callable=AsyncMock) as mock_move:
            mock_move.side_effect = track_move

            with patch.object(orchestrator, "_run_skill_pipeline", new_callable=AsyncMock) as mock_pipeline:
                all_success = [
                    SkillResult(skill=s, success=True, output={})
                    for s in [SkillName.PLAN, SkillName.DESIGN_PRD, SkillName.TDD,
                              SkillName.PROVE_IT, SkillName.RELEASE_IT]
                ]
                mock_pipeline.return_value = all_success

                await orchestrator.execute_story(story)

                # Should have moved through: In Progress → Validation → Done
                assert StoryLifecycle.IN_PROGRESS in lifecycle_moves
                assert StoryLifecycle.DONE in lifecycle_moves

    # HC-22: Progress comments at each skill stage
    @pytest.mark.asyncio
    async def test_progress_comment_posted_on_plan(self, orchestrator, story):
        """HC-22: Progress comment posted when /plan completes."""
        with patch.object(orchestrator, "_post_comment", new_callable=AsyncMock) as mock_comment:
            await orchestrator._on_skill_complete(
                story,
                SkillResult(skill=SkillName.PLAN, success=True, output={"steps": 3}),
            )

            mock_comment.assert_called_once()
            call_args = mock_comment.call_args
            assert "plan" in call_args[0][1].lower()

    @pytest.mark.asyncio
    async def test_progress_comment_posted_on_tdd(self, orchestrator, story):
        """HC-22: Progress comment posted when /tdd completes."""
        with patch.object(orchestrator, "_post_comment", new_callable=AsyncMock) as mock_comment:
            await orchestrator._on_skill_complete(
                story,
                SkillResult(skill=SkillName.TDD, success=True, output={"tests": 10}),
            )

            mock_comment.assert_called_once()
            call_args = mock_comment.call_args
            assert "tdd" in call_args[0][1].lower()

    @pytest.mark.asyncio
    async def test_progress_comment_on_failure(self, orchestrator, story):
        """HC-22: Failure comment includes error details."""
        with patch.object(orchestrator, "_post_comment", new_callable=AsyncMock) as mock_comment:
            await orchestrator._on_skill_complete(
                story,
                SkillResult(skill=SkillName.PROVE_IT, success=False, output={}, error="Tests failed"),
            )

            mock_comment.assert_called_once()
            call_args = mock_comment.call_args
            comment_text = call_args[0][1]
            assert "failed" in comment_text.lower() or "error" in comment_text.lower()

    # Edge cases
    @pytest.mark.asyncio
    async def test_pipeline_stops_on_failure(self, orchestrator, story):
        """Pipeline stops when a skill fails."""
        with patch.object(orchestrator, "_claim_story", new_callable=AsyncMock) as mock_claim:
            mock_claim.return_value = True

            with patch.object(orchestrator, "_run_skill_pipeline", new_callable=AsyncMock) as mock_pipeline:
                # TDD fails
                mock_pipeline.return_value = [
                    SkillResult(skill=SkillName.PLAN, success=True, output={}),
                    SkillResult(skill=SkillName.DESIGN_PRD, success=True, output={}),
                    SkillResult(skill=SkillName.TDD, success=False, output={}, error="Tests failed"),
                ]

                with patch.object(orchestrator, "_move_to_done", new_callable=AsyncMock) as mock_done:
                    result = await orchestrator.execute_story(story)

                    # Should NOT move to done on failure
                    mock_done.assert_not_called()
                    assert result.success is False
                    assert result.skills_completed == 2  # Only plan + prd

    def test_story_lifecycle_enum(self):
        """StoryLifecycle enum has all columns."""
        assert StoryLifecycle.BACKLOG.value == "Backlog"
        assert StoryLifecycle.IN_PROGRESS.value == "In Progress"
        assert StoryLifecycle.VALIDATION.value == "Validation"
        assert StoryLifecycle.DONE.value == "Done"

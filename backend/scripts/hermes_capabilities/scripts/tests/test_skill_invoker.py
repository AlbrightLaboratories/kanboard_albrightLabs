"""
Tests for SkillInvoker - HC-11 to HC-18.

TDD: Write failing tests first.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from scripts.hermes_capabilities.scripts.skill_invoker import (
    SkillInvoker,
    SkillResult,
    SkillName,
    SkillState,
)


class TestSkillInvoker:
    """Tests for SkillInvoker triggering Claude skills."""

    @pytest.fixture
    def invoker(self) -> SkillInvoker:
        return SkillInvoker()

    @pytest.fixture
    def story_context(self) -> dict:
        return {
            "story_id": 17,
            "title": "Implement user auth",
            "description": "Add OAuth2 login flow",
            "repo": "kanboard_albrightLabs",
            "branch": "feat/user-auth",
            "acceptance_criteria": [
                "OAuth2 flow works",
                "Session persists",
            ],
        }

    # HC-11: /plan skill
    @pytest.mark.asyncio
    async def test_invoke_plan_skill(self, invoker, story_context):
        """HC-11: SkillInvoker triggers /plan skill with story context."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.PLAN,
                success=True,
                output={"steps": ["step1", "step2"]},
            )

            result = await invoker.invoke_plan(story_context)

            assert result.success is True
            assert result.skill == SkillName.PLAN
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args
            assert call_args[0][0] == SkillName.PLAN
            assert "story_id" in call_args[0][1]

    # HC-12: /design-a-prd skill
    @pytest.mark.asyncio
    async def test_invoke_design_prd_skill(self, invoker, story_context):
        """HC-12: SkillInvoker triggers /design-a-prd skill."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.DESIGN_PRD,
                success=True,
                output={"modules": ["auth", "api"], "acs": ["AC-01", "AC-02"]},
            )

            result = await invoker.invoke_design_prd(story_context)

            assert result.success is True
            assert result.skill == SkillName.DESIGN_PRD
            assert "modules" in result.output

    # HC-13: /tdd skill
    @pytest.mark.asyncio
    async def test_invoke_tdd_skill(self, invoker, story_context):
        """HC-13: SkillInvoker triggers /tdd skill."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.TDD,
                success=True,
                output={"test_file": "test_auth.py", "status": "green"},
            )

            result = await invoker.invoke_tdd(story_context)

            assert result.success is True
            assert result.skill == SkillName.TDD

    # HC-14: /prove-it skill
    @pytest.mark.asyncio
    async def test_invoke_prove_it_skill(self, invoker, story_context):
        """HC-14: SkillInvoker triggers /prove-it skill."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.PROVE_IT,
                success=True,
                output={"coverage": 95, "all_tests_pass": True},
            )

            result = await invoker.invoke_prove_it(story_context)

            assert result.success is True
            assert result.skill == SkillName.PROVE_IT

    # HC-15: /release-it skill
    @pytest.mark.asyncio
    async def test_invoke_release_it_skill(self, invoker, story_context):
        """HC-15: SkillInvoker triggers /release-it skill."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.RELEASE_IT,
                success=True,
                output={"version": "1.2.0", "toc_link": "issue#17"},
            )

            result = await invoker.invoke_release_it(story_context)

            assert result.success is True
            assert result.skill == SkillName.RELEASE_IT

    # HC-16: Skill pipeline orchestration
    @pytest.mark.asyncio
    async def test_run_pipeline(self, invoker, story_context):
        """HC-16: Skill pipeline orchestrates plan→prd→tdd→prove-it→release-it."""
        # Mock returns different result for each skill
        def make_result(skill, ctx):
            return SkillResult(skill=skill, success=True, output={})

        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = make_result

            results = await invoker.run_pipeline(story_context)

            assert len(results) == 5
            # Verify order
            skills_called = [r.skill for r in results]
            assert skills_called == [
                SkillName.PLAN,
                SkillName.DESIGN_PRD,
                SkillName.TDD,
                SkillName.PROVE_IT,
                SkillName.RELEASE_IT,
            ]

    # HC-17: Skill state persistence
    @pytest.mark.asyncio
    async def test_state_persisted_to_memory(self, invoker, story_context):
        """HC-17: Skill state persisted in hermes-memory."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.PLAN,
                success=True,
                output={"steps": ["step1"]},
            )

            with patch.object(invoker, "_save_state", new_callable=AsyncMock) as mock_save:
                await invoker.invoke_plan(story_context)
                mock_save.assert_called_once()
                saved_state = mock_save.call_args[0][0]
                assert saved_state.story_id == story_context["story_id"]
                assert saved_state.current_skill == SkillName.PLAN

    @pytest.mark.asyncio
    async def test_state_recovered_on_resume(self, invoker, story_context):
        """HC-17: State recovered after restart."""
        saved_state = SkillState(
            story_id=17,
            current_skill=SkillName.TDD,
            completed_skills=[SkillName.PLAN, SkillName.DESIGN_PRD],
            outputs={},
        )

        with patch.object(invoker, "_load_state", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = saved_state

            state = await invoker.get_state(17)

            assert state.current_skill == SkillName.TDD
            assert SkillName.PLAN in state.completed_skills

    # HC-18: Skill failure triggers rework
    @pytest.mark.asyncio
    async def test_failure_triggers_rework(self, invoker, story_context):
        """HC-18: Skill failure triggers rework loop."""
        with patch.object(invoker, "_execute_skill", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = SkillResult(
                skill=SkillName.TDD,
                success=False,
                output={},
                error="Tests failed: 3 errors",
            )

            result = await invoker.invoke_tdd(story_context)

            assert result.success is False
            assert result.error is not None
            assert invoker.needs_rework(result) is True

    @pytest.mark.asyncio
    async def test_rework_includes_failure_context(self, invoker, story_context):
        """HC-18: Rework loop includes failure context."""
        failed_result = SkillResult(
            skill=SkillName.PROVE_IT,
            success=False,
            output={},
            error="Coverage too low: 45%",
        )

        rework_context = invoker.build_rework_context(story_context, failed_result)

        assert "Coverage too low" in rework_context["failure_reason"]
        assert rework_context["failed_skill"] == SkillName.PROVE_IT
        assert rework_context["story_id"] == story_context["story_id"]

    # Edge cases
    def test_skill_names_enum(self):
        """All required skills are defined."""
        assert SkillName.PLAN.value == "plan"
        assert SkillName.DESIGN_PRD.value == "design-a-prd"
        assert SkillName.TDD.value == "tdd"
        assert SkillName.PROVE_IT.value == "prove-it"
        assert SkillName.RELEASE_IT.value == "release-it"

    def test_skill_result_dataclass(self):
        """SkillResult has required fields."""
        result = SkillResult(
            skill=SkillName.PLAN,
            success=True,
            output={"key": "value"},
        )
        assert result.skill == SkillName.PLAN
        assert result.success is True
        assert result.error is None

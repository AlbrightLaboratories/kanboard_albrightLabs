"""
Test AIC-07: Successful sandbox updates code in repo via PR
"""

import pytest
from unittest.mock import AsyncMock
from ..execution_handler import (
    create_pr_from_result,
    ExecutionResult,
    ExecutionStatus,
)


@pytest.fixture
def passed_result():
    """Sample passed execution result."""
    return ExecutionResult(
        request_id="exec-123-c1",
        status=ExecutionStatus.PASSED,
        exit_code=0,
        stdout="All tests passed",
        stderr="",
        duration_seconds=5.0,
    )


@pytest.fixture
def failed_result():
    """Sample failed execution result."""
    return ExecutionResult(
        request_id="exec-123-c1",
        status=ExecutionStatus.FAILED,
        exit_code=1,
        stdout="",
        stderr="Test failed",
        duration_seconds=3.0,
    )


@pytest.fixture
def story_data():
    """Sample story data with repo info."""
    return {
        "id": "123",
        "title": "Fix login bug",
        "linked_repo": "AlbrightLaboratories/app",
        "linked_branch": "main",
    }


class TestCreatePrFromResult:
    """Tests for create_pr_from_result function."""

    @pytest.mark.asyncio
    async def test_creates_pr_on_success(self, passed_result, story_data):
        """PR is created for successful execution."""
        github_client = AsyncMock()
        github_client.create_pull_request.return_value = (
            "https://github.com/AlbrightLaboratories/app/pull/123"
        )

        pr_url = await create_pr_from_result(
            result=passed_result,
            story_data=story_data,
            github_client=github_client,
        )

        assert pr_url is not None
        assert "pull/123" in pr_url
        github_client.create_pull_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_pr_on_failure(self, failed_result, story_data):
        """No PR is created for failed execution."""
        github_client = AsyncMock()

        pr_url = await create_pr_from_result(
            result=failed_result,
            story_data=story_data,
            github_client=github_client,
        )

        assert pr_url is None
        github_client.create_pull_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_pr_without_repo(self, passed_result):
        """No PR is created if story has no linked repo."""
        github_client = AsyncMock()
        story_data = {"id": "123", "title": "No repo story"}

        pr_url = await create_pr_from_result(
            result=passed_result,
            story_data=story_data,
            github_client=github_client,
        )

        assert pr_url is None
        github_client.create_pull_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_title_includes_story(self, passed_result, story_data):
        """PR title includes story ID."""
        github_client = AsyncMock()
        github_client.create_pull_request.return_value = "https://pr.url"

        await create_pr_from_result(
            result=passed_result,
            story_data=story_data,
            github_client=github_client,
        )

        call_kwargs = github_client.create_pull_request.call_args[1]
        assert "123" in call_kwargs["title"]

    @pytest.mark.asyncio
    async def test_pr_uses_agent_branch(self, passed_result, story_data):
        """PR head branch uses agent prefix."""
        github_client = AsyncMock()
        github_client.create_pull_request.return_value = "https://pr.url"

        await create_pr_from_result(
            result=passed_result,
            story_data=story_data,
            github_client=github_client,
        )

        call_kwargs = github_client.create_pull_request.call_args[1]
        assert call_kwargs["head"].startswith("agent/")

    @pytest.mark.asyncio
    async def test_pr_base_is_story_branch(self, passed_result, story_data):
        """PR base branch is story's linked branch."""
        github_client = AsyncMock()
        github_client.create_pull_request.return_value = "https://pr.url"

        await create_pr_from_result(
            result=passed_result,
            story_data=story_data,
            github_client=github_client,
        )

        call_kwargs = github_client.create_pull_request.call_args[1]
        assert call_kwargs["base"] == "main"

    @pytest.mark.asyncio
    async def test_pr_body_includes_execution_id(self, passed_result, story_data):
        """PR body includes execution ID."""
        github_client = AsyncMock()
        github_client.create_pull_request.return_value = "https://pr.url"

        await create_pr_from_result(
            result=passed_result,
            story_data=story_data,
            github_client=github_client,
        )

        call_kwargs = github_client.create_pull_request.call_args[1]
        assert "exec-123-c1" in call_kwargs["body"]

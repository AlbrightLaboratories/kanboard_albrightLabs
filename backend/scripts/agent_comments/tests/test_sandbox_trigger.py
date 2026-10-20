"""
Test AIC-05: User approval triggers sandbox pod execution
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from ..execution_handler import (
    trigger_sandbox_execution,
    ExecutionRequest,
    ExecutionStatus,
)


@pytest.fixture
def sample_request():
    """Sample execution request."""
    return ExecutionRequest(
        request_id="exec-123-c1",
        story_id="123",
        comment_id="c1",
        agent_id="claude-001",
        execution_type="test",
        commands=["pytest tests/"],
        working_directory="/workspace",
        environment={"NODE_ENV": "test"},
        timeout_seconds=300,
        status=ExecutionStatus.APPROVED,
    )


class TestTriggerSandboxExecution:
    """Tests for trigger_sandbox_execution function."""

    @pytest.mark.asyncio
    async def test_creates_kubernetes_job(self, sample_request):
        """Kubernetes job is created for execution."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        job_id = await trigger_sandbox_execution(sample_request, sandbox_client)

        assert job_id == "job-123"
        sandbox_client.create_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_commands(self, sample_request):
        """Commands are passed to sandbox client."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        await trigger_sandbox_execution(sample_request, sandbox_client)

        call_args = sandbox_client.create_job.call_args[0][0]
        assert call_args["commands"] == ["pytest tests/"]

    @pytest.mark.asyncio
    async def test_passes_working_directory(self, sample_request):
        """Working directory is passed to sandbox client."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        await trigger_sandbox_execution(sample_request, sandbox_client)

        call_args = sandbox_client.create_job.call_args[0][0]
        assert call_args["working_directory"] == "/workspace"

    @pytest.mark.asyncio
    async def test_passes_environment(self, sample_request):
        """Environment variables are passed."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        await trigger_sandbox_execution(sample_request, sandbox_client)

        call_args = sandbox_client.create_job.call_args[0][0]
        assert call_args["environment"]["NODE_ENV"] == "test"

    @pytest.mark.asyncio
    async def test_passes_timeout(self, sample_request):
        """Timeout is passed to sandbox client."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        await trigger_sandbox_execution(sample_request, sandbox_client)

        call_args = sandbox_client.create_job.call_args[0][0]
        assert call_args["timeout_seconds"] == 300

    @pytest.mark.asyncio
    async def test_includes_labels(self, sample_request):
        """Labels include story_id and agent_id."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        await trigger_sandbox_execution(sample_request, sandbox_client)

        call_args = sandbox_client.create_job.call_args[0][0]
        assert call_args["labels"]["story_id"] == "123"
        assert call_args["labels"]["agent_id"] == "claude-001"

    @pytest.mark.asyncio
    async def test_updates_status_to_running(self, sample_request):
        """Request status is updated to RUNNING."""
        sandbox_client = AsyncMock()
        sandbox_client.create_job.return_value = "job-123"

        await trigger_sandbox_execution(sample_request, sandbox_client)

        assert sample_request.status == ExecutionStatus.RUNNING

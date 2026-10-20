"""
Test AIC-04: Agent can request sandbox execution via [READY_TO_EXECUTE] marker
"""

import pytest
from ..execution_handler import (
    parse_execution_request,
    ExecutionRequest,
    ExecutionStatus,
    EXECUTION_MARKER,
)


class TestParseExecutionRequest:
    """Tests for parse_execution_request function."""

    def test_parses_json_execution_block(self):
        """JSON execution block is parsed correctly."""
        content = f"""
I've prepared the fix. Ready to execute:

{EXECUTION_MARKER}
{{
    "type": "test",
    "commands": ["pytest tests/", "npm run lint"],
    "timeout": 600
}}
        """

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request is not None
        assert request.execution_type == "test"
        assert request.commands == ["pytest tests/", "npm run lint"]
        assert request.timeout_seconds == 600
        assert request.status == ExecutionStatus.PENDING_APPROVAL

    def test_parses_simple_command(self):
        """Simple command after marker is parsed."""
        content = f"""
Ready to run tests.

{EXECUTION_MARKER} npm test
        """

        request = parse_execution_request(
            content=content,
            story_id="456",
            comment_id="c2",
            agent_id="gemini-001",
        )

        assert request is not None
        assert request.execution_type == "script"
        assert "npm test" in request.commands[0]

    def test_no_marker_returns_none(self):
        """No marker in content returns None."""
        content = "Just a regular response without execution request"

        request = parse_execution_request(
            content=content,
            story_id="789",
            comment_id="c3",
            agent_id="codex-001",
        )

        assert request is None

    def test_generates_request_id(self):
        """Request ID is generated from story and comment."""
        content = f"{EXECUTION_MARKER} echo test"

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request is not None
        assert request.request_id == "exec-123-c1"

    def test_stores_agent_id(self):
        """Agent ID is stored in request."""
        content = f"{EXECUTION_MARKER} npm test"

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request.agent_id == "claude-001"

    def test_parses_working_directory(self):
        """Working directory is parsed from JSON."""
        content = f"""
{EXECUTION_MARKER}
{{
    "type": "build",
    "commands": ["npm run build"],
    "working_directory": "/workspace/frontend"
}}
        """

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request.working_directory == "/workspace/frontend"

    def test_parses_environment_variables(self):
        """Environment variables are parsed from JSON."""
        content = f"""
{EXECUTION_MARKER}
{{
    "type": "test",
    "commands": ["pytest"],
    "environment": {{"NODE_ENV": "test", "DEBUG": "true"}}
}}
        """

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request.environment.get("NODE_ENV") == "test"
        assert request.environment.get("DEBUG") == "true"

    def test_default_timeout(self):
        """Default timeout is 300 seconds."""
        content = f'{EXECUTION_MARKER} {{"type": "test", "commands": ["npm test"]}}'

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request.timeout_seconds == 300

    def test_initial_status_pending(self):
        """Initial status is PENDING_APPROVAL."""
        content = f"{EXECUTION_MARKER} npm test"

        request = parse_execution_request(
            content=content,
            story_id="123",
            comment_id="c1",
            agent_id="claude-001",
        )

        assert request.status == ExecutionStatus.PENDING_APPROVAL

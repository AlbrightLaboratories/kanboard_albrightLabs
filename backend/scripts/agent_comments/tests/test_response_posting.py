"""
Test AIC-03: Agent response is posted back as comment with agent badge
"""

import pytest
from ..response_handler import (
    create_agent_response,
    format_agent_comment,
    add_agent_badge,
    parse_execution_details,
    AgentResponse,
    EXECUTION_MARKER,
)


class TestCreateAgentResponse:
    """Tests for create_agent_response function."""

    def test_creates_basic_response(self):
        """Basic response is created correctly."""
        response = create_agent_response(
            agent_id="claude-001",
            agent_name="Claude",
            content="Here is my analysis...",
            story_id="123",
            in_reply_to="c1",
        )

        assert response.agent_id == "claude-001"
        assert response.agent_name == "Claude"
        assert response.content == "Here is my analysis..."
        assert response.story_id == "123"
        assert response.in_reply_to == "c1"
        assert response.has_execution_request is False

    def test_detects_execution_request(self):
        """Execution request is detected in content."""
        content = f"""
I've analyzed the issue and prepared a fix.

{EXECUTION_MARKER}
{{"type": "test", "commands": ["pytest tests/"]}}
        """

        response = create_agent_response(
            agent_id="claude-001",
            agent_name="Claude",
            content=content,
            story_id="123",
            in_reply_to="c1",
        )

        assert response.has_execution_request is True
        assert response.execution_details is not None
        assert response.execution_details.get("type") == "test"

    def test_sets_timestamp(self):
        """Timestamp is automatically set."""
        response = create_agent_response(
            agent_id="claude-001",
            agent_name="Claude",
            content="Test",
            story_id="123",
            in_reply_to="c1",
        )

        assert response.created_at != ""
        assert "T" in response.created_at  # ISO format


class TestParseExecutionDetails:
    """Tests for parse_execution_details function."""

    def test_parses_json_block(self):
        """JSON block after marker is parsed."""
        content = f'{EXECUTION_MARKER}{{"type": "test", "commands": ["npm test"]}}'

        details = parse_execution_details(content)

        assert details is not None
        assert details["type"] == "test"
        assert details["commands"] == ["npm test"]

    def test_handles_simple_command(self):
        """Simple command without JSON is handled."""
        content = f"{EXECUTION_MARKER} npm test"

        details = parse_execution_details(content)

        assert details is not None
        assert details["type"] == "simple"
        assert "npm test" in details["command"]

    def test_no_marker_returns_none(self):
        """No marker returns None."""
        content = "Regular content without marker"

        details = parse_execution_details(content)

        assert details is None


class TestFormatAgentComment:
    """Tests for format_agent_comment function."""

    def test_formats_basic_comment(self):
        """Basic comment is formatted correctly."""
        response = AgentResponse(
            agent_id="claude-001",
            agent_name="Claude",
            content="My response",
            story_id="123",
            in_reply_to="c1",
        )

        payload = format_agent_comment(response)

        assert payload["story_id"] == "123"
        assert payload["content"] == "My response"
        assert payload["is_agent_response"] is True
        assert payload["agent_id"] == "claude-001"
        assert "Claude (Agent)" in payload["author"]

    def test_includes_execution_metadata(self):
        """Execution metadata is included."""
        response = AgentResponse(
            agent_id="claude-001",
            agent_name="Claude",
            content="My response",
            story_id="123",
            in_reply_to="c1",
            has_execution_request=True,
            execution_details={"type": "test"},
        )

        payload = format_agent_comment(response)

        assert payload["metadata"]["has_execution_request"] is True
        assert payload["metadata"]["execution_details"]["type"] == "test"


class TestAddAgentBadge:
    """Tests for add_agent_badge function."""

    def test_adds_badge_prefix(self):
        """Badge is added as prefix."""
        content = "Here is my analysis"
        badged = add_agent_badge(content, "Claude")

        assert badged.startswith("🤖")
        assert "**Claude**" in badged
        assert "Here is my analysis" in badged

    def test_preserves_content(self):
        """Original content is preserved."""
        content = "Line 1\nLine 2\nLine 3"
        badged = add_agent_badge(content, "Gemini")

        assert "Line 1" in badged
        assert "Line 2" in badged
        assert "Line 3" in badged

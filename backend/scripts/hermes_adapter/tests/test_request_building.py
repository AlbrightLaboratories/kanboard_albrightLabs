"""
Tests for request building functions.
"""
import pytest

from ..scripts.request_builder import (
    build_simple_prompt,
    build_comment_context_prompt,
    format_agent_response,
    StoryContext,
    HERMES_SYSTEM_PROMPT,
)


class TestBuildSimplePrompt:
    """Tests for build_simple_prompt function."""

    def test_returns_list_of_messages(self):
        """Returns properly formatted message list."""
        messages = build_simple_prompt("Hello @hermes")

        assert isinstance(messages, list)
        assert len(messages) == 2

    def test_includes_system_prompt(self):
        """System message contains Hermes system prompt."""
        messages = build_simple_prompt("Hello")

        assert messages[0]["role"] == "system"
        assert "Hermes" in messages[0]["content"]

    def test_includes_user_message(self):
        """User message contains the provided text."""
        user_text = "@hermes can you hear me"
        messages = build_simple_prompt(user_text)

        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == user_text


class TestBuildCommentContextPrompt:
    """Tests for build_comment_context_prompt function."""

    @pytest.fixture
    def sample_story(self):
        """Sample story context for testing."""
        return StoryContext(
            story_id="123",
            title="Test Story",
            description="This is a test story description.",
            column="In Progress",
            assignee="testuser",
            acceptance_criteria=["AC-1: First criterion", "AC-2: Second criterion"],
            previous_comments=[
                {"author": "alice", "content": "First comment"},
                {"author": "bob", "content": "Second comment"},
            ],
        )

    def test_includes_story_context(self, sample_story):
        """System message includes story context."""
        messages = build_comment_context_prompt(
            "@hermes help",
            sample_story,
        )

        system_content = messages[0]["content"]
        assert "Story ID:** 123" in system_content
        assert "Test Story" in system_content
        assert "In Progress" in system_content
        assert "testuser" in system_content

    def test_includes_acceptance_criteria(self, sample_story):
        """System message includes acceptance criteria."""
        messages = build_comment_context_prompt(
            "@hermes help",
            sample_story,
        )

        system_content = messages[0]["content"]
        assert "AC-1: First criterion" in system_content
        assert "AC-2: Second criterion" in system_content

    def test_includes_thread_history(self, sample_story):
        """System message includes previous comments."""
        messages = build_comment_context_prompt(
            "@hermes help",
            sample_story,
            include_thread=True,
        )

        system_content = messages[0]["content"]
        assert "alice" in system_content
        assert "First comment" in system_content
        assert "bob" in system_content

    def test_excludes_thread_when_disabled(self, sample_story):
        """Thread history excluded when include_thread=False."""
        messages = build_comment_context_prompt(
            "@hermes help",
            sample_story,
            include_thread=False,
        )

        system_content = messages[0]["content"]
        assert "Previous Comments" not in system_content

    def test_handles_missing_optional_fields(self):
        """Works with minimal story context."""
        minimal_story = StoryContext(
            story_id="456",
            title="Minimal Story",
            description="",
            column="Backlog",
        )

        messages = build_comment_context_prompt(
            "@hermes help",
            minimal_story,
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "456" in messages[0]["content"]


class TestFormatAgentResponse:
    """Tests for format_agent_response function."""

    def test_adds_agent_badge(self):
        """Response includes robot emoji and agent name."""
        formatted = format_agent_response("Hello!", "Hermes")

        assert formatted.startswith("🤖 **Hermes**")
        assert "Hello!" in formatted

    def test_preserves_reply_content(self):
        """Original reply content is preserved."""
        reply = "This is a multi-line\nresponse with **markdown**."
        formatted = format_agent_response(reply, "Hermes")

        assert reply in formatted

    def test_custom_agent_name(self):
        """Works with custom agent names."""
        formatted = format_agent_response("Hi", "CustomAgent")

        assert "**CustomAgent**" in formatted

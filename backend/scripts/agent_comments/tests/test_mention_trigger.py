"""
Test AIC-01: Comments with @agent mention trigger agent notification
"""

import pytest
from ..mention_parser import (
    parse_mentions,
    extract_agent_name,
    is_agent_mentioned,
    get_mentioned_agents,
    Mention,
)


class TestParseMentions:
    """Tests for parse_mentions function."""

    def test_single_mention(self):
        """Single @mention is detected."""
        text = "Hey @claude can you help?"
        mentions = parse_mentions(text)

        assert len(mentions) == 1
        assert mentions[0].agent_name == "claude"
        assert mentions[0].raw_text == "@claude"

    def test_multiple_mentions(self):
        """Multiple @mentions are detected."""
        text = "@claude and @gemini please review"
        mentions = parse_mentions(text)

        assert len(mentions) == 2
        assert mentions[0].agent_name == "claude"
        assert mentions[1].agent_name == "gemini"

    def test_no_mentions(self):
        """No mentions returns empty list."""
        text = "Just a regular comment"
        mentions = parse_mentions(text)

        assert len(mentions) == 0

    def test_mention_with_hyphen(self):
        """@mention with hyphen is detected."""
        text = "Ask @corey-coder for help"
        mentions = parse_mentions(text)

        assert len(mentions) == 1
        assert mentions[0].agent_name == "corey-coder"

    def test_mention_case_insensitive(self):
        """@mentions are case insensitive."""
        text = "@CLAUDE please help"
        mentions = parse_mentions(text)

        assert len(mentions) == 1
        assert mentions[0].agent_name == "claude"

    def test_mention_position_tracked(self):
        """Position of mention is tracked."""
        text = "Hello @claude"
        mentions = parse_mentions(text)

        assert mentions[0].position == 6  # After "Hello "


class TestExtractAgentName:
    """Tests for extract_agent_name function."""

    def test_known_agent(self):
        """Known agent name is extracted."""
        assert extract_agent_name("@claude help") == "claude"
        assert extract_agent_name("@gemini review") == "gemini"
        assert extract_agent_name("@codex check") == "codex"

    def test_unknown_agent(self):
        """Unknown agent returns None."""
        assert extract_agent_name("@unknown please") is None

    def test_partial_match(self):
        """Partial agent name matches."""
        assert extract_agent_name("@claude-opus help") == "claude"
        assert extract_agent_name("@corey-coder fix") == "corey-coder"

    def test_no_mention(self):
        """No mention returns None."""
        assert extract_agent_name("no mention here") is None


class TestIsAgentMentioned:
    """Tests for is_agent_mentioned function."""

    def test_agent_mentioned(self):
        """Returns True when agent is mentioned."""
        assert is_agent_mentioned("@claude help", "claude") is True
        assert is_agent_mentioned("hey @gemini", "gemini") is True

    def test_agent_not_mentioned(self):
        """Returns False when agent is not mentioned."""
        assert is_agent_mentioned("@claude help", "gemini") is False
        assert is_agent_mentioned("no mention", "claude") is False

    def test_partial_match(self):
        """Partial match works."""
        assert is_agent_mentioned("@claude-opus help", "claude") is True


class TestGetMentionedAgents:
    """Tests for get_mentioned_agents function."""

    def test_single_known_agent(self):
        """Single known agent returned."""
        agents = get_mentioned_agents("@claude help")
        assert agents == ["claude"]

    def test_multiple_known_agents(self):
        """Multiple known agents returned."""
        agents = get_mentioned_agents("@claude and @gemini")
        assert "claude" in agents
        assert "gemini" in agents

    def test_filters_unknown(self):
        """Unknown agents filtered out."""
        agents = get_mentioned_agents("@claude and @unknown")
        assert agents == ["claude"]

    def test_no_duplicates(self):
        """No duplicate agents returned."""
        agents = get_mentioned_agents("@claude @claude @claude")
        assert agents == ["claude"]


class TestHermesMention:
    """Tests for hermes agent mention detection (AC-MP-01, AC-MP-02)."""

    def test_hermes_extract_agent_name(self):
        """AC-MP-01: extract_agent_name('@hermes help') returns 'hermes'."""
        assert extract_agent_name("@hermes help") == "hermes"
        assert extract_agent_name("@hermes can you hear me") == "hermes"
        assert extract_agent_name("Hey @hermes, what's up?") == "hermes"

    def test_hermes_is_mentioned(self):
        """AC-MP-02: is_agent_mentioned works for hermes."""
        assert is_agent_mentioned("@hermes help", "hermes") is True
        assert is_agent_mentioned("hermes can you hear me", "hermes") is False  # No @
        assert is_agent_mentioned("@HERMES please respond", "hermes") is True  # Case insensitive

    def test_hermes_in_get_mentioned_agents(self):
        """Hermes appears in get_mentioned_agents output."""
        agents = get_mentioned_agents("@hermes and @claude")
        assert "hermes" in agents
        assert "claude" in agents

    def test_hermes_parse_mentions(self):
        """Hermes appears in parse_mentions output."""
        mentions = parse_mentions("@hermes can you hear me")
        assert len(mentions) == 1
        assert mentions[0].agent_name == "hermes"
        assert mentions[0].raw_text == "@hermes"

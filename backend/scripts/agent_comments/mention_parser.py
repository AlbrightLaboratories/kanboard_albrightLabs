"""
Mention Parser - Detects @mentions in comment text

Implements AIC-01: Comments with @agent mention trigger agent notification
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Mention:
    """Represents a detected @mention in comment text."""
    agent_name: str
    position: int
    raw_text: str


# Known agent types that can be mentioned
KNOWN_AGENTS = {
    "claude": "claude",
    "gemini": "gemini",
    "codex": "codex",
    "corey": "corey",
    "corey-coder": "corey-coder",
}

# Regex pattern for @mentions
MENTION_PATTERN = re.compile(r"@(\w+[-\w]*)", re.IGNORECASE)


def parse_mentions(text: str) -> List[Mention]:
    """
    Parse all @mentions from comment text.

    Args:
        text: The comment text to parse

    Returns:
        List of Mention objects found in the text
    """
    mentions = []

    for match in MENTION_PATTERN.finditer(text):
        agent_name = match.group(1).lower()
        mentions.append(Mention(
            agent_name=agent_name,
            position=match.start(),
            raw_text=match.group(0),
        ))

    return mentions


def extract_agent_name(text: str) -> Optional[str]:
    """
    Extract the first known agent name from text.

    Args:
        text: The comment text to search

    Returns:
        Agent name if found, None otherwise
    """
    mentions = parse_mentions(text)

    for mention in mentions:
        # Check if it's a known agent
        if mention.agent_name in KNOWN_AGENTS:
            return KNOWN_AGENTS[mention.agent_name]

        # Check partial matches (e.g., "claude-opus" matches "claude")
        for known, canonical in KNOWN_AGENTS.items():
            if mention.agent_name.startswith(known):
                return canonical

    return None


def is_agent_mentioned(text: str, agent_name: str) -> bool:
    """
    Check if a specific agent is mentioned in text.

    Args:
        text: The comment text to search
        agent_name: The agent name to look for

    Returns:
        True if the agent is mentioned
    """
    mentions = parse_mentions(text)
    agent_lower = agent_name.lower()

    return any(
        m.agent_name == agent_lower or m.agent_name.startswith(agent_lower)
        for m in mentions
    )


def get_mentioned_agents(text: str) -> List[str]:
    """
    Get all known agents mentioned in text.

    Args:
        text: The comment text to search

    Returns:
        List of canonical agent names mentioned
    """
    mentions = parse_mentions(text)
    found_agents = []

    for mention in mentions:
        if mention.agent_name in KNOWN_AGENTS:
            canonical = KNOWN_AGENTS[mention.agent_name]
            if canonical not in found_agents:
                found_agents.append(canonical)

    return found_agents

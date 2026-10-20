"""
Commit Linker

Links commits to stories and validates commit message format.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CommitInfo:
    """Information about a linked commit."""

    sha: str
    message: str
    story_id: Optional[int] = None
    valid_format: bool = False
    commit_type: Optional[str] = None
    scope: Optional[str] = None


class CommitLinker:
    """Links commits to stories using conventional commit format."""

    # Valid commit types per conventional commits
    VALID_TYPES = {
        "feat",
        "fix",
        "chore",
        "docs",
        "refactor",
        "test",
        "style",
        "ci",
        "build",
        "perf",
    }

    # Pattern for TOC format: type(scope): description
    TOC_PATTERN = re.compile(
        r"^(?P<type>\w+)\((?P<scope>[^)]+)\):\s+(?P<description>.+)",
        re.IGNORECASE
    )

    # Pattern to extract story ID from scope: US-123 or #123
    STORY_ID_PATTERN = re.compile(
        r"(?:US[-_]?)?(\d+)",
        re.IGNORECASE
    )

    def __init__(self) -> None:
        """Initialize commit linker."""
        self._linked_commits: Dict[int, List[CommitInfo]] = {}

    def parse_commit(self, sha: str, message: str) -> CommitInfo:
        """
        Parse a commit message and extract information.

        Args:
            sha: Commit SHA
            message: Commit message (first line)

        Returns:
            CommitInfo with parsed data
        """
        # Get first line only
        first_line = message.split("\n")[0].strip()

        info = CommitInfo(sha=sha, message=first_line)

        # Try to match TOC pattern
        match = self.TOC_PATTERN.match(first_line)
        if match:
            info.commit_type = match.group("type").lower()
            info.scope = match.group("scope")

            # Check if type is valid
            if info.commit_type in self.VALID_TYPES:
                info.valid_format = True

            # Try to extract story ID from scope
            story_match = self.STORY_ID_PATTERN.search(info.scope)
            if story_match:
                try:
                    info.story_id = int(story_match.group(1))
                except ValueError:
                    pass

        return info

    def validate_format(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Validate commit message follows TOC format.

        Args:
            message: Commit message

        Returns:
            Tuple of (is_valid, error_message)
        """
        first_line = message.split("\n")[0].strip()

        if not first_line:
            return False, "Empty commit message"

        match = self.TOC_PATTERN.match(first_line)
        if not match:
            return False, "Message does not follow 'type(scope): description' format"

        commit_type = match.group("type").lower()
        if commit_type not in self.VALID_TYPES:
            valid_types = ", ".join(sorted(self.VALID_TYPES))
            return False, f"Invalid type '{commit_type}'. Valid types: {valid_types}"

        description = match.group("description")
        if len(description) < 5:
            return False, "Description too short (minimum 5 characters)"

        return True, None

    def format_commit_message(
        self,
        story_id: int,
        commit_type: str,
        description: str,
        additional_scope: Optional[str] = None
    ) -> str:
        """
        Format a commit message for a story.

        Args:
            story_id: Story ID
            commit_type: Type (feat, fix, etc.)
            description: Commit description
            additional_scope: Optional additional scope info

        Returns:
            Formatted commit message
        """
        scope = f"US-{story_id}"
        if additional_scope:
            scope = f"{scope} {additional_scope}"

        return f"{commit_type}({scope}): {description}"

    def link_commit(self, story_id: int, commit: CommitInfo) -> None:
        """
        Link a commit to a story.

        Args:
            story_id: Story ID
            commit: CommitInfo to link
        """
        commit.story_id = story_id
        if story_id not in self._linked_commits:
            self._linked_commits[story_id] = []
        self._linked_commits[story_id].append(commit)

    def get_commits_for_story(self, story_id: int) -> List[CommitInfo]:
        """Get all commits linked to a story."""
        return self._linked_commits.get(story_id, [])

    def find_story_in_message(self, message: str) -> Optional[int]:
        """
        Find story ID in a commit message.

        Args:
            message: Commit message

        Returns:
            Story ID if found, None otherwise
        """
        info = self.parse_commit("", message)
        return info.story_id

    def format_toc_entry(self, commit: CommitInfo) -> str:
        """
        Format commit info as a TOC entry.

        Args:
            commit: CommitInfo

        Returns:
            TOC-formatted string
        """
        sha_short = commit.sha[:8] if len(commit.sha) >= 8 else commit.sha
        return f"- [{sha_short}] {commit.message}"

    def get_story_toc_entries(self, story_id: int) -> List[str]:
        """
        Get all TOC entries for a story's commits.

        Args:
            story_id: Story ID

        Returns:
            List of formatted TOC entries
        """
        commits = self.get_commits_for_story(story_id)
        return [self.format_toc_entry(c) for c in commits]

    def clear_links(self, story_id: Optional[int] = None) -> None:
        """
        Clear commit links.

        Args:
            story_id: Optional story ID (clears all if None)
        """
        if story_id:
            self._linked_commits.pop(story_id, None)
        else:
            self._linked_commits.clear()

"""
TOC Comment Poster

Posts completion comments to the Master TOC (issue #17).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TOCComment:
    """Represents a comment to post to the TOC."""

    story_id: int
    title: str
    summary: str
    commit_links: List[str]
    status: str = "pending"  # pending, posted, failed
    error: Optional[str] = None


class TOCCommentPoster:
    """Posts completion comments to the Master TOC issue."""

    # Master TOC issue location
    TOC_REPO = "AlbrightLaboratories/daxxon-ai-gpu-01"
    TOC_ISSUE_NUMBER = 17

    def __init__(
        self,
        repo: Optional[str] = None,
        issue_number: Optional[int] = None
    ) -> None:
        """
        Initialize TOC poster.

        Args:
            repo: Repository containing TOC issue (default: AlbrightLaboratories/daxxon-ai-gpu-01)
            issue_number: TOC issue number (default: 17)
        """
        self.repo = repo or self.TOC_REPO
        self.issue_number = issue_number or self.TOC_ISSUE_NUMBER
        self._gh_authenticated: Optional[bool] = None

    def check_gh_auth(self) -> bool:
        """Check if gh CLI is authenticated."""
        if self._gh_authenticated is not None:
            return self._gh_authenticated

        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._gh_authenticated = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._gh_authenticated = False

        return self._gh_authenticated

    def post_completion(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        commits: Optional[List[Dict[str, str]]] = None
    ) -> TOCComment:
        """
        Post story completion comment to the Master TOC.

        Args:
            story_id: Story ID
            story_data: Story data dict
            commits: Optional list of commit dicts with sha and message

        Returns:
            TOCComment with post status
        """
        title = story_data.get("title", f"Story #{story_id}")
        summary = self._build_summary(story_data)
        commit_links = self._extract_commit_links(commits or [])

        comment = TOCComment(
            story_id=story_id,
            title=title,
            summary=summary,
            commit_links=commit_links
        )

        # Check auth
        if not self.check_gh_auth():
            comment.status = "failed"
            comment.error = "GitHub CLI not authenticated"
            return comment

        # Build and post comment
        try:
            body = self._build_comment_body(comment)
            self._post_to_github(body)
            comment.status = "posted"
        except Exception as e:
            comment.status = "failed"
            comment.error = str(e)

        return comment

    def _build_summary(self, story_data: Dict[str, Any]) -> str:
        """Build a brief summary from story data."""
        description = story_data.get("description", "")

        # Use first sentence or first 200 chars
        if description:
            # Try to find first sentence
            sentences = description.split(".")
            if sentences:
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 200:
                    return first_sentence[:200] + "..."
                return first_sentence + ("." if first_sentence else "")

        # Fallback to title
        return story_data.get("title", "Story completed")

    def _extract_commit_links(
        self,
        commits: List[Dict[str, str]]
    ) -> List[str]:
        """Extract formatted commit links."""
        links = []
        for commit in commits:
            sha = commit.get("sha", "")[:8]
            message = commit.get("message", "").split("\n")[0][:60]
            if sha:
                links.append(f"[{sha}] {message}")
        return links

    def _build_comment_body(self, comment: TOCComment) -> str:
        """Build the comment body for the TOC issue."""
        body = f"**Completed: {comment.title}**\n\n"
        body += f"- Story: #{comment.story_id}\n"
        body += f"- Summary: {comment.summary}\n"

        if comment.commit_links:
            body += "\n**Commits:**\n"
            for link in comment.commit_links:
                body += f"- {link}\n"

        return body

    def _post_to_github(self, body: str) -> None:
        """Post comment to GitHub issue using gh CLI."""
        cmd = [
            "gh", "issue", "comment",
            str(self.issue_number),
            "--repo", self.repo,
            "--body", body
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to post comment: {result.stderr or 'Unknown error'}"
            )

    def format_toc_entry(
        self,
        story_id: int,
        title: str
    ) -> str:
        """
        Format a TOC entry for the story.

        Args:
            story_id: Story ID
            title: Story title

        Returns:
            Formatted TOC entry string
        """
        return f"feat(US-{story_id}): {title}"

    def validate_commit_format(self, commit_message: str) -> bool:
        """
        Validate commit message follows TOC format.

        Expected format: type(scope): description
        Examples:
            - feat(US-123): Add new feature
            - fix(US-456): Fix bug
            - chore(US-789): Update dependencies

        Args:
            commit_message: Commit message to validate

        Returns:
            True if format is valid
        """
        import re

        # Pattern: type(scope): description
        pattern = r"^(feat|fix|chore|docs|refactor|test|style|ci|build)\([^)]+\):\s+.+"

        return bool(re.match(pattern, commit_message, re.IGNORECASE))

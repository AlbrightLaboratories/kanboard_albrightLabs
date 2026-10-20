"""
Test TI-02: Comment includes story title, summary, commit links
"""
import pytest
from unittest.mock import patch, MagicMock
from ..comment_poster import TOCCommentPoster, TOCComment


class TestCommentFormat:
    """Test comment body formatting."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.poster = TOCCommentPoster()
        self.story_id = 456
        self.story_data = {
            "title": "Add user authentication",
            "description": "Implement OAuth2 login flow with JWT tokens. "
                          "Support Google and GitHub providers."
        }
        self.commits = [
            {"sha": "abc12345678", "message": "feat(US-456): Add OAuth2 config"},
            {"sha": "def98765432", "message": "feat(US-456): Implement JWT tokens"},
        ]

    def test_comment_includes_story_title(self) -> None:
        """Verify comment body includes the story title."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        # Build the comment body to check
        body = self.poster._build_comment_body(result)
        assert "Add user authentication" in body

    def test_comment_includes_summary(self) -> None:
        """Verify comment body includes summary from description."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        body = self.poster._build_comment_body(result)
        # Summary should be first sentence of description
        assert "Implement OAuth2 login flow with JWT tokens" in body

    def test_comment_includes_commit_links(self) -> None:
        """Verify comment body includes commit links."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data,
                commits=self.commits
            )

        body = self.poster._build_comment_body(result)
        # Should include shortened SHA and message
        assert "abc12345" in body
        assert "def98765" in body
        assert "Add OAuth2 config" in body
        assert "Implement JWT tokens" in body

    def test_comment_has_completed_header(self) -> None:
        """Verify comment starts with Completed header."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        body = self.poster._build_comment_body(result)
        assert "**Completed:" in body

    def test_comment_includes_story_id_reference(self) -> None:
        """Verify comment includes story ID reference."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        body = self.poster._build_comment_body(result)
        assert f"#{self.story_id}" in body or f"Story: #{self.story_id}" in body

    def test_summary_truncates_long_description(self) -> None:
        """Verify long descriptions are truncated in summary."""
        long_desc = "A" * 300  # 300 characters
        story_data = {
            "title": "Test Story",
            "description": long_desc
        }

        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                story_data
            )

        # Summary should be truncated
        assert len(result.summary) <= 203  # 200 + "..."

    def test_summary_uses_title_when_no_description(self) -> None:
        """Verify summary falls back to title when no description."""
        story_data = {
            "title": "Simple Story Title",
            "description": ""
        }

        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                story_data
            )

        assert result.summary == "Simple Story Title"

    def test_commit_links_section_only_when_commits_present(self) -> None:
        """Verify Commits section only appears when commits provided."""
        # Without commits
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result_no_commits = self.poster.post_completion(
                self.story_id,
                self.story_data,
                commits=None
            )

        body_no_commits = self.poster._build_comment_body(result_no_commits)
        assert "**Commits:**" not in body_no_commits

        # With commits
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result_with_commits = self.poster.post_completion(
                self.story_id,
                self.story_data,
                commits=self.commits
            )

        body_with_commits = self.poster._build_comment_body(result_with_commits)
        assert "**Commits:**" in body_with_commits

    def test_commit_message_truncates_long_messages(self) -> None:
        """Verify long commit messages are truncated."""
        commits = [
            {"sha": "abc12345678", "message": "A" * 100}  # 100 chars
        ]

        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data,
                commits=commits
            )

        # Commit links should have truncated messages
        for link in result.commit_links:
            # SHA (8) + space + message should be reasonable length
            assert len(link) <= 80  # 8 for sha + space + up to 60 for message + brackets


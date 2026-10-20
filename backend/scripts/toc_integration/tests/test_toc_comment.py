"""
Test TI-01: Story completion posts comment to issue #17
"""
import pytest
from unittest.mock import patch, MagicMock
from ..comment_poster import TOCCommentPoster, TOCComment


class TestTOCComment:
    """Test posting completion comments to Master TOC."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.poster = TOCCommentPoster()
        self.story_id = 123
        self.story_data = {
            "title": "Implement feature X",
            "description": "Add feature X with full test coverage"
        }

    def test_post_completion_returns_toc_comment(self) -> None:
        """Verify post_completion returns TOCComment."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        assert isinstance(result, TOCComment)
        assert result.story_id == self.story_id

    def test_post_completion_extracts_title(self) -> None:
        """Verify title is extracted from story data."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        assert result.title == "Implement feature X"

    def test_toc_repo_is_correct(self) -> None:
        """Verify TOC repo is AlbrightLaboratories/daxxon-ai-gpu-01."""
        assert self.poster.repo == "AlbrightLaboratories/daxxon-ai-gpu-01"

    def test_toc_issue_is_17(self) -> None:
        """Verify TOC issue number is 17."""
        assert self.poster.issue_number == 17

    def test_fails_without_gh_auth(self) -> None:
        """Verify posting fails without gh authentication."""
        with patch.object(self.poster, 'check_gh_auth', return_value=False):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        assert result.status == "failed"
        assert "not authenticated" in result.error.lower()

    @patch('subprocess.run')
    def test_posts_to_github_on_success(self, mock_run: MagicMock) -> None:
        """Verify comment is posted to GitHub on success."""
        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(self.poster, 'check_gh_auth', return_value=True):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        assert result.status == "posted"
        mock_run.assert_called()
        call_args = mock_run.call_args
        assert "issue" in call_args[0][0]
        assert "comment" in call_args[0][0]

    @patch('subprocess.run')
    def test_posts_to_issue_17(self, mock_run: MagicMock) -> None:
        """Verify comment is posted to issue 17."""
        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(self.poster, 'check_gh_auth', return_value=True):
            self.poster.post_completion(self.story_id, self.story_data)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "17" in cmd

    @patch('subprocess.run')
    def test_posts_to_correct_repo(self, mock_run: MagicMock) -> None:
        """Verify comment is posted to correct repo."""
        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(self.poster, 'check_gh_auth', return_value=True):
            self.poster.post_completion(self.story_id, self.story_data)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "AlbrightLaboratories/daxxon-ai-gpu-01" in cmd

    @patch('subprocess.run')
    def test_custom_repo_used_if_provided(self, mock_run: MagicMock) -> None:
        """Verify custom repo is used if provided."""
        mock_run.return_value = MagicMock(returncode=0)
        poster = TOCCommentPoster(repo="custom/repo", issue_number=42)

        with patch.object(poster, 'check_gh_auth', return_value=True):
            poster.post_completion(self.story_id, self.story_data)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "custom/repo" in cmd
        assert "42" in cmd

    @patch('subprocess.run')
    def test_handles_post_error(self, mock_run: MagicMock) -> None:
        """Verify posting handles errors gracefully."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="API error"
        )

        with patch.object(self.poster, 'check_gh_auth', return_value=True):
            result = self.poster.post_completion(
                self.story_id,
                self.story_data
            )

        assert result.status == "failed"
        assert result.error is not None

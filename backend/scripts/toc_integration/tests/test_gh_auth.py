"""
Test TI-04: gh CLI authentication works from cluster
"""
import pytest
from unittest.mock import patch, MagicMock
import subprocess
from ..comment_poster import TOCCommentPoster


class TestGhAuth:
    """Test GitHub CLI authentication handling."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.poster = TOCCommentPoster()

    @patch('subprocess.run')
    def test_check_gh_auth_returns_true_when_authenticated(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify check_gh_auth returns True when gh is authenticated."""
        mock_run.return_value = MagicMock(returncode=0)

        # Reset cached value
        self.poster._gh_authenticated = None

        result = self.poster.check_gh_auth()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "gh" in call_args
        assert "auth" in call_args
        assert "status" in call_args

    @patch('subprocess.run')
    def test_check_gh_auth_returns_false_when_not_authenticated(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify check_gh_auth returns False when gh is not authenticated."""
        mock_run.return_value = MagicMock(returncode=1)

        # Reset cached value
        self.poster._gh_authenticated = None

        result = self.poster.check_gh_auth()

        assert result is False

    @patch('subprocess.run')
    def test_check_gh_auth_handles_timeout(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify check_gh_auth handles timeout gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["gh", "auth", "status"],
            timeout=10
        )

        # Reset cached value
        self.poster._gh_authenticated = None

        result = self.poster.check_gh_auth()

        assert result is False

    @patch('subprocess.run')
    def test_check_gh_auth_handles_missing_gh_cli(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify check_gh_auth handles missing gh CLI."""
        mock_run.side_effect = FileNotFoundError(
            "gh command not found"
        )

        # Reset cached value
        self.poster._gh_authenticated = None

        result = self.poster.check_gh_auth()

        assert result is False

    @patch('subprocess.run')
    def test_check_gh_auth_caches_result(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify check_gh_auth caches authentication result."""
        mock_run.return_value = MagicMock(returncode=0)

        # Reset cached value
        self.poster._gh_authenticated = None

        # First call
        result1 = self.poster.check_gh_auth()
        # Second call (should use cache)
        result2 = self.poster.check_gh_auth()

        assert result1 is True
        assert result2 is True
        # Should only be called once due to caching
        assert mock_run.call_count == 1

    @patch('subprocess.run')
    def test_post_completion_requires_auth(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify post_completion fails without authentication."""
        # Set up mock to show not authenticated
        mock_run.return_value = MagicMock(returncode=1)

        # Reset cached value
        self.poster._gh_authenticated = None

        result = self.poster.post_completion(
            story_id=123,
            story_data={"title": "Test Story"}
        )

        assert result.status == "failed"
        assert "not authenticated" in result.error.lower()

    @patch('subprocess.run')
    def test_post_to_github_uses_correct_command(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify _post_to_github uses correct gh command."""
        mock_run.return_value = MagicMock(returncode=0)

        self.poster._post_to_github("Test comment body")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        # Should use gh issue comment
        assert "gh" in call_args
        assert "issue" in call_args
        assert "comment" in call_args

        # Should include issue number
        assert str(self.poster.issue_number) in call_args

        # Should include repo
        assert "--repo" in call_args
        assert self.poster.repo in call_args

        # Should include body
        assert "--body" in call_args

    @patch('subprocess.run')
    def test_post_to_github_raises_on_failure(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify _post_to_github raises error on failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="API rate limit exceeded"
        )

        with pytest.raises(RuntimeError) as exc_info:
            self.poster._post_to_github("Test comment body")

        assert "Failed to post comment" in str(exc_info.value)

    @patch('subprocess.run')
    def test_post_to_github_has_timeout(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify _post_to_github has reasonable timeout."""
        mock_run.return_value = MagicMock(returncode=0)

        self.poster._post_to_github("Test comment body")

        # Check timeout was set in call
        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] >= 10  # At least 10 seconds

    @patch('subprocess.run')
    def test_check_auth_uses_timeout(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify check_gh_auth uses timeout."""
        mock_run.return_value = MagicMock(returncode=0)

        # Reset cached value
        self.poster._gh_authenticated = None

        self.poster.check_gh_auth()

        # Check timeout was set in call
        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs

    @patch('subprocess.run')
    def test_full_auth_flow_success(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify full authentication and posting flow works."""
        # All subprocess calls succeed
        mock_run.return_value = MagicMock(returncode=0)

        # Reset cached value
        self.poster._gh_authenticated = None

        result = self.poster.post_completion(
            story_id=789,
            story_data={
                "title": "Complete authentication feature",
                "description": "Full OAuth2 implementation"
            }
        )

        assert result.status == "posted"
        assert result.error is None
        # Should have called for auth check and for posting
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_custom_repo_and_issue_used(
        self,
        mock_run: MagicMock
    ) -> None:
        """Verify custom repo and issue number are used in gh command."""
        mock_run.return_value = MagicMock(returncode=0)

        custom_poster = TOCCommentPoster(
            repo="MyOrg/my-repo",
            issue_number=42
        )
        custom_poster._gh_authenticated = True  # Skip auth check

        custom_poster.post_completion(
            story_id=123,
            story_data={"title": "Test"}
        )

        call_args = mock_run.call_args[0][0]
        assert "MyOrg/my-repo" in call_args
        assert "42" in call_args


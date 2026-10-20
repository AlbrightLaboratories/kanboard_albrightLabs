"""
Test VW-01: Story entering Validation column triggers GitHub workflow
Test VW-02: Workflow checks out correct repo + branch from story
"""
import pytest
from unittest.mock import patch, MagicMock
from ..trigger import ValidationTrigger, WorkflowTriggerResult


class TestValidationTrigger:
    """Test validation workflow triggering."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.trigger = ValidationTrigger()
        self.story_data = {
            "id": 123,
            "title": "Test Story",
            "linked_repo": "https://github.com/AlbrightLaboratories/test-repo",
            "linked_branch": "feature/test",
            "linked_pr": "https://github.com/AlbrightLaboratories/test-repo/pull/42"
        }

    def test_trigger_returns_result(self) -> None:
        """Verify trigger returns WorkflowTriggerResult."""
        with patch.object(self.trigger, 'check_gh_auth', return_value=False):
            result = self.trigger.trigger_validation(123, self.story_data)

        assert isinstance(result, WorkflowTriggerResult)
        assert result.story_id == 123

    def test_trigger_fails_without_auth(self) -> None:
        """Verify trigger fails if gh not authenticated."""
        with patch.object(self.trigger, 'check_gh_auth', return_value=False):
            result = self.trigger.trigger_validation(123, self.story_data)

        assert result.status == "failed"
        assert "not authenticated" in result.error.lower()

    def test_trigger_extracts_repo(self) -> None:
        """Verify trigger extracts repo from story data."""
        with patch.object(self.trigger, 'check_gh_auth', return_value=False):
            result = self.trigger.trigger_validation(123, self.story_data)

        assert result.repo == "AlbrightLaboratories/test-repo"

    def test_trigger_extracts_branch(self) -> None:
        """Verify trigger extracts branch from story data."""
        with patch.object(self.trigger, 'check_gh_auth', return_value=False):
            result = self.trigger.trigger_validation(123, self.story_data)

        assert result.branch == "feature/test"

    def test_normalize_repo_url(self) -> None:
        """Verify repo URL normalization."""
        # Full URL
        result = self.trigger._normalize_repo(
            "https://github.com/AlbrightLaboratories/test-repo"
        )
        assert result == "AlbrightLaboratories/test-repo"

        # URL with .git
        result = self.trigger._normalize_repo(
            "https://github.com/AlbrightLaboratories/test-repo.git"
        )
        assert result == "AlbrightLaboratories/test-repo"

        # Already normalized
        result = self.trigger._normalize_repo("owner/repo")
        assert result == "owner/repo"

    def test_extract_checkout_info(self) -> None:
        """Verify checkout info extraction."""
        info = self.trigger.extract_checkout_info(self.story_data)

        assert info["repo"] == "AlbrightLaboratories/test-repo"
        assert info["branch"] == "feature/test"
        assert info["pr_number"] == "42"
        assert "pull/42" in info["ref"]

    def test_extract_checkout_info_no_pr(self) -> None:
        """Verify checkout info without PR."""
        story_data = {
            "linked_repo": "https://github.com/owner/repo",
            "linked_branch": "main"
        }
        info = self.trigger.extract_checkout_info(story_data)

        assert info["branch"] == "main"
        assert info["pr_number"] == ""
        assert "heads/main" in info["ref"]

    def test_can_validate_with_required_fields(self) -> None:
        """Verify can_validate returns True with required fields."""
        can_validate, missing = self.trigger.can_validate(self.story_data)

        assert can_validate is True
        assert len(missing) == 0

    def test_can_validate_missing_repo(self) -> None:
        """Verify can_validate returns False without repo."""
        story_data = {"linked_branch": "main"}
        can_validate, missing = self.trigger.can_validate(story_data)

        assert can_validate is False
        assert "linked_repo" in missing

    def test_can_validate_missing_branch(self) -> None:
        """Verify can_validate returns False without branch."""
        story_data = {"linked_repo": "owner/repo"}
        can_validate, missing = self.trigger.can_validate(story_data)

        assert can_validate is False
        assert "linked_branch" in missing

    @patch('subprocess.run')
    def test_check_gh_auth_success(self, mock_run: MagicMock) -> None:
        """Verify gh auth check succeeds."""
        mock_run.return_value = MagicMock(returncode=0)
        trigger = ValidationTrigger()

        result = trigger.check_gh_auth()

        assert result is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_check_gh_auth_failure(self, mock_run: MagicMock) -> None:
        """Verify gh auth check fails."""
        mock_run.return_value = MagicMock(returncode=1)
        trigger = ValidationTrigger()

        result = trigger.check_gh_auth()

        assert result is False

    def test_default_repo_used_when_missing(self) -> None:
        """Verify default repo is used when not in story."""
        story_data = {"linked_branch": "main"}
        with patch.object(self.trigger, 'check_gh_auth', return_value=False):
            result = self.trigger.trigger_validation(123, story_data)

        assert result.repo == self.trigger.default_repo

    def test_uses_repo_url_if_linked_repo_missing(self) -> None:
        """Verify repo_url is used as fallback."""
        story_data = {
            "repo_url": "https://github.com/fallback/repo",
            "branch": "develop"
        }
        with patch.object(self.trigger, 'check_gh_auth', return_value=False):
            result = self.trigger.trigger_validation(123, story_data)

        assert result.repo == "fallback/repo"
        assert result.branch == "develop"

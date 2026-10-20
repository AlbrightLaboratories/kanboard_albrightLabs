"""
Test VW-02: Workflow checks out correct repo + branch from story
"""
import pytest
from ..trigger import ValidationTrigger


class TestCheckout:
    """Test checkout info extraction for workflows."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.trigger = ValidationTrigger()

    def test_extract_repo_from_full_url(self) -> None:
        """Verify repo extracted from full GitHub URL."""
        story_data = {
            "linked_repo": "https://github.com/AlbrightLaboratories/kanboard_albrightLabs",
            "linked_branch": "main"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["repo"] == "AlbrightLaboratories/kanboard_albrightLabs"

    def test_extract_branch_from_story(self) -> None:
        """Verify branch extracted from story data."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "feature/new-feature"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["branch"] == "feature/new-feature"

    def test_extract_pr_number_from_url(self) -> None:
        """Verify PR number extracted from PR URL."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "feature/test",
            "linked_pr": "https://github.com/owner/repo/pull/42"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["pr_number"] == "42"

    def test_ref_for_branch(self) -> None:
        """Verify ref format for branch checkout."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "develop"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["ref"] == "refs/heads/develop"

    def test_ref_for_pr(self) -> None:
        """Verify ref format for PR checkout."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "feature/test",
            "linked_pr": "https://github.com/owner/repo/pull/123"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["ref"] == "refs/pull/123/merge"

    def test_handles_repo_url_fallback(self) -> None:
        """Verify repo_url used as fallback."""
        story_data = {
            "repo_url": "https://github.com/fallback/repo",
            "branch": "staging"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["repo"] == "fallback/repo"
        assert info["branch"] == "staging"

    def test_default_branch_is_main(self) -> None:
        """Verify default branch is main."""
        story_data = {
            "linked_repo": "owner/repo"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["branch"] == "main"

    def test_handles_git_suffix(self) -> None:
        """Verify .git suffix is stripped."""
        story_data = {
            "linked_repo": "https://github.com/owner/repo.git",
            "linked_branch": "main"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["repo"] == "owner/repo"
        assert ".git" not in info["repo"]

    def test_handles_trailing_slash(self) -> None:
        """Verify trailing slash is handled."""
        story_data = {
            "linked_repo": "https://github.com/owner/repo/",
            "linked_branch": "main"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["repo"] == "owner/repo"

    def test_handles_complex_pr_url(self) -> None:
        """Verify complex PR URL parsing."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "feature/test",
            "linked_pr": "https://github.com/owner/repo/pull/999/files"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["pr_number"] == "999"

    def test_empty_pr_number_for_no_pr(self) -> None:
        """Verify empty PR number when no PR linked."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "main"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["pr_number"] == ""

    def test_empty_repo_handled(self) -> None:
        """Verify empty repo is handled gracefully."""
        story_data = {
            "linked_branch": "main"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert info["repo"] == ""

    def test_all_fields_returned(self) -> None:
        """Verify all required fields are returned."""
        story_data = {
            "linked_repo": "owner/repo",
            "linked_branch": "develop",
            "linked_pr": "https://github.com/owner/repo/pull/50"
        }

        info = self.trigger.extract_checkout_info(story_data)

        assert "repo" in info
        assert "branch" in info
        assert "pr_number" in info
        assert "ref" in info

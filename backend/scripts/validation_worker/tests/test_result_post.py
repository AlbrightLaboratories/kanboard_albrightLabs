"""
Test VW-05: Validation result posted back to Kanboard API
"""
import pytest
from unittest.mock import MagicMock
from ..result_handler import ValidationResultHandler, ValidationResult


class TestResultPost:
    """Test posting validation results to Kanboard."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.handler = ValidationResultHandler(kanboard_client=self.mock_client)
        self.story_id = 789

    def test_post_result_calls_add_comment(self) -> None:
        """Verify posting result adds comment to story."""
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0
        )

        self.handler.post_result_to_kanboard(result)

        self.mock_client.add_comment.assert_called_once()
        call_args = self.mock_client.add_comment.call_args
        assert call_args.kwargs["story_id"] == self.story_id

    def test_post_result_updates_story_status(self) -> None:
        """Verify posting result updates story status."""
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0
        )

        self.handler.post_result_to_kanboard(result)

        self.mock_client.update_story.assert_called_once()
        call_args = self.mock_client.update_story.call_args
        assert call_args.kwargs["validation_status"] == "passed"

    def test_post_failed_result_sets_failed_status(self) -> None:
        """Verify failed result sets failed validation status."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=85.0
        )

        self.handler.post_result_to_kanboard(result)

        call_args = self.mock_client.update_story.call_args
        assert call_args.kwargs["validation_status"] == "failed"

    def test_post_result_returns_true_on_success(self) -> None:
        """Verify post_result returns True on success."""
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0
        )

        success = self.handler.post_result_to_kanboard(result)

        assert success is True

    def test_post_result_returns_false_on_error(self) -> None:
        """Verify post_result returns False on error."""
        self.mock_client.add_comment.side_effect = Exception("API error")
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0
        )

        success = self.handler.post_result_to_kanboard(result)

        assert success is False

    def test_post_result_without_client_returns_false(self) -> None:
        """Verify post without client returns False."""
        handler = ValidationResultHandler()  # No client
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0
        )

        success = handler.post_result_to_kanboard(result)

        assert success is False

    def test_passed_comment_contains_passed(self) -> None:
        """Verify passed comment contains PASSED."""
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0
        )

        self.handler.post_result_to_kanboard(result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "PASSED" in comment

    def test_failed_comment_contains_issues(self) -> None:
        """Verify failed comment contains failure info."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["2 tests failed", "Coverage 70% below threshold"]
        )

        self.handler.post_result_to_kanboard(result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "FAILED" in comment
        assert "Issues Found" in comment

    def test_comment_includes_workflow_url(self) -> None:
        """Verify comment includes workflow URL."""
        result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0,
            workflow_run_url="https://github.com/owner/repo/actions/runs/123"
        )

        self.handler.post_result_to_kanboard(result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "actions/runs/123" in comment

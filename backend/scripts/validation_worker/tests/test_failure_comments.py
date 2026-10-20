"""
Test VW-07: Failed story carries failure comments for agent to read
"""
import pytest
from unittest.mock import MagicMock
from ..result_handler import ValidationResult
from ..rework_flow import ReworkFlow


class TestFailureComments:
    """Test failure comments added to stories."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.rework = ReworkFlow(kanboard_client=self.mock_client)
        self.story_id = 202

    def test_failure_comment_added(self) -> None:
        """Verify failure comment is added to story."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["Tests failed"]
        )

        action = self.rework.handle_failed_validation(
            self.story_id,
            result
        )

        self.mock_client.add_comment.assert_called()
        assert action.comment_added is True

    def test_comment_contains_rework_required(self) -> None:
        """Verify comment contains REWORK REQUIRED header."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["Tests failed"]
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "REWORK REQUIRED" in comment

    def test_comment_contains_failure_reasons(self) -> None:
        """Verify comment lists failure reasons."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["2 tests failed", "Coverage below 80%"]
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "2 tests failed" in comment
        assert "Coverage" in comment

    def test_comment_contains_test_summary(self) -> None:
        """Verify comment contains test summary table."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["Tests failed"]
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "Tests Passed" in comment
        assert "Tests Failed" in comment
        assert "Coverage" in comment

    def test_comment_contains_failure_log(self) -> None:
        """Verify comment contains failure log when available."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=85.0,
            failure_reasons=["Tests failed"],
            failure_log="AssertionError: Expected True, got False"
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "AssertionError" in comment

    def test_comment_contains_modularity_issues(self) -> None:
        """Verify comment contains modularity issues."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=10,
            tests_failed=0,
            coverage_percentage=85.0,
            failure_reasons=["Modularity violations"],
            modularity_issues=["big_file.py exceeds 200 LOC"]
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "big_file.py" in comment
        assert "200 LOC" in comment

    def test_comment_contains_next_steps(self) -> None:
        """Verify comment contains next steps guidance."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=85.0,
            failure_reasons=["Tests failed"]
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "Next Steps" in comment
        assert "Re-run TDD" in comment or "Submit for validation" in comment

    def test_comment_contains_workflow_url(self) -> None:
        """Verify comment links to workflow run."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=85.0,
            failure_reasons=["Tests failed"],
            workflow_run_url="https://github.com/owner/repo/actions/runs/12345"
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        assert "actions/runs/12345" in comment

    def test_long_failure_log_truncated(self) -> None:
        """Verify very long failure logs are truncated."""
        long_log = "X" * 5000  # 5000 chars
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=85.0,
            failure_reasons=["Tests failed"],
            failure_log=long_log
        )

        self.rework.handle_failed_validation(self.story_id, result)

        call_args = self.mock_client.add_comment.call_args
        comment = call_args.kwargs["content"]
        # Should contain truncated indicator
        assert "truncated" in comment.lower() or len(comment) < len(long_log) + 500

    def test_get_latest_failure_reasons(self) -> None:
        """Verify can get latest failure reasons."""
        result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["Tests failed", "Coverage low"]
        )

        self.rework.handle_failed_validation(self.story_id, result)

        reasons = self.rework.get_latest_failure_reasons(self.story_id)
        assert "Tests failed" in reasons
        assert "Coverage low" in reasons

    def test_no_failure_reasons_returns_empty(self) -> None:
        """Verify empty list returned if no rework history."""
        reasons = self.rework.get_latest_failure_reasons(999)
        assert reasons == []

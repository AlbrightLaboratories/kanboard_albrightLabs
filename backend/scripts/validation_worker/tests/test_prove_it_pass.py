"""
Test VW-03: prove-it runs: all tests pass = validation passed
"""
import pytest
from ..result_handler import ValidationResultHandler, ValidationResult


class TestProveItPass:
    """Test successful prove-it validation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.handler = ValidationResultHandler()
        self.story_id = 123

    def test_all_tests_pass_gives_passed_status(self) -> None:
        """Verify all tests passing gives passed status."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "passed"

    def test_passed_result_has_correct_counts(self) -> None:
        """Verify passed result has correct test counts."""
        raw_result = {
            "tests_passed": 25,
            "tests_failed": 0,
            "tests_skipped": 3,
            "coverage_percentage": 90.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.tests_passed == 25
        assert result.tests_failed == 0
        assert result.tests_skipped == 3

    def test_passed_result_has_no_failure_reasons(self) -> None:
        """Verify passed result has no failure reasons."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert len(result.failure_reasons) == 0

    def test_all_tests_pass_property(self) -> None:
        """Verify all_tests_pass property works."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.all_tests_pass is True

    def test_passed_with_skipped_still_passes(self) -> None:
        """Verify skipped tests don't affect pass status."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "tests_skipped": 5,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "passed"
        assert result.tests_skipped == 5

    def test_passed_summary_format(self) -> None:
        """Verify passed summary format."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.5
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert "PASSED" in result.summary
        assert "10 tests" in result.summary
        assert "85.5%" in result.summary

    def test_passed_stores_workflow_info(self) -> None:
        """Verify passed result stores workflow info."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.0,
            "run_id": "12345",
            "run_url": "https://github.com/owner/repo/actions/runs/12345"
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.workflow_run_id == "12345"
        assert "actions/runs/12345" in result.workflow_run_url

    def test_passed_stores_duration(self) -> None:
        """Verify passed result stores duration."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.0,
            "duration_seconds": 45.5
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.duration_seconds == 45.5

    def test_high_coverage_passes(self) -> None:
        """Verify 100% coverage passes."""
        raw_result = {
            "tests_passed": 50,
            "tests_failed": 0,
            "coverage_percentage": 100.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "passed"
        assert result.coverage_percentage == 100.0

    def test_exactly_80_coverage_passes(self) -> None:
        """Verify exactly 80% coverage passes."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 80.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "passed"

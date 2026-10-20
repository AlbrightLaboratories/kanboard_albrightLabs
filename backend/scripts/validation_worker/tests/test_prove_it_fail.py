"""
Test VW-04: prove-it runs: any test fails = validation failed with log
"""
import pytest
from ..result_handler import ValidationResultHandler, ValidationResult


class TestProveItFail:
    """Test failed prove-it validation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.handler = ValidationResultHandler()
        self.story_id = 456

    def test_failed_tests_gives_failed_status(self) -> None:
        """Verify any failed test gives failed status."""
        raw_result = {
            "tests_passed": 9,
            "tests_failed": 1,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "failed"

    def test_failed_result_has_failure_reasons(self) -> None:
        """Verify failed result includes failure reasons."""
        raw_result = {
            "tests_passed": 8,
            "tests_failed": 2,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert len(result.failure_reasons) > 0
        assert any("2 test" in reason for reason in result.failure_reasons)

    def test_failed_result_includes_failure_log(self) -> None:
        """Verify failed result includes failure log."""
        raw_result = {
            "tests_passed": 9,
            "tests_failed": 1,
            "coverage_percentage": 85.0,
            "failure_log": "AssertionError: Expected 5, got 3"
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.failure_log is not None
        assert "AssertionError" in result.failure_log

    def test_low_coverage_fails(self) -> None:
        """Verify coverage below 80% causes failure."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 75.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "failed"
        assert any("coverage" in reason.lower() for reason in result.failure_reasons)

    def test_modularity_issues_reported(self) -> None:
        """Verify modularity issues are included in result."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": 85.0,
            "modularity_issues": ["file.py exceeds 200 LOC"]
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert len(result.modularity_issues) > 0
        assert "200 LOC" in result.modularity_issues[0]

    def test_all_tests_pass_false_when_failed(self) -> None:
        """Verify all_tests_pass is False with failures."""
        raw_result = {
            "tests_passed": 9,
            "tests_failed": 1,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.all_tests_pass is False

    def test_failed_summary_format(self) -> None:
        """Verify failed summary format."""
        raw_result = {
            "tests_passed": 8,
            "tests_failed": 2,
            "coverage_percentage": 70.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert "FAILED" in result.summary
        assert "2/10" in result.summary  # 2 failed out of 10 total

    def test_multiple_failure_reasons(self) -> None:
        """Verify multiple failure reasons are captured."""
        raw_result = {
            "tests_passed": 8,
            "tests_failed": 2,
            "coverage_percentage": 70.0,
            "modularity_issues": ["big_file.py"]
        }

        result = self.handler.process_result(self.story_id, raw_result)

        # Should have failures for: tests failed, coverage, modularity
        assert len(result.failure_reasons) >= 2

    def test_zero_tests_passed_is_failure(self) -> None:
        """Verify zero passed tests is failure."""
        raw_result = {
            "tests_passed": 0,
            "tests_failed": 5,
            "coverage_percentage": 0.0
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.status == "failed"
        assert result.all_tests_pass is False

    def test_coverage_string_percentage_parsed(self) -> None:
        """Verify coverage string with % is parsed."""
        raw_result = {
            "tests_passed": 10,
            "tests_failed": 0,
            "coverage_percentage": "65.5%"
        }

        result = self.handler.process_result(self.story_id, raw_result)

        assert result.coverage_percentage == 65.5
        assert result.status == "failed"  # Below 80%

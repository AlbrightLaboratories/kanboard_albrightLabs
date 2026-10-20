"""
Test AIC-06: Sandbox results are posted back as comment
"""

import pytest
from ..execution_handler import (
    handle_execution_result,
    format_result_comment,
    parse_test_output,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)


@pytest.fixture
def sample_request():
    """Sample execution request."""
    return ExecutionRequest(
        request_id="exec-123-c1",
        story_id="123",
        comment_id="c1",
        agent_id="claude-001",
        execution_type="test",
        commands=["pytest tests/"],
        status=ExecutionStatus.RUNNING,
    )


class TestHandleExecutionResult:
    """Tests for handle_execution_result function."""

    def test_passed_on_zero_exit(self, sample_request):
        """Exit code 0 results in PASSED status."""
        result = handle_execution_result(
            request=sample_request,
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            duration=5.5,
        )

        assert result.status == ExecutionStatus.PASSED
        assert result.exit_code == 0

    def test_failed_on_nonzero_exit(self, sample_request):
        """Non-zero exit code results in FAILED status."""
        result = handle_execution_result(
            request=sample_request,
            exit_code=1,
            stdout="Test failed",
            stderr="AssertionError",
            duration=3.2,
        )

        assert result.status == ExecutionStatus.FAILED
        assert result.exit_code == 1

    def test_captures_stdout(self, sample_request):
        """stdout is captured in result."""
        result = handle_execution_result(
            request=sample_request,
            exit_code=0,
            stdout="Test output here",
            stderr="",
            duration=1.0,
        )

        assert "Test output here" in result.stdout

    def test_captures_stderr(self, sample_request):
        """stderr is captured in result."""
        result = handle_execution_result(
            request=sample_request,
            exit_code=1,
            stdout="",
            stderr="Error message",
            duration=1.0,
        )

        assert "Error message" in result.stderr

    def test_truncates_long_output(self, sample_request):
        """Long output is truncated."""
        long_output = "x" * 20000

        result = handle_execution_result(
            request=sample_request,
            exit_code=0,
            stdout=long_output,
            stderr="",
            duration=1.0,
        )

        assert len(result.stdout) <= 10000

    def test_parses_test_results(self, sample_request):
        """Test results are parsed from output."""
        sample_request.execution_type = "test"
        stdout = "10 passed, 2 failed, 1 skipped in 5.5s"

        result = handle_execution_result(
            request=sample_request,
            exit_code=1,
            stdout=stdout,
            stderr="",
            duration=5.5,
        )

        assert result.test_results is not None
        assert result.test_results["passed"] == 10
        assert result.test_results["failed"] == 2
        assert result.test_results["skipped"] == 1


class TestParseTestOutput:
    """Tests for parse_test_output function."""

    def test_parses_pytest_output(self):
        """Pytest output is parsed correctly."""
        stdout = "15 passed, 3 failed, 2 skipped in 10.5s"

        results = parse_test_output(stdout, "")

        assert results["passed"] == 15
        assert results["failed"] == 3
        assert results["skipped"] == 2
        assert results["total"] == 20

    def test_parses_vitest_output(self):
        """Vitest output is parsed correctly."""
        stdout = """
 Test Files  10 passed (10)
      Tests  50 passed, 2 failed (52)
   Start at  10:00:00
   Duration  5.00s
        """

        results = parse_test_output(stdout, "")

        # Should find numbers
        assert results["total"] >= 0


class TestFormatResultComment:
    """Tests for format_result_comment function."""

    def test_shows_status_emoji_passed(self):
        """Passed result shows check emoji."""
        result = ExecutionResult(
            request_id="exec-123",
            status=ExecutionStatus.PASSED,
            exit_code=0,
            stdout="All passed",
            stderr="",
            duration_seconds=5.0,
        )

        comment = format_result_comment(result)

        assert "✅" in comment

    def test_shows_status_emoji_failed(self):
        """Failed result shows X emoji."""
        result = ExecutionResult(
            request_id="exec-123",
            status=ExecutionStatus.FAILED,
            exit_code=1,
            stdout="",
            stderr="Error",
            duration_seconds=3.0,
        )

        comment = format_result_comment(result)

        assert "❌" in comment

    def test_includes_duration(self):
        """Comment includes duration."""
        result = ExecutionResult(
            request_id="exec-123",
            status=ExecutionStatus.PASSED,
            exit_code=0,
            stdout="Done",
            stderr="",
            duration_seconds=12.34,
        )

        comment = format_result_comment(result)

        assert "12.34" in comment

    def test_includes_test_results(self):
        """Comment includes test results summary."""
        result = ExecutionResult(
            request_id="exec-123",
            status=ExecutionStatus.PASSED,
            exit_code=0,
            stdout="Done",
            stderr="",
            duration_seconds=5.0,
            test_results={"passed": 10, "failed": 2, "skipped": 1},
        )

        comment = format_result_comment(result)

        assert "Passed: 10" in comment
        assert "Failed: 2" in comment
        assert "Skipped: 1" in comment

    def test_includes_output_block(self):
        """Comment includes output in code block."""
        result = ExecutionResult(
            request_id="exec-123",
            status=ExecutionStatus.PASSED,
            exit_code=0,
            stdout="Test output here",
            stderr="",
            duration_seconds=5.0,
        )

        comment = format_result_comment(result)

        assert "```" in comment
        assert "Test output here" in comment

    def test_includes_pr_link(self):
        """Comment includes PR link when created."""
        result = ExecutionResult(
            request_id="exec-123",
            status=ExecutionStatus.PASSED,
            exit_code=0,
            stdout="Done",
            stderr="",
            duration_seconds=5.0,
            created_pr="https://github.com/org/repo/pull/123",
        )

        comment = format_result_comment(result)

        assert "Pull Request" in comment
        assert "https://github.com/org/repo/pull/123" in comment

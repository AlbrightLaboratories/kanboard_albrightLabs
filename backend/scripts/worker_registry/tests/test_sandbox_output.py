"""
Test WR-18: Sandbox captures stdout/stderr/exit code.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSandboxOutput:
    """Tests for sandbox output capture."""

    def test_captures_stdout(self):
        """WR-18a: Stdout is captured."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="docker")

        mock_result = MagicMock()
        mock_result.stdout = "standard output"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            result = executor.execute("echo test")

            assert result.stdout == "standard output"

    def test_captures_stderr(self):
        """WR-18b: Stderr is captured."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="docker")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "error output"
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = executor.execute("invalid_command")

            assert result.stderr == "error output"

    def test_captures_exit_code(self):
        """WR-18c: Exit code is captured."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="docker")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 42

        with patch("subprocess.run", return_value=mock_result):
            result = executor.execute("exit 42")

            assert result.exit_code == 42

    def test_to_dict_conversion(self):
        """WR-18d: Result can be converted to dict."""
        from worker_registry.sandbox_executor import SandboxResult

        result = SandboxResult(
            stdout="output",
            stderr="error",
            exit_code=1,
            timed_out=False
        )

        d = result.to_dict()

        assert d["stdout"] == "output"
        assert d["stderr"] == "error"
        assert d["exit_code"] == 1
        assert d["timed_out"] is False
        assert d["success"] is False  # exit_code != 0

    def test_success_flag(self):
        """WR-18e: Success flag based on exit code and timeout."""
        from worker_registry.sandbox_executor import SandboxResult

        # Success case
        success = SandboxResult(stdout="ok", stderr="", exit_code=0)
        assert success.to_dict()["success"] is True

        # Failed exit code
        failed = SandboxResult(stdout="", stderr="error", exit_code=1)
        assert failed.to_dict()["success"] is False

        # Timed out
        timeout = SandboxResult(stdout="", stderr="", exit_code=0, timed_out=True)
        assert timeout.to_dict()["success"] is False

"""
Test WR-19: Sandbox enforces resource limits (CPU, memory).
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSandboxLimits:
    """Tests for sandbox resource limits."""

    def test_memory_limit_applied(self):
        """WR-19a: Memory limit is passed to Docker."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            memory_limit="256m"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("echo test")

            call_args = mock_run.call_args[0][0]
            assert "--memory=256m" in call_args

    def test_cpu_limit_applied(self):
        """WR-19b: CPU limit is passed to Docker."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            cpu_limit="0.5"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("echo test")

            call_args = mock_run.call_args[0][0]
            assert "--cpus=0.5" in call_args

    def test_override_limits_per_call(self):
        """WR-19c: Limits can be overridden per execution."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            memory_limit="256m",
            cpu_limit="0.5"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute(
                "echo test",
                memory_limit="1g",
                cpu_limit="2.0"
            )

            call_args = mock_run.call_args[0][0]
            assert "--memory=1g" in call_args
            assert "--cpus=2.0" in call_args

    def test_default_limits(self):
        """WR-19d: Default limits are applied."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="docker")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("echo test")

            call_args = mock_run.call_args[0][0]
            # Default is 512m memory and 1.0 CPU
            assert "--memory=512m" in call_args
            assert "--cpus=1.0" in call_args

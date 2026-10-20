"""
Test WR-17: Sandbox executes command in Docker container with timeout.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSandboxDocker:
    """Tests for Docker sandbox execution."""

    def test_execute_in_docker(self):
        """WR-17a: Command executes in Docker container."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="docker")

        mock_result = MagicMock()
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = executor.execute("echo hello")

            assert result.stdout == "hello"
            assert result.exit_code == 0

            # Verify docker run was called
            call_args = mock_run.call_args[0][0]
            assert "docker" in call_args
            assert "run" in call_args

    def test_docker_timeout(self):
        """WR-17b: Command times out after specified duration."""
        from worker_registry import SandboxExecutor
        import subprocess

        executor = SandboxExecutor(sandbox_type="docker", timeout=5)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)

            result = executor.execute("sleep 100")

            assert result.timed_out is True
            assert result.exit_code == -1

    def test_docker_uses_image(self):
        """WR-17c: Correct Docker image is used."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            image="node:18-slim"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("node --version")

            call_args = mock_run.call_args[0][0]
            assert "node:18-slim" in call_args

    def test_docker_network_disabled_by_default(self):
        """WR-17d: Network is disabled by default."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="docker")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("echo test")

            call_args = mock_run.call_args[0][0]
            assert "--network=none" in call_args

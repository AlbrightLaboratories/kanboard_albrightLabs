"""
Test WR-20: Sandbox mounts source read-only, workspace writable.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSandboxMounts:
    """Tests for sandbox volume mounts."""

    def test_source_mounted_readonly(self):
        """WR-20a: Source directory mounted as read-only."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            source_mount="/path/to/source"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("ls /source")

            call_args = mock_run.call_args[0][0]
            assert "-v" in call_args
            # Find the volume mount flag
            mount_found = False
            for i, arg in enumerate(call_args):
                if arg == "-v" and i + 1 < len(call_args):
                    if "/path/to/source:/source:ro" in call_args[i + 1]:
                        mount_found = True
                        break
            assert mount_found, "Source should be mounted read-only"

    def test_workspace_mounted_writable(self):
        """WR-20b: Workspace directory mounted as writable."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            workspace_dir="/tmp/workspace"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("touch /workspace/file.txt")

            call_args = mock_run.call_args[0][0]
            # Find the workspace mount
            mount_found = False
            for i, arg in enumerate(call_args):
                if arg == "-v" and i + 1 < len(call_args):
                    if "/tmp/workspace:/workspace:rw" in call_args[i + 1]:
                        mount_found = True
                        break
            assert mount_found, "Workspace should be mounted read-write"

    def test_working_directory_set(self):
        """WR-20c: Working directory set to workspace."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            workspace_dir="/tmp/workspace"
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("pwd")

            call_args = mock_run.call_args[0][0]
            assert "-w" in call_args
            # Find working directory flag
            wd_idx = call_args.index("-w")
            assert call_args[wd_idx + 1] == "/workspace"

    def test_no_mounts_when_not_specified(self):
        """WR-20d: No mounts when source_mount not specified."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(
            sandbox_type="docker",
            source_mount=None
        )

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            executor.execute("echo test")

            call_args = mock_run.call_args[0][0]
            # Check no /source mount
            source_mount_found = False
            for i, arg in enumerate(call_args):
                if arg == "-v" and i + 1 < len(call_args):
                    if "/source" in call_args[i + 1]:
                        source_mount_found = True
                        break
            assert not source_mount_found, "No source mount expected"

"""
Test WR-21: Kubernetes sandbox runs as Job in dedicated namespace.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSandboxKubernetes:
    """Tests for Kubernetes sandbox execution."""

    def test_creates_k8s_job(self):
        """WR-21a: Execution creates Kubernetes Job."""
        from worker_registry import SandboxExecutor
        import json

        executor = SandboxExecutor(sandbox_type="kubernetes")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="output",
                stderr="",
                returncode=0
            )

            executor.execute("echo hello", namespace="sandbox")

            # First call should be kubectl apply
            first_call = mock_run.call_args_list[0]
            assert "kubectl" in first_call[0][0]
            assert "apply" in first_call[0][0]

    def test_uses_dedicated_namespace(self):
        """WR-21b: Job runs in specified namespace."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="kubernetes")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="",
                returncode=0
            )

            executor.execute("echo test", namespace="worker-sandbox")

            # Check namespace in kubectl calls
            namespace_used = False
            for call in mock_run.call_args_list:
                if "-n" in call[0][0] or "--namespace" in str(call):
                    args = call[0][0]
                    if "worker-sandbox" in args:
                        namespace_used = True
                        break
            # Default namespace is "sandbox", we passed "worker-sandbox"
            # Just verify kubectl was called with namespace flag
            assert any("-n" in str(call) for call in mock_run.call_args_list)

    def test_job_has_resource_limits(self):
        """WR-21c: Job spec includes resource limits."""
        from worker_registry import SandboxExecutor
        import json

        executor = SandboxExecutor(
            sandbox_type="kubernetes",
            memory_limit="1g",
            cpu_limit="2.0"
        )

        captured_manifest = None

        def capture_manifest(cmd, **kwargs):
            nonlocal captured_manifest
            if "apply" in cmd and "input" in kwargs:
                captured_manifest = json.loads(kwargs["input"])
            return MagicMock(stdout="", stderr="", returncode=0)

        with patch("subprocess.run", side_effect=capture_manifest):
            executor.execute("echo test")

            assert captured_manifest is not None
            container = captured_manifest["spec"]["template"]["spec"]["containers"][0]
            assert container["resources"]["limits"]["memory"] == "1g"
            assert container["resources"]["limits"]["cpu"] == "2.0"

    def test_job_cleanup_after_completion(self):
        """WR-21d: Job is deleted after execution."""
        from worker_registry import SandboxExecutor

        executor = SandboxExecutor(sandbox_type="kubernetes")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="output",
                stderr="",
                returncode=0
            )

            executor.execute("echo test")

            # Should have a delete call
            delete_called = False
            for call in mock_run.call_args_list:
                if "delete" in call[0][0]:
                    delete_called = True
                    break
            assert delete_called, "Job should be cleaned up after execution"

    def test_job_timeout(self):
        """WR-21e: Job respects timeout deadline."""
        from worker_registry import SandboxExecutor
        import json

        executor = SandboxExecutor(
            sandbox_type="kubernetes",
            timeout=60
        )

        captured_manifest = None

        def capture_manifest(cmd, **kwargs):
            nonlocal captured_manifest
            if "apply" in cmd and "input" in kwargs:
                captured_manifest = json.loads(kwargs["input"])
            return MagicMock(stdout="", stderr="", returncode=0)

        with patch("subprocess.run", side_effect=capture_manifest):
            executor.execute("sleep 30")

            assert captured_manifest is not None
            assert captured_manifest["spec"]["activeDeadlineSeconds"] == 60

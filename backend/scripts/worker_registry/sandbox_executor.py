"""
Sandbox Executor

Executes commands in isolated sandbox environments (Docker/Kubernetes).
"""
from __future__ import annotations

import subprocess
import tempfile
import os
from typing import Any, Dict, Optional


class SandboxResult:
    """Result of a sandbox execution."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        timed_out: bool = False
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.timed_out = timed_out

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "success": self.exit_code == 0 and not self.timed_out
        }


class SandboxExecutor:
    """Executes commands in sandboxed environments."""

    def __init__(
        self,
        sandbox_type: str = "docker",
        image: str = "python:3.11-slim",
        timeout: int = 300,
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
        network_enabled: bool = False,
        source_mount: Optional[str] = None,
        workspace_dir: Optional[str] = None
    ):
        """
        Initialize sandbox executor.

        Args:
            sandbox_type: Type of sandbox ("docker", "kubernetes", "none")
            image: Container image to use
            timeout: Execution timeout in seconds
            memory_limit: Memory limit (e.g., "512m", "1g")
            cpu_limit: CPU limit (e.g., "1.0", "0.5")
            network_enabled: Allow network access
            source_mount: Path to mount as read-only source
            workspace_dir: Writable workspace directory
        """
        self.sandbox_type = sandbox_type
        self.image = image
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.network_enabled = network_enabled
        self.source_mount = source_mount
        self.workspace_dir = workspace_dir or tempfile.mkdtemp()

    def execute(self, command: str, **kwargs: Any) -> SandboxResult:
        """
        Execute command in sandbox.

        Args:
            command: Command to execute
            **kwargs: Override initialization parameters

        Returns:
            SandboxResult with stdout, stderr, exit_code
        """
        sandbox_type = kwargs.get("sandbox_type", self.sandbox_type)

        if sandbox_type == "docker":
            return self._execute_docker(command, **kwargs)
        elif sandbox_type == "kubernetes":
            return self._execute_kubernetes(command, **kwargs)
        elif sandbox_type == "none":
            return self._execute_direct(command, **kwargs)
        else:
            raise ValueError(f"Unknown sandbox type: {sandbox_type}")

    def _execute_docker(self, command: str, **kwargs: Any) -> SandboxResult:
        """Execute command in Docker container."""
        timeout = kwargs.get("timeout", self.timeout)
        image = kwargs.get("image", self.image)
        memory_limit = kwargs.get("memory_limit", self.memory_limit)
        cpu_limit = kwargs.get("cpu_limit", self.cpu_limit)
        network_enabled = kwargs.get("network_enabled", self.network_enabled)
        source_mount = kwargs.get("source_mount", self.source_mount)
        workspace_dir = kwargs.get("workspace_dir", self.workspace_dir)

        docker_cmd = [
            "docker", "run",
            "--rm",
            f"--memory={memory_limit}",
            f"--cpus={cpu_limit}",
        ]

        if not network_enabled:
            docker_cmd.append("--network=none")

        if source_mount:
            docker_cmd.extend(["-v", f"{source_mount}:/source:ro"])

        if workspace_dir:
            docker_cmd.extend(["-v", f"{workspace_dir}:/workspace:rw"])
            docker_cmd.extend(["-w", "/workspace"])

        docker_cmd.extend([image, "sh", "-c", command])

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return SandboxResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                timed_out=True
            )
        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    def _execute_kubernetes(self, command: str, **kwargs: Any) -> SandboxResult:
        """Execute command as Kubernetes Job."""
        timeout = kwargs.get("timeout", self.timeout)
        image = kwargs.get("image", self.image)
        namespace = kwargs.get("namespace", "sandbox")
        memory_limit = kwargs.get("memory_limit", self.memory_limit)
        cpu_limit = kwargs.get("cpu_limit", self.cpu_limit)

        import uuid
        job_name = f"sandbox-{uuid.uuid4().hex[:8]}"

        # Create job manifest
        job_manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": namespace
            },
            "spec": {
                "ttlSecondsAfterFinished": 60,
                "backoffLimit": 0,
                "activeDeadlineSeconds": timeout,
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [{
                            "name": "sandbox",
                            "image": image,
                            "command": ["sh", "-c", command],
                            "resources": {
                                "limits": {
                                    "memory": memory_limit,
                                    "cpu": cpu_limit
                                }
                            }
                        }]
                    }
                }
            }
        }

        try:
            import json

            # Create job
            create_cmd = [
                "kubectl", "apply", "-f", "-",
                "-n", namespace
            ]
            subprocess.run(
                create_cmd,
                input=json.dumps(job_manifest),
                text=True,
                capture_output=True,
                check=True
            )

            # Wait for completion
            wait_cmd = [
                "kubectl", "wait",
                f"--for=condition=complete",
                f"--timeout={timeout}s",
                f"job/{job_name}",
                "-n", namespace
            ]

            try:
                subprocess.run(wait_cmd, check=True, capture_output=True, text=True)
                timed_out = False
            except subprocess.CalledProcessError:
                timed_out = True

            # Get logs
            logs_cmd = [
                "kubectl", "logs",
                f"job/{job_name}",
                "-n", namespace
            ]
            logs_result = subprocess.run(logs_cmd, capture_output=True, text=True)

            # Cleanup
            delete_cmd = [
                "kubectl", "delete",
                f"job/{job_name}",
                "-n", namespace,
                "--ignore-not-found"
            ]
            subprocess.run(delete_cmd, capture_output=True)

            return SandboxResult(
                stdout=logs_result.stdout,
                stderr=logs_result.stderr,
                exit_code=0 if not timed_out else -1,
                timed_out=timed_out
            )

        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    def _execute_direct(self, command: str, **kwargs: Any) -> SandboxResult:
        """Execute command directly (no sandbox - dangerous!)."""
        timeout = kwargs.get("timeout", self.timeout)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return SandboxResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                timed_out=True
            )
        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

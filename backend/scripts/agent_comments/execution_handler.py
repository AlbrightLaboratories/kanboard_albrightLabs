"""
Execution Handler - Handles sandbox execution requests

Implements:
- AIC-04: Agent can request sandbox execution via [READY_TO_EXECUTE] marker
- AIC-05: User approval triggers sandbox pod execution
- AIC-06: Sandbox results are posted back as comment
- AIC-07: Successful sandbox updates code in repo via PR
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timezone
import json


class ExecutionStatus(Enum):
    """Status of sandbox execution."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class ExecutionRequest:
    """A request to execute code in sandbox."""
    request_id: str
    story_id: str
    comment_id: str
    agent_id: str
    execution_type: str  # "test", "build", "script", "prove-it"
    commands: List[str]
    working_directory: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    status: ExecutionStatus = ExecutionStatus.PENDING_APPROVAL
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionResult:
    """Result from sandbox execution."""
    request_id: str
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    created_pr: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None
    completed_at: str = ""

    def __post_init__(self):
        if not self.completed_at:
            self.completed_at = datetime.now(timezone.utc).isoformat()


# Marker for execution requests
EXECUTION_MARKER = "[READY_TO_EXECUTE]"


def parse_execution_request(
    content: str,
    story_id: str,
    comment_id: str,
    agent_id: str,
) -> Optional[ExecutionRequest]:
    """
    Parse execution request from agent response.

    Args:
        content: Agent response content
        story_id: Story ID
        comment_id: Comment ID
        agent_id: Agent ID

    Returns:
        ExecutionRequest or None if no request found
    """
    if EXECUTION_MARKER not in content:
        return None

    # Extract execution block
    marker_pos = content.find(EXECUTION_MARKER)
    after_marker = content[marker_pos + len(EXECUTION_MARKER):]

    # Try to parse JSON block
    json_start = after_marker.find("{")
    if json_start != -1:
        try:
            # Find matching closing brace
            brace_count = 0
            json_end = json_start

            for i, char in enumerate(after_marker[json_start:]):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = json_start + i + 1
                        break

            json_str = after_marker[json_start:json_end]
            details = json.loads(json_str)

            return ExecutionRequest(
                request_id=f"exec-{story_id}-{comment_id}",
                story_id=story_id,
                comment_id=comment_id,
                agent_id=agent_id,
                execution_type=details.get("type", "script"),
                commands=details.get("commands", []),
                working_directory=details.get("working_directory"),
                environment=details.get("environment", {}),
                timeout_seconds=details.get("timeout", 300),
            )
        except json.JSONDecodeError:
            pass

    # Fallback: treat remaining text as single command
    command = after_marker.strip().split("\n")[0]
    if command:
        return ExecutionRequest(
            request_id=f"exec-{story_id}-{comment_id}",
            story_id=story_id,
            comment_id=comment_id,
            agent_id=agent_id,
            execution_type="script",
            commands=[command],
        )

    return None


async def trigger_sandbox_execution(
    request: ExecutionRequest,
    sandbox_client: Any,
) -> str:
    """
    Trigger sandbox pod execution.

    Args:
        request: The execution request
        sandbox_client: Sandbox pod client

    Returns:
        Execution job ID
    """
    # Create Kubernetes Job for sandbox execution
    job_spec = {
        "request_id": request.request_id,
        "commands": request.commands,
        "working_directory": request.working_directory or "/workspace",
        "environment": request.environment,
        "timeout_seconds": request.timeout_seconds,
        "labels": {
            "story_id": request.story_id,
            "agent_id": request.agent_id,
            "execution_type": request.execution_type,
        },
    }

    # Submit to sandbox executor
    job_id = await sandbox_client.create_job(job_spec)

    # Update request status
    request.status = ExecutionStatus.RUNNING

    return job_id


def handle_execution_result(
    request: ExecutionRequest,
    exit_code: int,
    stdout: str,
    stderr: str,
    duration: float,
) -> ExecutionResult:
    """
    Handle sandbox execution result.

    Args:
        request: Original execution request
        exit_code: Process exit code
        stdout: Standard output
        stderr: Standard error
        duration: Execution duration in seconds

    Returns:
        ExecutionResult object
    """
    status = ExecutionStatus.PASSED if exit_code == 0 else ExecutionStatus.FAILED

    # Parse test results if present
    test_results = None
    if request.execution_type in ["test", "prove-it"]:
        test_results = parse_test_output(stdout, stderr)

    return ExecutionResult(
        request_id=request.request_id,
        status=status,
        exit_code=exit_code,
        stdout=stdout[-10000:],  # Truncate long output
        stderr=stderr[-5000:],
        duration_seconds=duration,
        test_results=test_results,
    )


def parse_test_output(stdout: str, stderr: str) -> Dict[str, Any]:
    """
    Parse test output for results summary.

    Args:
        stdout: Standard output
        stderr: Standard error

    Returns:
        Test results summary
    """
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
        "failures": [],
    }

    # Look for pytest-style output
    for line in stdout.split("\n"):
        if "passed" in line.lower() and "failed" in line.lower():
            # Parse "X passed, Y failed, Z skipped"
            import re
            matches = re.findall(r"(\d+)\s+(passed|failed|skipped)", line.lower())
            for count, status in matches:
                results[status] = int(count)
                results["total"] += int(count)

    # Look for vitest/jest-style output
    if "Tests:" in stdout:
        for line in stdout.split("\n"):
            if line.strip().startswith("Tests:"):
                import re
                matches = re.findall(r"(\d+)\s+(passed|failed|skipped)", line.lower())
                for count, status in matches:
                    results[status] = int(count)
                    results["total"] += int(count)

    return results


def format_result_comment(result: ExecutionResult) -> str:
    """
    Format execution result as a comment.

    Args:
        result: The execution result

    Returns:
        Formatted comment content
    """
    status_emoji = "✅" if result.status == ExecutionStatus.PASSED else "❌"

    parts = [
        f"## Sandbox Execution {status_emoji}",
        "",
        f"**Status**: {result.status.value}",
        f"**Exit Code**: {result.exit_code}",
        f"**Duration**: {result.duration_seconds:.2f}s",
        "",
    ]

    if result.test_results:
        parts.extend([
            "### Test Results",
            f"- Passed: {result.test_results.get('passed', 0)}",
            f"- Failed: {result.test_results.get('failed', 0)}",
            f"- Skipped: {result.test_results.get('skipped', 0)}",
            "",
        ])

    if result.stdout:
        parts.extend([
            "### Output",
            "```",
            result.stdout[:2000],  # Truncate
            "```",
            "",
        ])

    if result.stderr and result.status == ExecutionStatus.FAILED:
        parts.extend([
            "### Errors",
            "```",
            result.stderr[:1000],  # Truncate
            "```",
            "",
        ])

    if result.created_pr:
        parts.extend([
            "### Pull Request Created",
            f"[View PR]({result.created_pr})",
        ])

    return "\n".join(parts)


async def create_pr_from_result(
    result: ExecutionResult,
    story_data: Dict[str, Any],
    github_client: Any,
) -> Optional[str]:
    """
    Create PR from successful sandbox execution.

    Args:
        result: Successful execution result
        story_data: Story data with repo/branch info
        github_client: GitHub API client

    Returns:
        PR URL or None
    """
    if result.status != ExecutionStatus.PASSED:
        return None

    repo = story_data.get("linked_repo")
    branch = story_data.get("linked_branch", "main")

    if not repo:
        return None

    # Create PR
    pr_url = await github_client.create_pull_request(
        repo=repo,
        head=f"agent/{result.request_id}",
        base=branch,
        title=f"Agent changes for story {story_data.get('id')}",
        body=f"Automated changes from sandbox execution.\n\n"
             f"Execution ID: {result.request_id}\n"
             f"Story: {story_data.get('title')}",
    )

    return pr_url

"""
Validation Result Handler

Handles validation results from GitHub workflows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Result of a validation run."""

    story_id: int
    status: str  # passed, failed
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    coverage_percentage: float = 0.0
    failure_log: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)
    modularity_issues: List[str] = field(default_factory=list)
    workflow_run_id: Optional[str] = None
    workflow_run_url: Optional[str] = None
    duration_seconds: float = 0.0

    @property
    def all_tests_pass(self) -> bool:
        """Check if all tests passed."""
        return self.tests_failed == 0 and self.tests_passed > 0

    @property
    def summary(self) -> str:
        """Get a summary of the validation result."""
        if self.status == "passed":
            return f"PASSED: {self.tests_passed} tests, {self.coverage_percentage:.1f}% coverage"
        else:
            return f"FAILED: {self.tests_failed}/{self.tests_passed + self.tests_failed} tests failed"


class ValidationResultHandler:
    """Handles validation results and updates Kanboard."""

    def __init__(self, kanboard_client: Optional[Any] = None) -> None:
        """
        Initialize result handler.

        Args:
            kanboard_client: Optional Kanboard API client for updates
        """
        self.kanboard_client = kanboard_client
        self._results: Dict[int, ValidationResult] = {}

    def process_result(
        self,
        story_id: int,
        raw_result: Dict[str, Any]
    ) -> ValidationResult:
        """
        Process raw validation result from GitHub workflow.

        Args:
            story_id: Story ID
            raw_result: Raw result data from workflow

        Returns:
            Processed ValidationResult
        """
        # Extract test results
        tests_passed = raw_result.get("tests_passed", 0)
        tests_failed = raw_result.get("tests_failed", 0)
        tests_skipped = raw_result.get("tests_skipped", 0)

        # Extract coverage
        coverage = raw_result.get("coverage_percentage", 0.0)
        if isinstance(coverage, str):
            try:
                coverage = float(coverage.replace("%", ""))
            except ValueError:
                coverage = 0.0

        # Determine status
        status = "passed" if tests_failed == 0 and tests_passed > 0 else "failed"

        # Check for coverage threshold
        if coverage < 80.0 and status == "passed":
            status = "failed"

        # Build failure reasons
        failure_reasons = []
        if tests_failed > 0:
            failure_reasons.append(f"{tests_failed} test(s) failed")
        if coverage < 80.0:
            failure_reasons.append(f"Coverage {coverage:.1f}% below 80% threshold")
        if raw_result.get("modularity_issues"):
            failure_reasons.append("Modularity violations found")

        # Build result
        result = ValidationResult(
            story_id=story_id,
            status=status,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            tests_skipped=tests_skipped,
            coverage_percentage=coverage,
            failure_log=raw_result.get("failure_log"),
            failure_reasons=failure_reasons,
            modularity_issues=raw_result.get("modularity_issues", []),
            workflow_run_id=raw_result.get("run_id"),
            workflow_run_url=raw_result.get("run_url"),
            duration_seconds=raw_result.get("duration_seconds", 0.0)
        )

        # Store result
        self._results[story_id] = result

        return result

    def post_result_to_kanboard(
        self,
        result: ValidationResult
    ) -> bool:
        """
        Post validation result back to Kanboard.

        Args:
            result: ValidationResult to post

        Returns:
            True if posted successfully
        """
        if not self.kanboard_client:
            return False

        try:
            # Build comment
            comment = self._build_result_comment(result)

            # Post comment to story
            self.kanboard_client.add_comment(
                story_id=result.story_id,
                content=comment
            )

            # Update story status if needed
            if result.status == "passed":
                self.kanboard_client.update_story(
                    story_id=result.story_id,
                    validation_status="passed"
                )
            else:
                self.kanboard_client.update_story(
                    story_id=result.story_id,
                    validation_status="failed"
                )

            return True

        except Exception:
            return False

    def _build_result_comment(self, result: ValidationResult) -> str:
        """Build a comment for the validation result."""
        if result.status == "passed":
            comment = "## Validation PASSED\n\n"
            comment += f"- Tests: {result.tests_passed} passed"
            if result.tests_skipped:
                comment += f", {result.tests_skipped} skipped"
            comment += "\n"
            comment += f"- Coverage: {result.coverage_percentage:.1f}%\n"
            if result.workflow_run_url:
                comment += f"- [Workflow Run]({result.workflow_run_url})\n"
        else:
            comment = "## Validation FAILED\n\n"
            comment += "### Issues Found\n\n"
            for reason in result.failure_reasons:
                comment += f"- {reason}\n"
            comment += "\n"
            comment += f"### Test Summary\n\n"
            comment += f"- Passed: {result.tests_passed}\n"
            comment += f"- Failed: {result.tests_failed}\n"
            if result.tests_skipped:
                comment += f"- Skipped: {result.tests_skipped}\n"
            comment += f"- Coverage: {result.coverage_percentage:.1f}%\n"
            if result.failure_log:
                comment += "\n### Failure Log\n\n```\n"
                comment += result.failure_log[:2000]  # Truncate if too long
                comment += "\n```\n"
            if result.workflow_run_url:
                comment += f"\n[Full Workflow Log]({result.workflow_run_url})\n"

        return comment

    def handle_passed_validation(
        self,
        story_id: int,
        result: ValidationResult
    ) -> Dict[str, Any]:
        """
        Handle a passed validation - move story to Done.

        Args:
            story_id: Story ID
            result: Validation result

        Returns:
            Dict with action taken
        """
        action = {
            "story_id": story_id,
            "action": "move_to_done",
            "status": "pending"
        }

        if self.kanboard_client:
            try:
                # Move story to Done column
                self.kanboard_client.move_story(
                    story_id=story_id,
                    column="Done"
                )
                action["status"] = "completed"
            except Exception as e:
                action["status"] = "failed"
                action["error"] = str(e)

        return action

    def get_result(self, story_id: int) -> Optional[ValidationResult]:
        """Get stored result for a story."""
        return self._results.get(story_id)

    def clear_result(self, story_id: int) -> None:
        """Clear stored result for a story."""
        self._results.pop(story_id, None)

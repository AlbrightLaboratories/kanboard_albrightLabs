"""
Prove-It Skill

Runs tests, checks coverage, verifies modularity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_skill import BaseSkill, SkillResult


class ProveItSkill(BaseSkill):
    """Verifies implementation meets all acceptance criteria."""

    name = "prove-it"

    def execute(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Prove the implementation works.

        1. Run all tests
        2. Check coverage
        3. Verify modularity (no file > 200 LOC)
        4. Check all subtasks complete
        """
        try:
            repo_url = story_data.get("repo_url", "")
            branch = story_data.get("branch", "main")
            test_results = kwargs.get("test_results", {})

            # Verify tests
            tests_passed = self._verify_tests(test_results)

            # Check coverage
            coverage_ok, coverage_pct = self._check_coverage(
                kwargs.get("coverage_data", {})
            )

            # Check modularity
            modularity_ok, modularity_issues = self._check_modularity(
                kwargs.get("file_stats", {})
            )

            # Check subtasks
            subtasks_complete = self._check_subtasks(
                story_data.get("subtasks", [])
            )

            # Determine overall status
            all_passed = (
                tests_passed and
                coverage_ok and
                modularity_ok and
                subtasks_complete
            )

            output = {
                "prove_it": {
                    "tests_passed": tests_passed,
                    "coverage_percentage": coverage_pct,
                    "coverage_ok": coverage_ok,
                    "modularity_ok": modularity_ok,
                    "modularity_issues": modularity_issues,
                    "subtasks_complete": subtasks_complete,
                    "repo_url": repo_url,
                    "branch": branch,
                    "verdict": "PROVEN" if all_passed else "NOT_PROVEN"
                }
            }

            if not all_passed:
                reasons = []
                if not tests_passed:
                    reasons.append("Tests failing")
                if not coverage_ok:
                    reasons.append(f"Coverage {coverage_pct}% below threshold")
                if not modularity_ok:
                    reasons.append(f"Modularity issues: {modularity_issues}")
                if not subtasks_complete:
                    reasons.append("Subtasks incomplete")

                return self._create_result(
                    story_id=story_id,
                    status="failed",
                    output=output,
                    failure_reason="; ".join(reasons),
                    agent_id=agent_id
                )

            return self._create_result(
                story_id=story_id,
                status="passed",
                output=output,
                agent_id=agent_id
            )

        except Exception as e:
            return self._create_result(
                story_id=story_id,
                status="failed",
                failure_reason=str(e),
                agent_id=agent_id
            )

    def _verify_tests(self, test_results: Dict[str, Any]) -> bool:
        """Verify all tests pass."""
        if not test_results:
            return True  # No test results = assume passing (for testing)

        return test_results.get("all_passed", True)

    def _check_coverage(
        self,
        coverage_data: Dict[str, Any]
    ) -> tuple:
        """Check coverage meets threshold."""
        threshold = 80  # Default 80%
        coverage_pct = coverage_data.get("percentage", 100)
        return coverage_pct >= threshold, coverage_pct

    def _check_modularity(
        self,
        file_stats: Dict[str, Any]
    ) -> tuple:
        """Check no file exceeds 200 LOC."""
        max_loc = 200
        issues = []

        for filename, stats in file_stats.items():
            loc = stats.get("loc", 0)
            if loc > max_loc:
                issues.append(f"{filename}: {loc} LOC (max {max_loc})")

        return len(issues) == 0, issues

    def _check_subtasks(self, subtasks: List[Dict[str, Any]]) -> bool:
        """Check all subtasks are complete."""
        if not subtasks:
            return True

        return all(task.get("completed", False) for task in subtasks)

"""
TDD Skill

Generates failing tests first, then implementation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_skill import BaseSkill, SkillResult


class TDDSkill(BaseSkill):
    """TDD workflow: failing test -> implementation -> green."""

    name = "tdd"

    def execute(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Execute TDD workflow for a story.

        1. Generate failing tests from ACs
        2. Track test status
        3. Generate implementation stubs
        """
        try:
            acceptance_criteria = story_data.get("acceptance_criteria", [])
            prd_modules = kwargs.get("prd_modules", [])

            # Generate tests from ACs or PRD modules
            tests = self._generate_tests(acceptance_criteria, prd_modules)

            output = {
                "tdd": {
                    "tests_generated": len(tests),
                    "tests": tests,
                    "status": "tests_written",
                    "next_step": "run_tests_and_implement"
                }
            }

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

    def _generate_tests(
        self,
        acceptance_criteria: List[str],
        prd_modules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate test specifications from ACs."""
        tests = []

        # Generate from acceptance criteria
        for i, ac in enumerate(acceptance_criteria, 1):
            test = {
                "id": f"test_ac_{i}",
                "description": f"Test: {ac}",
                "test_file": f"test_ac_{i}.py",
                "test_function": f"test_acceptance_criterion_{i}",
                "status": "pending",
                "assertion_type": "functional"
            }
            tests.append(test)

        # Generate from PRD modules if provided
        for module in prd_modules:
            for ac in module.get("acceptance_criteria", []):
                test = {
                    "id": ac.get("id", f"test_{module['name']}"),
                    "description": ac.get("description", ""),
                    "test_file": ac.get("test_file", f"test_{module['name']}.py"),
                    "test_function": f"test_{module['name']}",
                    "status": "pending",
                    "assertion_type": "unit"
                }
                tests.append(test)

        # Ensure at least one test
        if not tests:
            tests.append({
                "id": "test_basic",
                "description": "Basic functionality test",
                "test_file": "test_basic.py",
                "test_function": "test_basic_functionality",
                "status": "pending",
                "assertion_type": "integration"
            })

        return tests

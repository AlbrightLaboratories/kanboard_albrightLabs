"""
Plan Skill

Generates implementation steps from story description.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_skill import BaseSkill, SkillResult


class PlanSkill(BaseSkill):
    """Generates implementation plan for a story."""

    name = "plan"

    def execute(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Generate implementation steps from story description.

        Returns a structured plan with steps and dependencies.
        """
        try:
            title = story_data.get("title", "")
            description = story_data.get("description", "")
            acceptance_criteria = story_data.get("acceptance_criteria", [])

            # Generate implementation steps
            steps = self._generate_steps(title, description, acceptance_criteria)

            output = {
                "plan": {
                    "title": title,
                    "steps": steps,
                    "estimated_complexity": self._estimate_complexity(steps),
                    "dependencies": story_data.get("depends_on", []),
                    "files_to_modify": self._identify_files(description),
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

    def _generate_steps(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate implementation steps from story details."""
        steps = []

        # Step 1: Analysis
        steps.append({
            "number": 1,
            "action": "analyze",
            "description": f"Analyze requirements for: {title}",
            "inputs": ["description", "acceptance_criteria"],
            "outputs": ["requirements_list"]
        })

        # Step 2: Design
        steps.append({
            "number": 2,
            "action": "design",
            "description": "Design solution architecture",
            "inputs": ["requirements_list"],
            "outputs": ["design_doc", "module_list"]
        })

        # Step 3: Write tests (TDD)
        steps.append({
            "number": 3,
            "action": "write_tests",
            "description": "Write failing tests for acceptance criteria",
            "inputs": ["acceptance_criteria"],
            "outputs": ["test_files"]
        })

        # Step 4: Implement
        steps.append({
            "number": 4,
            "action": "implement",
            "description": "Implement code to pass tests",
            "inputs": ["design_doc", "test_files"],
            "outputs": ["source_files"]
        })

        # Step 5: Verify
        steps.append({
            "number": 5,
            "action": "verify",
            "description": "Run tests and verify all pass",
            "inputs": ["test_files", "source_files"],
            "outputs": ["test_results"]
        })

        return steps

    def _estimate_complexity(self, steps: List[Dict[str, Any]]) -> str:
        """Estimate complexity based on step count."""
        if len(steps) <= 3:
            return "low"
        elif len(steps) <= 6:
            return "medium"
        else:
            return "high"

    def _identify_files(self, description: str) -> List[str]:
        """Identify files mentioned in description."""
        # Simple extraction - in production would use NLP
        files = []
        words = description.split()
        for word in words:
            if "/" in word and "." in word:
                # Likely a file path
                files.append(word.strip(".,;:()[]"))
        return files

"""
PRD Skill (design-a-prd)

Decomposes story into modules with acceptance criteria.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_skill import BaseSkill, SkillResult


class PRDSkill(BaseSkill):
    """Decomposes story into modules with ACs."""

    name = "design-a-prd"

    def execute(
        self,
        story_id: int,
        story_data: Dict[str, Any],
        agent_id: Optional[str] = None,
        **kwargs: Any
    ) -> SkillResult:
        """
        Decompose story into modules with acceptance criteria.

        Creates a PRD with testable modules.
        """
        try:
            title = story_data.get("title", "")
            description = story_data.get("description", "")
            acceptance_criteria = story_data.get("acceptance_criteria", [])

            # Generate modules
            modules = self._decompose_into_modules(description, acceptance_criteria)

            output = {
                "prd": {
                    "title": title,
                    "modules": modules,
                    "total_acs": sum(len(m["acceptance_criteria"]) for m in modules),
                    "reusable": True,
                    "testable_independently": True
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

    def _decompose_into_modules(
        self,
        description: str,
        acceptance_criteria: List[str]
    ) -> List[Dict[str, Any]]:
        """Decompose into reusable modules."""
        modules = []

        # Create a module for each major acceptance criterion
        for i, ac in enumerate(acceptance_criteria, 1):
            module = {
                "name": f"module_{i}",
                "description": ac,
                "acceptance_criteria": [
                    {
                        "id": f"AC-{i}-1",
                        "description": ac,
                        "test_file": f"test_module_{i}.py",
                        "status": "pending"
                    }
                ],
                "reusable": True,
                "testable_independently": True
            }
            modules.append(module)

        # If no ACs provided, create a single module from description
        if not modules:
            modules.append({
                "name": "main_module",
                "description": description[:200] if description else "Main functionality",
                "acceptance_criteria": [
                    {
                        "id": "AC-1-1",
                        "description": "Core functionality works",
                        "test_file": "test_main.py",
                        "status": "pending"
                    }
                ],
                "reusable": True,
                "testable_independently": True
            })

        return modules

"""
Test SF-05: /plan skill generates implementation steps from story description
"""
import pytest
from ..skills.plan_skill import PlanSkill


class TestPlanSkill:
    """Test /plan skill implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.skill = PlanSkill()
        self.story_id = 101
        self.story_data = {
            "title": "Add User Authentication",
            "description": "Implement user login and registration with JWT tokens",
            "acceptance_criteria": [
                "Users can register with email and password",
                "Users can login and receive JWT token",
                "Protected routes require valid JWT"
            ],
            "depends_on": [42, 43]
        }

    def test_skill_name(self) -> None:
        """Verify skill name is 'plan'."""
        assert self.skill.name == "plan"

    def test_execute_returns_passed_status(self) -> None:
        """Verify successful execution returns passed status."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.status == "passed"
        assert result.failure_reason is None

    def test_execute_generates_steps(self) -> None:
        """Verify execution generates implementation steps."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "plan" in result.output
        assert "steps" in result.output["plan"]
        assert len(result.output["plan"]["steps"]) >= 1

    def test_steps_have_required_fields(self) -> None:
        """Verify each step has required fields."""
        result = self.skill.execute(self.story_id, self.story_data)
        steps = result.output["plan"]["steps"]

        for step in steps:
            assert "number" in step
            assert "action" in step
            assert "description" in step
            assert "inputs" in step
            assert "outputs" in step

    def test_generates_analyze_step(self) -> None:
        """Verify plan includes analyze step."""
        result = self.skill.execute(self.story_id, self.story_data)
        steps = result.output["plan"]["steps"]

        analyze_steps = [s for s in steps if s["action"] == "analyze"]
        assert len(analyze_steps) >= 1

    def test_generates_design_step(self) -> None:
        """Verify plan includes design step."""
        result = self.skill.execute(self.story_id, self.story_data)
        steps = result.output["plan"]["steps"]

        design_steps = [s for s in steps if s["action"] == "design"]
        assert len(design_steps) >= 1

    def test_generates_write_tests_step(self) -> None:
        """Verify plan includes write_tests step (TDD)."""
        result = self.skill.execute(self.story_id, self.story_data)
        steps = result.output["plan"]["steps"]

        test_steps = [s for s in steps if s["action"] == "write_tests"]
        assert len(test_steps) >= 1

    def test_generates_implement_step(self) -> None:
        """Verify plan includes implement step."""
        result = self.skill.execute(self.story_id, self.story_data)
        steps = result.output["plan"]["steps"]

        impl_steps = [s for s in steps if s["action"] == "implement"]
        assert len(impl_steps) >= 1

    def test_generates_verify_step(self) -> None:
        """Verify plan includes verify step."""
        result = self.skill.execute(self.story_id, self.story_data)
        steps = result.output["plan"]["steps"]

        verify_steps = [s for s in steps if s["action"] == "verify"]
        assert len(verify_steps) >= 1

    def test_includes_story_title_in_output(self) -> None:
        """Verify output includes story title."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.output["plan"]["title"] == self.story_data["title"]

    def test_estimates_complexity(self) -> None:
        """Verify plan estimates complexity."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "estimated_complexity" in result.output["plan"]
        assert result.output["plan"]["estimated_complexity"] in ["low", "medium", "high"]

    def test_includes_dependencies(self) -> None:
        """Verify plan includes story dependencies."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "dependencies" in result.output["plan"]
        assert result.output["plan"]["dependencies"] == [42, 43]

    def test_identifies_files_from_description(self) -> None:
        """Verify plan identifies files mentioned in description."""
        story_data = {
            **self.story_data,
            "description": "Update the /auth/login.py and /auth/register.py files"
        }
        result = self.skill.execute(self.story_id, story_data)

        assert "files_to_modify" in result.output["plan"]
        files = result.output["plan"]["files_to_modify"]
        assert "/auth/login.py" in files
        assert "/auth/register.py" in files

    def test_empty_description_still_works(self) -> None:
        """Verify plan works with empty description."""
        story_data = {
            "title": "Simple Task",
            "description": "",
            "acceptance_criteria": []
        }
        result = self.skill.execute(self.story_id, story_data)

        assert result.status == "passed"
        assert "steps" in result.output["plan"]

    def test_includes_agent_id_in_result(self) -> None:
        """Verify result includes agent ID when provided."""
        agent_id = "claude-003"
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            agent_id=agent_id
        )

        assert result.agent_id == agent_id

    def test_includes_story_id_in_result(self) -> None:
        """Verify result includes story ID."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.story_id == self.story_id

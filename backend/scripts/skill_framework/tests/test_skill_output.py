"""
Test SF-10: Skill output stored in JSON, retrievable via skill_output()
"""
import pytest
from ..skill_runner import SkillRunner


class TestSkillOutput:
    """Test skill output storage and retrieval."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = SkillRunner()
        self.story_id = 606
        self.story_data = {
            "title": "Test Story",
            "description": "A test story",
            "acceptance_criteria": ["AC1", "AC2"]
        }

    def test_output_stored_after_execution(self) -> None:
        """Verify skill output is stored after execution."""
        self.runner.execute("plan", self.story_id, self.story_data)

        output = self.runner.get_skill_output(self.story_id, "plan")
        assert output is not None

    def test_retrieve_specific_skill_output(self) -> None:
        """Verify can retrieve output for a specific skill."""
        self.runner.execute("plan", self.story_id, self.story_data)

        output = self.runner.get_skill_output(self.story_id, "plan")
        assert "plan" in output
        assert "steps" in output["plan"]

    def test_retrieve_all_outputs_for_story(self) -> None:
        """Verify can retrieve all outputs for a story."""
        self.runner.execute("plan", self.story_id, self.story_data)
        self.runner.execute("design-a-prd", self.story_id, self.story_data)
        self.runner.execute("tdd", self.story_id, self.story_data)

        all_outputs = self.runner.get_skill_output(self.story_id)

        assert "plan" in all_outputs
        assert "design-a-prd" in all_outputs
        assert "tdd" in all_outputs

    def test_output_is_json_serializable(self) -> None:
        """Verify skill output is JSON serializable."""
        import json

        self.runner.execute("plan", self.story_id, self.story_data)
        output = self.runner.get_skill_output(self.story_id, "plan")

        # Should not raise
        json_str = json.dumps(output)
        assert isinstance(json_str, str)

        # Should round-trip
        parsed = json.loads(json_str)
        assert parsed == output

    def test_output_persists_multiple_skills(self) -> None:
        """Verify outputs persist for multiple skill executions."""
        self.runner.execute("plan", self.story_id, self.story_data)
        self.runner.execute("design-a-prd", self.story_id, self.story_data)

        # Both should be retrievable
        plan_output = self.runner.get_skill_output(self.story_id, "plan")
        prd_output = self.runner.get_skill_output(self.story_id, "design-a-prd")

        assert plan_output is not None
        assert prd_output is not None

    def test_output_isolated_per_story(self) -> None:
        """Verify outputs are isolated per story."""
        story_id_1 = 606
        story_id_2 = 707

        self.runner.execute("plan", story_id_1, self.story_data)
        self.runner.execute("design-a-prd", story_id_2, self.story_data)

        # Story 1 should only have plan
        story1_outputs = self.runner.get_skill_output(story_id_1)
        assert "plan" in story1_outputs
        assert "design-a-prd" not in story1_outputs

        # Story 2 should only have prd
        story2_outputs = self.runner.get_skill_output(story_id_2)
        assert "design-a-prd" in story2_outputs
        assert "plan" not in story2_outputs

    def test_nonexistent_story_returns_none(self) -> None:
        """Verify nonexistent story returns None."""
        output = self.runner.get_skill_output(99999)
        assert output is None

    def test_nonexistent_skill_returns_none(self) -> None:
        """Verify nonexistent skill for story returns None."""
        self.runner.execute("plan", self.story_id, self.story_data)

        output = self.runner.get_skill_output(self.story_id, "nonexistent")
        assert output is None

    def test_output_updates_on_reexecution(self) -> None:
        """Verify output updates when skill is re-executed."""
        # First execution
        result1 = self.runner.execute("plan", self.story_id, self.story_data)
        output1 = self.runner.get_skill_output(self.story_id, "plan")

        # Second execution
        result2 = self.runner.execute("plan", self.story_id, self.story_data)
        output2 = self.runner.get_skill_output(self.story_id, "plan")

        # Both should be valid plan outputs
        assert "plan" in output1
        assert "plan" in output2

    def test_clear_outputs_removes_all(self) -> None:
        """Verify clear_outputs removes all stored outputs."""
        self.runner.execute("plan", self.story_id, self.story_data)
        self.runner.execute("design-a-prd", self.story_id, self.story_data)

        self.runner.clear_outputs()

        assert self.runner.get_skill_output(self.story_id) is None

    def test_clear_outputs_for_specific_story(self) -> None:
        """Verify clear_outputs can target specific story."""
        story_id_1 = 606
        story_id_2 = 707

        self.runner.execute("plan", story_id_1, self.story_data)
        self.runner.execute("plan", story_id_2, self.story_data)

        # Clear only story 1
        self.runner.clear_outputs(story_id_1)

        # Story 1 should be cleared
        assert self.runner.get_skill_output(story_id_1) is None

        # Story 2 should still exist
        assert self.runner.get_skill_output(story_id_2) is not None

    def test_get_skill_status_returns_correct_status(self) -> None:
        """Verify get_skill_status returns correct status."""
        self.runner.execute("plan", self.story_id, self.story_data)

        status = self.runner.get_skill_status(self.story_id, "plan")
        assert status == "passed"

    def test_output_contains_skill_result_output(self) -> None:
        """Verify stored output is the SkillResult output field."""
        result = self.runner.execute("plan", self.story_id, self.story_data)
        stored = self.runner.get_skill_output(self.story_id, "plan")

        # Stored should match result.output
        assert stored == result.output

    def test_all_outputs_dict_structure(self) -> None:
        """Verify all outputs returned as dict with skill names as keys."""
        self.runner.execute_phase("in_progress", self.story_id, self.story_data)

        all_outputs = self.runner.get_skill_output(self.story_id)

        assert isinstance(all_outputs, dict)
        assert "plan" in all_outputs
        assert "design-a-prd" in all_outputs
        assert "tdd" in all_outputs

    def test_output_includes_nested_structures(self) -> None:
        """Verify complex nested output is preserved."""
        self.runner.execute("design-a-prd", self.story_id, self.story_data)

        output = self.runner.get_skill_output(self.story_id, "design-a-prd")

        # Should have nested modules with acceptance_criteria
        assert "prd" in output
        assert "modules" in output["prd"]
        for module in output["prd"]["modules"]:
            assert "acceptance_criteria" in module
            for ac in module["acceptance_criteria"]:
                assert "id" in ac
                assert "description" in ac

    def test_phase_execution_stores_all_outputs(self) -> None:
        """Verify phase execution stores outputs for all skills."""
        results = self.runner.execute_phase(
            "in_progress",
            self.story_id,
            self.story_data
        )

        # All three skills should have stored outputs
        for skill_name in ["plan", "design-a-prd", "tdd"]:
            output = self.runner.get_skill_output(self.story_id, skill_name)
            assert output is not None

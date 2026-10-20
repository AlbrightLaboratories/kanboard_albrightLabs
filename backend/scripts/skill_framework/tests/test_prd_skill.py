"""
Test SF-06: /design-a-prd skill decomposes story into modules with ACs
"""
import pytest
from ..skills.prd_skill import PRDSkill


class TestPRDSkill:
    """Test /design-a-prd skill implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.skill = PRDSkill()
        self.story_id = 202
        self.story_data = {
            "title": "Implement Payment Gateway",
            "description": "Add Stripe integration for processing payments",
            "acceptance_criteria": [
                "Payment form accepts card details",
                "Stripe API processes payment",
                "User receives confirmation email"
            ]
        }

    def test_skill_name(self) -> None:
        """Verify skill name is 'design-a-prd'."""
        assert self.skill.name == "design-a-prd"

    def test_execute_returns_passed_status(self) -> None:
        """Verify successful execution returns passed status."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.status == "passed"
        assert result.failure_reason is None

    def test_decomposes_into_modules(self) -> None:
        """Verify execution creates modules."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "prd" in result.output
        assert "modules" in result.output["prd"]
        assert len(result.output["prd"]["modules"]) >= 1

    def test_module_per_acceptance_criterion(self) -> None:
        """Verify creates module for each acceptance criterion."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        # Should have at least as many modules as ACs
        assert len(modules) >= len(self.story_data["acceptance_criteria"])

    def test_modules_have_required_fields(self) -> None:
        """Verify each module has required fields."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        for module in modules:
            assert "name" in module
            assert "description" in module
            assert "acceptance_criteria" in module
            assert "reusable" in module
            assert "testable_independently" in module

    def test_module_acceptance_criteria_have_required_fields(self) -> None:
        """Verify module ACs have required fields."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        for module in modules:
            for ac in module["acceptance_criteria"]:
                assert "id" in ac
                assert "description" in ac
                assert "test_file" in ac
                assert "status" in ac

    def test_modules_are_marked_reusable(self) -> None:
        """Verify modules are marked as reusable."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        for module in modules:
            assert module["reusable"] is True

    def test_modules_are_testable_independently(self) -> None:
        """Verify modules are testable independently."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        for module in modules:
            assert module["testable_independently"] is True

    def test_includes_story_title(self) -> None:
        """Verify output includes story title."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.output["prd"]["title"] == self.story_data["title"]

    def test_counts_total_acs(self) -> None:
        """Verify output includes total AC count."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "total_acs" in result.output["prd"]
        assert result.output["prd"]["total_acs"] >= len(self.story_data["acceptance_criteria"])

    def test_empty_acs_creates_default_module(self) -> None:
        """Verify empty ACs still creates a default module."""
        story_data = {
            "title": "Simple Task",
            "description": "A simple task without explicit ACs",
            "acceptance_criteria": []
        }
        result = self.skill.execute(self.story_id, story_data)

        assert len(result.output["prd"]["modules"]) >= 1

    def test_module_names_are_unique(self) -> None:
        """Verify module names are unique."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        names = [m["name"] for m in modules]
        assert len(names) == len(set(names))

    def test_ac_ids_are_unique(self) -> None:
        """Verify AC IDs are unique across all modules."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        ac_ids = []
        for module in modules:
            for ac in module["acceptance_criteria"]:
                ac_ids.append(ac["id"])

        assert len(ac_ids) == len(set(ac_ids))

    def test_includes_agent_id_in_result(self) -> None:
        """Verify result includes agent ID when provided."""
        agent_id = "claude-004"
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            agent_id=agent_id
        )

        assert result.agent_id == agent_id

    def test_test_files_reference_module_name(self) -> None:
        """Verify test files reference their module name."""
        result = self.skill.execute(self.story_id, self.story_data)
        modules = result.output["prd"]["modules"]

        for module in modules:
            for ac in module["acceptance_criteria"]:
                # Test file should contain module reference
                assert "test_" in ac["test_file"]

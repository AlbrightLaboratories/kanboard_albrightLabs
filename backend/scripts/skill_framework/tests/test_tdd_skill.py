"""
Test SF-07: /tdd skill generates failing tests, then implementation
"""
import pytest
from ..skills.tdd_skill import TDDSkill


class TestTDDSkill:
    """Test /tdd skill implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.skill = TDDSkill()
        self.story_id = 303
        self.story_data = {
            "title": "Add Search Feature",
            "description": "Implement full-text search for stories",
            "acceptance_criteria": [
                "Search returns matching stories",
                "Search is case-insensitive",
                "Search supports filters"
            ]
        }

    def test_skill_name(self) -> None:
        """Verify skill name is 'tdd'."""
        assert self.skill.name == "tdd"

    def test_execute_returns_passed_status(self) -> None:
        """Verify successful execution returns passed status."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.status == "passed"
        assert result.failure_reason is None

    def test_generates_tests_from_acs(self) -> None:
        """Verify execution generates tests from ACs."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "tdd" in result.output
        assert "tests" in result.output["tdd"]
        assert len(result.output["tdd"]["tests"]) >= len(self.story_data["acceptance_criteria"])

    def test_tests_have_required_fields(self) -> None:
        """Verify each test has required fields."""
        result = self.skill.execute(self.story_id, self.story_data)
        tests = result.output["tdd"]["tests"]

        for test in tests:
            assert "id" in test
            assert "description" in test
            assert "test_file" in test
            assert "test_function" in test
            assert "status" in test
            assert "assertion_type" in test

    def test_tests_start_as_pending(self) -> None:
        """Verify generated tests start with pending status."""
        result = self.skill.execute(self.story_id, self.story_data)
        tests = result.output["tdd"]["tests"]

        for test in tests:
            assert test["status"] == "pending"

    def test_test_ids_are_unique(self) -> None:
        """Verify test IDs are unique."""
        result = self.skill.execute(self.story_id, self.story_data)
        tests = result.output["tdd"]["tests"]

        ids = [t["id"] for t in tests]
        assert len(ids) == len(set(ids))

    def test_tracks_tests_generated_count(self) -> None:
        """Verify output includes count of tests generated."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "tests_generated" in result.output["tdd"]
        assert result.output["tdd"]["tests_generated"] == len(result.output["tdd"]["tests"])

    def test_includes_workflow_status(self) -> None:
        """Verify output includes TDD workflow status."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "status" in result.output["tdd"]
        assert result.output["tdd"]["status"] == "tests_written"

    def test_includes_next_step(self) -> None:
        """Verify output includes next step guidance."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert "next_step" in result.output["tdd"]
        assert result.output["tdd"]["next_step"] == "run_tests_and_implement"

    def test_generates_tests_from_prd_modules(self) -> None:
        """Verify generates tests from PRD modules if provided."""
        prd_modules = [
            {
                "name": "search_module",
                "acceptance_criteria": [
                    {
                        "id": "AC-SEARCH-1",
                        "description": "Search returns results",
                        "test_file": "test_search.py"
                    }
                ]
            }
        ]

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            prd_modules=prd_modules
        )

        tests = result.output["tdd"]["tests"]
        # Should have tests from both ACs and PRD modules
        assert len(tests) >= len(self.story_data["acceptance_criteria"]) + 1

    def test_empty_acs_generates_basic_test(self) -> None:
        """Verify empty ACs still generates at least one test."""
        story_data = {
            "title": "Simple Task",
            "description": "A task with no explicit ACs",
            "acceptance_criteria": []
        }
        result = self.skill.execute(self.story_id, story_data)

        assert len(result.output["tdd"]["tests"]) >= 1

    def test_test_function_names_are_valid(self) -> None:
        """Verify test function names are valid Python identifiers."""
        result = self.skill.execute(self.story_id, self.story_data)
        tests = result.output["tdd"]["tests"]

        import re
        for test in tests:
            # Should be a valid Python identifier starting with test_
            assert test["test_function"].startswith("test_")
            assert re.match(r"^[a-z_][a-z0-9_]*$", test["test_function"])

    def test_test_files_have_py_extension(self) -> None:
        """Verify test files have .py extension."""
        result = self.skill.execute(self.story_id, self.story_data)
        tests = result.output["tdd"]["tests"]

        for test in tests:
            assert test["test_file"].endswith(".py")

    def test_assertion_types_are_valid(self) -> None:
        """Verify assertion types are recognized values."""
        result = self.skill.execute(self.story_id, self.story_data)
        tests = result.output["tdd"]["tests"]

        valid_types = {"functional", "unit", "integration"}
        for test in tests:
            assert test["assertion_type"] in valid_types

    def test_includes_agent_id_in_result(self) -> None:
        """Verify result includes agent ID when provided."""
        agent_id = "claude-005"
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            agent_id=agent_id
        )

        assert result.agent_id == agent_id

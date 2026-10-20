"""
Test SF-08: /prove-it skill runs tests, checks coverage, verifies modularity
"""
import pytest
from ..skills.prove_it_skill import ProveItSkill


class TestProveItSkill:
    """Test /prove-it skill implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.skill = ProveItSkill()
        self.story_id = 404
        self.story_data = {
            "title": "API Endpoint Implementation",
            "description": "Implement REST API endpoints",
            "repo_url": "https://github.com/test/repo",
            "branch": "feature/api",
            "subtasks": [
                {"id": 1, "title": "Create endpoint", "completed": True},
                {"id": 2, "title": "Add tests", "completed": True}
            ]
        }

    def test_skill_name(self) -> None:
        """Verify skill name is 'prove-it'."""
        assert self.skill.name == "prove-it"

    def test_execute_returns_passed_when_all_pass(self) -> None:
        """Verify successful execution when all checks pass."""
        test_results = {"all_passed": True, "failed": 0, "passed": 10}
        coverage_data = {"percentage": 85}
        file_stats = {"main.py": {"loc": 150}}

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data=coverage_data,
            file_stats=file_stats
        )

        assert result.status == "passed"
        assert result.output["prove_it"]["verdict"] == "PROVEN"

    def test_fails_when_tests_fail(self) -> None:
        """Verify failure when tests don't pass."""
        test_results = {"all_passed": False, "failed": 3, "passed": 7}
        coverage_data = {"percentage": 85}

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data=coverage_data
        )

        assert result.status == "failed"
        assert "Tests failing" in result.failure_reason

    def test_fails_when_coverage_below_threshold(self) -> None:
        """Verify failure when coverage below 80%."""
        test_results = {"all_passed": True}
        coverage_data = {"percentage": 65}

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data=coverage_data
        )

        assert result.status == "failed"
        assert "Coverage" in result.failure_reason
        assert "below threshold" in result.failure_reason

    def test_fails_when_file_exceeds_200_loc(self) -> None:
        """Verify failure when file exceeds 200 LOC."""
        test_results = {"all_passed": True}
        coverage_data = {"percentage": 85}
        file_stats = {"monolith.py": {"loc": 350}}

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data=coverage_data,
            file_stats=file_stats
        )

        assert result.status == "failed"
        assert "Modularity" in result.failure_reason
        assert "monolith.py" in str(result.output["prove_it"]["modularity_issues"])

    def test_fails_when_subtasks_incomplete(self) -> None:
        """Verify failure when subtasks not complete."""
        story_data = {
            **self.story_data,
            "subtasks": [
                {"id": 1, "title": "Task 1", "completed": True},
                {"id": 2, "title": "Task 2", "completed": False}  # Not complete
            ]
        }
        test_results = {"all_passed": True}
        coverage_data = {"percentage": 85}

        result = self.skill.execute(
            self.story_id,
            story_data,
            test_results=test_results,
            coverage_data=coverage_data
        )

        assert result.status == "failed"
        assert "Subtasks incomplete" in result.failure_reason

    def test_output_includes_all_checks(self) -> None:
        """Verify output includes all verification checks."""
        test_results = {"all_passed": True}
        coverage_data = {"percentage": 85}

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data=coverage_data
        )

        output = result.output["prove_it"]
        assert "tests_passed" in output
        assert "coverage_percentage" in output
        assert "coverage_ok" in output
        assert "modularity_ok" in output
        assert "subtasks_complete" in output
        assert "verdict" in output

    def test_includes_repo_info_in_output(self) -> None:
        """Verify output includes repo information."""
        result = self.skill.execute(self.story_id, self.story_data)

        output = result.output["prove_it"]
        assert output["repo_url"] == self.story_data["repo_url"]
        assert output["branch"] == self.story_data["branch"]

    def test_default_coverage_threshold_is_80(self) -> None:
        """Verify default coverage threshold is 80%."""
        test_results = {"all_passed": True}

        # 79% should fail
        result79 = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data={"percentage": 79}
        )
        assert result79.output["prove_it"]["coverage_ok"] is False

        # 80% should pass
        result80 = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data={"percentage": 80}
        )
        assert result80.output["prove_it"]["coverage_ok"] is True

    def test_modularity_check_allows_200_loc(self) -> None:
        """Verify 200 LOC files are allowed."""
        test_results = {"all_passed": True}
        coverage_data = {"percentage": 85}
        file_stats = {"exactly_200.py": {"loc": 200}}

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            test_results=test_results,
            coverage_data=coverage_data,
            file_stats=file_stats
        )

        assert result.output["prove_it"]["modularity_ok"] is True

    def test_multiple_modularity_issues_reported(self) -> None:
        """Verify multiple modularity issues are all reported."""
        file_stats = {
            "big1.py": {"loc": 250},
            "big2.py": {"loc": 300},
            "ok.py": {"loc": 100}
        }

        result = self.skill.execute(
            self.story_id,
            self.story_data,
            file_stats=file_stats
        )

        issues = result.output["prove_it"]["modularity_issues"]
        assert len(issues) == 2
        assert any("big1.py" in issue for issue in issues)
        assert any("big2.py" in issue for issue in issues)

    def test_empty_subtasks_passes(self) -> None:
        """Verify empty subtasks list passes subtask check."""
        story_data = {**self.story_data, "subtasks": []}
        test_results = {"all_passed": True}
        coverage_data = {"percentage": 85}

        result = self.skill.execute(
            self.story_id,
            story_data,
            test_results=test_results,
            coverage_data=coverage_data
        )

        assert result.output["prove_it"]["subtasks_complete"] is True

    def test_no_test_results_assumes_passing(self) -> None:
        """Verify missing test results assumes passing (for testing)."""
        result = self.skill.execute(self.story_id, self.story_data)

        assert result.output["prove_it"]["tests_passed"] is True

    def test_includes_agent_id_in_result(self) -> None:
        """Verify result includes agent ID when provided."""
        agent_id = "claude-006"
        result = self.skill.execute(
            self.story_id,
            self.story_data,
            agent_id=agent_id
        )

        assert result.agent_id == agent_id

    def test_multiple_failures_all_reported(self) -> None:
        """Verify all failure reasons are reported."""
        test_results = {"all_passed": False}
        coverage_data = {"percentage": 50}
        file_stats = {"big.py": {"loc": 500}}
        story_data = {
            **self.story_data,
            "subtasks": [{"id": 1, "completed": False}]
        }

        result = self.skill.execute(
            self.story_id,
            story_data,
            test_results=test_results,
            coverage_data=coverage_data,
            file_stats=file_stats
        )

        assert result.status == "failed"
        assert "Tests failing" in result.failure_reason
        assert "Coverage" in result.failure_reason
        assert "Modularity" in result.failure_reason
        assert "Subtasks" in result.failure_reason

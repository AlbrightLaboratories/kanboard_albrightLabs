"""
Test SF-03: Skill gate blocks Validation→Done if prove-it/release-it incomplete
"""
import pytest
from ..skill_runner import SkillRunner
from ..skill_gate import SkillGate


class TestValidationGate:
    """Test skill gate blocks Validation to Done transitions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = SkillRunner()
        self.gate = SkillGate(self.runner)
        self.story_id = 456
        self.story_data = {
            "title": "Test Story",
            "description": "Test description",
            "acceptance_criteria": ["AC1"]
        }

    def test_blocks_without_any_validation_skills(self) -> None:
        """Verify transition blocked if no validation skills executed."""
        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "validation",
            "done"
        )

        assert can_move is False
        assert "prove-it" in incomplete
        assert "release-it" in incomplete

    def test_blocks_without_prove_it(self) -> None:
        """Verify transition blocked if prove-it not executed."""
        self.runner.execute("release-it", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "validation",
            "done"
        )

        assert can_move is False
        assert "prove-it" in incomplete
        assert "release-it" not in incomplete

    def test_blocks_without_release_it(self) -> None:
        """Verify transition blocked if release-it not executed."""
        self.runner.execute("prove-it", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "validation",
            "done"
        )

        assert can_move is False
        assert "release-it" in incomplete
        assert "prove-it" not in incomplete

    def test_allows_with_both_validation_skills_complete(self) -> None:
        """Verify transition allowed when both validation skills pass."""
        self.runner.execute("prove-it", self.story_id, self.story_data)
        self.runner.execute("release-it", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "validation",
            "done"
        )

        assert can_move is True
        assert len(incomplete) == 0

    def test_execute_validation_phase_then_transition(self) -> None:
        """Verify executing validation phase allows done transition."""
        self.runner.execute_phase("validation", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "validation",
            "done"
        )

        assert can_move is True

    def test_block_transition_returns_details(self) -> None:
        """Verify block_transition returns blocking info for validation."""
        block_info = self.gate.block_transition(
            self.story_id,
            "validation",
            "done"
        )

        assert block_info is not None
        assert block_info["blocked"] is True
        assert "prove-it" in block_info["incomplete_skills"]
        assert "release-it" in block_info["incomplete_skills"]
        assert "Cannot move to done" in block_info["message"]

    def test_get_required_skills_validation_to_done(self) -> None:
        """Verify get_required_skills returns correct list."""
        required = self.gate.get_required_skills("validation", "done")

        assert required == ["prove-it", "release-it"]

    def test_get_skill_progress_validation(self) -> None:
        """Verify get_skill_progress returns correct progress for validation."""
        # Execute one skill
        self.runner.execute("prove-it", self.story_id, self.story_data)

        progress = self.gate.get_skill_progress(self.story_id, "validation")

        assert progress["completed"] == 1
        assert progress["total"] == 2
        assert progress["percentage"] == 50.0
        assert progress["all_complete"] is False
        assert progress["skills"]["prove-it"] == "passed"
        assert progress["skills"]["release-it"] == "pending"

    def test_full_skill_progress_when_complete(self) -> None:
        """Verify 100% progress when all validation skills complete."""
        self.runner.execute("prove-it", self.story_id, self.story_data)
        self.runner.execute("release-it", self.story_id, self.story_data)

        progress = self.gate.get_skill_progress(self.story_id, "validation")

        assert progress["completed"] == 2
        assert progress["total"] == 2
        assert progress["percentage"] == 100.0
        assert progress["all_complete"] is True

    def test_handles_column_name_variations(self) -> None:
        """Verify gate handles various column name formats for validation."""
        formats = [
            ("Validation", "Done"),
            ("validation", "done"),
            ("VALIDATION", "DONE"),
        ]

        for from_col, to_col in formats:
            can_move, incomplete = self.gate.can_transition(
                self.story_id,
                from_col,
                to_col
            )
            assert can_move is False
            assert len(incomplete) == 2

    def test_other_transitions_not_blocked(self) -> None:
        """Verify non-gated transitions are allowed."""
        # Backlog to Groomed - no skill requirements
        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "backlog",
            "groomed"
        )
        assert can_move is True
        assert len(incomplete) == 0

        # Groomed to In Progress - no skill requirements
        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "groomed",
            "in_progress"
        )
        assert can_move is True

    def test_get_required_skills_no_requirements(self) -> None:
        """Verify get_required_skills returns empty for non-gated transitions."""
        required = self.gate.get_required_skills("backlog", "groomed")
        assert required == []

        required = self.gate.get_required_skills("groomed", "in_progress")
        assert required == []

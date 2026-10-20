"""
Test SF-02: Skill gate blocks In Progress→Validation if plan/prd/tdd incomplete
"""
import pytest
from ..skill_runner import SkillRunner
from ..skill_gate import SkillGate


class TestSkillGateInProgressBlock:
    """Test skill gate blocks In Progress to Validation transitions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = SkillRunner()
        self.gate = SkillGate(self.runner)
        self.story_id = 123
        self.story_data = {
            "title": "Test Story",
            "description": "Test description",
            "acceptance_criteria": ["AC1"]
        }

    def test_blocks_without_any_skills(self) -> None:
        """Verify transition blocked if no skills executed."""
        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert can_move is False
        assert "plan" in incomplete
        assert "design-a-prd" in incomplete
        assert "tdd" in incomplete

    def test_blocks_without_plan(self) -> None:
        """Verify transition blocked if plan not executed."""
        # Execute only prd and tdd
        self.runner.execute("design-a-prd", self.story_id, self.story_data)
        self.runner.execute("tdd", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert can_move is False
        assert "plan" in incomplete
        assert "design-a-prd" not in incomplete
        assert "tdd" not in incomplete

    def test_blocks_without_prd(self) -> None:
        """Verify transition blocked if design-a-prd not executed."""
        self.runner.execute("plan", self.story_id, self.story_data)
        self.runner.execute("tdd", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert can_move is False
        assert "design-a-prd" in incomplete

    def test_blocks_without_tdd(self) -> None:
        """Verify transition blocked if tdd not executed."""
        self.runner.execute("plan", self.story_id, self.story_data)
        self.runner.execute("design-a-prd", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert can_move is False
        assert "tdd" in incomplete

    def test_allows_with_all_skills_complete(self) -> None:
        """Verify transition allowed when all skills pass."""
        self.runner.execute("plan", self.story_id, self.story_data)
        self.runner.execute("design-a-prd", self.story_id, self.story_data)
        self.runner.execute("tdd", self.story_id, self.story_data)

        can_move, incomplete = self.gate.can_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert can_move is True
        assert len(incomplete) == 0

    def test_block_transition_returns_details(self) -> None:
        """Verify block_transition returns blocking info."""
        block_info = self.gate.block_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert block_info is not None
        assert block_info["blocked"] is True
        assert "plan" in block_info["incomplete_skills"]
        assert "Cannot move to validation" in block_info["message"]

    def test_block_transition_returns_none_when_allowed(self) -> None:
        """Verify block_transition returns None when transition allowed."""
        self.runner.execute_phase("in_progress", self.story_id, self.story_data)

        block_info = self.gate.block_transition(
            self.story_id,
            "in_progress",
            "validation"
        )

        assert block_info is None

    def test_handles_column_name_variations(self) -> None:
        """Verify gate handles various column name formats."""
        # Test different formats
        formats = [
            ("In Progress", "Validation"),
            ("in_progress", "validation"),
            ("in-progress", "validation"),
            ("IN_PROGRESS", "VALIDATION"),
        ]

        for from_col, to_col in formats:
            can_move, incomplete = self.gate.can_transition(
                self.story_id,
                from_col,
                to_col
            )
            assert can_move is False
            assert len(incomplete) == 3

    def test_get_required_skills_in_progress_to_validation(self) -> None:
        """Verify get_required_skills returns correct list."""
        required = self.gate.get_required_skills("in_progress", "validation")

        assert required == ["plan", "design-a-prd", "tdd"]

    def test_get_skill_progress(self) -> None:
        """Verify get_skill_progress returns correct progress info."""
        # Execute one skill
        self.runner.execute("plan", self.story_id, self.story_data)

        progress = self.gate.get_skill_progress(self.story_id, "in_progress")

        assert progress["completed"] == 1
        assert progress["total"] == 3
        assert progress["percentage"] == pytest.approx(33.33, rel=0.1)
        assert progress["all_complete"] is False
        assert progress["skills"]["plan"] == "passed"
        assert progress["skills"]["design-a-prd"] == "pending"

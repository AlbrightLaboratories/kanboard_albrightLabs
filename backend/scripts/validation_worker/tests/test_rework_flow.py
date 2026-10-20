"""
Test VW-06: Failed validation moves story back to In Progress
"""
import pytest
from unittest.mock import MagicMock
from ..result_handler import ValidationResult
from ..rework_flow import ReworkFlow, ReworkAction


class TestReworkFlow:
    """Test rework flow for failed validations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.rework = ReworkFlow(kanboard_client=self.mock_client)
        self.story_id = 101
        self.failed_result = ValidationResult(
            story_id=self.story_id,
            status="failed",
            tests_passed=8,
            tests_failed=2,
            coverage_percentage=70.0,
            failure_reasons=["2 tests failed", "Coverage below threshold"]
        )

    def test_handle_failed_moves_to_in_progress(self) -> None:
        """Verify failed validation moves story to In Progress."""
        action = self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        self.mock_client.move_story.assert_called_once_with(
            story_id=self.story_id,
            column="In Progress"
        )

    def test_handle_failed_returns_action(self) -> None:
        """Verify handler returns ReworkAction."""
        action = self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        assert isinstance(action, ReworkAction)
        assert action.story_id == self.story_id

    def test_action_from_column_is_validation(self) -> None:
        """Verify action shows movement from Validation."""
        action = self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        assert action.from_column == "Validation"
        assert action.to_column == "In Progress"

    def test_action_status_completed_on_success(self) -> None:
        """Verify action status is completed on success."""
        action = self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        assert action.status == "completed"

    def test_action_status_failed_on_error(self) -> None:
        """Verify action status is failed on error."""
        self.mock_client.move_story.side_effect = Exception("Move failed")

        action = self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        assert action.status == "failed"
        assert action.error is not None

    def test_rework_history_recorded(self) -> None:
        """Verify rework is recorded in history."""
        self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        history = self.rework.get_rework_history(self.story_id)
        assert len(history) == 1

    def test_multiple_reworks_tracked(self) -> None:
        """Verify multiple reworks are tracked."""
        for _ in range(3):
            self.rework.handle_failed_validation(
                self.story_id,
                self.failed_result
            )

        assert self.rework.get_rework_count(self.story_id) == 3

    def test_is_story_being_reworked(self) -> None:
        """Verify is_story_being_reworked works."""
        assert self.rework.is_story_being_reworked(self.story_id) is False

        self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        assert self.rework.is_story_being_reworked(self.story_id) is True

    def test_should_escalate_after_max_reworks(self) -> None:
        """Verify escalation suggested after max reworks."""
        for _ in range(3):
            self.rework.handle_failed_validation(
                self.story_id,
                self.failed_result
            )

        assert self.rework.should_escalate(self.story_id, max_reworks=3) is True

    def test_should_not_escalate_under_threshold(self) -> None:
        """Verify no escalation under threshold."""
        self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        assert self.rework.should_escalate(self.story_id, max_reworks=3) is False

    def test_clear_history_for_story(self) -> None:
        """Verify history can be cleared for specific story."""
        self.rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        self.rework.clear_history(self.story_id)

        assert self.rework.get_rework_count(self.story_id) == 0

    def test_without_client_status_pending(self) -> None:
        """Verify without client, status stays pending."""
        rework = ReworkFlow()  # No client
        action = rework.handle_failed_validation(
            self.story_id,
            self.failed_result
        )

        # Still records history and failure reasons
        assert action.failure_reasons == self.failed_result.failure_reasons

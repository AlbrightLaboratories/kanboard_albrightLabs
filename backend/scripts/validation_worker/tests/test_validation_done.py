"""
Test VW-08: Passed validation + release-it moves story to Done
"""
import pytest
from unittest.mock import MagicMock
from ..result_handler import ValidationResultHandler, ValidationResult


class TestValidationDone:
    """Test passed validation moves story to Done."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.handler = ValidationResultHandler(kanboard_client=self.mock_client)
        self.story_id = 303
        self.passed_result = ValidationResult(
            story_id=self.story_id,
            status="passed",
            tests_passed=25,
            tests_failed=0,
            coverage_percentage=92.0
        )

    def test_handle_passed_moves_to_done(self) -> None:
        """Verify passed validation moves story to Done."""
        action = self.handler.handle_passed_validation(
            self.story_id,
            self.passed_result
        )

        self.mock_client.move_story.assert_called_once_with(
            story_id=self.story_id,
            column="Done"
        )

    def test_handle_passed_returns_action_dict(self) -> None:
        """Verify handler returns action dict."""
        action = self.handler.handle_passed_validation(
            self.story_id,
            self.passed_result
        )

        assert isinstance(action, dict)
        assert action["story_id"] == self.story_id
        assert action["action"] == "move_to_done"

    def test_action_status_completed_on_success(self) -> None:
        """Verify action status is completed on success."""
        action = self.handler.handle_passed_validation(
            self.story_id,
            self.passed_result
        )

        assert action["status"] == "completed"

    def test_action_status_failed_on_error(self) -> None:
        """Verify action status is failed on error."""
        self.mock_client.move_story.side_effect = Exception("API error")

        action = self.handler.handle_passed_validation(
            self.story_id,
            self.passed_result
        )

        assert action["status"] == "failed"
        assert "error" in action

    def test_without_client_status_pending(self) -> None:
        """Verify without client status is pending."""
        handler = ValidationResultHandler()  # No client
        action = handler.handle_passed_validation(
            self.story_id,
            self.passed_result
        )

        assert action["status"] == "pending"

    def test_process_and_move_flow(self) -> None:
        """Test full flow: process result then move to Done."""
        raw_result = {
            "tests_passed": 25,
            "tests_failed": 0,
            "coverage_percentage": 92.0
        }

        # Process result
        result = self.handler.process_result(self.story_id, raw_result)
        assert result.status == "passed"

        # Move to Done
        action = self.handler.handle_passed_validation(self.story_id, result)
        assert action["status"] == "completed"

    def test_result_stored_for_retrieval(self) -> None:
        """Verify result is stored for later retrieval."""
        raw_result = {
            "tests_passed": 25,
            "tests_failed": 0,
            "coverage_percentage": 92.0
        }

        self.handler.process_result(self.story_id, raw_result)

        stored = self.handler.get_result(self.story_id)
        assert stored is not None
        assert stored.tests_passed == 25

    def test_clear_result_removes_stored(self) -> None:
        """Verify clear_result removes stored result."""
        raw_result = {
            "tests_passed": 25,
            "tests_failed": 0,
            "coverage_percentage": 92.0
        }

        self.handler.process_result(self.story_id, raw_result)
        self.handler.clear_result(self.story_id)

        assert self.handler.get_result(self.story_id) is None

    def test_high_coverage_with_skipped_still_moves_to_done(self) -> None:
        """Verify high coverage with skipped tests still passes."""
        raw_result = {
            "tests_passed": 20,
            "tests_failed": 0,
            "tests_skipped": 5,
            "coverage_percentage": 85.0
        }

        result = self.handler.process_result(self.story_id, raw_result)
        assert result.status == "passed"

        action = self.handler.handle_passed_validation(self.story_id, result)
        self.mock_client.move_story.assert_called_once()

    def test_perfect_score_moves_to_done(self) -> None:
        """Verify perfect validation moves to Done."""
        raw_result = {
            "tests_passed": 100,
            "tests_failed": 0,
            "tests_skipped": 0,
            "coverage_percentage": 100.0
        }

        result = self.handler.process_result(self.story_id, raw_result)
        action = self.handler.handle_passed_validation(self.story_id, result)

        assert action["status"] == "completed"
        self.mock_client.move_story.assert_called_once_with(
            story_id=self.story_id,
            column="Done"
        )

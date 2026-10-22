"""
Tests for comment tracking functionality.

AC-HCL-03: No duplicate processing
"""
import pytest

from ..scripts.comment_tracker import CommentTracker


class TestCommentTracker:
    """Tests for CommentTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh in-memory tracker for each test."""
        t = CommentTracker(redis_url="")  # Force in-memory
        t.clear_all()
        return t

    def test_initially_not_processed(self, tracker):
        """New comment IDs are not marked as processed."""
        assert tracker.is_processed("123") is False

    def test_mark_processed(self, tracker):
        """Marking a comment sets it as processed."""
        tracker.mark_processed("123")
        assert tracker.is_processed("123") is True

    def test_multiple_comments(self, tracker):
        """Can track multiple comments independently."""
        tracker.mark_processed("123")
        tracker.mark_processed("456")

        assert tracker.is_processed("123") is True
        assert tracker.is_processed("456") is True
        assert tracker.is_processed("789") is False

    def test_clear_all(self, tracker):
        """Clear all removes all tracked comments."""
        tracker.mark_processed("123")
        tracker.mark_processed("456")
        tracker.clear_all()

        assert tracker.is_processed("123") is False
        assert tracker.is_processed("456") is False

    def test_count(self, tracker):
        """Count returns number of tracked comments."""
        assert tracker.count == 0

        tracker.mark_processed("123")
        assert tracker.count == 1

        tracker.mark_processed("456")
        assert tracker.count == 2


class TestProcessingLock:
    """Tests for the mark_processing atomic lock."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh in-memory tracker."""
        t = CommentTracker(redis_url="")
        t.clear_all()
        return t

    def test_mark_processing_first_call(self, tracker):
        """First call to mark_processing returns True."""
        assert tracker.mark_processing("123") is True

    def test_mark_processing_duplicate(self, tracker):
        """AC-HCL-03: Second call to mark_processing returns False."""
        assert tracker.mark_processing("123") is True
        assert tracker.mark_processing("123") is False

    def test_different_comments(self, tracker):
        """Different comments can be locked independently."""
        assert tracker.mark_processing("123") is True
        assert tracker.mark_processing("456") is True
        assert tracker.mark_processing("123") is False

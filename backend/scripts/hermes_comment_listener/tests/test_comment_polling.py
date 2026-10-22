"""
Tests for comment polling functionality.

AC-HCL-01: Detect comments within 5s of posting
AC-HCL-02: @hermes mentions recognized
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ..scripts.comment_poller import (
    CommentPoller,
    Comment,
    KanboardClient,
)
from ..scripts.comment_tracker import CommentTracker


class TestCommentPolling:
    """Tests for CommentPoller.poll_once()."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Kanboard client."""
        client = MagicMock(spec=KanboardClient)
        client.get_all_projects = AsyncMock(return_value=[
            {"id": "1", "name": "Test Project"}
        ])
        client.get_all_tasks = AsyncMock(return_value=[
            {"id": "100", "title": "Test Task"}
        ])
        client.get_all_comments = AsyncMock(return_value=[])
        client.create_comment = AsyncMock(return_value=999)
        return client

    @pytest.fixture
    def tracker(self):
        """Create a fresh tracker."""
        t = CommentTracker(redis_url="")
        t.clear_all()
        return t

    @pytest.mark.asyncio
    async def test_poll_detects_hermes_mention(self, mock_client, tracker):
        """AC-HCL-02: @hermes mentions are recognized."""
        mock_client.get_all_comments = AsyncMock(return_value=[
            {
                "id": "1",
                "user_id": "2",
                "username": "testuser",
                "comment": "@hermes can you hear me",
                "date_creation": "2024-01-01 12:00:00",
            }
        ])

        poller = CommentPoller(
            kanboard_client=mock_client,
            tracker=tracker,
        )

        mentions = await poller.poll_once()

        assert len(mentions) == 1
        assert mentions[0].id == "1"
        assert "@hermes" in mentions[0].content

    @pytest.mark.asyncio
    async def test_poll_ignores_non_hermes_mentions(self, mock_client, tracker):
        """Non-@hermes mentions are ignored."""
        mock_client.get_all_comments = AsyncMock(return_value=[
            {
                "id": "1",
                "user_id": "2",
                "username": "testuser",
                "comment": "@claude help me",
                "date_creation": "2024-01-01 12:00:00",
            }
        ])

        poller = CommentPoller(
            kanboard_client=mock_client,
            tracker=tracker,
        )

        mentions = await poller.poll_once()

        assert len(mentions) == 0

    @pytest.mark.asyncio
    async def test_poll_skips_processed_comments(self, mock_client, tracker):
        """AC-HCL-03: Already processed comments are skipped."""
        mock_client.get_all_comments = AsyncMock(return_value=[
            {
                "id": "1",
                "user_id": "2",
                "username": "testuser",
                "comment": "@hermes hello",
                "date_creation": "2024-01-01 12:00:00",
            }
        ])

        # Mark as already processed
        tracker.mark_processed("1")

        poller = CommentPoller(
            kanboard_client=mock_client,
            tracker=tracker,
        )

        mentions = await poller.poll_once()

        assert len(mentions) == 0

    @pytest.mark.asyncio
    async def test_poll_multiple_comments(self, mock_client, tracker):
        """Multiple @hermes mentions are detected."""
        mock_client.get_all_comments = AsyncMock(return_value=[
            {
                "id": "1",
                "user_id": "2",
                "username": "user1",
                "comment": "@hermes first question",
                "date_creation": "2024-01-01 12:00:00",
            },
            {
                "id": "2",
                "user_id": "3",
                "username": "user2",
                "comment": "no mention here",
                "date_creation": "2024-01-01 12:01:00",
            },
            {
                "id": "3",
                "user_id": "4",
                "username": "user3",
                "comment": "@HERMES second question",  # Case insensitive
                "date_creation": "2024-01-01 12:02:00",
            },
        ])

        poller = CommentPoller(
            kanboard_client=mock_client,
            tracker=tracker,
        )

        mentions = await poller.poll_once()

        assert len(mentions) == 2
        assert mentions[0].id == "1"
        assert mentions[1].id == "3"


class TestMentionProcessing:
    """Tests for CommentPoller.process_mention()."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Kanboard client."""
        client = MagicMock(spec=KanboardClient)
        client.create_comment = AsyncMock(return_value=999)
        return client

    @pytest.fixture
    def tracker(self):
        """Create a fresh tracker."""
        t = CommentTracker(redis_url="")
        t.clear_all()
        return t

    @pytest.fixture
    def sample_comment(self):
        """Create a sample comment."""
        return Comment(
            id="1",
            task_id="100",
            user_id="2",
            username="testuser",
            content="@hermes can you hear me",
            date_creation="2024-01-01 12:00:00",
            project_id="1",
        )

    @pytest.mark.asyncio
    async def test_process_calls_hermes(self, mock_client, tracker, sample_comment):
        """Processing a mention calls Hermes."""
        from scripts.hermes_adapter.scripts import hermes_client

        # Set API key to enable Hermes
        hermes_client.HERMES_API_KEY = "test-key"

        with patch("scripts.hermes_adapter.complete") as mock_complete:
            mock_complete.return_value = MagicMock(
                reply="I can hear you!",
                failure_reason=None,
            )

            poller = CommentPoller(
                kanboard_client=mock_client,
                tracker=tracker,
            )

            result = await poller.process_mention(sample_comment)

            # Hermes should have been called
            mock_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_posts_response(self, mock_client, tracker, sample_comment):
        """Processing posts Hermes response as comment."""
        from scripts.hermes_adapter.scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        with patch("scripts.hermes_adapter.complete") as mock_complete:
            mock_complete.return_value = MagicMock(
                reply="I can hear you!",
                failure_reason=None,
            )

            poller = CommentPoller(
                kanboard_client=mock_client,
                tracker=tracker,
            )

            await poller.process_mention(sample_comment)

            # Should have posted a comment
            mock_client.create_comment.assert_called_once()
            call_args = mock_client.create_comment.call_args
            assert call_args.kwargs["task_id"] == 100
            assert "Hermes" in call_args.kwargs["content"]

    @pytest.mark.asyncio
    async def test_process_marks_as_processed(self, mock_client, tracker, sample_comment):
        """Processing marks the comment as processed."""
        from scripts.hermes_adapter.scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        with patch("scripts.hermes_adapter.complete") as mock_complete:
            mock_complete.return_value = MagicMock(
                reply="Response",
                failure_reason=None,
            )

            poller = CommentPoller(
                kanboard_client=mock_client,
                tracker=tracker,
            )

            await poller.process_mention(sample_comment)

            # Comment should be marked as processed
            assert tracker.is_processed("1") is True

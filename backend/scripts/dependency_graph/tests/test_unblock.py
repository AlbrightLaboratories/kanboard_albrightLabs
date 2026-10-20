"""
Test DG-05: When blocker completes, blocked stories become claimable.

TDD Phase: RED -> GREEN
"""
import pytest


class TestUnblock:
    """Tests for unblocking stories when blockers complete."""

    def test_completing_blocker_unblocks_story(self):
        """DG-05a: Completing blocker makes blocked story claimable."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 2 blocked by Story 1
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")
        graph.set_story_status(story_id=1, status="in_progress")

        # Initially not claimable
        assert graph.is_claimable(story_id=2) is False

        # Complete the blocker
        graph.set_story_status(story_id=1, status="done")

        # Now claimable
        assert graph.is_claimable(story_id=2) is True

    def test_get_newly_unblocked_stories(self):
        """DG-05b: get_newly_unblocked() returns stories that became claimable."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 2 and 3 blocked by Story 1
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")
        graph.add_dependency(from_story_id=1, to_story_id=3, dependency_type="blocks")
        graph.set_story_status(story_id=1, status="in_progress")

        # Complete Story 1
        unblocked = graph.complete_and_get_unblocked(story_id=1)

        assert 2 in unblocked
        assert 3 in unblocked

    def test_partial_unblock_not_claimable(self):
        """DG-05c: Story with multiple blockers stays blocked if only one completes."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 3 blocked by both 1 and 2
        graph.add_dependency(from_story_id=1, to_story_id=3, dependency_type="blocks")
        graph.add_dependency(from_story_id=2, to_story_id=3, dependency_type="blocks")
        graph.set_story_status(story_id=1, status="in_progress")
        graph.set_story_status(story_id=2, status="in_progress")

        # Complete only Story 1
        graph.set_story_status(story_id=1, status="done")

        # Still blocked by Story 2
        assert graph.is_claimable(story_id=3) is False

        # Complete Story 2
        graph.set_story_status(story_id=2, status="done")

        # Now claimable
        assert graph.is_claimable(story_id=3) is True

"""
Test DG-04: Blocked story cannot be claimed by agent.

TDD Phase: RED -> GREEN
"""
import pytest


class TestBlockedClaim:
    """Tests for blocked story claiming logic."""

    def test_blocked_story_not_claimable(self):
        """DG-04a: Story with incomplete blockers cannot be claimed."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 2 is blocked by Story 1
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")

        # Story 1 is not done
        graph.set_story_status(story_id=1, status="in_progress")

        is_claimable = graph.is_claimable(story_id=2)

        assert is_claimable is False

    def test_unblocked_story_is_claimable(self):
        """DG-04b: Story with no blockers can be claimed."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 1 has no blockers
        is_claimable = graph.is_claimable(story_id=1)

        assert is_claimable is True

    def test_story_with_complete_blockers_is_claimable(self):
        """DG-04c: Story with all blockers done can be claimed."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 2 is blocked by Story 1
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")

        # Story 1 is done
        graph.set_story_status(story_id=1, status="done")

        is_claimable = graph.is_claimable(story_id=2)

        assert is_claimable is True

    def test_get_blockers_returns_incomplete(self):
        """DG-04d: get_blockers() returns list of incomplete blocking stories."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story 3 is blocked by 1 and 2
        graph.add_dependency(from_story_id=1, to_story_id=3, dependency_type="blocks")
        graph.add_dependency(from_story_id=2, to_story_id=3, dependency_type="blocks")

        # Story 1 done, Story 2 in progress
        graph.set_story_status(story_id=1, status="done")
        graph.set_story_status(story_id=2, status="in_progress")

        blockers = graph.get_blockers(story_id=3)

        assert 1 not in blockers  # Done, not blocking
        assert 2 in blockers       # Still in progress

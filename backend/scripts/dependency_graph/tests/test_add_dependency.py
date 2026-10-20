"""
Test DG-01: add_dependency() creates blocks/blocked_by relationship.

TDD Phase: RED -> GREEN
"""
import pytest


class TestAddDependency:
    """Tests for adding dependencies between stories."""

    def test_add_blocks_dependency(self):
        """DG-01a: add_dependency() creates 'blocks' relationship."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story A blocks Story B (B depends on A)
        result = graph.add_dependency(
            from_story_id=1,
            to_story_id=2,
            dependency_type="blocks"
        )

        assert result is True
        deps = graph.get_dependencies(story_id=1)
        assert 2 in deps["blocks"]

    def test_add_blocked_by_dependency(self):
        """DG-01b: add_dependency() creates 'blocked_by' relationship."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story B is blocked by Story A
        result = graph.add_dependency(
            from_story_id=2,
            to_story_id=1,
            dependency_type="blocked_by"
        )

        assert result is True
        deps = graph.get_dependencies(story_id=2)
        assert 1 in deps["blocked_by"]

    def test_add_multiple_dependencies(self):
        """DG-01c: A story can have multiple dependencies."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story C blocks both A and B
        graph.add_dependency(from_story_id=3, to_story_id=1, dependency_type="blocks")
        graph.add_dependency(from_story_id=3, to_story_id=2, dependency_type="blocks")

        deps = graph.get_dependencies(story_id=3)
        assert 1 in deps["blocks"]
        assert 2 in deps["blocks"]
        assert len(deps["blocks"]) == 2

    def test_bidirectional_tracking(self):
        """DG-01d: Dependencies are tracked bidirectionally."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # Story A blocks Story B
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")

        # Check from A's perspective
        deps_a = graph.get_dependencies(story_id=1)
        assert 2 in deps_a["blocks"]

        # Check from B's perspective
        deps_b = graph.get_dependencies(story_id=2)
        assert 1 in deps_b["blocked_by"]

"""
Test DG-03: Circular dependency detected and rejected with error.

TDD Phase: RED -> GREEN
"""
import pytest


class TestCircularDetect:
    """Tests for circular dependency detection."""

    def test_direct_circular_rejected(self):
        """DG-03a: Direct circular dependency (A->B->A) is rejected."""
        from dependency_graph.graph import DependencyGraph
        from dependency_graph.exceptions import CircularDependencyError

        graph = DependencyGraph()

        # A blocks B
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")

        # B blocks A would create cycle
        with pytest.raises(CircularDependencyError) as exc_info:
            graph.add_dependency(from_story_id=2, to_story_id=1, dependency_type="blocks")

        assert "circular" in str(exc_info.value).lower()

    def test_indirect_circular_rejected(self):
        """DG-03b: Indirect circular dependency (A->B->C->A) is rejected."""
        from dependency_graph.graph import DependencyGraph
        from dependency_graph.exceptions import CircularDependencyError

        graph = DependencyGraph()

        # A -> B -> C
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")
        graph.add_dependency(from_story_id=2, to_story_id=3, dependency_type="blocks")

        # C -> A would create cycle
        with pytest.raises(CircularDependencyError):
            graph.add_dependency(from_story_id=3, to_story_id=1, dependency_type="blocks")

    def test_self_reference_rejected(self):
        """DG-03c: Self-reference (A->A) is rejected."""
        from dependency_graph.graph import DependencyGraph
        from dependency_graph.exceptions import CircularDependencyError

        graph = DependencyGraph()

        with pytest.raises(CircularDependencyError):
            graph.add_dependency(from_story_id=1, to_story_id=1, dependency_type="blocks")

    def test_valid_dependency_still_works(self):
        """DG-03d: Valid dependencies still work after failed circular attempt."""
        from dependency_graph.graph import DependencyGraph
        from dependency_graph.exceptions import CircularDependencyError

        graph = DependencyGraph()

        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")

        # This should fail
        try:
            graph.add_dependency(from_story_id=2, to_story_id=1, dependency_type="blocks")
        except CircularDependencyError:
            pass

        # This should still work (no cycle)
        result = graph.add_dependency(from_story_id=2, to_story_id=3, dependency_type="blocks")
        assert result is True

"""
Test DG-02: get_graph() returns full dependency tree for story.

TDD Phase: RED -> GREEN
"""
import pytest


class TestGetGraph:
    """Tests for getting full dependency tree."""

    def test_get_graph_returns_tree(self):
        """DG-02a: get_graph() returns complete dependency tree."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # A -> B -> C (chain)
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")
        graph.add_dependency(from_story_id=2, to_story_id=3, dependency_type="blocks")

        tree = graph.get_graph(story_id=1)

        assert tree["story_id"] == 1
        assert "children" in tree
        assert len(tree["children"]) == 1
        assert tree["children"][0]["story_id"] == 2

    def test_get_graph_includes_all_levels(self):
        """DG-02b: get_graph() includes all levels of dependencies."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        # A blocks B, B blocks C and D
        graph.add_dependency(from_story_id=1, to_story_id=2, dependency_type="blocks")
        graph.add_dependency(from_story_id=2, to_story_id=3, dependency_type="blocks")
        graph.add_dependency(from_story_id=2, to_story_id=4, dependency_type="blocks")

        tree = graph.get_graph(story_id=1)

        # Level 1: A
        assert tree["story_id"] == 1
        # Level 2: B
        b_node = tree["children"][0]
        assert b_node["story_id"] == 2
        # Level 3: C and D
        assert len(b_node["children"]) == 2
        child_ids = [c["story_id"] for c in b_node["children"]]
        assert 3 in child_ids
        assert 4 in child_ids

    def test_get_graph_empty_for_no_dependencies(self):
        """DG-02c: get_graph() returns leaf node for story with no deps."""
        from dependency_graph.graph import DependencyGraph

        graph = DependencyGraph()

        tree = graph.get_graph(story_id=99)

        assert tree["story_id"] == 99
        assert tree["children"] == []

"""
Test WR-05: delete_worker() removes worker and reassigns queued stories.
"""
import pytest


class TestDeleteWorker:
    """Tests for worker deletion."""

    def test_delete_removes_worker(self):
        """WR-05a: Delete removes worker from registry."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        result = registry.delete_worker(worker_id)
        assert result is not None

        worker = registry.get_worker(worker_id)
        assert worker is None

    def test_delete_returns_assigned_stories(self):
        """WR-05b: Delete returns list of assigned story IDs."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=5
        )

        # Assign some stories
        registry.assign_story(worker_id, 101)
        registry.assign_story(worker_id, 102)
        registry.assign_story(worker_id, 103)

        assigned = registry.delete_worker(worker_id)
        assert len(assigned) == 3
        assert 101 in assigned
        assert 102 in assigned
        assert 103 in assigned

    def test_delete_unknown_returns_none(self):
        """WR-05c: Delete returns None for unknown worker."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        result = registry.delete_worker("nonexistent-id")
        assert result is None

    def test_delete_empty_assignments(self):
        """WR-05d: Delete with no assignments returns empty list."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        assigned = registry.delete_worker(worker_id)
        assert assigned == []

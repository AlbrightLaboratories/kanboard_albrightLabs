"""
Test WR-04: deactivate_worker() marks worker offline, stops routing to it.
"""
import pytest


class TestDeactivateWorker:
    """Tests for worker deactivation."""

    def test_deactivate_marks_offline(self):
        """WR-04a: Deactivate marks worker as offline."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        result = registry.deactivate_worker(worker_id)
        assert result is True

        worker = registry.get_worker(worker_id)
        assert worker["status"] == "offline"

    def test_deactivate_excludes_from_routing(self):
        """WR-04b: Deactivated worker not included in available workers."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        registry.deactivate_worker(worker_id)
        available = registry.get_available_workers()
        assert len(available) == 0

    def test_deactivate_unknown_returns_false(self):
        """WR-04c: Deactivate returns False for unknown worker."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        result = registry.deactivate_worker("nonexistent-id")
        assert result is False

    def test_reactivate_worker(self):
        """WR-04d: Worker can be reactivated after deactivation."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        registry.deactivate_worker(worker_id)
        assert registry.get_worker(worker_id)["status"] == "offline"

        registry.activate_worker(worker_id)
        assert registry.get_worker(worker_id)["status"] == "active"

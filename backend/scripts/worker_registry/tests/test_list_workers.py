"""
Test WR-02: list_workers() returns all workers with current status.
"""
import pytest


class TestListWorkers:
    """Tests for listing workers."""

    def test_list_returns_all_workers(self):
        """WR-02a: List returns all registered workers."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        registry.register_worker(
            name="worker-1",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )
        registry.register_worker(
            name="worker-2",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"]
        )

        workers = registry.list_workers()
        assert len(workers) == 2
        names = [w["name"] for w in workers]
        assert "worker-1" in names
        assert "worker-2" in names

    def test_list_includes_status(self):
        """WR-02b: List includes current worker status."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        workers = registry.list_workers()
        assert len(workers) == 1
        assert workers[0]["status"] == "active"
        assert "last_heartbeat" in workers[0]

    def test_list_empty_registry(self):
        """WR-02c: List returns empty array for empty registry."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        workers = registry.list_workers()
        assert workers == []

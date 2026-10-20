"""
Test WR-01: register_worker() stores worker config, returns worker_id.
"""
import pytest


class TestRegisterWorker:
    """Tests for worker registration."""

    def test_register_returns_worker_id(self):
        """WR-01a: Registration returns a unique worker_id."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        assert worker_id is not None
        assert isinstance(worker_id, str)
        assert len(worker_id) > 0

    def test_register_stores_config(self):
        """WR-01b: Registration stores worker configuration."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation", "code_review"],
            labels=["python", "backend"]
        )

        worker = registry.get_worker(worker_id)
        assert worker is not None
        assert worker["name"] == "test-worker"
        assert worker["type"] == "vllm"
        assert worker["endpoint"] == "http://localhost:8000"
        assert "code_generation" in worker["capabilities"]
        assert "python" in worker["labels"]

    def test_register_with_optional_fields(self):
        """WR-01c: Registration accepts optional fields."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="gpu-worker",
            worker_type="vllm",
            endpoint="http://spark:8000",
            capabilities=["code_generation"],
            labels=["gpu-required"],
            gpu_required=True,
            gpu_vram_min=48,
            max_concurrent=2,
            terminal_enabled=True,
            terminal_sandbox="docker"
        )

        worker = registry.get_worker(worker_id)
        assert worker["gpu_required"] is True
        assert worker["gpu_vram_min"] == 48
        assert worker["max_concurrent"] == 2
        assert worker["terminal_enabled"] is True
        assert worker["terminal_sandbox"] == "docker"

    def test_register_sets_initial_status(self):
        """WR-01d: New worker starts with 'active' status."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        worker = registry.get_worker(worker_id)
        assert worker["status"] == "active"
        assert worker["active_stories"] == 0

    def test_register_unique_ids(self):
        """WR-01e: Each registration gets a unique ID."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        id1 = registry.register_worker(
            name="worker-1",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )
        id2 = registry.register_worker(
            name="worker-2",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"]
        )

        assert id1 != id2

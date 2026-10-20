"""
Test WR-07: 3 missed heartbeats marks worker offline.
"""
import pytest
import time


class TestMissedHeartbeat:
    """Tests for missed heartbeat handling."""

    def test_three_missed_marks_offline(self):
        """WR-07a: 3 missed heartbeats marks worker offline."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)
        monitor.set_heartbeat_interval(10)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Set heartbeat to 35 seconds ago (3+ intervals)
        registry.get_worker(worker_id)["last_heartbeat"] = time.time() - 35

        # Check workers
        marked_offline = monitor.check_workers()

        assert worker_id in marked_offline
        assert registry.get_worker(worker_id)["status"] == "offline"

    def test_two_missed_stays_active(self):
        """WR-07b: 2 missed heartbeats keeps worker active."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)
        monitor.set_heartbeat_interval(10)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Set heartbeat to 25 seconds ago (2+ intervals)
        registry.get_worker(worker_id)["last_heartbeat"] = time.time() - 25

        # Check workers
        marked_offline = monitor.check_workers()

        assert worker_id not in marked_offline
        assert registry.get_worker(worker_id)["status"] == "active"
        assert registry.get_worker(worker_id)["missed_heartbeats"] == 2

    def test_check_returns_marked_workers(self):
        """WR-07c: check_workers returns list of marked offline workers."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)
        monitor.set_heartbeat_interval(10)

        # Register multiple workers
        worker1 = registry.register_worker(
            name="worker-1",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )
        worker2 = registry.register_worker(
            name="worker-2",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"]
        )

        # Worker 1: stale (3+ intervals)
        registry.get_worker(worker1)["last_heartbeat"] = time.time() - 35
        # Worker 2: active
        registry.get_worker(worker2)["last_heartbeat"] = time.time()

        marked = monitor.check_workers()

        assert len(marked) == 1
        assert worker1 in marked
        assert worker2 not in marked

    def test_already_offline_not_rechecked(self):
        """WR-07d: Already offline workers are not re-checked."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Manually deactivate
        registry.deactivate_worker(worker_id)

        # Check workers
        marked = monitor.check_workers()

        # Should not be in the newly marked list
        assert worker_id not in marked

    def test_get_worker_health(self):
        """WR-07e: get_worker_health returns detailed health info."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)
        monitor.set_heartbeat_interval(10)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=5
        )

        # Set some missed heartbeats
        registry.get_worker(worker_id)["last_heartbeat"] = time.time() - 15
        registry.get_worker(worker_id)["missed_heartbeats"] = 1

        health = monitor.get_worker_health(worker_id)

        assert health["worker_id"] == worker_id
        assert health["status"] == "active"
        assert health["missed_heartbeats"] == 1
        assert health["max_concurrent"] == 5
        assert health["healthy"] is True  # Only 1 missed, < 3

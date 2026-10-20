"""
Test WR-06: Heartbeat updates last_heartbeat, marks worker active.
"""
import pytest
import time


class TestHeartbeat:
    """Tests for worker heartbeat."""

    def test_heartbeat_updates_timestamp(self):
        """WR-06a: Heartbeat updates last_heartbeat timestamp."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Set old timestamp
        registry.get_worker(worker_id)["last_heartbeat"] = time.time() - 100

        # Send heartbeat
        result = monitor.heartbeat(worker_id)
        assert result is not None

        worker = registry.get_worker(worker_id)
        assert time.time() - worker["last_heartbeat"] < 1

    def test_heartbeat_returns_status(self):
        """WR-06b: Heartbeat returns worker status info."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        result = monitor.heartbeat(worker_id)
        assert result["status"] == "active"
        assert "active_stories" in result
        assert "last_heartbeat" in result

    def test_heartbeat_resets_missed_count(self):
        """WR-06c: Heartbeat resets missed heartbeat count."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Simulate missed heartbeats
        registry.get_worker(worker_id)["missed_heartbeats"] = 2

        # Send heartbeat
        monitor.heartbeat(worker_id)

        worker = registry.get_worker(worker_id)
        assert worker["missed_heartbeats"] == 0

    def test_heartbeat_reactivates_offline_worker(self):
        """WR-06d: Heartbeat reactivates an offline worker."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)

        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Mark offline
        registry.deactivate_worker(worker_id)
        assert registry.get_worker(worker_id)["status"] == "offline"

        # Send heartbeat
        monitor.heartbeat(worker_id)

        worker = registry.get_worker(worker_id)
        assert worker["status"] == "active"

    def test_heartbeat_unknown_worker_returns_none(self):
        """WR-06e: Heartbeat for unknown worker returns None."""
        from worker_registry import WorkerRegistry, HealthMonitor

        registry = WorkerRegistry()
        monitor = HealthMonitor(registry)

        result = monitor.heartbeat("nonexistent-id")
        assert result is None

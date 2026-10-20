"""
Test WR-03: update_worker() modifies labels/config without losing state.
"""
import pytest


class TestUpdateWorker:
    """Tests for updating workers."""

    def test_update_modifies_labels(self):
        """WR-03a: Update modifies worker labels."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"]
        )

        result = registry.update_worker(worker_id, labels=["python", "backend", "gpu-required"])
        assert result is True

        worker = registry.get_worker(worker_id)
        assert "gpu-required" in worker["labels"]
        assert len(worker["labels"]) == 3

    def test_update_preserves_state(self):
        """WR-03b: Update preserves worker state (active_stories, status)."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        # Assign a story to change state
        registry.assign_story(worker_id, 123)
        original_active = registry.get_worker(worker_id)["active_stories"]

        # Update labels
        registry.update_worker(worker_id, labels=["new-label"])

        worker = registry.get_worker(worker_id)
        assert worker["active_stories"] == original_active
        assert worker["status"] == "active"

    def test_update_modifies_config(self):
        """WR-03c: Update modifies configuration fields."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        worker_id = registry.register_worker(
            name="test-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=1
        )

        registry.update_worker(worker_id, max_concurrent=5, gpu_vram_min=32)

        worker = registry.get_worker(worker_id)
        assert worker["max_concurrent"] == 5
        assert worker["gpu_vram_min"] == 32

    def test_update_unknown_worker_returns_false(self):
        """WR-03d: Update returns False for unknown worker."""
        from worker_registry import WorkerRegistry

        registry = WorkerRegistry()
        result = registry.update_worker("nonexistent-id", labels=["test"])
        assert result is False

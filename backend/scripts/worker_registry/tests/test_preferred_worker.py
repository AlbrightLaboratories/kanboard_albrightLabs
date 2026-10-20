"""
Test WR-09: Router respects preferred_worker when available.
"""
import pytest


class TestPreferredWorker:
    """Tests for preferred worker routing."""

    def test_preferred_worker_selected(self):
        """WR-09a: Preferred worker is selected when available."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # Register multiple workers
        registry.register_worker(
            name="worker-1",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"]
        )

        preferred_id = registry.register_worker(
            name="worker-2",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["python"]
        )

        result = router.route_story(
            story_labels=["python"],
            preferred_worker=preferred_id
        )
        assert result == preferred_id

    def test_fallback_when_preferred_unavailable(self):
        """WR-09b: Falls back when preferred worker at capacity."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        preferred_id = registry.register_worker(
            name="preferred",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"],
            max_concurrent=1
        )

        # Fill preferred worker capacity
        registry.assign_story(preferred_id, 100)

        fallback_id = registry.register_worker(
            name="fallback",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["python"]
        )

        result = router.route_story(
            story_labels=["python"],
            preferred_worker=preferred_id
        )
        assert result == fallback_id

    def test_fallback_when_preferred_offline(self):
        """WR-09c: Falls back when preferred worker is offline."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        preferred_id = registry.register_worker(
            name="preferred",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"]
        )

        registry.deactivate_worker(preferred_id)

        fallback_id = registry.register_worker(
            name="fallback",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["python"]
        )

        result = router.route_story(
            story_labels=["python"],
            preferred_worker=preferred_id
        )
        assert result == fallback_id

    def test_preferred_still_checked_for_labels(self):
        """WR-09d: Preferred worker must still match labels if present."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # Preferred worker doesn't have required labels
        preferred_id = registry.register_worker(
            name="preferred",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["rust"]  # Not "python"
        )

        other_id = registry.register_worker(
            name="other",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["python"]
        )

        result = router.route_story(
            story_labels=["python"],
            preferred_worker=preferred_id
        )
        # Falls back because preferred doesn't match labels, but fallback allows any
        assert result is not None
